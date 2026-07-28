import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).parents[1] / "scripts" / "search_knowledge.py"


def load_module():
    spec = importlib.util.spec_from_file_location("search_knowledge", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class SearchKnowledgeTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.cards_path = Path(self.tempdir.name) / "cards.jsonl"
        cards = [
            {
                "card_id": "YT-KNOW-000001",
                "topic_path": ["대본", "후킹"],
                "question_variants": ["쇼츠 첫 장면 후킹은 어떻게 만드는가?"],
                "canonical_answer": "첫 장면에서 결과나 갈등을 먼저 보여준다.",
                "authority_tier": "A",
                "evidence": [{"author": "마라하기", "date": "2026-06-04", "line_start": 10, "line_end": 11}],
                "conflict_ids": [],
                "temporal_status": "STABLE",
                "confidence": "HIGH",
            },
            {
                "card_id": "YT-KNOW-000002",
                "topic_path": ["편집", "자막"],
                "question_variants": ["자막 길이는 어떻게 정하는가?"],
                "canonical_answer": "한눈에 읽히는 길이로 줄인다.",
                "authority_tier": "EXPERIENCE",
                "evidence": [{"author": "P001", "date": "2026-06-05", "line_start": 20, "line_end": 20}],
                "conflict_ids": [],
                "temporal_status": "STABLE",
                "confidence": "MEDIUM",
            },
        ]
        with self.cards_path.open("w", encoding="utf-8") as handle:
            for card in cards:
                handle.write(json.dumps(card, ensure_ascii=False) + "\n")

    def tearDown(self):
        self.tempdir.cleanup()

    def test_exact_question_match_ranks_first(self):
        module = load_module()
        payload = module.search_cards("쇼츠 첫 장면 후킹", self.cards_path, limit=2)
        self.assertEqual(payload["results"][0]["card_id"], "YT-KNOW-000001")
        self.assertGreater(payload["results"][0]["score"], 0)

    def test_korean_topic_token_finds_editing_card(self):
        module = load_module()
        payload = module.search_cards("편집 자막", self.cards_path)
        self.assertEqual(payload["results"][0]["card_id"], "YT-KNOW-000002")

    def test_category_filter_excludes_other_topics(self):
        module = load_module()
        payload = module.search_cards("어떻게", self.cards_path, category="편집")
        self.assertEqual([item["card_id"] for item in payload["results"]], ["YT-KNOW-000002"])

    def test_empty_query_is_rejected(self):
        module = load_module()
        with self.assertRaisesRegex(ValueError, "query must not be empty"):
            module.search_cards("   ", self.cards_path)

    def test_malformed_jsonl_is_skipped_and_reported(self):
        module = load_module()
        with self.cards_path.open("a", encoding="utf-8") as handle:
            handle.write("{malformed}\n")
        payload = module.search_cards("후킹", self.cards_path)
        self.assertEqual(payload["skipped_malformed"], 1)
        self.assertEqual(payload["results"][0]["card_id"], "YT-KNOW-000001")

    def test_missing_cards_file_fails(self):
        module = load_module()
        missing = Path(self.tempdir.name) / "missing.jsonl"
        with self.assertRaises(FileNotFoundError):
            module.search_cards("후킹", missing)

    def test_search_card_files_combines_multiple_corpora(self):
        module = load_module()
        lecture_path = Path(self.tempdir.name) / "lecture_cards.jsonl"
        lecture_card = {
            "card_id": "YT-MARA-001-001",
            "topic_path": ["채널 운영", "초기 세팅"],
            "question_variants": ["초기 채널은 어떻게 세팅하는가?"],
            "canonical_answer": "교본의 초기 채널 세팅 공식을 따른다.",
            "authority_tier": "MARA_CANONICAL",
            "evidence": [{"source_title": "일반반 1강", "page_start": 10, "page_end": 12}],
            "conflict_ids": [],
            "temporal_status": "STABLE",
            "confidence": "HIGH",
        }
        lecture_path.write_text(json.dumps(lecture_card, ensure_ascii=False) + "\n", encoding="utf-8")

        payload = module.search_card_files("초기 채널 세팅", [self.cards_path, lecture_path])

        self.assertEqual(payload["results"][0]["card_id"], "YT-MARA-001-001")
        self.assertEqual(payload["corpora_searched"], 2)

    def test_mara_canonical_ranks_above_a_when_relevance_ties(self):
        module = load_module()
        cards = [
            {
                "card_id": "AAA-CHAT",
                "topic_path": ["소재"],
                "question_variants": ["소재는 어떻게 고르는가?"],
                "canonical_answer": "채팅 답변",
                "authority_tier": "A",
            },
            {
                "card_id": "ZZZ-CANONICAL",
                "topic_path": ["소재"],
                "question_variants": ["소재는 어떻게 고르는가?"],
                "canonical_answer": "교본 답변",
                "authority_tier": "MARA_CANONICAL",
                "evidence": [{"source_title": "일반반 2강", "page_start": 22, "page_end": 22}],
            },
        ]
        self.cards_path.write_text(
            "".join(json.dumps(card, ensure_ascii=False) + "\n" for card in cards),
            encoding="utf-8",
        )

        payload = module.search_cards("소재는 어떻게 고르는가", self.cards_path, limit=2)

        self.assertEqual(payload["results"][0]["card_id"], "ZZZ-CANONICAL")
        self.assertEqual(payload["results"][0]["evidence"][0]["page_start"], 22)

    def test_search_card_files_sums_malformed_lines(self):
        module = load_module()
        second_path = Path(self.tempdir.name) / "lecture_cards.jsonl"
        second_path.write_text("{broken}\n", encoding="utf-8")

        payload = module.search_card_files("후킹", [self.cards_path, second_path])

        self.assertEqual(payload["skipped_malformed"], 1)

    def test_explicit_single_cards_path_remains_supported(self):
        module = load_module()
        payload = module.search_cards("후킹", self.cards_path)
        self.assertEqual(payload["results"][0]["card_id"], "YT-KNOW-000001")


if __name__ == "__main__":
    unittest.main()

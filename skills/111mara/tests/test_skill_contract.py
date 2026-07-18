import json
import unittest
from pathlib import Path


ROOT = Path(__file__).parents[1]
SKILL = ROOT / "SKILL.md"
LECTURE_CARDS = ROOT / "references" / "lecture_cards.jsonl"
SENIOR_LONGFORM = ROOT / "references" / "senior-longform-momcare.md"


class SkillContractTests(unittest.TestCase):
    def test_skill_declares_canonical_curriculum_priority(self):
        text = SKILL.read_text(encoding="utf-8")
        self.assertIn("MARA_CANONICAL", text)
        self.assertIn("lecture_cards.jsonl", text)
        self.assertIn("페이지", text)

    def test_lecture_cards_are_valid_and_unique(self):
        cards = [json.loads(line) for line in LECTURE_CARDS.read_text(encoding="utf-8").splitlines() if line]
        ids = [card["card_id"] for card in cards]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertGreaterEqual(len(cards), 20)
        for card in cards:
            self.assertEqual(card["authority_tier"], "MARA_CANONICAL")
            self.assertTrue(card["evidence"])
            for evidence in card["evidence"]:
                self.assertIn("page_start", evidence)
                self.assertIn("page_end", evidence)
                self.assertEqual(len(evidence["source_sha256"]), 64)

    def test_skill_routes_senior_longform_and_external_review(self):
        text = SKILL.read_text(encoding="utf-8")
        required = [
            "시니어롱폼",
            "시니어 롱폼",
            "맘케어",
            "senior-longform-momcare.md",
            "PREP",
            "댄 하먼",
            "기승전결",
            "NEEDS_EVIDENCE",
            "source_id",
            "segment_id",
            "채택/부분채택/거절",
            "사용자 승인",
        ]
        for token in required:
            with self.subTest(token=token):
                self.assertIn(token, text)

    def test_senior_longform_reference_covers_verified_course(self):
        self.assertTrue(SENIOR_LONGFORM.exists())
        text = SENIOR_LONGFORM.read_text(encoding="utf-8")
        required = [
            "PASS_WITH_DOCUMENTED_LIMITS",
            "마음·철학",
            "경제·복지",
            "시사·뉴스",
            "역사",
            "건강",
            "‘이’ 지시어",
            "부정어",
            "감정",
            "이유",
            "발작버튼",
            "PREP",
            "댄 하먼",
            "기승전결",
            "원출처",
            "572",
            "13개 탭",
            "44개",
            "29/29",
        ]
        for token in required:
            with self.subTest(token=token):
                self.assertIn(token, text)
        for index in range(1, 30):
            with self.subTest(qna=index):
                self.assertIn(f"q{index:02d}", text)

    def test_senior_longform_cards_are_searchable(self):
        cards = [json.loads(line) for line in LECTURE_CARDS.read_text(encoding="utf-8").splitlines() if line]
        ids = {card["card_id"] for card in cards}
        expected = {f"YT-MARA-005-{index:03d}" for index in range(1, 7)}
        self.assertTrue(expected.issubset(ids))


if __name__ == "__main__":
    unittest.main()

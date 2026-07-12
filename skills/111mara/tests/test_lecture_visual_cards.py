import json
import unittest
from pathlib import Path


ROOT = Path(__file__).parents[1]
LECTURE_CARDS = ROOT / "references" / "lecture_cards.jsonl"


def load_cards():
    cards = [
        json.loads(line)
        for line in LECTURE_CARDS.read_text(encoding="utf-8").splitlines()
        if line
    ]
    return {card["card_id"]: card for card in cards}


class LectureVisualCardTests(unittest.TestCase):
    def setUp(self):
        self.cards = load_cards()

    def test_low_view_benchmark_keeps_visual_example_and_conditions(self):
        card = self.cards["YT-MARA-002-002"]
        rendered = json.dumps(card, ensure_ascii=False)
        self.assertIn("36만", rendered)
        self.assertIn("230만", rendered)
        self.assertIn("5만", rendered)
        self.assertIn("3주", rendered)

    def test_gadanya_preserves_four_visual_script_roles(self):
        card = self.cards["YT-MARA-002-006"]
        answer = card["canonical_answer"]
        for role in ("벤치 구간", "TTS", "원본 대화", "자막 전용"):
            self.assertIn(role, answer)

    def test_analytics_examples_are_not_universal_thresholds(self):
        card = self.cards["YT-MARA-004-001"]
        rendered = json.dumps(card, ensure_ascii=False)
        self.assertIn("88%", rendered)
        self.assertIn("128.8%", rendered)
        self.assertIn("보편 기준", rendered)

    def test_view_table_preserves_missing_ten_to_thirty_thousand_band(self):
        card = self.cards["YT-MARA-004-002"]
        rendered = json.dumps(card, ensure_ascii=False)
        self.assertIn("100 미만", rendered)
        self.assertIn("100~1천 미만", rendered)
        self.assertIn("1천~1만 미만", rendered)
        self.assertIn("1만~3만", rendered)
        self.assertIn("제시하지", rendered)
        self.assertIn("3만 이상", rendered)

    def test_hybrid_card_does_not_claim_unshown_conversion_loop(self):
        card = self.cards["YT-MARA-004-004"]
        answer = card["canonical_answer"]
        self.assertNotIn("롱폼을 다시 숏폼 소재로 유통", answer)
        self.assertIn("구체적인 양방향 전환 순서", answer)
        self.assertIn("확인되지 않는다", answer)

    def test_ai_drafting_tool_card_is_risk_labeled(self):
        card = self.cards["YT-MARA-004-005"]
        rendered = json.dumps(card, ensure_ascii=False)
        self.assertIn("GPT", rendered)
        self.assertIn("Gemini", rendered)
        self.assertIn("권리", rendered)
        self.assertEqual(card["temporal_status"], "NEEDS_LIVE_CHECK")


if __name__ == "__main__":
    unittest.main()

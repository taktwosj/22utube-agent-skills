import json
import unittest
from pathlib import Path


ROOT = Path(__file__).parents[1]
SKILL = ROOT / "SKILL.md"
LECTURE_CARDS = ROOT / "references" / "lecture_cards.jsonl"


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


if __name__ == "__main__":
    unittest.main()

import json
import unittest
from pathlib import Path


REPO = Path(__file__).parents[1]
SKILL_ROOT = REPO / "skills" / "111mara"


class MaraSkillContractTests(unittest.TestCase):
    def test_manifest_manages_111mara_for_all_runtimes(self):
        manifest = json.loads(
            (REPO / "manifests" / "skill-set.json").read_text(encoding="utf-8")
        )
        entries = {entry["name"]: entry for entry in manifest["skills"]}
        self.assertIn("111mara", entries)
        self.assertTrue(entries["111mara"]["enabled"])
        self.assertEqual(
            set(entries["111mara"]["targets"]),
            {"codex", "claude", "hermes"},
        )

    def test_skill_is_self_contained_and_offline_only(self):
        skill_text = (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("MARA_CANONICAL", skill_text)
        self.assertIn("lecture_cards.jsonl", skill_text)
        self.assertIn("외부 검색은 하지 않음", skill_text)

    def test_visual_lecture_cards_are_packaged(self):
        path = SKILL_ROOT / "references" / "lecture_cards.jsonl"
        cards = [
            json.loads(line)
            for line in path.read_text(encoding="utf-8").splitlines()
            if line
        ]
        ids = {card["card_id"] for card in cards}
        self.assertGreaterEqual(len(cards), 28)
        for required in (
            "YT-MARA-002-002",
            "YT-MARA-002-006",
            "YT-MARA-004-002",
            "YT-MARA-004-004",
            "YT-MARA-004-005",
        ):
            self.assertIn(required, ids)

    def test_runtime_garbage_is_not_packaged(self):
        self.assertFalse(any(SKILL_ROOT.rglob("__pycache__")))
        self.assertFalse(any(SKILL_ROOT.rglob("*.pyc")))


if __name__ == "__main__":
    unittest.main()

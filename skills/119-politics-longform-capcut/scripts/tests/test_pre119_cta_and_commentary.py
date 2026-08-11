from __future__ import annotations

import sys
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1]
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import compile_pre119_episode_cards as compiler


class Pre119CtaAndCommentaryTests(unittest.TestCase):
    def test_commentary_lines_compile_to_lower_text(self) -> None:
        card = {
            "card_id": "C001",
            "lower_mode": "COMMENTARY_2LINE",
            "lower_line1": "정책 방향은 같았지만",
            "lower_line2": "시행 준비는 충분했나",
        }
        compiler.normalize_lower_text(card)
        self.assertEqual(card["lower_text"], "정책 방향은 같았지만\n시행 준비는 충분했나")

    def test_mixed_lower_plan_accepts_each_supported_mode(self) -> None:
        cards = [
            {"card_id": "C001", "card_type": "SOURCE_VIDEO", "lower_mode": "SRT"},
            {"card_id": "C002", "card_type": "SOURCE_VIDEO", "lower_mode": "COMMENTARY_2LINE"},
            {"card_id": "C003", "card_type": "SOURCE_VIDEO", "lower_mode": "NONE"},
        ]
        compiler.validate_plan_bindings(
            {"between_narration": "NO", "between_image": "NO", "lower_mode": "MIXED"},
            cards,
        )

    def test_uniform_cta_off_passes(self) -> None:
        cards = [{"card_id": "C001"}, {"card_id": "C002", "cta_like_subscribe": "OFF"}]
        policy = compiler.normalize_cta_policy(cards, {"cta_like_subscribe": "OFF"})
        self.assertEqual(policy, "OFF")
        self.assertEqual({card["cta_like_subscribe"] for card in cards}, {"OFF"})

    def test_mixed_cta_is_blocked(self) -> None:
        cards = [
            {"card_id": "C001", "cta_like_subscribe": "ON"},
            {"card_id": "C002", "cta_like_subscribe": "OFF"},
        ]
        with self.assertRaisesRegex(RuntimeError, "CTA_POLICY_MIXED_UNSUPPORTED"):
            compiler.normalize_cta_policy(cards, {})


if __name__ == "__main__":
    unittest.main()

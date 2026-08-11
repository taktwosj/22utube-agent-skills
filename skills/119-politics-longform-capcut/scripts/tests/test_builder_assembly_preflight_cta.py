from __future__ import annotations

import sys
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1]
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import build_politics_card_project as builder


class BuilderAssemblyPreflightCtaTests(unittest.TestCase):
    def source_card(self, card_id: str, start: int, *, cta: str | None = None) -> dict[str, object]:
        card: dict[str, object] = {
            "card_id": card_id,
            "card_type": "SOURCE_VIDEO",
            "target_start_us": start,
            "target_duration_us": 1_000_000,
            "lower_mode": "NONE",
        }
        if cta is not None:
            card["cta_like_subscribe"] = cta
        return card

    def test_global_cta_off_propagates_to_cards(self) -> None:
        cards, _ = builder.normalize_cards(
            {
                "cta_like_subscribe": "OFF",
                "cards": [self.source_card("C001", 0), self.source_card("C002", 1_000_000)],
            }
        )
        self.assertEqual({card["cta_like_subscribe"] for card in cards}, {"OFF"})

    def test_mixed_card_cta_is_blocked(self) -> None:
        with self.assertRaisesRegex(RuntimeError, "CTA_POLICY_MIXED_UNSUPPORTED"):
            builder.normalize_cards(
                {
                    "cta_like_subscribe": "ON",
                    "cards": [
                        self.source_card("C001", 0, cta="ON"),
                        self.source_card("C002", 1_000_000, cta="OFF"),
                    ],
                }
            )

    def test_presentation_contract_allows_no_cta_when_off(self) -> None:
        document = {"materials": {"texts": []}, "tracks": []}
        cards = [
            {
                "card_id": "C001",
                "card_type": "INTRO",
                "lower_mode": "NONE",
                "cta_like_subscribe": "OFF",
            }
        ]
        contract = builder.capture_presentation_contract(document, cards)
        self.assertIsNone(contract["cta_hud"])


if __name__ == "__main__":
    unittest.main()

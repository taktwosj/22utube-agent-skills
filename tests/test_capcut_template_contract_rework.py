"""RW-P02-01 regression tests.

Codex blocker: shrt white media path fields contain numeric 0 and
material_classifications contains an empty key.

Required fix: normalize path/source to string or null and use a stable
slot_id-based classification record when no path exists.
"""

from __future__ import annotations

import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTRACTS_DIR = ROOT / "manifests" / "capcut-template-contracts"

SHRT_WHITE = CONTRACTS_DIR / "shrt_white_base_v1.json"
JUNGCHILONG = CONTRACTS_DIR / "jungchilong_base_v3_intro15.json"
SHRTJUNGCHI = CONTRACTS_DIR / "shrtjungchi_base_v1.json"


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


class ShrtWhiteMediaPathNormalizationTests(unittest.TestCase):
    def test_no_numeric_zero_in_file_path_or_media_fingerprint(self):
        """file_path and media_fingerprint must never carry a raw numeric 0.
        They must be either a non-empty string or null."""
        for contract_path in (SHRT_WHITE, JUNGCHILONG, SHRTJUNGCHI):
            contract = _load(contract_path)
            for slot in contract["slots"]:
                fp = slot.get("file_path")
                mf = slot.get("media_fingerprint")
                # Reject raw integer 0 (or any non-string, non-null value).
                for field_name, value in (("file_path", fp), ("media_fingerprint", mf)):
                    if value is None:
                        continue
                    self.assertIsInstance(
                        value,
                        str,
                        f"{contract_path.name} slot {slot.get('slot_id')} "
                        f"{field_name} must be str or null, got "
                        f"{type(value).__name__}={value!r}",
                    )

    def test_material_classifications_keys_are_non_empty_strings(self):
        """Classification keys must be non-empty strings, OR a structured
        slot-id-keyed record must be used. No empty key or numeric key."""
        for contract_path in (SHRT_WHITE, JUNGCHILONG, SHRTJUNGCHI):
            contract = _load(contract_path)
            classifications = contract.get("material_classifications", {})
            for key in classifications.keys():
                self.assertIsInstance(
                    key,
                    str,
                    f"{contract_path.name} classification key must be str, "
                    f"got {type(key).__name__}={key!r}",
                )
                self.assertTrue(
                    key.strip(),
                    f"{contract_path.name} classification key must be non-empty",
                )

    def test_per_slot_classification_record_exists(self):
        """Every slot must carry an in-slot classification so that slots
        without a file_path can still be classified deterministically."""
        for contract_path in (SHRT_WHITE, JUNGCHILONG, SHRTJUNGCHI):
            contract = _load(contract_path)
            for slot in contract["slots"]:
                self.assertIn(
                    "classification",
                    slot,
                    f"{contract_path.name} slot {slot.get('slot_id')} "
                    f"missing classification field",
                )
                self.assertIn(
                    slot["classification"],
                    ("FIXED_REUSABLE", "REPLACE_REQUIRED", "REFERENCE_ONLY", "FORBIDDEN_IN_OUTPUT"),
                    f"{contract_path.name} slot {slot.get('slot_id')} "
                    f"invalid classification {slot['classification']!r}",
                )


if __name__ == "__main__":
    unittest.main()

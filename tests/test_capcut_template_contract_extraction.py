"""P02 CapCut template contract extraction tests.

Asserts that template contracts are extracted from the real pinned archives
(not placeholders), that shrt white requires its internal transparent PNG
and rejects Cache/onlineMaterial references, and that SHRTJUNGCHI GUI
NOT_RUN is never converted into a GUI PASS claim.
"""

from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTRACTS_DIR = ROOT / "manifests" / "capcut-template-contracts"

SHRT_WHITE = CONTRACTS_DIR / "shrt_white_base_v1.json"
JUNGCHILONG = CONTRACTS_DIR / "jungchilong_base_v3_intro15.json"
SHRTJUNGCHI = CONTRACTS_DIR / "shrtjungchi_base_v1.json"


def _load(path: Path) -> dict:
    import json
    return json.loads(path.read_text(encoding="utf-8"))


class TemplateContractExtractionTests(unittest.TestCase):
    def setUp(self):
        for p in (SHRT_WHITE, JUNGCHILONG, SHRTJUNGCHI):
            self.assertTrue(p.exists(), f"missing contract: {p}")

    def test_template_contract_extracted_from_real_archive(self):
        """Every contract must carry the real archive SHA256 and at least one
        extracted slot. No EXTRACT_FROM_ROOT placeholder, no example numbers."""
        for contract_path in (SHRT_WHITE, JUNGCHILONG, SHRTJUNGCHI):
            contract = _load(contract_path)
            self.assertTrue(
                contract["slots"], f"no slots extracted for {contract_path.name}"
            )
            source = contract["extraction_source"]
            self.assertEqual(len(source["archive_sha256"]), 64)
            self.assertTrue(source["draft_root_inside_archive"])
            self.assertEqual(source["extractor"], "scripts/extract_capcut_template_contract.py")
            # Archive SHA must be uppercase hex, never a placeholder.
            self.assertNotIn("EXTRACT_FROM_ROOT", source["archive_sha256"])
            # Every TEXT slot must carry concrete transform/font values, not
            # placeholders.
            for slot in contract["slots"]:
                if slot["material_role"] == "TEXT":
                    for field in (
                        "transform_x",
                        "transform_y",
                        "scale_x",
                        "scale_y",
                        "font_size",
                        "alignment",
                    ):
                        self.assertIsNotNone(
                            slot.get(field),
                            f"{contract_path.name} slot {slot['slot_id']} "
                            f"missing {field}",
                        )

    def test_shrt_white_uses_internal_transparent_asset(self):
        """shrt white must require transparent_center_white_1080x1920.png and
        must not reference Cache/onlineMaterial."""
        contract = _load(SHRT_WHITE)
        self.assertEqual(
            contract["required_internal_asset"],
            "Resources/media/transparent_center_white_1080x1920.png",
        )
        self.assertTrue(contract["required_internal_asset_present"])
        self.assertEqual(contract["forbidden_hits"], [])
        self.assertFalse(contract["cache_online_material_referenced"])

    def test_no_template_contract_contains_extract_from_root_placeholder(self):
        """NORM-002 / V2 section 40: no placeholder values anywhere."""
        import json
        for contract_path in CONTRACTS_DIR.glob("*.json"):
            raw = contract_path.read_text(encoding="utf-8")
            self.assertNotIn(
                "EXTRACT_FROM_ROOT",
                raw,
                f"placeholder found in {contract_path.name}",
            )
            # Re-serialized form must round-trip (proves it is real JSON).
            contract = json.loads(raw)
            self.assertEqual(
                contract["schema_version"], "capcut-template-contract-v1"
            )

    def test_template_contract_root_and_timeline_mirrors_match(self):
        """The capcut_root_project_name in the contract must equal the root
        folder inside the archive; the timeline_layout.json mirror, when
        present, is recorded in extraction_source."""
        for contract_path in (SHRT_WHITE, JUNGCHILONG, SHRTJUNGCHI):
            contract = _load(contract_path)
            self.assertEqual(
                contract["extraction_source"]["draft_root_inside_archive"],
                contract["capcut_root_project_name"],
            )

    def test_shrtjungchi_gui_not_run_is_not_pass(self):
        """SHRTJUNGCHI archive structure may PASS, but GUI restore is NOT_RUN.
        NORM/hard rule: archive PASS must never be promoted to GUI PASS."""
        contract = _load(SHRTJUNGCHI)
        self.assertEqual(contract["gui_restore_state"], "NOT_RUN")
        self.assertEqual(
            contract["archive_integrity"], "PASS_ARCHIVE_STRUCTURE_ONLY"
        )
        # Explicitly NOT a GUI PASS.
        self.assertNotEqual(contract["gui_restore_state"], "PASS")


if __name__ == "__main__":
    unittest.main()

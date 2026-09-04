from __future__ import annotations

import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class CurrentProductionRootsContractTests(unittest.TestCase):
    def test_manifest_names_exactly_three_current_roots(self) -> None:
        manifest = json.loads(
            (ROOT / "manifests" / "capcut-template-set.json").read_text(encoding="utf-8")
        )
        roots = {item["id"]: item for item in manifest["production_roots"]}
        self.assertEqual(
            set(roots),
            {"001_white_v3", "001_black_dialogue_v1", "119_v8_manual_overlay_65"},
        )
        self.assertTrue(all(item["status"] == "ACTIVE" for item in roots.values()))
        self.assertEqual(roots["001_white_v3"]["template_profile"], "shrt_white_base_v3")
        self.assertEqual(
            roots["001_black_dialogue_v1"]["template_profile"],
            "shrt_black_headline_dialogue_v1",
        )
        self.assertEqual(
            roots["119_v8_manual_overlay_65"]["root_profile"],
            "V8_MANUAL_OVERLAY_65",
        )
        self.assertFalse(
            manifest["legacy_compatibility"]["jungchilong_v7_pointer"][
                "selected_by_current_production"
            ]
        )

    def test_001_contract_preserves_verified_proper_nouns_without_literal_copying(self) -> None:
        taxonomy = (
            ROOT
            / "skills"
            / "001short-production-agent"
            / "references"
            / "shorts-structure-taxonomy.md"
        ).read_text(encoding="utf-8")
        for marker in (
            "IDENTITY_ANCHOR_REQUIRED_WHEN_VERIFIED",
            "PROPER_NOUN_SUBSTITUTION_FORBIDDEN",
            "CREATIVE_DIALOGUE_ALLOWED",
            "HIGH_RISK_FALSE_CLAIM_FORBIDDEN",
            "STRUCTURAL_REWRITE_REQUIRED",
        ):
            self.assertIn(marker, taxonomy)

    def test_119_runtime_contract_routes_new_work_to_v8_only(self) -> None:
        skill_root = ROOT / "skills" / "119-politics-longform-capcut"
        skill = (skill_root / "SKILL.md").read_text(encoding="utf-8")
        assembly = (skill_root / "references" / "capcut-assembly.md").read_text(
            encoding="utf-8"
        )
        legacy = (skill_root / "references" / "root-bundle-contract.md").read_text(
            encoding="utf-8"
        )
        for text in (skill, assembly, legacy):
            self.assertIn("LEGACY_V7_ROLLBACK_ONLY", text)
        self.assertIn("V8_MANUAL_OVERLAY_65", skill)
        self.assertIn("build_politics_v8_project.py", assembly)


if __name__ == "__main__":
    unittest.main()

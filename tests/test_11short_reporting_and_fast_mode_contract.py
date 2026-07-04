from __future__ import annotations

import importlib.util
import json
import unittest
from pathlib import Path


SKILL = (
    Path(__file__).resolve().parents[1]
    / "skills"
    / "000short-production-agent"
    / "SKILL.md"
)
SKILL_DIR = SKILL.parent
ROOT = SKILL.parents[2]
LAYOUT_CONTRACT = SKILL_DIR / "03_CAPCUT_LAYOUT_CONTRACT.md"
HARNESS_REQUIREMENTS = SKILL_DIR / "04_HARNESS_REQUIREMENTS.md"
REPORT_CONTRACT = SKILL_DIR / "07_DRAFT_FAST_REPORT_CONTRACT.md"
TIMELINE_GATE = SKILL_DIR / "scripts" / "validate_capcut_timeline_order.py"
PRODUCTION_GATE = SKILL_DIR / "scripts" / "validate_production_gate.py"
CONTRACT_FILES = [
    SKILL,
    SKILL_DIR / "02_PIPELINE_RULES.md",
    LAYOUT_CONTRACT,
    HARNESS_REQUIREMENTS,
    SKILL_DIR / "05_CODEX_EXECUTION_PROMPT.md",
    SKILL_DIR / "06_CAPCUT_CUT_ASSEMBLY_CONTRACT.md",
    REPORT_CONTRACT,
    TIMELINE_GATE,
    PRODUCTION_GATE,
]


class ReportingAndFastModeContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        missing = [str(path) for path in CONTRACT_FILES if not path.is_file()]
        if missing:
            raise AssertionError(f"missing contract file(s): {missing}")
        cls.text = "\n\n".join(
            f"\n<!-- {path.relative_to(ROOT)} -->\n" + path.read_text(encoding="utf-8")
            for path in CONTRACT_FILES
        )

    def test_report_contract_sections_are_present(self):
        required = [
            "## 11short Factory Report Contract",
            "DRAFT_FAST report shape",
            "FINAL_LOCK final report shape",
            "COPY_READY_OUTPUT_BLOCK",
            "CAPCUT_COPY_BLOCK_LAST",
        ]
        for token in required:
            with self.subTest(token=token):
                self.assertIn(token, self.text)

    def test_fast_mode_cost_budget_is_explicit(self):
        required = [
            "DRAFT_FAST_COST_BUDGET",
            "skill_rule_check=5-10%",
            "input_srt_tts=15-25%",
            "capcut_create_rebuild=35-45%",
            "korean_repair=0-5%",
            "final_verify_report=10-15%",
        ]
        for token in required:
            with self.subTest(token=token):
                self.assertIn(token, self.text)

    def test_korean_text_gate_blocks_mojibake_before_repair(self):
        required = [
            "KOREAN_TEXT_FAST_GATE",
            "NO_INLINE_KOREAN_IN_SHELL",
            "MOJIBAKE_PATTERN_FAIL",
            "draft_content.json text scan",
        ]
        for token in required:
            with self.subTest(token=token):
                self.assertIn(token, self.text)

    def test_capcut_mandatory_settings_are_visible_in_skill(self):
        required = [
            "QualityEnhance",
            "-14 LUFS",
            "smart_color_adjust",
            "clear",
            "sharpen",
            "particle",
            "30-50",
            "5-30",
        ]
        for token in required:
            with self.subTest(token=token):
                self.assertIn(token, self.text)

    def test_draft_fast_disarms_final_lock_only_gates(self):
        required = [
            "DRAFT_FAST_WORKING_DRAFT_CREATED",
            "WORKING_DRAFT_CREATED",
            "technical_ready=true",
            "upload_ready=YES",
            "pre_capcut_script_package.md",
            "FINAL_LOCK only",
        ]
        for token in required:
            with self.subTest(token=token):
                self.assertIn(token, self.text)

    def test_current_template_defaults_are_black_and_insta_only(self):
        layout = LAYOUT_CONTRACT.read_text(encoding="utf-8")
        harness = HARNESS_REQUIREMENTS.read_text(encoding="utf-8")
        self.assertIn("black", layout)
        self.assertIn("insta white", layout)
        self.assertIn("black", harness)
        self.assertIn("insta white", harness)
        self.assertIn("there is no separate official", self.text)
        self.assertNotIn("subtitle_1", layout)
        self.assertNotIn("tts_caption", layout)
        self.assertNotIn("verified_speaker_1", layout)

    def test_post_capcut_gate_fails_mojibake_text(self):
        spec = importlib.util.spec_from_file_location("timeline_gate", TIMELINE_GATE)
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        clean = {
            "materials": {
                "texts": [
                    {"id": "clean", "content": json.dumps({"text": "정상 자막"}, ensure_ascii=False)}
                ]
            }
        }
        self.assertEqual(module.validate_korean_text_fast_gate(clean)["korean_text_fast_gate"], "PASS")

        broken = {
            "materials": {
                "texts": [
                    {"id": "broken", "content": json.dumps({"text": "????"}, ensure_ascii=False)}
                ]
            }
        }
        with self.assertRaisesRegex(module.GateFail, "KOREAN_TEXT_FAST_GATE"):
            module.validate_korean_text_fast_gate(broken)

    def test_pre_capcut_gate_no_longer_requires_final_report_before_capcut(self):
        gate_text = PRODUCTION_GATE.read_text(encoding="utf-8")
        self.assertIn("pre_capcut_script_package_status", gate_text)
        self.assertNotIn("final_report_before_capcut", gate_text)


if __name__ == "__main__":
    unittest.main()

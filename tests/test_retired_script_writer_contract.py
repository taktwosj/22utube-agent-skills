from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class RetiredScriptWriterContractTests(unittest.TestCase):
    def test_retired_script_writer_is_not_managed_or_routable(self):
        active_files = [
            ROOT / "manifests" / "skill-set.json",
            ROOT / "skills" / "00-tikitaka" / "SKILL.md",
            ROOT / "skills" / "000short-production-agent" / "SKILL.md",
        ]

        self.assertFalse((ROOT / "skills" / "00script-writer").exists())
        for path in active_files:
            self.assertNotIn(
                "00script-writer",
                path.read_text(encoding="utf-8-sig"),
                path.as_posix(),
            )

    def test_shorts_pipeline_has_no_persona_or_writer_agent_final_gate(self):
        active_files = [
            ROOT
            / "skills"
            / "00-tikitaka"
            / "scripts"
            / "tikitaka_harness_runner.py",
            ROOT
            / "skills"
            / "000short-production-agent"
            / "scripts"
            / "validate_production_gate.py",
            ROOT / "skills" / "00-tikitaka" / "SKILL.md",
            ROOT / "skills" / "000short-production-agent" / "SKILL.md",
        ]
        retired_tokens = [
            "persona_outputs",
            "persona_mode",
            "script_gate_report",
            "writer_persona",
            "writer_agent_source",
            "writer_agent_mode_status",
            "writer_agent_evidence_files",
            "5작가 모드",
        ]

        for path in active_files:
            text = path.read_text(encoding="utf-8-sig")
            for token in retired_tokens:
                self.assertNotIn(token, text, f"{token} remains in {path}")


if __name__ == "__main__":
    unittest.main()

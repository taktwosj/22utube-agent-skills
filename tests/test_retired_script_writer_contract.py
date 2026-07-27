from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class RetiredScriptWriterContractTests(unittest.TestCase):
    def test_retired_skills_are_not_managed_or_routable(self):
        active_files = [
            ROOT / "manifests" / "skill-set.json",
            ROOT / "skills" / "00-tikitaka" / "SKILL.md",
            ROOT / "skills" / "000short-production-agent" / "SKILL.md",
            ROOT / "skills" / "119-politics-longform-capcut" / "SKILL.md",
        ]
        retired_skills = [
            "00script-writer",
            "0shrt-korea-production-agent",
            "josun-historychoon-production-agent",
            "00utube-lm-production-agent",
        ]

        for skill_name in retired_skills:
            self.assertFalse((ROOT / "skills" / skill_name).exists())
            for path in active_files:
                self.assertNotIn(
                    skill_name,
                    path.read_text(encoding="utf-8-sig"),
                    path.as_posix(),
                )

    def test_shorts_pipeline_has_no_persona_or_writer_agent_final_gate(self):
        active_files = []
        for skill_name in ("00-tikitaka", "000short-production-agent"):
            skill_root = ROOT / "skills" / skill_name
            active_files.extend(
                path
                for path in skill_root.rglob("*")
                if path.is_file()
                and path.suffix.lower() in {".md", ".py", ".json", ".txt", ".yaml", ".yml"}
            )
        retired_tokens = [
            "persona_outputs",
            "persona_mode",
            "script_gate_report",
            "writer_persona",
            "writer_agent_source",
            "writer_agent_mode_status",
            "writer_agent_evidence_files",
            "5작가 모드",
            "5-persona",
            "writer/persona",
            "memory anchor",
            "memory_anchor",
            "기억앵커",
            "스타일 코퍼스",
            "style corpus",
            "style_corpus",
        ]

        for path in active_files:
            text = path.read_text(encoding="utf-8-sig").lower()
            for token in retired_tokens:
                self.assertNotIn(token.lower(), text, f"{token} remains in {path}")


if __name__ == "__main__":
    unittest.main()

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
TIKITAKA = (ROOT / "skills" / "00-tikitaka" / "SKILL.md").read_text(encoding="utf-8")
PRODUCTION = (ROOT / "skills" / "000short-production-agent" / "SKILL.md").read_text(encoding="utf-8")
POLITICS = (ROOT / "skills" / "119-politics-longform-capcut" / "SKILL.md").read_text(encoding="utf-8")


class SkillRouterContractTests(unittest.TestCase):
    def test_tikitaka_distinguishes_generic_script_lock_from_stage_one_package(self):
        self.assertIn("generic `SCRIPT_LOCK`", TIKITAKA)
        self.assertIn("`SCRIPT_LOCK_PACKAGE`", TIKITAKA)
        self.assertIn("script_handoff_gate.json status=PASS", TIKITAKA)

    def test_dual_writer_is_explicit_optional_mode_without_dangerous_cli_flag(self):
        self.assertIn("Dual Writer Mode (Explicit Optional Mode)", TIKITAKA)
        self.assertIn("only when the user explicitly asks", TIKITAKA)
        self.assertNotIn("--dangerously-skip-permissions", TIKITAKA)

    def test_factory_root_resolution_is_fail_closed(self):
        for text in (TIKITAKA, PRODUCTION, POLITICS):
            self.assertIn("WAIT_FACTORY_ROOT_NOT_RESOLVED", text)

    def test_auto_full_selects_target_but_does_not_waive_approval(self):
        self.assertIn("AUTO_FULL_CAPCUT_PROJECT selects the target", PRODUCTION)
        self.assertIn("does not waive report1 approval", PRODUCTION)


if __name__ == "__main__":
    unittest.main()

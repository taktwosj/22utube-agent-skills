import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path


sys.dont_write_bytecode = True


ROOT = Path(__file__).parents[1]
SKILL_DIR = ROOT / "skills" / "111-politics-longform"
SKILL = SKILL_DIR / "SKILL.md"
SCRIPTS = SKILL_DIR / "scripts"
VALIDATOR = SCRIPTS / "validate_clean_base.py"
SCANNER = SCRIPTS / "scan_forbidden_capcut_refs.py"


def load_validator():
    if not VALIDATOR.exists():
        raise AssertionError(f"missing validator: {VALIDATOR}")
    sys.path.insert(0, str(SCRIPTS))
    try:
        spec = importlib.util.spec_from_file_location("politics_validate_clean_base", VALIDATOR)
        assert spec and spec.loader
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    finally:
        sys.path.pop(0)


def write_placeholder_draft(base: Path) -> None:
    base.mkdir(parents=True, exist_ok=True)
    payload = {
        "materials": {
            "texts": [
                {"content": json.dumps({"text": "__SOURCE__"}, ensure_ascii=False)},
                {"content": json.dumps({"text": "__DATE__"}, ensure_ascii=False)},
                {"content": json.dumps({"text": "__LOWER_T1_A__"}, ensure_ascii=False)},
            ]
        }
    }
    (base / "draft_content.json").write_text(
        json.dumps(payload, ensure_ascii=False), encoding="utf-8"
    )


class PoliticsLongformJungchilongBaseContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.skill_text = SKILL.read_text(encoding="utf-8-sig")

    def test_jungchilong_is_the_only_default_base(self):
        self.assertIn("Default CapCut base: jungchilong", self.skill_text)
        self.assertIn("Never modify `jungchilong` in place", self.skill_text)
        self.assertIn("Do not automatically fall back", self.skill_text)
        self.assertNotIn("Default CapCut base priority 1: YP007", self.skill_text)
        self.assertNotIn("Fallback production base: YP005", self.skill_text)

    def test_skill_has_fail_closed_base_codes_and_validator_command(self):
        self.assertIn("WAIT_JUNGCHILONG_BASE_MISSING", self.skill_text)
        self.assertIn("FAIL_JUNGCHILONG_DIRTY_BASE", self.skill_text)
        self.assertIn("scripts/validate_clean_base.py", self.skill_text)

    def test_clean_base_tools_are_shipped(self):
        self.assertTrue(SCANNER.is_file(), f"missing scanner: {SCANNER}")
        self.assertTrue(VALIDATOR.is_file(), f"missing validator: {VALIDATOR}")

    def test_missing_base_fails_with_exact_wait_code(self):
        validator = load_validator()
        with tempfile.TemporaryDirectory() as tmp:
            result = validator.validate_base(Path(tmp) / "missing-jungchilong")
        self.assertEqual(result["status"], "FAIL")
        self.assertIn(
            "WAIT_JUNGCHILONG_BASE_MISSING",
            {item["code"] for item in result["errors"]},
        )

    def test_dirty_base_fails_with_exact_code(self):
        validator = load_validator()
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp) / "jungchilong"
            write_placeholder_draft(base)
            (base / "draft_content.json.bak").write_text("{}", encoding="utf-8")
            result = validator.validate_base(base)
        self.assertEqual(result["status"], "FAIL")
        self.assertIn(
            "FAIL_JUNGCHILONG_DIRTY_BASE",
            {item["code"] for item in result["errors"]},
        )

    def test_placeholder_only_base_passes(self):
        validator = load_validator()
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp) / "jungchilong"
            write_placeholder_draft(base)
            result = validator.validate_base(base)
        self.assertEqual(result["status"], "PASS", result)
        self.assertEqual(result["errors"], [])


if __name__ == "__main__":
    unittest.main()

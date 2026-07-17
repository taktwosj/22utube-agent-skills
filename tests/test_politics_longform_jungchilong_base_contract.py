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

    def test_skill_uses_the_pinned_v3_root_contract(self):
        for token in (
            "target_profile: jungchilong_base_v3_intro15",
            r"jungchilong\jungchilong_v3_intro15_CAPCUT_20260715.zip",
            r"jungchilong\template_manifest_v3_intro15.json",
            "archive_sha256: B461A07FF18E1491E837E56A0681A35CCB0A25CBF9D7BFA2B6004C6D32CC878A",
            "packaged_file_count: 39",
            "intro_sha256: E899A65CC6C089FF116CBB6175B6A43B8580A69C523720B093FBE259F05717B9",
            "canvas: 1920x1080",
            "content_start_sec=15.083333",
            "YP007, YP005, YM007 are legacy visual references only.",
        ):
            self.assertIn(token, self.skill_text)
        self.assertNotIn("Default CapCut base priority 1: YP007", self.skill_text)
        self.assertNotIn("Fallback production base: YP005", self.skill_text)

    def test_skill_forbids_mutating_or_falling_back_from_the_v3_root(self):
        self.assertIn("ZIP과 로컬 복구본을 직접 수정하지 않는다", self.skill_text)
        self.assertIn("fallback 근본", self.skill_text)
        self.assertIn("FAIL_ARCHIVE_INTEGRITY", self.skill_text)

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

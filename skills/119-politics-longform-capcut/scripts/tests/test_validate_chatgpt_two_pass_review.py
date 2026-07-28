import importlib.util
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "validate_chatgpt_two_pass_review.py"
SPEC = importlib.util.spec_from_file_location("review_validator", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


class TextHygieneTests(unittest.TestCase):
    def check(self, text: str):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "script.md"
            path.write_text(text, encoding="utf-8")
            errors = []
            MODULE._check_text_hygiene(path, errors)
            return errors

    def test_source_evidence_markers_are_not_audience_text(self):
        errors = self.check(
            "제목\n\n원문 근거 (S1 0-1): >> 원본 화자 구분\n\n정상 평론 문장\n"
        )
        self.assertEqual(errors, [])

    def test_visible_editor_artifact_fails(self):
        errors = self.check("제목\n\n시청자 문장에 << 잔여 기호\n")
        self.assertTrue(any(error["code"] == "FAIL_TEXT_HYGIENE" for error in errors))


if __name__ == "__main__":
    unittest.main()

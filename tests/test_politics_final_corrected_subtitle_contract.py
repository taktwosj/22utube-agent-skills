import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILL_DIR = ROOT / "skills" / "119-politics-longform-capcut"
SKILL = SKILL_DIR / "SKILL.md"
REFERENCE = SKILL_DIR / "references" / "final-corrected-subtitle-lock.md"
VALIDATOR = SKILL_DIR / "scripts" / "validate_final_corrected_srt.py"


class PoliticsFinalCorrectedSubtitleContractTests(unittest.TestCase):
    def test_skill_routes_user_corrected_srt_lock(self):
        text = SKILL.read_text(encoding="utf-8-sig")
        for token in (
            "USER_CORRECTED_SRT_LOCK",
            "final-corrected-subtitle-lock.md",
            "validate_final_corrected_srt.py",
            "FINAL_CORRECTED_CAPTION_FIDELITY",
            "USER_CORRECTED_SRT_LOCK=NOT_APPLICABLE|PASS",
            "사용자 교정본",
            "가운데점 `·`",
            "[콧방귀]",
            "[웃음]",
            "정리하겠습니다",
        ):
            self.assertIn(token, text)

    def test_reference_and_validator_exist(self):
        self.assertTrue(REFERENCE.is_file())
        self.assertTrue(VALIDATOR.is_file())

    def test_validator_accepts_locked_corrections_and_rejects_regressions(self):
        corrections = {
            "replacements": [
                {"from": "20분한테", "to": "20명한테"},
                {"from": "수사,기소", "to": "수사·기소"},
                {"from": "재건축,재개발", "to": "재건축·재개발"},
            ],
            "remove_tokens": ["[콧방귀]", "[웃음]", ">>"],
            "max_occurrences": {"정리하겠습니다": 1},
        }
        good_srt = """1
00:00:00,000 --> 00:00:02,000
20명한테 물었습니다.

2
00:00:02,000 --> 00:00:04,000
수사·기소와 재건축·재개발

3
00:00:04,000 --> 00:00:06,000
정리하겠습니다.
"""
        bad_srt = good_srt.replace("20명한테", "20분한테").replace(
            "정리하겠습니다.", "정리하겠습니다. 정리하겠습니다."
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            temp = Path(temp_dir)
            corrections_path = temp / "corrections.json"
            good_path = temp / "good.srt"
            bad_path = temp / "bad.srt"
            corrections_path.write_text(
                json.dumps(corrections, ensure_ascii=False), encoding="utf-8"
            )
            good_path.write_text(good_srt, encoding="utf-8")
            bad_path.write_text(bad_srt, encoding="utf-8")

            good = subprocess.run(
                [
                    sys.executable,
                    str(VALIDATOR),
                    "--srt",
                    str(good_path),
                    "--corrections-json",
                    str(corrections_path),
                    "--expected-cue-count",
                    "3",
                ],
                text=True,
                capture_output=True,
                encoding="utf-8",
            )
            self.assertEqual(good.returncode, 0, good.stdout + good.stderr)
            good_report = json.loads(good.stdout)
            self.assertEqual(good_report["status"], "PASS")

            bad = subprocess.run(
                [
                    sys.executable,
                    str(VALIDATOR),
                    "--srt",
                    str(bad_path),
                    "--corrections-json",
                    str(corrections_path),
                    "--expected-cue-count",
                    "3",
                ],
                text=True,
                capture_output=True,
                encoding="utf-8",
            )
            self.assertNotEqual(bad.returncode, 0)
            bad_report = json.loads(bad.stdout)
            self.assertEqual(bad_report["status"], "FAIL")
            self.assertIn("FORBIDDEN_OLD_TEXT_PRESENT", bad_report["failures"])
            self.assertIn("MAX_OCCURRENCES_EXCEEDED", bad_report["failures"])


if __name__ == "__main__":
    unittest.main()

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1]
VALIDATOR = SCRIPTS / "validate_pre119_handoff.py"


class Pre119HandoffV28Tests(unittest.TestCase):
    def test_mixed_lower_and_cta_off_reach_validated_plan(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            package = Path(temporary)
            script = package / "20_script" / "119_final_script.md"
            script.parent.mkdir(parents=True)
            script.write_text(
                "# approved\n\n"
                "[ASSEMBLY_ONLY_SEED]\n"
                "execution_mode=ASSEMBLY_ONLY\n"
                "between_image=YES\n"
                "between_narration=YES\n"
                "lower_mode=MIXED\n"
                "cta_like_subscribe=OFF\n\n"
                "[CARD]\n"
                "card_id=C001\n"
                "card_type=NARRATION_IMAGE\n"
                "chapter_label=Chapter 1\n"
                "chapter_title=Chapter 1\n"
                "lower_mode=COMMENTARY_2LINE\n"
                "cta_like_subscribe=OFF\n"
                "next_card=END\n",
                encoding="utf-8",
            )
            digest = hashlib.sha256(script.read_bytes()).hexdigest().upper()
            handoff = {
                "schema": "togun-pre119-handoff-v3",
                "route": "TOGUN_PRE119_TO_119_DIRECT",
                "editorial_owner": "TOGUN_PRE119",
                "source_state": "PRE119_SOURCE_CANDIDATE",
                "execution_mode": "ASSEMBLY_ONLY",
                "episode_id": "PL_20260811_V28",
                "project_name": "PL_20260811_V28_capcut",
                "central_question": "무엇이 달랐나",
                "selected_thesis": "방향과 집행을 분리해 본다",
                "chapter_order": ["CH1", "CH2"],
                "between_image": "YES",
                "between_narration": "YES",
                "lower_mode": "MIXED",
                "cta_like_subscribe": "OFF",
                "publication_report": {
                    "title": "Fixture title",
                    "content": {
                        "simple_summary": "Fixture summary",
                        "timeline": [{"at": "00:00", "label": "Opening"}],
                        "sources": [{"label": "Fixture source", "url": None}],
                    },
                    "thumbnail": {
                        "words": ["책임", "패배", "함께"],
                        "sentences": ["Strongest", "Second", "Third"],
                    },
                },
                "script_lock": {"current_final_script_sha256": digest},
            }
            handoff_path = package / "20_script" / "pre119_handoff.json"
            handoff_path.write_text(json.dumps(handoff, ensure_ascii=False), encoding="utf-8")
            result = subprocess.run(
                [
                    sys.executable,
                    "-B",
                    str(VALIDATOR),
                    "--package-root",
                    str(package),
                    "--approved-script-sha256",
                    digest,
                    "--approval-evidence",
                    "user_message:v28-approved",
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            report = json.loads(
                (package / "90_reports" / "pre119_handoff_validation.json").read_text(
                    encoding="utf-8"
                )
            )
            self.assertEqual(report["status"], "PASS")
            self.assertEqual(report["validated_plan"]["lower_mode"], "MIXED")
            self.assertEqual(report["validated_plan"]["execution_mode"], "ASSEMBLY_ONLY")
            self.assertEqual(report["validated_plan"]["cta_like_subscribe"], "OFF")


if __name__ == "__main__":
    unittest.main()

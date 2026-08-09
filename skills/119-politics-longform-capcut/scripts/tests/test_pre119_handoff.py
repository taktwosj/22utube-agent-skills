from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[2]
VALIDATOR = SKILL_ROOT / "scripts" / "validate_pre119_handoff.py"


class Pre119HandoffTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.package = Path(self.temporary.name)

    @property
    def report_path(self) -> Path:
        return self.package / "90_reports" / "pre119_handoff_validation.json"

    def write_valid_packet(self) -> str:
        script_path = self.package / "20_script" / "119_final_script.md"
        script_path.parent.mkdir(parents=True)
        script_path.write_bytes("# approved\n\nlocked bytes\n".encode("utf-8"))
        digest = hashlib.sha256(script_path.read_bytes()).hexdigest().upper()
        handoff = {
            "schema": "togun-pre119-handoff-v3",
            "route": "TOGUN_PRE119_TO_119_DIRECT",
            "editorial_owner": "TOGUN_PRE119",
            "source_state": "PRE119_SOURCE_CANDIDATE",
            "episode_id": "PL_20260809_PRE119",
            "project_name": "PL_20260809_PRE119_capcut_v1",
            "central_question": "What changed?",
            "selected_thesis": "The verified change matters.",
            "chapter_order": ["CH1", "CH2"],
            "between_image": "NO",
            "between_narration": "NO",
            "lower_mode": "NONE",
            "script_lock": {
                "current_final_script_sha256": digest,
                "user_approved_final_script_sha256": "",
                "status": "WAIT",
            },
            "artifacts": {
                "final_script_path": "20_script/119_final_script.md",
                "source_packet_path": "00_source/source_packet.md",
            },
        }
        handoff_path = self.package / "20_script" / "pre119_handoff.json"
        handoff_path.write_text(json.dumps(handoff), encoding="utf-8")
        return digest

    def run_validator(
        self,
        *,
        approved_sha: str | None = None,
        evidence: str | None = None,
    ) -> subprocess.CompletedProcess[str]:
        command = [sys.executable, "-B", str(VALIDATOR), "--package-root", str(self.package)]
        if approved_sha is not None:
            command.extend(["--approved-script-sha256", approved_sha])
        if evidence is not None:
            command.extend(["--approval-evidence", evidence])
        return subprocess.run(command, capture_output=True, text=True, check=False)

    def read_report(self) -> dict[str, object]:
        self.assertTrue(self.report_path.is_file())
        return json.loads(self.report_path.read_text(encoding="utf-8"))

    def test_strong_marker_locks_pre119_before_direct_script_fallback(self) -> None:
        self.write_valid_packet()

        result = self.run_validator()

        self.assertNotEqual(result.returncode, 0)
        report = self.read_report()
        self.assertEqual(report["route"], "PRE119")
        self.assertEqual(report["status"], "WAIT_EXTERNAL_APPROVAL_REQUIRED")

    def test_one_auxiliary_marker_does_not_false_match_pre119(self) -> None:
        (self.package / "00_README.md").write_text("ordinary episode notes", encoding="utf-8")

        result = self.run_validator()

        self.assertEqual(result.returncode, 0, result.stderr)
        report = self.read_report()
        self.assertEqual(report["route"], "DIRECT_SCRIPT")
        self.assertEqual(report["status"], "NOT_PRE119")

    def test_packet_internal_pass_cannot_replace_external_approval(self) -> None:
        digest = self.write_valid_packet()
        handoff_path = self.package / "20_script" / "pre119_handoff.json"
        handoff = json.loads(handoff_path.read_text(encoding="utf-8"))
        handoff["script_lock"].update(
            {
                "status": "PASS",
                "user_approved_final_script_sha256": digest,
            }
        )
        handoff["user_approval"] = {"status": "PASS"}
        handoff_path.write_text(json.dumps(handoff), encoding="utf-8")

        result = self.run_validator(evidence="user_message:approved")

        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(self.read_report()["status"], "WAIT_EXTERNAL_APPROVAL_REQUIRED")

    def test_actual_packet_and_external_sha_must_all_match(self) -> None:
        digest = self.write_valid_packet()

        result = self.run_validator(
            approved_sha=digest,
            evidence="user_message:019fe54b-approved",
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        report = self.read_report()
        self.assertEqual(report["status"], "PASS")
        self.assertEqual(report["script_lock"]["actual_final_script_sha256"], digest)
        self.assertEqual(report["script_lock"]["packet_current_final_script_sha256"], digest)
        self.assertEqual(report["script_lock"]["external_approved_script_sha256"], digest)
        self.assertFalse((self.package / "50_capcut_project" / "episode_cards.json").exists())

    def test_hash_mismatch_is_blocked_and_reported(self) -> None:
        self.write_valid_packet()

        result = self.run_validator(
            approved_sha="0" * 64,
            evidence="user_message:approved",
        )

        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(self.read_report()["status"], "WAIT_APPROVAL_HASH_MISMATCH")

    def test_absolute_packet_path_is_rejected(self) -> None:
        digest = self.write_valid_packet()
        handoff_path = self.package / "20_script" / "pre119_handoff.json"
        handoff = json.loads(handoff_path.read_text(encoding="utf-8"))
        handoff["artifacts"]["source_packet_path"] = "C:/Users/person/source_packet.md"
        handoff_path.write_text(json.dumps(handoff), encoding="utf-8")

        result = self.run_validator(approved_sha=digest, evidence="user_message:approved")

        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(self.read_report()["status"], "FAIL_PACKET_PATH_UNSAFE")

    def test_parent_traversal_packet_path_is_rejected(self) -> None:
        digest = self.write_valid_packet()
        handoff_path = self.package / "20_script" / "pre119_handoff.json"
        handoff = json.loads(handoff_path.read_text(encoding="utf-8"))
        handoff["artifacts"]["source_packet_path"] = "../outside/source_packet.md"
        handoff_path.write_text(json.dumps(handoff), encoding="utf-8")

        result = self.run_validator(approved_sha=digest, evidence="user_message:approved")

        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(self.read_report()["status"], "FAIL_PACKET_PATH_UNSAFE")

    def test_invalid_handoff_identity_cannot_receive_pass(self) -> None:
        digest = self.write_valid_packet()
        handoff_path = self.package / "20_script" / "pre119_handoff.json"
        handoff = json.loads(handoff_path.read_text(encoding="utf-8"))
        handoff["schema"] = "untrusted-schema"
        handoff_path.write_text(json.dumps(handoff), encoding="utf-8")

        result = self.run_validator(approved_sha=digest, evidence="user_message:approved")

        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(self.read_report()["status"], "FAIL_PRE119_HANDOFF_IDENTITY")


if __name__ == "__main__":
    unittest.main()

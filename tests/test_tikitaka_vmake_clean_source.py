from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from _support import load_source_module_no_bytecode, write_valid_source_mp4


ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills" / "00-tikitaka" / "SKILL.md"
WORKFLOW = (
    ROOT
    / "skills"
    / "00-tikitaka"
    / "references"
    / "vmake_clean_source_workflow.md"
)
REGISTER = (
    ROOT
    / "skills"
    / "00-tikitaka"
    / "scripts"
    / "register_vmake_clean_source.py"
)
VALIDATOR = (
    ROOT
    / "skills"
    / "00-tikitaka"
    / "scripts"
    / "validate_vmake_clean_source.py"
)
HARNESS = (
    ROOT
    / "skills"
    / "00-tikitaka"
    / "scripts"
    / "tikitaka_harness_runner.py"
)
SOURCE_URL = "https://www.youtube.com/shorts/F0TeJK7oUuA"
VIDEO_ID = "F0TeJK7oUuA"


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def create_source_lock(root: Path) -> Path:
    source = root / "00_source" / "source.mp4"
    write_valid_source_mp4(source)
    write_json(
        root / "10_analysis" / "source_identity_lock.json",
        {
            "status": "PASS",
            "gate_name": "SOURCE_IDENTITY_LOCK",
            "owner_skill": "00-tikitaka",
            "canonical_url": SOURCE_URL,
            "video_id": VIDEO_ID,
            "local_source_path": "00_source/source.mp4",
            "sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
            "duration_sec": 8.0,
            "width": 720,
            "height": 1280,
        },
    )
    return source


def create_download(path: Path) -> Path:
    write_valid_source_mp4(path)
    return path


class TikitakaVmakeCleanSourceTests(unittest.TestCase):
    def test_skill_documents_user_confirmed_vmake_reuse_without_retest(self) -> None:
        skill = SKILL.read_text(encoding="utf-8")
        workflow = WORKFLOW.read_text(encoding="utf-8")

        for token in [
            "USER_CONFIRMED_VMAKE_REUSE",
            "vmake_reuse_mode=USER_CONFIRMED_NO_REDOWNLOAD_NO_RETEST",
            "user_vmake_confirmation=true",
            "WAIT_EXISTING_VMAKE_CLEAN_FILE",
            "Do not open Vmake, download or re-download",
            "Do not run `register_vmake_clean_source.py` or "
            "`validate_vmake_clean_source.py`",
            "Keep the original-source analysis, timing, edit order, captions, "
            "and audio plan unchanged",
            "Place the user-specified narration at the first scene",
        ]:
            with self.subTest(token=token):
                self.assertIn(token, skill)

        for token in [
            "User-Confirmed Existing Result",
            "USER_CONFIRMED_NO_REDOWNLOAD_NO_RETEST",
            "Do not run Vmake again",
            "Do not run ffprobe duration parity, aspect-ratio parity, OCR, STT, "
            "frame analysis, or visual quality review",
            "Use the original analysis and timeline unchanged",
        ]:
            with self.subTest(token=token):
                self.assertIn(token, workflow)

    def test_skill_documents_original_analysis_and_vmake_clean_visual_split(self) -> None:
        skill = SKILL.read_text(encoding="utf-8")
        workflow = WORKFLOW.read_text(encoding="utf-8")

        for token in [
            "Vmake Clean Visual Preprocessing",
            "VMAKE_CLEAN_SOURCE_GATE",
            "00_source/clean_source.mp4",
            "WAIT_VMAKE_CLEAN_SOURCE",
            "WAIT_VMAKE_RIGHTS_CONFIRMATION",
            "embedded_audio_policy=muted_always",
        ]:
            with self.subTest(token=token):
                self.assertIn(token, skill)

        for token in [
            "https://vmake.ai/video-watermark-remover/upload",
            "Import from link",
            "We support YouTube, TikTok, IG, and FB links.",
            "I confirm I have the rights to use the imported links.",
            "Processing...",
            "Download",
            "File_from_link_",
            "source.mp4",
            "clean_source.mp4",
        ]:
            with self.subTest(token=token):
                self.assertIn(token, workflow)

    def test_register_and_validator_accept_bound_vmake_download(self) -> None:
        register = load_source_module_no_bytecode(
            "register_vmake_clean_source_pass",
            REGISTER,
        )
        validator = load_source_module_no_bytecode(
            "validate_vmake_clean_source_pass",
            VALIDATOR,
        )
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "episode"
            create_source_lock(root)
            download = create_download(
                Path(tmp)
                / "Downloads"
                / "File_from_link_-_b3c0b723-e5b6-4c08-8dee-3b7417802fda.mp4"
            )

            registered = register.register_vmake_clean_source(
                root,
                download,
                source_url=SOURCE_URL,
                job_id="b3c0b723-e5b6-4c08-8dee-3b7417802fda",
                rights_confirmed=True,
                confirmation_source="user",
            )
            validated = validator.validate_vmake_clean_source(root)

            self.assertEqual(registered["status"], "PASS")
            self.assertEqual(validated["vmake_clean_source_status"], "PASS")
            self.assertTrue((root / "00_source" / "clean_source.mp4").is_file())
            self.assertEqual(
                registered["embedded_audio_policy"],
                "muted_always",
            )

    def test_register_rejects_missing_rights_confirmation(self) -> None:
        register = load_source_module_no_bytecode(
            "register_vmake_clean_source_rights",
            REGISTER,
        )
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "episode"
            create_source_lock(root)
            download = create_download(
                Path(tmp) / "Downloads" / "File_from_link_-_job-test.mp4"
            )

            with self.assertRaisesRegex(
                register.GateFail,
                "WAIT_VMAKE_RIGHTS_CONFIRMATION",
            ):
                register.register_vmake_clean_source(
                    root,
                    download,
                    source_url=SOURCE_URL,
                    job_id="job-test",
                    rights_confirmed=False,
                    confirmation_source="",
                )

    def test_register_rejects_unknown_download_method(self) -> None:
        register = load_source_module_no_bytecode(
            "register_vmake_clean_source_method",
            REGISTER,
        )
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "episode"
            create_source_lock(root)
            download = create_download(
                Path(tmp) / "Downloads" / "File_from_link_-_job-test.mp4"
            )

            with self.assertRaisesRegex(
                register.GateFail,
                "unsupported download_method",
            ):
                register.register_vmake_clean_source(
                    root,
                    download,
                    source_url=SOURCE_URL,
                    job_id="job-test",
                    rights_confirmed=True,
                    confirmation_source="user",
                    download_method="untrusted",
                )

    def test_validator_rejects_source_url_mismatch(self) -> None:
        register = load_source_module_no_bytecode(
            "register_vmake_clean_source_url",
            REGISTER,
        )
        validator = load_source_module_no_bytecode(
            "validate_vmake_clean_source_url",
            VALIDATOR,
        )
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "episode"
            create_source_lock(root)
            download = create_download(
                Path(tmp) / "Downloads" / "File_from_link_-_job-test.mp4"
            )
            register.register_vmake_clean_source(
                root,
                download,
                source_url=SOURCE_URL,
                job_id="job-test",
                rights_confirmed=True,
                confirmation_source="user",
            )
            manifest_path = root / "10_analysis" / "vmake_clean_source.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["requested_source_url"] = (
                "https://www.youtube.com/shorts/different123"
            )
            write_json(manifest_path, manifest)

            with self.assertRaisesRegex(
                validator.GateFail,
                "WAIT_VMAKE_SOURCE_IDENTITY",
            ):
                validator.validate_vmake_clean_source(root)

    def test_validator_rejects_duration_not_bound_to_original(self) -> None:
        register = load_source_module_no_bytecode(
            "register_vmake_clean_source_duration",
            REGISTER,
        )
        validator = load_source_module_no_bytecode(
            "validate_vmake_clean_source_duration",
            VALIDATOR,
        )
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "episode"
            create_source_lock(root)
            download = create_download(
                Path(tmp) / "Downloads" / "File_from_link_-_job-test.mp4"
            )
            register.register_vmake_clean_source(
                root,
                download,
                source_url=SOURCE_URL,
                job_id="job-test",
                rights_confirmed=True,
                confirmation_source="user",
            )
            manifest_path = root / "10_analysis" / "vmake_clean_source.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["clean_duration_sec"] = 1.0
            write_json(manifest_path, manifest)

            with self.assertRaisesRegex(
                validator.GateFail,
                "WAIT_VMAKE_DURATION_PARITY",
            ):
                validator.validate_vmake_clean_source(root)

    def test_harness_requires_clean_source_only_for_stage_two(self) -> None:
        harness = load_source_module_no_bytecode(
            "tikitaka_harness_vmake_clean_source",
            HARNESS,
        )
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)

            stage1 = harness.vmake_clean_source_status(root, required=False)
            stage2 = harness.vmake_clean_source_status(root, required=True)

            self.assertEqual(stage1["status"], "NOT_REQUIRED")
            self.assertEqual(stage2["status"], "FAILED")
            self.assertIn("WAIT_VMAKE_CLEAN_SOURCE", stage2["reason"])


if __name__ == "__main__":
    unittest.main()

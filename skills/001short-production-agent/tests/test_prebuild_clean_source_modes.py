import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[1]
VALIDATOR = SKILL_ROOT / "scripts" / "validate_prebuild.py"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _make_video(path: Path, color: str) -> None:
    subprocess.run(
        [
            "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
            "-f", "lavfi", "-i", f"color=c={color}:s=16x24:d=0.4:r=10",
            "-pix_fmt", "yuv420p", str(path),
        ],
        check=True,
    )


def _media(path: Path) -> dict:
    completed = subprocess.run(
        [
            "ffprobe", "-v", "error", "-select_streams", "v:0", "-count_frames",
            "-show_entries", "stream=width,height,nb_read_frames:format=duration",
            "-of", "json", str(path),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    payload = json.loads(completed.stdout)
    stream = payload["streams"][0]
    return {
        "path": str(path),
        "sha256": _sha256(path),
        "duration_us": round(float(payload["format"]["duration"]) * 1_000_000),
        "width": int(stream["width"]),
        "height": int(stream["height"]),
        "frame_count": int(stream["nb_read_frames"]),
    }


class PrebuildCleanSourceModesTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.source = self.root / "source.mp4"
        self.clean = self.root / "clean_source.mp4"
        _make_video(self.source, "red")
        _make_video(self.clean, "blue")
        self.source_media = _media(self.source)
        self.clean_media = _media(self.clean)
        self.template = self.root / "root.zip"
        self.template.write_bytes(b"root-template")

    def tearDown(self):
        self.temp.cleanup()

    def _manifest(self, source_type: str) -> dict:
        clean = self.source_media if source_type == "SOURCE_PROVISIONAL" else self.clean_media
        manifest = {
            "schema_version": "001short-build-manifest-v1",
            "episode_id": "SH_TEST",
            "source": self.source_media,
            "template": {
                "root_name": "shrt white",
                "root_zip_path": str(self.template),
                "root_zip_sha256": _sha256(self.template),
            },
            "vmake": {
                "source_type": source_type,
                "input_sha256": self.source_media["sha256"],
                **clean,
            },
            "urakkai": {
                "production_type": "URAKKAI",
                "target_duration_us": 400_000,
                "reorder_required": True,
                "locked_permutation": ["B", "A"],
                "video_clips": [
                    {
                        "clip_id": "B", "source_sha256": self.source_media["sha256"],
                        "source_range_us": [200_000, 400_000], "target_range_us": [0, 200_000],
                    },
                    {
                        "clip_id": "A", "source_sha256": self.source_media["sha256"],
                        "source_range_us": [0, 200_000], "target_range_us": [200_000, 400_000],
                    },
                ],
            },
            "source_audio": [
                {"clip_id": "B", "mode": "mute"},
                {"clip_id": "A", "mode": "mute"},
            ],
        }
        if source_type == "VMAKE":
            receipt = self.root / "vmake_receipt.json"
            receipt.write_text(
                json.dumps(
                    {
                        "provider": "vmake", "final_download": True,
                        "run_id": "run-1", "job_id": "job-1",
                        "uploaded_source_sha256": self.source_media["sha256"],
                        "downloaded_output_sha256": self.clean_media["sha256"],
                    }
                ),
                encoding="utf-8",
            )
            manifest["vmake"].update(
                {
                    "receipt_path": str(receipt), "final_download": True,
                    "run_id": "run-1", "job_id": "job-1",
                    "input_sha256": self.source_media["sha256"],
                    "output_sha256": self.clean_media["sha256"],
                    "output_path": str(self.clean),
                }
            )
        else:
            manifest["vmake"].update(
                {"output_sha256": clean["sha256"], "output_path": clean["path"]}
            )
        return manifest

    def _run_cli(self, manifest: dict) -> tuple[subprocess.CompletedProcess, dict]:
        path = self.root / "build_manifest.json"
        path.write_text(json.dumps(manifest), encoding="utf-8")
        completed = subprocess.run(
            [sys.executable, str(VALIDATOR), "--build-manifest", str(path)],
            capture_output=True,
            text=True,
            check=False,
        )
        return completed, json.loads(completed.stdout)

    def test_user_provided_is_accepted_without_fabricated_vmake_receipt(self):
        completed, payload = self._run_cli(self._manifest("USER_PROVIDED"))

        self.assertEqual(completed.returncode, 0, payload)
        self.assertEqual(payload["status"], "PASS")
        self.assertEqual(payload["evidence"]["clean_source_type"], "USER_PROVIDED")
        self.assertIs(payload["evidence"]["provisional"], False)

    def test_legacy_vmake_manifest_key_remains_the_cli_interface_for_all_modes(self):
        for source_type in ("VMAKE", "USER_PROVIDED", "SOURCE_PROVISIONAL"):
            with self.subTest(source_type=source_type):
                manifest = self._manifest(source_type)
                self.assertIn("vmake", manifest)
                self.assertNotIn("clean_source", manifest)

                completed, payload = self._run_cli(manifest)

                self.assertEqual(completed.returncode, 0, payload)
                self.assertEqual(payload["status"], "PASS")
                self.assertEqual(payload["evidence"]["clean_source_type"], source_type)

    def test_vmake_and_source_provisional_are_formal_modes(self):
        vmake_completed, vmake = self._run_cli(self._manifest("VMAKE"))
        provisional_completed, provisional = self._run_cli(self._manifest("SOURCE_PROVISIONAL"))

        self.assertEqual(vmake_completed.returncode, 0, vmake)
        self.assertEqual(vmake["evidence"]["clean_source_type"], "VMAKE")
        self.assertEqual(provisional_completed.returncode, 0, provisional)
        self.assertIs(provisional["evidence"]["provisional"], True)
        self.assertEqual(
            provisional["evidence"]["deferred_replacements"],
            ["CLEAN_SOURCE_SWAP_NONBLOCKING"],
        )

    def test_all_modes_keep_hash_resolution_and_frame_count_gates(self):
        mutations = (
            ("output_sha256", "0" * 64),
            ("input_sha256", "0" * 64),
            ("width", 99),
            ("frame_count", 99),
        )
        for source_type in ("VMAKE", "USER_PROVIDED", "SOURCE_PROVISIONAL"):
            for field, value in mutations:
                with self.subTest(source_type=source_type, field=field):
                    manifest = self._manifest(source_type)
                    manifest["vmake"][field] = value
                    completed, payload = self._run_cli(manifest)
                    self.assertEqual(completed.returncode, 1, payload)
                    self.assertIn(
                        "E_CLEAN_MEDIA_BINDING",
                        [error["code"] for error in payload["errors"]],
                    )

    def test_source_mp4_cannot_be_renamed_as_clean_video(self):
        disguised = self.root / "clean_video.mp4"
        disguised.write_bytes(self.source.read_bytes())
        manifest = self._manifest("USER_PROVIDED")
        disguised_media = _media(disguised)
        manifest["vmake"].update(disguised_media)
        manifest["vmake"].update(
            {"output_path": disguised_media["path"], "output_sha256": disguised_media["sha256"]}
        )
        completed, payload = self._run_cli(manifest)

        self.assertEqual(completed.returncode, 1, payload)
        self.assertIn("E_SOURCE_AS_CLEAN_VIDEO", [error["code"] for error in payload["errors"]])

    def test_protocol_declares_the_three_clean_source_types(self):
        protocol = json.loads((SKILL_ROOT / "protocol.json").read_text(encoding="utf-8"))

        self.assertEqual(
            protocol["invariants"]["clean_source_types"],
            ["VMAKE", "USER_PROVIDED", "SOURCE_PROVISIONAL"],
        )
        self.assertEqual(
            protocol["invariants"]["clean_source_technical_fields"],
            ["sha256", "duration_us", "width", "height", "frame_count"],
        )
        self.assertIs(protocol["invariants"]["source_mp4_clean_video_rename_forbidden"], True)


if __name__ == "__main__":
    unittest.main()

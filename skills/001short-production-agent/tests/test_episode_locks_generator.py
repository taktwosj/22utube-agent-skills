import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[1]
if str(SKILL_ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(SKILL_ROOT / "scripts"))

import build_episode_locks as generator  # noqa: E402
import validate_executable_protocol  # noqa: E402
from schema_runtime import validate_schema  # noqa: E402


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _silent_wav(path: Path, duration_us: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        ["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i", "anullsrc=r=44100:cl=mono",
         "-t", f"{duration_us / 1_000_000:.6f}", "-c:a", "pcm_s16le", str(path)],
        check=True,
    )


def _black_mp4(path: Path, duration_us: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        ["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i", "color=c=black:s=64x64:r=30",
         "-t", f"{duration_us / 1_000_000:.6f}", "-pix_fmt", "yuv420p", str(path)],
        check=True,
    )


class EpisodeLocksGeneratorTest(unittest.TestCase):
    """The generator is the single place segment boundaries are transcribed from."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name) / "260101_fixture_abcdefghijk"
        # URAKKAI requires a real structural reorder, so V01 takes the second beat.
        self.v_rows = [
            ["V01", "B02", 0, 1_400_000, 1_400_000, 2_800_000],
            ["V02", "B01", 1_400_000, 3_000_000, 0, 1_600_000],
        ]
        self.duration = 3_000_000

        _black_mp4(self.root / "00_input" / "source.mp4", self.duration)
        _black_mp4(self.root / "40_assets_used" / "clean_source.mp4", self.duration)
        _silent_wav(self.root / "30_audio_srt" / "tts" / "V01_fit.wav", 1_400_000)
        _silent_wav(self.root / "30_audio_srt" / "tts" / "V02_fit.wav", 1_600_000)

        source_sha = _sha(self.root / "00_input" / "source.mp4")
        clean_sha = _sha(self.root / "40_assets_used" / "clean_source.mp4")
        _write_json(self.root / "00_input" / "source_identity.json", {
            "schema_version": "source-identity-v1", "episode_id": self.root.name,
            "source_id": "abcdefghijk", "source_fingerprint": source_sha,
            "media_path": "source.mp4", "media_sha256": source_sha,
            "source_locator": "https://example.invalid/shorts/abcdefghijk",
        })
        _write_json(self.root / "00_input" / "source_intake_receipt.json",
                    {"local_media_duration_us": self.duration})
        _write_json(self.root / "40_assets_used" / "vmake_final_download_evidence.json", {
            "provider": "vmake", "run_id": "run-1", "job_id": "job-1",
            "uploaded_source_sha256": source_sha, "downloaded_output_sha256": clean_sha,
            "final_download": True,
        })
        _write_json(self.root / "30_audio_srt" / "audio_lock.json", {"schema_version": "x"})
        (self.root / "20_script" / "original-capcut-grid.md").parent.mkdir(parents=True, exist_ok=True)
        (self.root / "20_script" / "original-capcut-grid.md").write_text("original", encoding="utf-8")
        (self.root / "20_script" / "urakkai-capcut-grid.md").write_text("urakkai", encoding="utf-8")

        _write_json(self.root / "20_script" / "v_plan.json", {
            "V": self.v_rows, "DUR": self.duration, "type": "2",
            "audio_policy": "TTS_ONLY_MUTE_SOURCE", "execution_strategy": "full_tts",
            "audio_source": "SILENCE", "T1": "제목 하나", "T2": "제목 둘",
            "cues": [
                ["V01", "A9_V01", "첫 줄", 1_400_000, 0, 1_400_000, "V01_fit.wav"],
                ["V02", "A9_V02", "둘째<br>줄", 1_600_000, 1_400_000, 3_000_000, "V02_fit.wav"],
            ],
        })
        segments = [
            {"segment_id": row[0], "role": "VIDEO", "start": row[2], "duration": row[3] - row[2],
             "source_ref": "abcdefghijk", "source_beat_id": row[1],
             "source_range_us": [row[4], row[5]], "target_range_us": [row[2], row[3]],
             "volume": 0, "timeline_order": index}
            for index, row in enumerate(self.v_rows, start=1)
        ]
        for offset, (role, suffix) in enumerate((("A9", ""), ("A9_TEXT", "_TEXT"))):
            for index, row in enumerate(self.v_rows):
                segments.append({
                    "segment_id": f"A9_{row[0]}{suffix}", "role": role, "start": row[2],
                    "duration": row[3] - row[2], "source_ref": "abcdefghijk",
                    "text": "첫 줄" if row[0] == "V01" else "둘째\n줄",
                    "content_type": "TTS", "cue_id": f"A9_{row[0]}",
                    "timeline_order": 10 + offset * 10 + index,
                })
        _write_json(self.root / "20_script" / "approved_timeline.json", {
            "schema_version": "001short-approved-timeline-v2", "episode_id": self.root.name,
            "source_fingerprint": source_sha, "production_mode": "URAKKAI",
            "audio_policy": "TTS_ONLY_MUTE_SOURCE", "execution_strategy": "full_tts",
            "segments": segments,
        })
        self.template_zip = Path(self._tmp.name) / "template.zip"
        self.template_zip.write_bytes(b"template")

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def _generate(self) -> dict:
        return generator.generate(
            episode_root=self.root,
            capcut_root=Path(self._tmp.name) / "capcut",
            workspace_root=Path(self._tmp.name) / "workspace",
            template_zip=self.template_zip,
            root_profile="test_profile",
            root_contract_path="contract.json",
            work_root=Path(self._tmp.name) / "work",
        )

    def test_design_handoff_matches_its_schema(self) -> None:
        """The build refuses a handoff whose schema_version is not the tikitaka constant."""
        self._generate()
        handoff = json.loads((self.root / "20_script" / "design_handoff.json").read_text(encoding="utf-8"))
        schema = json.loads((SKILL_ROOT / "schemas" / "design_handoff.schema.json").read_text(encoding="utf-8"))
        self.assertEqual(handoff["schema_version"], "tikitaka-design-handoff-v1")
        self.assertEqual(handoff["status"], "PASS")
        self.assertEqual(validate_schema(handoff, schema), [])

    def test_production_plan_passes_the_protocol_gate(self) -> None:
        """build_episode_capcut runs this exact gate before it will stage anything."""
        self._generate()
        plan = json.loads((self.root / "20_script" / "production_plan.json").read_text(encoding="utf-8"))
        self.assertEqual(plan["root_profile"], "test_profile")
        self.assertEqual(
            validate_executable_protocol.validate_production_plan(
                plan, validate_executable_protocol.load_protocol()
            ),
            [],
        )

    def test_generated_artifacts_share_one_set_of_boundaries(self) -> None:
        payload = self._generate()
        self.assertEqual(payload["status"], "PASS")
        self.assertEqual(payload["caption_cue_count"], 2)
        self.assertEqual(payload["tts_cue_count"], 2)

        manifest = json.loads((self.root / "50_capcut_project" / "build_manifest.json").read_text(encoding="utf-8"))
        plan = json.loads((self.root / "20_script" / "production_plan.json").read_text(encoding="utf-8"))
        config = json.loads((self.root / "50_capcut_project" / "build_config.json").read_text(encoding="utf-8"))
        evidence = json.loads(
            (self.root / "30_audio_srt" / "caption_timing_evidence.json").read_text(encoding="utf-8")
        )
        expected = [[row[2], row[3]] for row in self.v_rows]
        self.assertEqual([clip["target_range_us"] for clip in manifest["urakkai"]["video_clips"]], expected)
        self.assertEqual([row["target_range_us"] for row in plan["timeline"]], expected)
        self.assertEqual([row["target_range_us"] for row in evidence["mapping"]], expected)
        self.assertEqual(config["duration_us"], self.duration)

    def test_srt_is_written_from_the_same_timeline(self) -> None:
        self._generate()
        srt = (self.root / "30_audio_srt" / "final.srt").read_text(encoding="utf-8")
        self.assertIn("00:00:00,000 --> 00:00:01,400", srt)
        self.assertIn("00:00:01,400 --> 00:00:03,000", srt)
        lock = json.loads((self.root / "30_audio_srt" / "caption_lock.json").read_text(encoding="utf-8"))
        self.assertEqual(lock["final_srt_sha256"], _sha(self.root / "30_audio_srt" / "final.srt"))

    def test_missing_vmake_receipt_is_refused(self) -> None:
        """A generated tree must never claim a VMake download that has no receipt."""
        (self.root / "40_assets_used" / "vmake_final_download_evidence.json").unlink()
        with self.assertRaises(ValueError) as caught:
            self._generate()
        self.assertEqual(str(caught.exception), "VMAKE_FINAL_DOWNLOAD_EVIDENCE_REQUIRED")

    def test_vmake_receipt_for_a_different_file_is_refused(self) -> None:
        receipt = self.root / "40_assets_used" / "vmake_final_download_evidence.json"
        payload = json.loads(receipt.read_text(encoding="utf-8"))
        payload["downloaded_output_sha256"] = "0" * 64
        _write_json(receipt, payload)
        with self.assertRaises(ValueError) as caught:
            self._generate()
        self.assertEqual(str(caught.exception), "VMAKE_EVIDENCE_OUTPUT_SHA_MISMATCH")

    def test_caption_spanning_two_segments_is_refused(self) -> None:
        """validate_audio_caption requires every cue to sit inside one mapping row."""
        timeline_path = self.root / "20_script" / "approved_timeline.json"
        timeline = json.loads(timeline_path.read_text(encoding="utf-8"))
        for segment in timeline["segments"]:
            if segment["segment_id"] == "A9_V01_TEXT":
                segment["duration"] = 2_000_000
        _write_json(timeline_path, timeline)
        with self.assertRaises(ValueError) as caught:
            self._generate()
        self.assertTrue(str(caught.exception).startswith("CAPTION_CUE_SPANS_SEGMENTS:"))


if __name__ == "__main__":
    unittest.main()

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SKILL = Path(__file__).resolve().parents[1]
SCRIPTS = SKILL / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from validate_audio_caption import validate_audio_caption
from validate_vocal_stem import validate_vocal_stem
import rebind_existing_draft_vocal_stem as existing_rebind
from separate_source_vocals import classify_demucs_failure


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def make_wav(path: Path, seconds: float = 0.4) -> int:
    subprocess.run([
        "ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-f", "lavfi",
        "-i", f"sine=frequency=440:duration={seconds}", "-ac", "1", "-ar", "48000",
        "-c:a", "pcm_s16le", str(path),
    ], check=True)
    return round(float(subprocess.run([
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "default=nw=1:nk=1", str(path),
    ], check=True, capture_output=True, text=True).stdout.strip()) * 1_000_000)


class VocalStemContractTest(unittest.TestCase):
    def _fixture(self, root: Path) -> tuple[Path, Path, Path]:
        source = root / "source.wav"
        vocals = root / "vocals.wav"
        residual = root / "no_vocals.wav"
        duration = make_wav(source)
        make_wav(vocals)
        make_wav(residual)
        manifest = root / "vocal_stem_manifest.json"
        manifest.write_text(json.dumps({
            "schema_version": "001short-vocal-stem-manifest-v1",
            "status": "STEM_GENERATED",
            "episode_id": "SH_VOCAL_TEST",
            "source_path": source.name,
            "source_sha256": sha256(source),
            "source_duration_us": duration,
            "separator": {"engine": "demucs", "model": "htdemucs", "python_executable": "fixture"},
            "vocals_path": vocals.name,
            "vocals_sha256": sha256(vocals),
            "vocals_duration_us": duration,
            "vocals_codec": "pcm_s16le",
            "vocals_ffprobe_verified": True,
            "residual_reference_path": residual.name,
            "residual_reference_sha256": sha256(residual),
            "capcut_audio_role": "A10",
            "capcut_allowed_audio_path": vocals.name,
            "a12_policy": "EMPTY",
            "human_listen_qc_required": True,
        }), encoding="utf-8")
        return source, vocals, manifest

    def test_validates_actual_a10_stem_identity(self):
        with tempfile.TemporaryDirectory() as temporary:
            _, vocals, manifest = self._fixture(Path(temporary))
            result = validate_vocal_stem(manifest)
            self.assertEqual(result["status"], "PASS")
            self.assertEqual(Path(result["evidence"]["a10_audio_path"]), vocals)
            self.assertEqual(result["evidence"]["a12_policy"], "EMPTY")
            self.assertTrue(result["evidence"]["human_listen_qc_required"])
            self.assertEqual(result["evidence"]["human_listen_qc_status"], "NOT_VERIFIED")
            self.assertEqual(result["evidence"]["audio_quality_status"], "NOT_VERIFIED")

    def test_requires_canonical_vocals_filename_and_independent_source_duration(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source, vocals, manifest = self._fixture(root)
            renamed = root / "speaker.wav"; vocals.rename(renamed)
            payload = json.loads(manifest.read_text(encoding="utf-8"))
            payload["vocals_path"] = renamed.name
            payload["capcut_allowed_audio_path"] = renamed.name
            payload["vocals_sha256"] = sha256(renamed)
            manifest.write_text(json.dumps(payload), encoding="utf-8")
            self.assertIn("VOCAL_STEM_CANONICAL_FILENAME_REQUIRED", {row["code"] for row in validate_vocal_stem(manifest)["errors"]})

            make_wav(source, 0.8)
            payload["source_sha256"] = sha256(source)
            payload["source_duration_us"] = payload["vocals_duration_us"]
            manifest.write_text(json.dumps(payload), encoding="utf-8")
            self.assertIn("VOCAL_STEM_SOURCE_DURATION_MISMATCH", {row["code"] for row in validate_vocal_stem(manifest)["errors"]})

    def test_demucs_environment_failures_are_distinct_from_processing_failures(self):
        self.assertEqual(classify_demucs_failure("Permission denied WinError 5"), "DEMUCS_EXECUTION_ENVIRONMENT_FAILED")
        self.assertEqual(classify_demucs_failure("CUDA out of memory during separation"), "DEMUCS_PROCESSING_FAILED")

    def test_rejects_a10_path_that_is_not_vocal_stem(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source, _, manifest = self._fixture(root)
            payload = json.loads(manifest.read_text(encoding="utf-8"))
            payload["capcut_allowed_audio_path"] = source.name
            manifest.write_text(json.dumps(payload), encoding="utf-8")
            result = validate_vocal_stem(manifest)
            self.assertEqual(result["status"], "FAIL")
            self.assertIn("VOCAL_STEM_CAPCUT_PATH_NOT_VOCALS", {row["code"] for row in result["errors"]})

    def test_audio_lock_requires_matching_a10_role_and_manifest(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            _, vocals, manifest = self._fixture(root)
            duration = make_wav(vocals) if not vocals.is_file() else round(float(subprocess.run([
                "ffprobe", "-v", "error", "-show_entries", "format=duration",
                "-of", "default=nw=1:nk=1", str(vocals),
            ], check=True, capture_output=True, text=True).stdout.strip()) * 1_000_000)
            audio_lock = root / "audio_lock.json"
            lock = {
                "schema_version": "001short-audio-lock-v3", "episode_id": "SH_VOCAL_TEST", "status": "PASS",
                "audio_source": "SOURCE_VOCAL_STEM", "audio_path": vocals.name,
                "audio_sha256": sha256(vocals), "measured_duration_us": duration,
                "audio_codec": "pcm_s16le", "ffprobe_verified": True,
                "vocal_stem_manifest_path": manifest.name, "vocal_stem_manifest_sha256": sha256(manifest),
                "role_files": [{
                    "role": "A10", "audio_path": vocals.name, "audio_sha256": sha256(vocals),
                    "measured_duration_us": duration, "audio_codec": "pcm_s16le", "ffprobe_verified": True,
                }],
            }
            audio_lock.write_text(json.dumps(lock), encoding="utf-8")
            srt = root / "final.srt"
            srt.write_text("1\n00:00:00,000 --> 00:00:00,200\n테스트\n", encoding="utf-8")
            caption = root / "caption_lock.json"
            caption.write_text(json.dumps({
                "schema_version": "001short-caption-lock-v1", "episode_id": "SH_VOCAL_TEST", "status": "PASS",
                "audio_lock_path": audio_lock.name, "audio_lock_sha256": sha256(audio_lock),
                "final_srt_path": srt.name, "final_srt_sha256": sha256(srt), "final_cue_count": 1,
                "cues": [{"cue_id": "1", "start_us": 0, "end_us": 200000, "text": "테스트"}],
                "all_cues_within_measured_audio": True, "no_overlap_verified": True,
            }), encoding="utf-8")
            self.assertEqual(validate_audio_caption(audio_lock, caption)["status"], "PASS")
            lock["role_files"] = []
            audio_lock.write_text(json.dumps(lock), encoding="utf-8")
            broken_caption = json.loads(caption.read_text(encoding="utf-8"))
            broken_caption["audio_lock_sha256"] = sha256(audio_lock)
            caption.write_text(json.dumps(broken_caption), encoding="utf-8")
            result = validate_audio_caption(audio_lock, caption)
            self.assertEqual(result["status"], "FAIL")
            self.assertIn("AUDIO_CAPTION_VOCAL_STEM_A10_MISSING", {row["code"] for row in result["errors"]})
            lock["audio_source"] = "SOURCE_CLIP"
            lock["role_files"] = []
            audio_lock.write_text(json.dumps(lock), encoding="utf-8")
            broken_caption["audio_lock_sha256"] = sha256(audio_lock)
            caption.write_text(json.dumps(broken_caption), encoding="utf-8")
            result = validate_audio_caption(audio_lock, caption)
            self.assertEqual(result["status"], "FAIL")
            self.assertIn("AUDIO_CAPTION_RAW_SOURCE_AUDIO_FORBIDDEN", {row["code"] for row in result["errors"]})
            lock["audio_source"] = "SOURCE_VOCAL_STEM"
            lock["role_files"] = [{"role": "A12", "audio_path": vocals.name, "audio_sha256": sha256(vocals), "measured_duration_us": duration, "audio_codec": "pcm_s16le", "ffprobe_verified": True}]
            audio_lock.write_text(json.dumps(lock), encoding="utf-8")
            broken_caption["audio_lock_sha256"] = sha256(audio_lock)
            caption.write_text(json.dumps(broken_caption), encoding="utf-8")
            result = validate_audio_caption(audio_lock, caption)
            self.assertEqual(result["status"], "FAIL")
            self.assertIn("AUDIO_CAPTION_AUDIO_LOCK_SCHEMA", {row["code"] for row in result["errors"]})

    def test_existing_draft_rebinds_only_portable_a10_to_vocal_stem(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            _, vocals, manifest = self._fixture(root)
            draft = root / "draft"
            (draft / "Resources" / "media").mkdir(parents=True)
            duration = round(float(subprocess.run([
                "ffprobe", "-v", "error", "-show_entries", "format=duration",
                "-of", "default=nw=1:nk=1", str(vocals),
            ], check=True, capture_output=True, text=True).stdout.strip()) * 1_000_000)
            material_id = "source-a10"
            (draft / "draft_content.json").write_text(json.dumps({
                "tracks": [
                    {"type": "video", "segments": [{"id": "video-1", "volume": 0.0}]},
                    {"type": "audio", "segments": [{
                        "id": "a10-1", "material_id": material_id,
                        "source_timerange": {"start": 0, "duration": duration},
                        "target_timerange": {"start": 0, "duration": duration},
                    }]},
                ],
                "materials": {"audios": [{
                    "id": material_id, "type": "extract_music", "name": "source_audio.m4a",
                    "path": "##_draftpath_placeholder_##/Resources/media/source_audio.m4a",
                    "duration": duration,
                }]},
            }), encoding="utf-8")
            original_open = existing_rebind._capcut_open
            existing_rebind._capcut_open = lambda: False
            try:
                result = existing_rebind.rebind(draft, manifest, dry_run=False)
            finally:
                existing_rebind._capcut_open = original_open
            self.assertEqual(result["status"], "STEM_REBOUND_NOT_GUI_VERIFIED")
            payload = json.loads((draft / "draft_content.json").read_text(encoding="utf-8"))
            segment = payload["tracks"][1]["segments"][0]
            material = payload["materials"]["audios"][0]
            self.assertEqual(segment["role"], "A10")
            self.assertEqual(material["role"], "A10")
            self.assertTrue(material["path"].endswith("/Resources/media/source_vocals.wav"))
            self.assertEqual(sha256(draft / "Resources" / "media" / "source_vocals.wav"), sha256(vocals))
            self.assertTrue((draft / "draft_content.pre_vocal_stem.json").is_file())


if __name__ == "__main__":
    unittest.main()

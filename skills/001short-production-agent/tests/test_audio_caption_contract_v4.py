from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SKILL = Path(__file__).resolve().parents[1]
SCRIPT = SKILL / "scripts" / "validate_audio_caption.py"
PREBUILD = SKILL / "scripts" / "validate_prebuild.py"
if str(SKILL / "scripts") not in sys.path:
    sys.path.insert(0, str(SKILL / "scripts"))
from validate_audio_caption import validate_audio_caption


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")


def wav(path: Path, seconds: float = 0.4) -> int:
    subprocess.run([
        "ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-f", "lavfi",
        "-i", f"sine=frequency=440:duration={seconds}", "-ac", "1", "-ar", "48000",
        "-c:a", "pcm_s16le", str(path),
    ], check=True)
    return round(float(subprocess.run([
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "default=nw=1:nk=1", str(path),
    ], check=True, capture_output=True, text=True).stdout.strip()) * 1_000_000)


def silence_wav(path: Path, seconds: float = 0.4) -> int:
    subprocess.run([
        "ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-f", "lavfi",
        "-i", f"anullsrc=r=48000:cl=mono:d={seconds}", "-c:a", "pcm_s16le", str(path),
    ], check=True)
    return round(float(subprocess.run([
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "default=nw=1:nk=1", str(path),
    ], check=True, capture_output=True, text=True).stdout.strip()) * 1_000_000)


def one_column_grid(kind: str, duration_us: int) -> str:
    seconds = duration_us / 1_000_000
    header = (
        f"| 레이어 \\ 원본 시간 | B01 0.0–{seconds:g} |"
        if kind == "original"
        else f"| 레이어 \\ 목표 시간 | V01 0.0–{seconds:g} B01 |"
    )
    roles = ("T1", "T2", "A9_TEXT", "A10_TEXT_YELLOW", "A10_TEXT_WHITE", "STATE_LASER", "STATE_GLITCH", "STATE_FLICKER", "SCREEN_WHITE", "SCREEN_EFFECT", "VIDEO", "A9", "A10", "A11", "A12_RESERVED_EMPTY")
    transcript = "" if kind != "original" else f"""## 원본 5분류 대본

### B01 0.0–{seconds:g}
(상황설명) 테스트 장면. 화면 OCR: 없음
\"화자발언\" 없음
<나레이션> 없음
TTS화자발언 없음
TTS나레이션 없음

"""
    return transcript + "\n".join([header, "|---|---|", *(f"| {role} | 비움 |" for role in roles)]) + "\n"


def zero_caption(root: Path, audio_lock: Path, episode_id: str) -> Path:
    final_srt = root / "final.srt"
    final_srt.write_text("", encoding="utf-8")
    source_identity = root / "source_identity.json"
    timing = root / "caption_timing_evidence.json"
    write(timing, {
        "schema_version": "001short-caption-timing-evidence-v1", "status": "PASS",
        "episode_id": episode_id, "source_identity_path": source_identity.name,
        "source_identity_sha256": sha(source_identity), "tolerance_us": 50_000,
        "zero_caption": True, "mapping": [], "cues": [],
    })
    caption = root / "caption_lock.json"
    write(caption, {
        "schema_version": "001short-caption-lock-v2", "episode_id": episode_id, "status": "PASS",
        "audio_lock_path": audio_lock.name, "audio_lock_sha256": sha(audio_lock),
        "final_srt_path": final_srt.name, "final_srt_sha256": sha(final_srt),
        "final_cue_count": 0, "cues": [], "all_cues_within_measured_audio": True,
        "no_overlap_verified": True, "caption_timing_evidence_path": timing.name,
        "caption_timing_evidence_sha256": sha(timing),
    })
    return caption


class AudioCaptionContractV4Test(unittest.TestCase):
    def test_caption_only_silence_lock_has_no_audio_role_files(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            marker = root / "caption_only_silence.wav"
            duration = silence_wav(marker)
            identity = root / "source_identity.json"
            write(identity, {"schema_version": "source-identity-v1", "episode_id": "EP", "source_id": "S",
                             "source_fingerprint": sha(marker), "media_path": marker.name,
                             "media_sha256": sha(marker), "duration_us": duration})
            lock = root / "audio_lock.json"
            write(lock, {"schema_version": "001short-audio-lock-v4", "episode_id": "EP", "status": "PASS",
                         "production_mode": "URAKKAI", "audio_policy": "CAPTION_ONLY_MUTE_SOURCE",
                         "audio_source": "SILENCE", "audio_path": marker.name, "audio_sha256": sha(marker),
                         "measured_duration_us": duration, "audio_codec": "pcm_s16le", "ffprobe_verified": True,
                         "role_files": []})
            caption = zero_caption(root, lock, "EP")

            result = validate_audio_caption(lock, caption)
            self.assertEqual(result["status"], "PASS", result)

    def test_urakkai_order_preserving_trim_accepts_raw_source_clip_a10(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            clip = root / "source_clip.wav"
            duration = wav(clip)
            identity = root / "source_identity.json"
            write(identity, {"schema_version": "source-identity-v1", "episode_id": "EP", "source_id": "S",
                             "source_fingerprint": sha(clip), "media_path": clip.name,
                             "media_sha256": sha(clip), "duration_us": duration})
            lock = root / "audio_lock.json"
            write(lock, {"schema_version": "001short-audio-lock-v4", "episode_id": "EP", "status": "PASS",
                         "production_mode": "URAKKAI", "audio_policy": "SOURCE_ORDER_CLEAN_AUDIO",
                         "audio_source": "SOURCE_CLIP", "audio_path": clip.name, "audio_sha256": sha(clip),
                         "measured_duration_us": duration, "audio_codec": "pcm_s16le", "ffprobe_verified": True,
                         "role_files": [{"role": "A10", "audio_path": clip.name, "audio_sha256": sha(clip),
                                         "measured_duration_us": duration, "audio_codec": "pcm_s16le",
                                         "ffprobe_verified": True}]})
            caption = zero_caption(root, lock, "EP")

            result = validate_audio_caption(lock, caption)
            self.assertEqual(result["status"], "PASS", result)

    def test_urakkai_trim_only_label_relaxes_effective_clip_floor(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source = root / "source.mp4"; source.write_bytes(b"source")
            template = root / "root.zip"; template.write_bytes(b"root")
            manifest = root / "build_manifest.json"
            clips = [
                {"clip_id": "V01", "source_sha256": sha(source), "source_range_us": [1_000_000, 2_000_000], "target_range_us": [0, 1_000_000]},
                {"clip_id": "V02", "source_sha256": sha(source), "source_range_us": [2_000_000, 3_000_000], "target_range_us": [1_000_000, 2_000_000]},
            ]
            payload = {
                "schema_version": "001short-build-manifest-v1", "episode_id": "EP",
                "visual_asset_mode": "SOURCE_VIDEO_PROVISIONAL",
                "production_mode": "URAKKAI",
                "audio_policy": "SOURCE_ORDER_CLEAN_AUDIO", "audio_source": "SOURCE_CLIP",
                "source": {"path": str(source), "sha256": sha(source), "duration_us": 3_000_000},
                "template": {"root_name": "shrt white", "root_zip_path": str(template), "root_zip_sha256": sha(template)},
                "urakkai": {"production_type": "TRIM_ONLY_NO_REORDER", "target_duration_us": 2_000_000,
                            "reorder_required": False, "video_clips": clips},
                "source_audio": [
                    {"clip_id": "V01", "mode": "on", "source_sha256": sha(source), "source_range_us": [1_000_000, 2_000_000], "target_range_us": [0, 1_000_000]},
                    {"clip_id": "V02", "mode": "on", "source_sha256": sha(source), "source_range_us": [2_000_000, 3_000_000], "target_range_us": [1_000_000, 2_000_000]},
                ],
            }
            write(manifest, payload)
            passed = subprocess.run([sys.executable, str(PREBUILD), "--build-manifest", str(manifest)], capture_output=True, text=True, encoding="utf-8", check=False)
            self.assertEqual(passed.returncode, 0, passed.stdout)
            payload["urakkai"]["production_type"] = "REORDER"
            write(manifest, payload)
            failed = subprocess.run([sys.executable, str(PREBUILD), "--build-manifest", str(manifest)], capture_output=True, text=True, encoding="utf-8", check=False)
            self.assertNotEqual(failed.returncode, 0)
            self.assertIn("E_EFFECTIVE_CLIP", failed.stdout)

    def test_urakkai_reassembled_stem_is_bound_to_valid_full_stem_and_mapping(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source = root / "source.wav"; source_duration = wav(source)
            vocals = root / "vocals.wav"; wav(vocals)
            reassembled = root / "a10_reassembled.wav"; target_duration = wav(reassembled, 0.2)
            identity = root / "source_identity.json"
            write(identity, {"schema_version": "source-identity-v1", "episode_id": "EP", "source_id": "S", "source_fingerprint": sha(source), "media_path": source.name, "media_sha256": sha(source), "duration_us": source_duration})
            full = root / "vocal_stem_manifest.json"
            write(full, {"schema_version": "001short-vocal-stem-manifest-v1", "status": "STEM_GENERATED", "episode_id": "EP",
                         "source_path": source.name, "source_sha256": sha(source), "source_duration_us": source_duration,
                         "separator": {"engine": "demucs", "model": "htdemucs", "python_executable": "fixture"},
                         "vocals_path": vocals.name, "vocals_sha256": sha(vocals), "vocals_duration_us": source_duration,
                         "vocals_codec": "pcm_s16le", "vocals_ffprobe_verified": True, "capcut_audio_role": "A10",
                         "capcut_allowed_audio_path": vocals.name, "a12_policy": "EMPTY", "human_listen_qc_required": True})
            assembled = root / "reassembled_stem_manifest.json"
            build_manifest = root / "build_manifest.json"
            write(build_manifest, {"schema_version": "001short-build-manifest-v1", "episode_id": "EP", "urakkai": {"video_clips": [{"clip_id": "V01", "source_range_us": [200_000, 400_000], "target_range_us": [0, target_duration]}]}})
            plan = root / "production_plan.json"
            write(plan, {"schema_version": "001short-production-plan-v2", "episode_id": "EP", "timeline": [{"segment_key": "B02", "source_beat_id": "B02", "target_segment_id": "V01", "target_range_us": [0, target_duration], "placements": [{"anchor": "VIDEO", "source_range_us": [200_000, 400_000], "target_range_us": [0, target_duration]}]}]})
            write(assembled, {"schema_version": "001short-reassembled-stem-manifest-v2", "status": "PASS", "episode_id": "EP",
                              "full_stem_manifest_path": full.name, "full_stem_manifest_sha256": sha(full),
                              "build_manifest_path": build_manifest.name, "build_manifest_sha256": sha(build_manifest),
                              "production_plan_path": plan.name, "production_plan_sha256": sha(plan),
                              "reassembled_audio_path": reassembled.name, "reassembled_audio_sha256": sha(reassembled),
                              "target_duration_us": target_duration,
                              "mapping": [{"source_beat_id": "B02", "target_segment_id": "V01", "source_range_us": [200_000, 400_000], "target_range_us": [0, target_duration]}]})
            lock = root / "audio_lock.json"
            role = {"role": "A10", "audio_path": reassembled.name, "audio_sha256": sha(reassembled), "measured_duration_us": target_duration, "audio_codec": "pcm_s16le", "ffprobe_verified": True}
            write(lock, {"schema_version": "001short-audio-lock-v4", "episode_id": "EP", "status": "PASS", "production_mode": "URAKKAI",
                         "audio_policy": "A10_REASSEMBLED_SYNC", "audio_source": "REASSEMBLED_VOCAL_STEM", "audio_path": reassembled.name,
                         "audio_sha256": sha(reassembled), "measured_duration_us": target_duration, "audio_codec": "pcm_s16le", "ffprobe_verified": True,
                         "reassembled_stem_manifest_path": assembled.name, "reassembled_stem_manifest_sha256": sha(assembled), "role_files": [role]})
            caption = zero_caption(root, lock, "EP")
            passed = subprocess.run([sys.executable, str(SCRIPT), "--audio-lock", str(lock), "--caption-lock", str(caption)], capture_output=True, text=True, encoding="utf-8", check=False)
            self.assertEqual(passed.returncode, 0, passed.stdout)
            receipt = root / "production_plan_validation.json"
            write(receipt, {"status": "PASS", "errors": [], "evidence": {"production_plan_path": str(plan), "production_plan_sha256": sha(plan)}})
            foreign = root / "foreign_plan.json"; write(foreign, json.loads(plan.read_text(encoding="utf-8")))
            foreign_manifest = json.loads(assembled.read_text(encoding="utf-8"))
            foreign_manifest.update(production_plan_path=foreign.name, production_plan_sha256=sha(foreign))
            write(assembled, foreign_manifest)
            lock_payload = json.loads(lock.read_text(encoding="utf-8")); lock_payload["reassembled_stem_manifest_sha256"] = sha(assembled); write(lock, lock_payload)
            caption_payload = json.loads(caption.read_text(encoding="utf-8")); caption_payload["audio_lock_sha256"] = sha(lock); write(caption, caption_payload)
            canonical = validate_audio_caption(
                lock, caption,
                expected_production_plan_path=plan,
                expected_production_plan_sha256=sha(plan),
                expected_production_plan_receipt_path=receipt,
                expected_production_plan_receipt_sha256=sha(receipt),
            )
            self.assertIn("AUDIO_CAPTION_REASSEMBLED_STEM_AUTHORITY_MISMATCH", {row["code"] for row in canonical["errors"]})
            write(assembled, {**foreign_manifest, "production_plan_path": plan.name, "production_plan_sha256": sha(plan)})
            lock_payload["reassembled_stem_manifest_sha256"] = sha(assembled); write(lock, lock_payload)
            caption_payload["audio_lock_sha256"] = sha(lock); write(caption, caption_payload)
            full.write_text("{}", encoding="utf-8")
            assembled_payload = json.loads(assembled.read_text(encoding="utf-8")); assembled_payload["full_stem_manifest_sha256"] = sha(full); write(assembled, assembled_payload)
            lock_payload = json.loads(lock.read_text(encoding="utf-8")); lock_payload["reassembled_stem_manifest_sha256"] = sha(assembled); write(lock, lock_payload)
            caption_payload = json.loads(caption.read_text(encoding="utf-8")); caption_payload["audio_lock_sha256"] = sha(lock); write(caption, caption_payload)
            failed = subprocess.run([sys.executable, str(SCRIPT), "--audio-lock", str(lock), "--caption-lock", str(caption)], capture_output=True, text=True, encoding="utf-8", check=False)
            self.assertNotEqual(failed.returncode, 0)
            self.assertIn("AUDIO_CAPTION_REASSEMBLED_STEM_EVIDENCE_INVALID", failed.stdout)

    def test_clean_only_prebuild_requires_explicit_raw_source_matrix(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source = root / "source.mp4"; source.write_bytes(b"source")
            template = root / "root.zip"; template.write_bytes(b"root")
            manifest = root / "build_manifest.json"
            payload = {
                "schema_version": "001short-build-manifest-v1", "episode_id": "EP",
                "visual_asset_mode": "SOURCE_VIDEO_PROVISIONAL",
                "production_mode": "SOURCE_ORDER_UNCHANGED_CLEAN_ONLY",
                "audio_policy": "SOURCE_ORDER_CLEAN_AUDIO", "audio_source": "SOURCE_CLIP",
                "source": {"path": str(source), "sha256": sha(source), "duration_us": 1_000_000},
                "template": {"root_name": "shrt white", "root_zip_path": str(template), "root_zip_sha256": sha(template)},
                "urakkai": {"production_type": "SOURCE_ORDER_UNCHANGED_CLEAN_ONLY", "target_duration_us": 1_000_000,
                            "reorder_required": False, "video_clips": [{"clip_id": "B01", "source_sha256": sha(source), "source_range_us": [0, 1_000_000], "target_range_us": [0, 1_000_000]}]},
                "source_audio": [{"clip_id": "B01", "mode": "on", "source_sha256": sha(source), "source_range_us": [0, 1_000_000], "target_range_us": [0, 1_000_000]}],
            }
            write(manifest, payload)
            passed = subprocess.run([sys.executable, str(PREBUILD), "--build-manifest", str(manifest)], capture_output=True, text=True, encoding="utf-8", check=False)
            self.assertEqual(passed.returncode, 0, passed.stdout)
            payload["audio_source"] = "SOURCE_VOCAL_STEM"
            write(manifest, payload)
            failed = subprocess.run([sys.executable, str(PREBUILD), "--build-manifest", str(manifest)], capture_output=True, text=True, encoding="utf-8", check=False)
            self.assertNotEqual(failed.returncode, 0)
            self.assertIn("E_AUDIO_MODE_MATRIX", failed.stdout)

    def test_clean_only_zero_caption_cli_passes_and_has_concise_json(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            audio = root / "source_audio.wav"
            duration = wav(audio)
            identity = root / "source_identity.json"
            write(identity, {
                "schema_version": "source-identity-v1", "episode_id": "EP", "source_id": "SRC",
                "source_fingerprint": sha(audio), "media_path": audio.name, "media_sha256": sha(audio),
                "duration_us": duration,
            })
            lock = root / "audio_lock.json"
            role = {"role": "A10", "audio_path": audio.name, "audio_sha256": sha(audio),
                    "measured_duration_us": duration, "audio_codec": "pcm_s16le", "ffprobe_verified": True}
            write(lock, {
                "schema_version": "001short-audio-lock-v4", "episode_id": "EP", "status": "PASS",
                "production_mode": "SOURCE_ORDER_UNCHANGED_CLEAN_ONLY",
                "audio_policy": "SOURCE_ORDER_CLEAN_AUDIO", "audio_source": "SOURCE_CLIP",
                "audio_path": audio.name, "audio_sha256": sha(audio), "measured_duration_us": duration,
                "audio_codec": "pcm_s16le", "ffprobe_verified": True,
                "source_identity_path": identity.name, "source_identity_sha256": sha(identity),
                "role_files": [role],
            })
            caption = zero_caption(root, lock, "EP")
            completed = subprocess.run([
                sys.executable, str(SCRIPT), "--audio-lock", str(lock), "--caption-lock", str(caption),
            ], capture_output=True, text=True, encoding="utf-8", check=False)
            self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
            payload = json.loads(completed.stdout)
            self.assertEqual(payload["status"], "PASS")
            self.assertEqual(payload["evidence"]["caption_cue_count"], 0)

    def test_clean_only_never_accepts_implicit_demucs_switch(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            audio = root / "audio.wav"; duration = wav(audio)
            identity = root / "source_identity.json"
            write(identity, {"schema_version": "source-identity-v1", "episode_id": "EP", "source_id": "S",
                             "source_fingerprint": sha(audio), "media_path": audio.name, "media_sha256": sha(audio), "duration_us": duration})
            lock = root / "audio_lock.json"
            write(lock, {"schema_version": "001short-audio-lock-v4", "episode_id": "EP", "status": "PASS",
                         "production_mode": "SOURCE_ORDER_UNCHANGED_CLEAN_ONLY", "audio_policy": "SOURCE_ORDER_CLEAN_AUDIO",
                         "audio_source": "SOURCE_VOCAL_STEM", "audio_path": audio.name, "audio_sha256": sha(audio),
                         "measured_duration_us": duration, "audio_codec": "pcm_s16le", "ffprobe_verified": True,
                         "source_identity_path": identity.name, "source_identity_sha256": sha(identity), "role_files": []})
            caption = zero_caption(root, lock, "EP")
            completed = subprocess.run([sys.executable, str(SCRIPT), "--audio-lock", str(lock), "--caption-lock", str(caption)], capture_output=True, text=True, encoding="utf-8", check=False)
            self.assertNotEqual(completed.returncode, 0)
            self.assertIn("AUDIO_CAPTION_MODE_MATRIX_MISMATCH", completed.stdout)

    def test_self_consistent_shifted_srt_and_lock_fail_source_timing_receipt(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            audio = root / "audio.wav"; duration = wav(audio)
            identity = root / "source_identity.json"
            write(identity, {"schema_version": "source-identity-v1", "episode_id": "EP", "source_id": "S",
                             "source_fingerprint": sha(audio), "media_path": audio.name, "media_sha256": sha(audio), "duration_us": duration})
            lock = root / "audio_lock.json"
            role = {"role": "A10", "audio_path": audio.name, "audio_sha256": sha(audio), "measured_duration_us": duration, "audio_codec": "pcm_s16le", "ffprobe_verified": True}
            write(lock, {"schema_version": "001short-audio-lock-v4", "episode_id": "EP", "status": "PASS",
                         "production_mode": "SOURCE_ORDER_UNCHANGED_CLEAN_ONLY", "audio_policy": "SOURCE_ORDER_CLEAN_AUDIO",
                         "audio_source": "SOURCE_CLIP", "audio_path": audio.name, "audio_sha256": sha(audio),
                         "measured_duration_us": duration, "audio_codec": "pcm_s16le", "ffprobe_verified": True,
                         "source_identity_path": identity.name, "source_identity_sha256": sha(identity), "role_files": [role]})
            srt = root / "final.srt"; srt.write_text("C1\n00:00:00,100 --> 00:00:00,200\n자막\n", encoding="utf-8")
            timing = root / "caption_timing_evidence.json"
            timeline = root / "approved_timeline.json"
            write(timeline, {"schema_version": "approved-timeline-v1", "episode_id": "EP", "source_fingerprint": sha(audio), "segments": [{"segment_id": "CAP1", "timeline_order": 1, "role": "A10_TEXT", "start": 100_000, "duration": 100_000, "source_ref": "B01", "source_range_us": [100_000, 200_000], "cue_id": "C1", "text": "자막"}]})
            build_manifest = root / "build_manifest.json"
            write(build_manifest, {"schema_version": "001short-build-manifest-v1", "episode_id": "EP", "urakkai": {"video_clips": [{"clip_id": "V01", "source_range_us": [0, duration], "target_range_us": [0, duration]}]}})
            plan = root / "production_plan.json"
            write(plan, {"schema_version": "001short-production-plan-v2", "episode_id": "EP", "timeline": [{"segment_key": "B01", "source_beat_id": "B01", "target_segment_id": "V01", "target_range_us": [0, duration], "placements": [{"anchor": "VIDEO", "source_range_us": [0, duration], "target_range_us": [0, duration]}]}]})
            original_grid = root / "original-capcut-grid.md"; original_grid.write_text(one_column_grid("original", duration), encoding="utf-8")
            urakkai_grid = root / "urakkai-capcut-grid.md"; urakkai_grid.write_text(one_column_grid("urakkai", duration), encoding="utf-8")
            write(timing, {"schema_version": "001short-caption-timing-evidence-v2", "status": "PASS", "episode_id": "EP",
                           "source_identity_path": identity.name, "source_identity_sha256": sha(identity), "tolerance_us": 10_000,
                           "approved_timeline_path": timeline.name, "approved_timeline_sha256": sha(timeline),
                           "build_manifest_path": build_manifest.name, "build_manifest_sha256": sha(build_manifest),
                           "production_plan_path": plan.name, "production_plan_sha256": sha(plan),
                           "original_grid_path": original_grid.name, "original_grid_sha256": sha(original_grid),
                           "urakkai_grid_path": urakkai_grid.name, "urakkai_grid_sha256": sha(urakkai_grid),
                           "zero_caption": False,
                           "mapping": [{"mapping_id": "M1", "source_beat_id": "B01", "target_segment_id": "V01", "source_range_us": [0, duration], "target_range_us": [0, duration]}],
                           "cues": [{"cue_id": "C1", "text": "자막", "authority": "BURNED_TEXT_FRAME", "mapping_id": "M1", "source_range_us": [100_000, 200_000], "target_range_us": [100_000, 200_000], "bound_file_path": audio.name, "bound_file_sha256": sha(audio)}]})
            caption = root / "caption_lock.json"
            payload = {"schema_version": "001short-caption-lock-v2", "episode_id": "EP", "status": "PASS",
                       "audio_lock_path": lock.name, "audio_lock_sha256": sha(lock), "final_srt_path": srt.name,
                       "final_srt_sha256": sha(srt), "final_cue_count": 1,
                       "cues": [{"cue_id": "C1", "start_us": 100_000, "end_us": 200_000, "text": "자막", "layer": "A10_TEXT", "caption_role": "A10_TEXT"}],
                       "all_cues_within_measured_audio": True, "no_overlap_verified": True,
                       "caption_timing_evidence_path": timing.name, "caption_timing_evidence_sha256": sha(timing)}
            write(caption, payload)
            passed = subprocess.run([sys.executable, str(SCRIPT), "--audio-lock", str(lock), "--caption-lock", str(caption)], capture_output=True, text=True, encoding="utf-8", check=False)
            self.assertEqual(passed.returncode, 0, passed.stdout)
            timing_payload = json.loads(timing.read_text(encoding="utf-8"))
            timing_payload["mapping"][0].update(source_beat_id="B99", target_segment_id="V99")
            write(timing, timing_payload)
            payload["caption_timing_evidence_sha256"] = sha(timing); write(caption, payload)
            wrong_ids = subprocess.run([sys.executable, str(SCRIPT), "--audio-lock", str(lock), "--caption-lock", str(caption)], capture_output=True, text=True, encoding="utf-8", check=False)
            self.assertNotEqual(wrong_ids.returncode, 0)
            self.assertIn("CAPTION_TIMING_BUILD_MAPPING_MISMATCH", wrong_ids.stdout)
            timing_payload["mapping"][0].update(source_beat_id="B01", target_segment_id="V01")
            write(timing, timing_payload)
            srt.write_text("C1\n00:00:00,150 --> 00:00:00,250\n자막\n", encoding="utf-8")
            payload["final_srt_sha256"] = sha(srt)
            payload["cues"][0].update(start_us=150_000, end_us=250_000)
            timing_payload = json.loads(timing.read_text(encoding="utf-8"))
            timing_payload["cues"][0]["source_range_us"] = [150_000, 250_000]
            timing_payload["cues"][0]["target_range_us"] = [150_000, 250_000]
            write(timing, timing_payload)
            payload["caption_timing_evidence_sha256"] = sha(timing)
            write(caption, payload)
            failed = subprocess.run([sys.executable, str(SCRIPT), "--audio-lock", str(lock), "--caption-lock", str(caption)], capture_output=True, text=True, encoding="utf-8", check=False)
            self.assertNotEqual(failed.returncode, 0)
            self.assertIn("CAPTION_TIMING_SOURCE_MISMATCH", failed.stdout)


if __name__ == "__main__":
    unittest.main()

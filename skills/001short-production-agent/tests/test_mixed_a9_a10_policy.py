from __future__ import annotations

import json
import argparse
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


SKILL = Path(__file__).resolve().parents[1]
SCRIPTS = SKILL / "scripts"
GRID_ORIGINAL = SKILL / "tests" / "fixtures" / "original_grid_8.pass.md"
GRID_URAKKAI = SKILL / "tests" / "fixtures" / "urakkai_grid_8.pass.md"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import build_episode_capcut as builder
import build_root_provisional_short as legacy_builder
import validate_design_lock
from test_public_builder_provisional import bind_state_artifacts, install_valid_grids, media, sha, template_archive, write


class MixedA9A10PolicyTest(unittest.TestCase):
    """A9_TTS_PLUS_A10_RETAINED keeps our generated narration and the retained
    source speech on their own lanes at the same time."""

    @unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"), "media tools required")
    def test_mixed_policy_builds_a9_narration_without_clearing_a10(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            episode = root / "episode"
            episode.mkdir()
            install_valid_grids(episode, mixed=True)
            source, vocals = media(root)
            narration = root / "tts_01.wav"
            subprocess.run([
                "ffmpeg", "-loglevel", "error", "-f", "lavfi", "-i",
                "sine=frequency=660:duration=1", "-ar", "48000", "-ac", "1",
                "-c:a", "pcm_s16le", "-y", str(narration),
            ], check=True)
            archive, _, contract = template_archive(root)

            identity = episode / "source_identity.json"
            write(identity, {
                "schema_version": "source-identity-v1", "episode_id": "EP", "source_id": "SRC",
                "source_fingerprint": "fp", "media_path": str(source), "media_sha256": sha(source),
            })
            rows = [
                {"segment_id": "V2", "timeline_order": 0, "role": "VIDEO", "start": 0, "duration": 1_000_000, "source_ref": "SRC"},
                {"segment_id": "V1", "timeline_order": 1, "role": "VIDEO", "start": 1_000_000, "duration": 1_000_000, "source_ref": "SRC"},
                {"segment_id": "T2", "timeline_order": 2, "role": "T2", "start": 0, "duration": 2_000_000, "source_ref": "SRC", "text": "subtitle", "content_type": "TITLE"},
                {"segment_id": "T1", "timeline_order": 3, "role": "T1", "start": 0, "duration": 2_000_000, "source_ref": "SRC", "text": "title", "content_type": "TITLE"},
                {"segment_id": "SCR_FX", "timeline_order": 4, "role": "SCREEN_EFFECT", "start": 0, "duration": 2_000_000, "source_ref": "SRC"},
                {"segment_id": "SCR_WHITE", "timeline_order": 5, "role": "SCREEN_WHITE", "start": 0, "duration": 2_000_000, "source_ref": "SRC"},
                {"segment_id": "SP1", "timeline_order": 6, "role": "A10_TEXT", "start": 0, "duration": 1_000_000, "source_ref": "SRC", "text": "hello", "content_type": "SPEAKER", "caption_role": "A10_TEXT", "speaker_id": "P1", "color_role": "WHITE"},
                {"segment_id": "SP2", "timeline_order": 7, "role": "A10_TEXT", "start": 1_000_000, "duration": 1_000_000, "source_ref": "SRC", "text": "there", "content_type": "SPEAKER", "caption_role": "A10_TEXT", "speaker_id": "P2", "color_role": "YELLOW"},
                {"segment_id": "TTS01", "timeline_order": 8, "role": "A9", "start": 0, "duration": 1_000_000, "source_ref": "SRC", "text": "narration", "content_type": "TTS", "cue_id": "TTS01"},
                {"segment_id": "TTS01_TXT", "timeline_order": 9, "role": "A9_TEXT", "start": 0, "duration": 1_000_000, "source_ref": "SRC", "text": "narration", "content_type": "TTS", "caption_role": "A9_TEXT", "cue_id": "TTS01"},
                {"segment_id": "A10-1", "timeline_order": 10, "role": "A10", "start": 0, "duration": 1_000_000, "source_ref": "SRC"},
                {"segment_id": "A10-2", "timeline_order": 11, "role": "A10", "start": 1_000_000, "duration": 1_000_000, "source_ref": "SRC"},
            ]
            timeline = episode / "approved_timeline.json"
            write(timeline, {
                "schema_version": "approved-timeline-v1", "episode_id": "EP",
                "source_fingerprint": "fp", "audio_policy": "A9_TTS_PLUS_A10_RETAINED",
                "primary_speaker_id": "P1", "segments": rows,
            })
            handoff = episode / "design_handoff.json"
            write(handoff, {
                "schema_version": "tikitaka-design-handoff-v1", "episode_id": "EP", "status": "PASS",
                "source_identity_path": identity.name, "source_identity_sha256": sha(identity),
                "timeline_path": timeline.name, "timeline_sha256": sha(timeline), "source_fingerprint": "fp",
                "approved_timeline_order": [row["segment_id"] for row in rows],
            })
            evidence = episode / "design_evidence.json"
            self.assertEqual(
                validate_design_lock.validate_handoff(handoff, identity, timeline, evidence)["status"],
                "PASS",
            )

            vocal_manifest = episode / "vocal_stem_manifest.json"
            write(vocal_manifest, {
                "schema_version": "001short-vocal-stem-manifest-v1", "status": "STEM_GENERATED", "episode_id": "EP",
                "source_path": str(source), "source_sha256": sha(source), "source_duration_us": 2_000_000,
                "separator": {"engine": "demucs", "model": "htdemucs", "python_executable": "python"},
                "vocals_path": str(vocals), "vocals_sha256": sha(vocals), "vocals_duration_us": 2_000_000,
                "vocals_codec": "pcm_s16le", "vocals_ffprobe_verified": True, "capcut_audio_role": "A10",
                "capcut_allowed_audio_path": str(vocals), "a12_policy": "EMPTY", "human_listen_qc_required": True,
            })
            tts_evidence = episode / "tts_evidence.json"
            narration_file = {
                "audio_path": str(narration), "audio_sha256": sha(narration),
                "measured_duration_us": 1_000_000, "audio_codec": "pcm_s16le", "ffprobe_verified": True,
            }
            write(tts_evidence, {
                "schema_version": "001short-tts-evidence-v2", "episode_id": "EP", "provider": "fixture",
                "audio_sha256": sha(narration), "measured_duration_us": 1_000_000,
                "audio_codec": "pcm_s16le", "ffprobe_verified": True,
            })
            audio_lock = episode / "audio_lock.json"
            stem_file = {
                "audio_path": str(vocals), "audio_sha256": sha(vocals),
                "measured_duration_us": 2_000_000, "audio_codec": "pcm_s16le", "ffprobe_verified": True,
            }
            write(audio_lock, {
                "schema_version": "001short-audio-lock-v3", "episode_id": "EP", "status": "PASS",
                "audio_source": "SOURCE_VOCAL_STEM", **stem_file,
                "vocal_stem_manifest_path": vocal_manifest.name,
                "vocal_stem_manifest_sha256": sha(vocal_manifest),
                "tts_evidence_path": tts_evidence.name, "tts_evidence_sha256": sha(tts_evidence),
                "role_files": [{"role": "A10", **stem_file}, {"role": "A9", **narration_file}],
            })
            srt = episode / "final.srt"
            srt.write_text(
                "TTS01\n00:00:00,000 --> 00:00:01,000\nnarration\n\n"
                "SP1\n00:00:00,000 --> 00:00:01,000\nhello\n\n"
                "SP2\n00:00:01,000 --> 00:00:02,000\nthere\n",
                encoding="utf-8",
            )
            caption = episode / "caption_lock.json"
            write(caption, {
                "schema_version": "001short-caption-lock-v1", "episode_id": "EP", "status": "PASS",
                "audio_lock_path": audio_lock.name, "audio_lock_sha256": sha(audio_lock),
                "final_srt_path": srt.name, "final_srt_sha256": sha(srt), "final_cue_count": 3,
                "cues": [
                    {"cue_id": "TTS01", "start_us": 0, "end_us": 1_000_000, "text": "narration", "layer": "A9_TEXT"},
                    {"cue_id": "SP1", "start_us": 0, "end_us": 1_000_000, "text": "hello", "layer": "A10_TEXT"},
                    {"cue_id": "SP2", "start_us": 1_000_000, "end_us": 2_000_000, "text": "there", "layer": "A10_TEXT"},
                ],
                "all_cues_within_measured_audio": True, "no_overlap_verified": True,
            })
            state = episode / "90_workflow" / "state.json"
            write(state, {
                "episode_id": "EP", "status": "AUDIO_CAPTION_VALIDATED",
                "audio_lock_path": str(audio_lock), "audio_lock_sha256": sha(audio_lock),
                "caption_lock_path": str(caption), "caption_lock_sha256": sha(caption),
            })
            build_manifest = episode / "build_manifest.json"
            write(build_manifest, {
                "schema_version": "001short-build-manifest-v1", "episode_id": "EP",
                "visual_asset_mode": "SOURCE_VIDEO_PROVISIONAL",
                "source": {"path": str(source), "sha256": sha(source), "duration_us": 2_000_000},
                "template": {"root_name": "shrt white", "root_zip_path": str(archive), "root_zip_sha256": sha(archive)},
                "urakkai": {
                    "production_type": "URAKKAI", "target_duration_us": 2_000_000, "reorder_required": True,
                    "locked_permutation": ["V2", "V1"],
                    "video_clips": [
                        {"clip_id": "V2", "source_sha256": sha(source), "source_range_us": [1_000_000, 2_000_000], "target_range_us": [0, 1_000_000]},
                        {"clip_id": "V1", "source_sha256": sha(source), "source_range_us": [0, 1_000_000], "target_range_us": [1_000_000, 2_000_000]},
                    ],
                },
                "source_audio": [
                    {"clip_id": "V2", "mode": "duck", "source_sha256": sha(source), "source_range_us": [1_000_000, 2_000_000], "target_range_us": [0, 1_000_000]},
                    {"clip_id": "V1", "mode": "on", "source_sha256": sha(source), "source_range_us": [0, 1_000_000], "target_range_us": [1_000_000, 2_000_000]},
                ],
            })
            bind_state_artifacts(
                state, timeline=timeline, build_manifest=build_manifest,
                design_evidence=evidence, audio_lock=audio_lock, caption_lock=caption,
            )
            config = {
                "episode_id": "EP", "visual_asset_mode": "SOURCE_VIDEO_PROVISIONAL",
                "duration_us": 2_000_000, "T1": "title", "T2": "subtitle", "state_cues": [],
                "tts_cues": [{
                    "cue_id": "TTS01", "text": "narration", "target_range_us": [0, 1_000_000],
                    "audio_path": str(narration), "resource_name": "tts_01.wav",
                }],
                "project_name": "project", "episode_root": str(episode), "work_root": str(root / "work"),
                "local_capcut_root": str(root / "capcut"), "source_identity_path": str(identity),
                "approved_timeline_path": str(timeline), "design_handoff_path": str(handoff),
                "design_lock_evidence_path": str(evidence), "build_manifest_path": str(build_manifest),
                "state_path": str(state), "audio_policy": "A9_TTS_PLUS_A10_RETAINED",
                "root_contract_path": contract.name, "workspace_root": str(root),
                "root_profile": "home_windows",
            }

            def relock_timeline() -> None:
                payload = json.loads(handoff.read_text(encoding="utf-8"))
                payload["timeline_sha256"] = sha(timeline)
                write(handoff, payload)
                locked = validate_design_lock.validate_handoff(
                    handoff, identity, timeline, evidence, allow_relock=True
                )
                self.assertEqual(locked["status"], "PASS", locked)

            original_timeline = json.loads(timeline.read_text(encoding="utf-8"))
            partial_timeline = json.loads(timeline.read_text(encoding="utf-8"))
            for row in partial_timeline["segments"]:
                if row.get("role") in {"A9", "A9_TEXT"}:
                    row["start"] = 500_000
                    row["duration"] = 500_000
            write(timeline, partial_timeline)
            config["tts_cues"][0]["target_range_us"] = [500_000, 1_000_000]
            partial_manifest = json.loads(build_manifest.read_text(encoding="utf-8"))
            partial_manifest["source_audio"][0]["target_range_us"] = [0, 2_000_000]
            partial_manifest["source_audio"][0]["mode"] = "duck"
            write(build_manifest, partial_manifest)
            relock_timeline()
            bind_state_artifacts(
                state, timeline=timeline, build_manifest=build_manifest,
                design_evidence=evidence, audio_lock=audio_lock, caption_lock=caption,
            )
            with patch.object(builder, "_assert_capcut_closed_for_target", return_value=None), patch.object(
                builder, "_register_capcut_project", return_value=None
            ):
                with self.assertRaisesRegex(
                    RuntimeError,
                    "MIXED_A10_PARTIAL_OVERLAP_UNSUPPORTED:V2",
                ):
                    builder.build_episode(config)
            write(timeline, original_timeline)
            relock_timeline()
            config["tts_cues"][0]["target_range_us"] = [0, 1_000_000]
            write(build_manifest, {
                **partial_manifest,
                "source_audio": [
                    {
                        **partial_manifest["source_audio"][0],
                        "target_range_us": [0, 1_000_000],
                    },
                    partial_manifest["source_audio"][1],
                ],
            })
            bind_state_artifacts(
                state, timeline=timeline, build_manifest=build_manifest,
                design_evidence=evidence, audio_lock=audio_lock, caption_lock=caption,
            )
            invalid_manifest = json.loads(build_manifest.read_text(encoding="utf-8"))
            invalid_manifest["source_audio"][0]["mode"] = "on"
            write(build_manifest, invalid_manifest)
            bind_state_artifacts(
                state, timeline=timeline, build_manifest=build_manifest,
                design_evidence=evidence, audio_lock=audio_lock, caption_lock=caption,
            )
            with patch.object(builder, "_assert_capcut_closed_for_target", return_value=None), patch.object(
                builder, "_register_capcut_project", return_value=None
            ):
                with self.assertRaisesRegex(
                    RuntimeError,
                    "MIXED_A10_MUTE_REQUIRED_UNDER_A9:V2",
                ):
                    builder.build_episode(config)
            invalid_manifest["source_audio"][0]["mode"] = "duck"
            write(build_manifest, invalid_manifest)
            bind_state_artifacts(
                state, timeline=timeline, build_manifest=build_manifest,
                design_evidence=evidence, audio_lock=audio_lock, caption_lock=caption,
            )
            with patch.object(builder, "_assert_capcut_closed_for_target", return_value=None), patch.object(
                builder, "_register_capcut_project", return_value=None
            ):
                result = builder.build_episode(config)

            self.assertEqual(result["status"], "CAPCUT_STATIC_VALIDATED")
            normalized = json.loads(
                (root / "capcut" / "project" / "draft_content.json").read_text(encoding="utf-8")
            )
            a9 = normalized["tracks"][builder.TRACK_INDEX["A9"]]["segments"]
            a10 = normalized["tracks"][builder.TRACK_INDEX["A10"]]["segments"]
            a9_text = normalized["tracks"][builder.TRACK_INDEX["A9_TEXT"]]["segments"]
            a10_text_white = normalized["tracks"][builder.TRACK_INDEX["A10_TEXT_WHITE"]]["segments"]
            a10_text_yellow = normalized["tracks"][builder.TRACK_INDEX["A10_TEXT_YELLOW"]]["segments"]
            # The regression this guards: TTS_ONLY cleared A10, so a mixed episode
            # silently lost every retained-speech segment.
            self.assertEqual(len(a9), 1)
            self.assertEqual(a9[0].get("volume"), 1.0)
            self.assertEqual(len(a9_text), 1)
            self.assertEqual(len(a10), 2)
            self.assertEqual(a10[0].get("volume"), 0.0)
            self.assertEqual(a10[1].get("volume"), 1.0)
            self.assertEqual(len(a10_text_white), 1)
            self.assertEqual(len(a10_text_yellow), 1)
            self.assertEqual(a9_text[0]["target_timerange"], a10_text_white[0]["target_timerange"])
            self.assertEqual(normalized["tracks"][builder.TRACK_INDEX["A11"]]["segments"], [])
            self.assertEqual(normalized["tracks"][builder.A12_INDEX]["segments"], [])
            materials = builder._materials(normalized["materials"])
            self.assertFalse(any(row.get("role") == "A11" for row in materials))
            self.assertFalse(any(row.get("role") in {"A12", "A12_RESERVED_EMPTY"} for row in materials))
            media_dir = root / "capcut" / "project" / "Resources" / "media"
            self.assertTrue((media_dir / "tts_01.wav").is_file())
            self.assertTrue((media_dir / "a10_vocal_stem.wav").is_file())

            draft_path = root / "capcut" / "project" / "draft_content.json"
            broken = json.loads(draft_path.read_text(encoding="utf-8"))
            broken["tracks"][builder.TRACK_INDEX["A10"]]["segments"][0]["volume"] = 1.0
            write(draft_path, broken)
            postbuild = builder.validate_postbuild.validate_postbuild(build_manifest, draft_path.parent)
            self.assertEqual(postbuild["status"], "FAIL")
            self.assertIn(
                {"code": "E_DRAFT_MISMATCH", "detail": "a10_volume", "clip_id": "V2"},
                postbuild["errors"],
            )

            broken["tracks"][builder.TRACK_INDEX["A10"]]["segments"][0]["volume"] = 0.0
            broken["tracks"][builder.TRACK_INDEX["A9"]]["segments"][0]["volume"] = 0.0
            write(draft_path, broken)
            postbuild = builder.validate_postbuild.validate_postbuild(build_manifest, draft_path.parent)
            self.assertEqual(postbuild["status"], "FAIL")
            self.assertIn(
                {"code": "E_DRAFT_MISMATCH", "detail": "a9_volume", "segment_id": "TTS01"},
                postbuild["errors"],
            )

    def test_legacy_12_track_builder_rejects_mixed_policy_at_public_boundary(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source = root / "source.mp4"
            source.write_bytes(b"fixture")
            assembly = root / "assembly.json"
            write(assembly, {
                "timeline": {
                    "audio_policy": "A9_TTS_PLUS_A10_RETAINED",
                    "target_duration_us": 1_000_000,
                    "clips": [{
                        "clip_id": "C1", "source_start_us": 0, "source_duration_us": 1_000_000,
                        "target_start_us": 0, "target_duration_us": 1_000_000,
                    }],
                },
            })
            _, _, contract = template_archive(root)
            args = argparse.Namespace(
                workspace_root=root, root_contract=contract, assembly_input=assembly,
                source_video=source, source_audio=None, episode_evidence_root=root / "evidence",
                episode_id="EP", title1="title", title2="subtitle", capcut_root=root / "capcut",
                project_name="legacy", report=root / "report.json",
            )
            with patch.object(legacy_builder, "_capcut_open", return_value=False):
                with self.assertRaisesRegex(
                    RuntimeError,
                    "LEGACY_12_TRACK_AUDIO_POLICY_UNSUPPORTED:A9_TTS_PLUS_A10_RETAINED",
                ):
                    legacy_builder.build(args)


if __name__ == "__main__":
    unittest.main()

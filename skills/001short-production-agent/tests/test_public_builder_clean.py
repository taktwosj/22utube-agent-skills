import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


SKILL = Path(__file__).resolve().parents[1]
SCRIPTS = SKILL / "scripts"
TESTS = Path(__file__).resolve().parent
for path in (SCRIPTS, TESTS):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

import build_episode_capcut as builder
import validate_clean_visual
import validate_design_lock
from test_public_builder_provisional import media, sha, template_archive, write


class PublicBuilderCleanTest(unittest.TestCase):
    @unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"), "media tools required")
    def test_public_builder_finishes_with_real_clean_vmake_chain(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); episode = root / "episode"; episode.mkdir()
            source, vocals = media(root)
            archive, _, contract = template_archive(root)
            clean_root = episode / "40_assets_used"; clean_root.mkdir()
            clean_video = clean_root / "clean_video.mp4"
            subprocess.run([
                "ffmpeg", "-loglevel", "error", "-f", "lavfi", "-i",
                "color=c=blue:s=1080x1920:r=30:d=2", "-y", str(clean_video),
            ], check=True)

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
                {"segment_id": "A10-1", "timeline_order": 7, "role": "A10", "start": 0, "duration": 1_000_000, "source_ref": "SRC"},
                {"segment_id": "A10-2", "timeline_order": 8, "role": "A10", "start": 1_000_000, "duration": 1_000_000, "source_ref": "SRC"},
            ]
            timeline = episode / "approved_timeline.json"
            write(timeline, {"schema_version": "approved-timeline-v1", "episode_id": "EP", "source_fingerprint": "fp", "audio_policy": "A10_RETAINED_SYNC", "primary_speaker_id": "P1", "segments": rows})
            handoff = episode / "design_handoff.json"
            write(handoff, {"schema_version": "tikitaka-design-handoff-v1", "episode_id": "EP", "status": "PASS", "source_identity_path": identity.name, "source_identity_sha256": sha(identity), "timeline_path": timeline.name, "timeline_sha256": sha(timeline), "source_fingerprint": "fp", "approved_timeline_order": [row["segment_id"] for row in rows]})
            evidence = episode / "design_evidence.json"
            self.assertEqual(validate_design_lock.validate_handoff(handoff, identity, timeline, evidence)["status"], "PASS")

            vocal_manifest = episode / "vocal_stem_manifest.json"
            write(vocal_manifest, {"schema_version": "001short-vocal-stem-manifest-v1", "status": "STEM_GENERATED", "episode_id": "EP", "source_path": str(source), "source_sha256": sha(source), "source_duration_us": 2_000_000, "separator": {"engine": "demucs", "model": "htdemucs", "python_executable": "python"}, "vocals_path": str(vocals), "vocals_sha256": sha(vocals), "vocals_duration_us": 2_000_000, "vocals_codec": "pcm_s16le", "vocals_ffprobe_verified": True, "capcut_audio_role": "A10", "capcut_allowed_audio_path": str(vocals), "a12_policy": "EMPTY", "human_listen_qc_required": True})
            audio_file = {"audio_path": str(vocals), "audio_sha256": sha(vocals), "measured_duration_us": 2_000_000, "audio_codec": "pcm_s16le", "ffprobe_verified": True}
            audio_lock = episode / "audio_lock.json"
            write(audio_lock, {"schema_version": "001short-audio-lock-v3", "episode_id": "EP", "status": "PASS", "audio_source": "SOURCE_VOCAL_STEM", **audio_file, "vocal_stem_manifest_path": vocal_manifest.name, "vocal_stem_manifest_sha256": sha(vocal_manifest), "role_files": [{"role": "A10", **audio_file}]})
            srt = episode / "final.srt"; srt.write_text("1\n00:00:00,000 --> 00:00:01,000\nhello\n", encoding="utf-8")
            caption = episode / "caption_lock.json"
            write(caption, {"schema_version": "001short-caption-lock-v1", "episode_id": "EP", "status": "PASS", "audio_lock_path": audio_lock.name, "audio_lock_sha256": sha(audio_lock), "final_srt_path": srt.name, "final_srt_sha256": sha(srt), "final_cue_count": 1, "cues": [{"cue_id": "1", "start_us": 0, "end_us": 1_000_000, "text": "hello", "layer": "A10_TEXT", "caption_role": "A10_TEXT"}], "all_cues_within_measured_audio": True, "no_overlap_verified": True})
            state = episode / "90_workflow" / "state.json"
            write(state, {"episode_id": "EP", "current_stage": "08", "status": "AUDIO_CAPTION_VALIDATED", "audio_lock_path": str(audio_lock), "audio_lock_sha256": sha(audio_lock), "caption_lock_path": str(caption), "caption_lock_sha256": sha(caption)})

            clean_manifest = clean_root / "clean_visual_manifest.json"
            write(clean_manifest, {"schema_version": "001short-clean-visual-manifest-v1", "episode_id": "EP", "source_identity_path": str(identity), "source_identity_sha256": sha(identity), "design_lock_evidence_path": str(evidence), "design_lock_evidence_sha256": sha(evidence), "clean_source_path": clean_video.name, "clean_source_sha256": sha(clean_video), "expected_duration_us": 2_000_000, "expected_width": 1080, "expected_height": 1920})
            clean_receipt = clean_root / "clean_visual_receipt.json"
            self.assertEqual(validate_clean_visual.validate_clean_visual(clean_manifest, identity, evidence, clean_receipt, clean_root)["status"], "PASS")
            vmake_receipt = clean_root / "vmake_receipt.json"
            write(vmake_receipt, {"provider": "vmake", "run_id": "run", "job_id": "job", "uploaded_source_sha256": sha(source), "downloaded_output_sha256": sha(clean_video), "final_download": True})
            build_manifest = episode / "build_manifest.json"
            write(build_manifest, {"schema_version": "001short-build-manifest-v1", "episode_id": "EP", "visual_asset_mode": "CLEAN_VISUAL_READY", "source": {"path": str(source), "sha256": sha(source), "duration_us": 2_000_000}, "template": {"root_name": "shrt white", "root_zip_path": str(archive), "root_zip_sha256": sha(archive)}, "vmake": {"receipt_path": str(vmake_receipt), "output_path": str(clean_video), "run_id": "run", "job_id": "job", "input_sha256": sha(source), "output_sha256": sha(clean_video), "final_download": True}, "urakkai": {"production_type": "URAKKAI", "target_duration_us": 2_000_000, "reorder_required": True, "locked_permutation": ["V2", "V1"], "video_clips": [{"clip_id": "V2", "source_sha256": sha(source), "source_range_us": [1_000_000, 2_000_000], "target_range_us": [0, 1_000_000]}, {"clip_id": "V1", "source_sha256": sha(source), "source_range_us": [0, 1_000_000], "target_range_us": [1_000_000, 2_000_000]}]}, "source_audio": [{"clip_id": "V2", "mode": "on", "source_sha256": sha(source), "source_range_us": [1_000_000, 2_000_000], "target_range_us": [0, 1_000_000]}, {"clip_id": "V1", "mode": "on", "source_sha256": sha(source), "source_range_us": [0, 1_000_000], "target_range_us": [1_000_000, 2_000_000]}]})
            config = {"episode_id": "EP", "visual_asset_mode": "CLEAN_VISUAL_READY", "clean_video": str(clean_video), "clean_asset_root": str(clean_root), "clean_evidence_root": str(clean_root), "duration_us": 2_000_000, "T1": "title", "T2": "subtitle", "state_cues": [], "project_name": "project", "episode_root": str(episode), "work_root": str(root / "work"), "local_capcut_root": str(root / "capcut"), "source_identity_path": str(identity), "approved_timeline_path": str(timeline), "design_handoff_path": str(handoff), "design_lock_evidence_path": str(evidence), "build_manifest_path": str(build_manifest), "state_path": str(state), "audio_policy": "A10_RETAINED_SYNC", "root_contract_path": contract.name, "workspace_root": str(root), "root_profile": "home_windows"}
            with patch.object(builder, "_assert_capcut_closed_for_target", return_value=None), patch.object(
                builder, "_register_capcut_project", return_value=None
            ):
                result = builder.build_episode(config)
            normalized_root = root / "capcut" / "project"
            self.assertTrue((normalized_root / "Resources" / "media" / "clean_video.mp4").is_file())
            self.assertFalse((normalized_root / "Resources" / "media" / "source.mp4").exists())
            self.assertEqual(result["status"], "CAPCUT_STATIC_VALIDATED")
            self.assertEqual(result["visual_asset_mode"], "CLEAN_VISUAL_READY")
            self.assertTrue(result["upload_ready"])
            report = json.loads((episode / "50_capcut_project" / "build_report.json").read_text(encoding="utf-8"))
            self.assertEqual(report["status"], "CAPCUT_STATIC_VALIDATED")
            self.assertTrue(report["upload_ready"])
            self.assertEqual(Path(report["project_path"]), root / "capcut" / "project")
            self.assertEqual(Path(report["media_source_path"]), clean_video.resolve())
            self.assertEqual(json.loads(state.read_text(encoding="utf-8"))["current_stage"], "09")


if __name__ == "__main__":
    unittest.main()

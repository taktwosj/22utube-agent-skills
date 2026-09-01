from __future__ import annotations

import hashlib
import io
import json
import subprocess
import sys
import tempfile
import unittest
import zipfile
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch


SKILL = Path(__file__).resolve().parents[1]
SCRIPTS = SKILL / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import validate_audio_caption
import validate_prebuild
import build_episode_capcut as builder


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")


def one_column_grid(kind: str, duration_us: int) -> str:
    seconds = duration_us / 1_000_000
    header = (
        f"| 레이어 \\ 원본 시간 | B01 0.0–{seconds:g} |"
        if kind == "original"
        else f"| 레이어 \\ 목표 시간 | V01 0.0–{seconds:g} B01 |"
    )
    roles = (
        "T1", "T2", "A9_TEXT", "A10_TEXT_YELLOW", "A10_TEXT_WHITE",
        "STATE_LASER", "STATE_GLITCH", "SOURCE_CREDIT", "SCREEN_WHITE",
        "SCREEN_EFFECT", "VIDEO", "A9", "A10", "A11", "A12_RESERVED_EMPTY",
    )
    transcript = "" if kind != "original" else f"""## 원본 5분류 대본

### B01 0.0–{seconds:g}
(상황설명) 테스트 장면. 화면 OCR: 없음
\"화자발언\" 없음
<나레이션> 없음
TTS화자발언 없음
TTS나레이션 없음

"""
    return transcript + "\n".join([header, "|---|---|", *(f"| {role} | 비움 |" for role in roles)]) + "\n"


class ContractDefects20260811Test(unittest.TestCase):
    def _template_archive(self, root: Path, *, mutate=None) -> Path:
        tracks = []
        materials = []
        for index, role in enumerate(builder.ROLE_BY_TRACK):
            material_id = f"material-{index}"
            tracks.append({
                "id": f"track-{index}",
                "segments": [{"id": f"seed-{index}", "material_id": material_id}],
            })
            materials.append({"id": material_id, "type": "video" if role == "VIDEO" else "music"})
        content = {"tracks": tracks, "materials": {"items": materials}}
        documents = {
            "template/draft_content.json": json.loads(json.dumps(content)),
            "template/Timelines/main/draft_content.json": json.loads(json.dumps(content)),
        }
        if mutate is not None:
            mutate(documents)
        archive = root / "root.zip"
        with zipfile.ZipFile(archive, "w") as zipped:
            for name, payload in documents.items():
                zipped.writestr(name, json.dumps(payload).encode("utf-8"))
        return archive

    def _public_stage08_duration_case(self, root: Path, *, drift_us: int) -> tuple[int, object]:
        episode = root / "episode"
        episode.mkdir()
        source = root / "source.mp4"
        source.write_bytes(b"source")
        audio = root / "source.wav"
        audio.write_bytes(b"audio")
        archive = self._template_archive(root)
        duration = 1_000_000
        identity = episode / "source_identity.json"
        write(identity, {"episode_id": "EP", "media_path": str(source), "media_sha256": sha(source)})
        timeline = episode / "approved_timeline.json"
        write(timeline, {"episode_id": "EP", "segments": []})
        handoff = episode / "design_handoff.json"
        write(handoff, {"episode_id": "EP"})
        evidence_payload = {
            "status": "PASS", "episode_id": "EP",
            "handoff_path": str(handoff.resolve()), "handoff_sha256": sha(handoff),
            "source_identity_path": str(identity.resolve()), "source_identity_sha256": sha(identity),
            "source_media_path": str(source.resolve()), "source_media_sha256": sha(source),
            "timeline_path": str(timeline.resolve()), "timeline_sha256": sha(timeline),
            "source_fingerprint": "fp",
        }
        evidence = episode / "design_evidence.json"
        write(evidence, evidence_payload)
        manifest = episode / "build_manifest.json"
        write(manifest, {
            "episode_id": "EP", "visual_asset_mode": "SOURCE_VIDEO_PROVISIONAL",
            "source": {"path": str(source), "sha256": sha(source), "duration_us": duration},
            "template": {"root_zip_path": str(archive), "root_zip_sha256": sha(archive)},
        })
        audio_lock = episode / "audio_lock.json"
        write(audio_lock, {
            "schema_version": "001short-audio-lock-v4", "episode_id": "EP", "status": "PASS",
            "production_mode": "SOURCE_ORDER_UNCHANGED_CLEAN_ONLY",
            "audio_policy": "SOURCE_ORDER_CLEAN_AUDIO", "audio_source": "SOURCE_CLIP",
            "audio_path": str(audio), "audio_sha256": sha(audio),
            "measured_duration_us": duration + drift_us,
        })
        final_srt = episode / "final.srt"
        final_srt.write_text("", encoding="utf-8")
        caption_lock = episode / "caption_lock.json"
        write(caption_lock, {
            "episode_id": "EP", "status": "PASS", "final_srt_path": str(final_srt),
        })
        plan = episode / "production_plan.json"
        write(plan, {"episode_id": "EP"})
        receipt = episode / "production_plan_receipt.json"
        write(receipt, {"status": "PASS"})
        state_path = episode / "90_workflow" / "revisions" / "v1" / "state.json"
        state_payload = {
            "episode_id": "EP", "status": "AUDIO_CAPTION_VALIDATED",
            "audio_lock_path": str(audio_lock), "audio_lock_sha256": sha(audio_lock),
            "caption_lock_path": str(caption_lock), "caption_lock_sha256": sha(caption_lock),
            "production_plan_path": str(plan), "production_plan_sha256": sha(plan),
            "production_plan_validation_receipt_path": str(receipt),
            "production_plan_validation_receipt_sha256": sha(receipt),
        }
        config = {
            "episode_id": "EP", "revision_id": "v1", "duration_us": duration,
            "production_mode": "SOURCE_ORDER_UNCHANGED_CLEAN_ONLY",
            "audio_policy": "SOURCE_ORDER_CLEAN_AUDIO",
            "visual_asset_mode": "SOURCE_VIDEO_PROVISIONAL",
            "source_video": str(source), "template_zip": str(archive),
            "episode_root": str(episode), "state_path": str(state_path),
            "source_identity_path": str(identity), "approved_timeline_path": str(timeline),
            "design_handoff_path": str(handoff), "design_lock_evidence_path": str(evidence),
            "build_manifest_path": str(manifest),
            "local_capcut_root": str(root / "capcut"), "project_name": "project_v1",
            "work_root": str(root / "work"),
        }
        config_path = root / "config.json"
        write(config_path, config)

        def validate_config(payload: dict) -> None:
            payload["template_zip"] = str(archive)
            payload["_visual_input"] = {
                "video_input_path": str(source), "visual_asset_mode": "SOURCE_VIDEO_PROVISIONAL",
                "resource_name": "source.mp4",
            }

        output = io.StringIO()
        initializer = patch.object(builder, "initialize_revision_state")
        with patch.object(builder, "_ensure_media_tools"), patch.object(
            builder, "_validate_config", side_effect=validate_config,
        ), patch.object(builder, "validate_grid_harness"), patch.object(
            builder, "prepare_revision_state_payload", return_value=(state_payload, {}),
        ), initializer as initialize, patch.object(
            builder, "_validate_mixed_audio_modes",
        ), patch.object(builder, "_assert_optional_edit_lock"), patch.object(
            builder.validate_design_lock, "validate_handoff", return_value={"status": "PASS", "evidence": evidence_payload},
        ), patch.object(
            builder.validate_prebuild, "validate_prebuild", return_value={"status": "PASS", "errors": []},
        ), patch.object(
            builder.validate_audio_caption, "validate_audio_caption", return_value={"status": "PASS", "errors": []},
        ), patch.object(
            builder, "_video_dimensions", return_value=(1080, 1920),
        ), patch.object(
            builder, "_build_episode_once", return_value={"status": "PASS"},
        ), patch.object(sys, "argv", ["build_episode_capcut.py", "--config", str(config_path)]), redirect_stdout(output):
            try:
                return builder.main(), initialize
            finally:
                pass

    def _source_order_manifest(self, root: Path, *, source_duration_us: int, target_duration_us: int) -> Path:
        source = root / "source.mp4"
        source.write_bytes(b"source")
        archive = root / "root.zip"
        archive.write_bytes(b"root")
        manifest = root / "build_manifest.json"
        clip = {
            "clip_id": "B01", "source_sha256": sha(source),
            "source_range_us": [0, target_duration_us],
            "target_range_us": [0, target_duration_us],
        }
        write(manifest, {
            "schema_version": "001short-build-manifest-v1", "episode_id": "EP",
            "visual_asset_mode": "SOURCE_VIDEO_PROVISIONAL",
            "production_mode": "SOURCE_ORDER_UNCHANGED_CLEAN_ONLY",
            "audio_policy": "SOURCE_ORDER_CLEAN_AUDIO", "audio_source": "SOURCE_CLIP",
            "source": {"path": str(source), "sha256": sha(source), "duration_us": source_duration_us},
            "template": {"root_name": "shrt white", "root_zip_path": str(archive), "root_zip_sha256": sha(archive)},
            "urakkai": {
                "production_type": "SOURCE_ORDER_UNCHANGED_CLEAN_ONLY",
                "target_duration_us": target_duration_us, "reorder_required": False,
                "video_clips": [clip],
            },
            "source_audio": [{**clip, "mode": "on"}],
        })
        return manifest

    def test_source_order_duration_allows_symmetric_50ms_drift_only(self):
        target = 1_000_000
        for drift in (979, 50_000):
            for direction in (-1, 1):
                with self.subTest(drift=drift, direction=direction), tempfile.TemporaryDirectory() as td:
                    manifest = self._source_order_manifest(
                        Path(td), source_duration_us=target + direction * drift,
                        target_duration_us=target,
                    )
                    self.assertEqual(validate_prebuild.validate_prebuild(manifest)["status"], "PASS")
        for direction in (-1, 1):
            with self.subTest(drift=50_001, direction=direction), tempfile.TemporaryDirectory() as td:
                manifest = self._source_order_manifest(
                    Path(td), source_duration_us=target + direction * 50_001,
                    target_duration_us=target,
                )
                result = validate_prebuild.validate_prebuild(manifest)
                self.assertEqual(result["status"], "FAIL")
                self.assertIn("E_SOURCE_ORDER_DURATION", {row["code"] for row in result["errors"]})

    def test_public_builder_cli_applies_source_order_duration_tolerance_before_writes(self):
        for drift in (-50_000, -979, 979, 50_000):
            with self.subTest(drift=drift), tempfile.TemporaryDirectory() as td:
                code, initialize = self._public_stage08_duration_case(Path(td), drift_us=drift)
                self.assertEqual(code, 0)
                initialize.assert_called_once()
        for drift in (-50_001, 50_001):
            with self.subTest(drift=drift), tempfile.TemporaryDirectory() as td:
                root = Path(td)
                with self.assertRaisesRegex(RuntimeError, "STAGE07_AUTHORITY_MISMATCH"):
                    self._public_stage08_duration_case(root, drift_us=drift)
                self.assertFalse((root / "episode" / "90_workflow" / "revisions" / "v1").exists())
                self.assertFalse((root / "work").exists())
                self.assertFalse((root / "capcut").exists())

    def test_public_builder_cli_preflights_every_primary_template_draft_and_seed(self):
        def timeline_has_fourteen(documents: dict) -> None:
            documents["template/Timelines/main/draft_content.json"]["tracks"].pop()

        mutations = [("timeline-layout", timeline_has_fourteen, "PINNED_TRACK_LAYOUT_INVALID")]
        for role in ("VIDEO", "A9", "A10"):
            def missing_seed(documents: dict, role=role) -> None:
                index = builder.ROLE_BY_TRACK.index(role)
                documents["template/Timelines/main/draft_content.json"]["tracks"][index]["segments"] = []
            mutations.append((f"missing-{role}-seed", missing_seed, f"PINNED_TEMPLATE_ANCHOR_MISSING:{role}"))

        def missing_video_material(documents: dict) -> None:
            items = documents["template/Timelines/main/draft_content.json"]["materials"]["items"]
            items[:] = [row for row in items if row["id"] != "material-0"]
        mutations.append(("missing-VIDEO-material", missing_video_material, "PINNED_TEMPLATE_MATERIAL_MISSING:VIDEO"))

        for label, mutate, error in mutations:
            with self.subTest(case=label), tempfile.TemporaryDirectory() as td:
                root = Path(td)
                archive = self._template_archive(root, mutate=mutate)
                config_path = root / "config.json"
                write(config_path, {"revision_id": "v1", "template_zip": str(archive)})
                with patch.object(builder, "_ensure_media_tools"), patch.object(
                    builder, "_validate_config",
                ), patch.object(
                    builder, "validate_grid_harness",
                ), patch.object(
                    builder, "prepare_revision_state_payload",
                ) as prepare, patch.object(
                    sys, "argv", ["build_episode_capcut.py", "--config", str(config_path)],
                ):
                    with self.assertRaisesRegex(RuntimeError, error):
                        builder.main()
                prepare.assert_not_called()
                self.assertFalse((root / "state.json").exists())
                self.assertFalse((root / "work").exists())
                self.assertFalse((root / "capcut").exists())

    def test_source_order_core_integrity_gates_remain_strict(self):
        mutations = {
            "source-sha": (lambda payload: payload["urakkai"]["video_clips"][0].update(source_sha256="0" * 64), "E_VIDEO_RANGE"),
            "gap": (lambda payload: payload["urakkai"]["video_clips"][0].update(target_range_us=[1, 1_000_001]), "E_VIDEO_RANGE"),
            "overlap": (lambda payload: payload["urakkai"].update(video_clips=[
                {**payload["urakkai"]["video_clips"][0], "clip_id": "B01a", "source_range_us": [0, 600_000], "target_range_us": [0, 600_000]},
                {**payload["urakkai"]["video_clips"][0], "clip_id": "B01b", "source_range_us": [500_000, 1_000_000], "target_range_us": [500_000, 1_000_000]},
            ]), "E_VIDEO_RANGE"),
            "a10-full-range": (lambda payload: payload["source_audio"][0].update(source_range_us=[1, 1_000_001]), "E_AUDIO_BINDING"),
        }
        for label, (mutate, expected_code) in mutations.items():
            with self.subTest(case=label), tempfile.TemporaryDirectory() as td:
                manifest = self._source_order_manifest(Path(td), source_duration_us=1_000_000, target_duration_us=1_000_000)
                payload = json.loads(manifest.read_text(encoding="utf-8"))
                mutate(payload)
                if label == "overlap":
                    payload["source_audio"] = [{**row, "mode": "on"} for row in payload["urakkai"]["video_clips"]]
                write(manifest, payload)
                result = validate_prebuild.validate_prebuild(manifest)
                self.assertEqual(result["status"], "FAIL", result)
                self.assertIn(expected_code, {row["code"] for row in result["errors"]})

    def test_urakkai_source_range_end_keeps_exact_source_duration_boundary(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            manifest = self._source_order_manifest(
                root, source_duration_us=999_021, target_duration_us=1_000_000,
            )
            payload = json.loads(manifest.read_text(encoding="utf-8"))
            source_sha = payload["source"]["sha256"]
            clips = [
                {"clip_id": "B01", "source_sha256": source_sha, "source_range_us": [0, 500_000], "target_range_us": [0, 500_000]},
                {"clip_id": "B02", "source_sha256": source_sha, "source_range_us": [500_000, 1_000_000], "target_range_us": [500_000, 1_000_000]},
            ]
            payload.update(production_mode="URAKKAI", audio_policy="A10_REASSEMBLED_SYNC", audio_source="REASSEMBLED_VOCAL_STEM")
            payload["urakkai"].update(
                production_type="URAKKAI", reorder_required=True,
                locked_permutation=["B01", "B02"], video_clips=clips,
            )
            payload["source_audio"] = [{**clip, "mode": "on"} for clip in clips]
            write(manifest, payload)
            result = validate_prebuild.validate_prebuild(manifest)
            self.assertEqual(result["status"], "FAIL")
            self.assertIn("E_VIDEO_RANGE", {row["code"] for row in result["errors"]})

    @unittest.skipUnless(__import__("shutil").which("ffmpeg") and __import__("shutil").which("ffprobe"), "media tools required")
    def test_v2_zero_caption_keeps_cue_mapping_empty_while_video_mapping_is_valid(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            audio = root / "source.wav"
            subprocess.run([
                "ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-f", "lavfi",
                "-i", "sine=frequency=440:duration=0.4", "-ac", "1", "-ar", "48000",
                "-c:a", "pcm_s16le", str(audio),
            ], check=True)
            duration = 400_000
            identity = root / "source_identity.json"
            write(identity, {
                "schema_version": "source-identity-v1", "episode_id": "EP", "source_id": "SRC",
                "source_fingerprint": sha(audio), "media_path": audio.name,
                "media_sha256": sha(audio), "duration_us": duration,
            })
            audio_lock = root / "audio_lock.json"
            role = {"role": "A10", "audio_path": audio.name, "audio_sha256": sha(audio),
                    "measured_duration_us": duration, "audio_codec": "pcm_s16le", "ffprobe_verified": True}
            write(audio_lock, {
                "schema_version": "001short-audio-lock-v4", "episode_id": "EP", "status": "PASS",
                "production_mode": "SOURCE_ORDER_UNCHANGED_CLEAN_ONLY",
                "audio_policy": "SOURCE_ORDER_CLEAN_AUDIO", "audio_source": "SOURCE_CLIP",
                "audio_path": audio.name, "audio_sha256": sha(audio), "measured_duration_us": duration,
                "audio_codec": "pcm_s16le", "ffprobe_verified": True,
                "source_identity_path": identity.name, "source_identity_sha256": sha(identity),
                "role_files": [role],
            })
            timeline = root / "approved_timeline.json"
            write(timeline, {"schema_version": "approved-timeline-v1", "episode_id": "EP", "segments": []})
            build_manifest = root / "build_manifest.json"
            write(build_manifest, {
                "schema_version": "001short-build-manifest-v1", "episode_id": "EP",
                "urakkai": {"video_clips": [{"clip_id": "B01", "source_range_us": [0, duration], "target_range_us": [0, duration]}]},
            })
            plan = root / "production_plan.json"
            write(plan, {
                "schema_version": "001short-production-plan-v2", "episode_id": "EP",
                "timeline": [{
                    "segment_key": "B01", "source_beat_id": "B01", "target_segment_id": "V01",
                    "target_range_us": [0, duration],
                    "placements": [{"anchor": "VIDEO", "source_range_us": [0, duration], "target_range_us": [0, duration]}],
                }],
            })
            original = root / "original-capcut-grid.md"
            urakkai = root / "urakkai-capcut-grid.md"
            original.write_text(one_column_grid("original", duration), encoding="utf-8")
            urakkai.write_text(one_column_grid("urakkai", duration), encoding="utf-8")
            timing = root / "caption_timing_evidence.json"
            write(timing, {
                "schema_version": "001short-caption-timing-evidence-v2", "status": "PASS",
                "episode_id": "EP", "source_identity_path": identity.name,
                "source_identity_sha256": sha(identity), "tolerance_us": 50_000,
                "approved_timeline_path": timeline.name, "approved_timeline_sha256": sha(timeline),
                "build_manifest_path": build_manifest.name, "build_manifest_sha256": sha(build_manifest),
                "production_plan_path": plan.name, "production_plan_sha256": sha(plan),
                "original_grid_path": original.name, "original_grid_sha256": sha(original),
                "urakkai_grid_path": urakkai.name, "urakkai_grid_sha256": sha(urakkai),
                "zero_caption": True, "mapping": [], "cues": [],
            })
            final_srt = root / "final.srt"
            final_srt.write_text("", encoding="utf-8")
            caption_lock = root / "caption_lock.json"
            write(caption_lock, {
                "schema_version": "001short-caption-lock-v2", "episode_id": "EP", "status": "PASS",
                "audio_lock_path": audio_lock.name, "audio_lock_sha256": sha(audio_lock),
                "final_srt_path": final_srt.name, "final_srt_sha256": sha(final_srt),
                "final_cue_count": 0, "cues": [], "all_cues_within_measured_audio": True,
                "no_overlap_verified": True, "caption_timing_evidence_path": timing.name,
                "caption_timing_evidence_sha256": sha(timing),
            })
            result = validate_audio_caption.validate_audio_caption(audio_lock, caption_lock)
            self.assertEqual(result["status"], "PASS", result)

            base_caption = json.loads(caption_lock.read_text(encoding="utf-8"))
            base_timing = json.loads(timing.read_text(encoding="utf-8"))
            base_timeline = json.loads(timeline.read_text(encoding="utf-8"))
            variants = ("caption_lock", "srt", "timeline")
            for variant in variants:
                with self.subTest(zero_caption_conflict=variant):
                    final_srt.write_text("", encoding="utf-8")
                    write(timeline, base_timeline)
                    write(timing, base_timing)
                    caption_payload = dict(base_caption)
                    if variant == "caption_lock":
                        caption_payload["final_cue_count"] = 1
                        caption_payload["cues"] = [{
                            "cue_id": "C1", "start_us": 0, "end_us": 100_000,
                            "text": "caption", "layer": "A10_TEXT", "caption_role": "A10_TEXT",
                        }]
                    elif variant == "srt":
                        final_srt.write_text("C1\n00:00:00,000 --> 00:00:00,100\ncaption\n", encoding="utf-8")
                    else:
                        timeline_payload = dict(base_timeline)
                        timeline_payload["segments"] = [{
                            "segment_id": "CAP1", "role": "A10_TEXT", "cue_id": "C1",
                            "start": 0, "duration": 100_000, "text": "caption",
                        }]
                        write(timeline, timeline_payload)
                        timing_payload = dict(base_timing)
                        timing_payload["approved_timeline_sha256"] = sha(timeline)
                        write(timing, timing_payload)
                    caption_payload["final_srt_sha256"] = sha(final_srt)
                    caption_payload["caption_timing_evidence_sha256"] = sha(timing)
                    write(caption_lock, caption_payload)
                    failed = validate_audio_caption.validate_audio_caption(audio_lock, caption_lock)
                    self.assertEqual(failed["status"], "FAIL", failed)


if __name__ == "__main__":
    unittest.main()

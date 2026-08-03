from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace


SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import build_episode_capcut as builder
import validate_postbuild
import validate_prebuild
import validate_stage


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class SourceVideoProvisionalBuilderTests(unittest.TestCase):
    def test_shared_base_work_root_is_namespaced_per_episode(self):
        base = "/tmp/shared-001short-work"
        first = builder._episode_work_root({"work_root": base, "episode_id": "P-19/01"})
        second = builder._episode_work_root({"work_root": base, "episode_id": "P-20/02"})
        self.assertNotEqual(first, second)
        self.assertEqual(first.parent, Path(base).resolve())
        self.assertEqual(second.parent, Path(base).resolve())

    def _provisional_manifest(self, root: Path) -> Path:
        source = root / "source.mp4"
        source.write_bytes(b"source-video")
        root_zip = root / "root.zip"
        root_zip.write_bytes(b"verified-root")
        payload = {
            "schema_version": "001short-build-manifest-v1",
            "episode_id": "EP-PROVISIONAL",
            "visual_asset_mode": "SOURCE_VIDEO_PROVISIONAL",
            "source": {"path": str(source), "sha256": sha256(source), "duration_us": 1_000_000},
            "template": {"root_name": "shrt white", "root_zip_path": str(root_zip), "root_zip_sha256": sha256(root_zip)},
            "vmake": {},
            "urakkai": {
                "production_type": "URAKKAI", "target_duration_us": 1_000_000,
                "reorder_required": True, "locked_permutation": ["clip-b", "clip-a"],
                "video_clips": [
                    {"clip_id": "clip-b", "source_sha256": sha256(source), "source_range_us": [500_000, 1_000_000], "target_range_us": [0, 500_000]},
                    {"clip_id": "clip-a", "source_sha256": sha256(source), "source_range_us": [0, 500_000], "target_range_us": [500_000, 1_000_000]},
                ],
            },
            "source_audio": [
                {"clip_id": "clip-b", "mode": "on", "source_sha256": sha256(source), "source_range_us": [500_000, 1_000_000], "target_range_us": [0, 500_000]},
                {"clip_id": "clip-a", "mode": "on", "source_sha256": sha256(source), "source_range_us": [0, 500_000], "target_range_us": [500_000, 1_000_000]},
            ],
        }
        manifest = root / "build_manifest.json"
        manifest.write_text(json.dumps(payload), encoding="utf-8")
        return manifest

    def test_provisional_prebuild_skips_vmake_receipt_but_keeps_source_sha_authority(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            manifest = self._provisional_manifest(root)
            self.assertEqual(
                validate_prebuild.validate_prebuild(manifest, allow_source_provisional=True)["status"],
                "PASS",
            )
            payload = json.loads(manifest.read_text(encoding="utf-8"))
            Path(payload["source"]["path"]).write_bytes(b"tampered-source")
            failed = validate_prebuild.validate_prebuild(manifest, allow_source_provisional=True)
            self.assertEqual(failed["status"], "FAIL")
            self.assertIn("source", [row.get("field") for row in failed["errors"]])

    def test_stage08_router_removes_only_clean_receipt_for_source_provisional(self):
        clean = validate_stage.prerequisites_for_stage(
            "08", {"visual_asset_mode": "CLEAN_VISUAL_READY"}
        )
        provisional = validate_stage.prerequisites_for_stage(
            "08", {"visual_asset_mode": "SOURCE_VIDEO_PROVISIONAL"}
        )
        self.assertIn("clean_visual", clean)
        self.assertNotIn("clean_visual", provisional)
        self.assertEqual(set(clean) - {"clean_visual"}, set(provisional))
        with tempfile.TemporaryDirectory() as temporary:
            manifest = self._provisional_manifest(Path(temporary))
            result = validate_stage._run(
                "prebuild",
                SimpleNamespace(
                    build_manifest=manifest,
                    visual_asset_mode="SOURCE_VIDEO_PROVISIONAL",
                ),
            )
            self.assertEqual(result["status"], "PASS")

    def test_provisional_config_video_must_match_manifest_source(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            manifest_path = self._provisional_manifest(root)
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            source = Path(manifest["source"]["path"])
            config = {"visual_asset_mode": "SOURCE_VIDEO_PROVISIONAL", "source_video": str(source)}
            self.assertTrue(builder._build_manifest_visual_matches(config, manifest, source))
            other = root / "other.mp4"
            other.write_bytes(b"different-video")
            config["source_video"] = str(other)
            self.assertFalse(builder._build_manifest_visual_matches(config, manifest, other))

    def test_clean_prebuild_still_requires_vmake_receipt(self):
        with tempfile.TemporaryDirectory() as temporary:
            manifest = self._provisional_manifest(Path(temporary))
            payload = json.loads(manifest.read_text(encoding="utf-8"))
            payload.pop("visual_asset_mode")
            manifest.write_text(json.dumps(payload), encoding="utf-8")
            failed = validate_prebuild.validate_prebuild(manifest)
            self.assertEqual(failed["status"], "FAIL")
            self.assertIn("E_VMAKE_BINDING", [row["code"] for row in failed["errors"]])

    def test_postbuild_enforces_provisional_video_mute_and_a10_full_volume(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            manifest_path = self._provisional_manifest(root)
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            project = root / "project"
            media = project / "Resources" / "media"
            media.mkdir(parents=True)
            source = Path(manifest["source"]["path"])
            (media / "source_video.mp4").write_bytes(source.read_bytes())
            materials = {"items": [{
                "id": "video-material", "type": "video",
                "path": "Resources/media/source_video.mp4",
            }]}
            tracks = [
                {"segments": [
                    {"id": "clip-b", "role": "VIDEO", "material_id": "video-material", "volume": 1.0,
                     "source_timerange": {"start": 500_000, "duration": 500_000},
                     "target_timerange": {"start": 0, "duration": 500_000}},
                    {"id": "clip-a", "role": "VIDEO", "material_id": "video-material", "volume": 0.0,
                     "source_timerange": {"start": 0, "duration": 500_000},
                     "target_timerange": {"start": 500_000, "duration": 500_000}},
                ]},
                {"segments": [
                    {"id": "audio-b", "role": "A10", "volume": 1.0,
                     "source_timerange": {"start": 500_000, "duration": 500_000},
                     "target_timerange": {"start": 0, "duration": 500_000}},
                    {"id": "audio-a", "role": "A10", "volume": 1.0,
                     "source_timerange": {"start": 0, "duration": 500_000},
                     "target_timerange": {"start": 500_000, "duration": 500_000}},
                ]},
            ]
            draft = project / "draft_content.json"
            draft.write_text(json.dumps({"materials": materials, "tracks": tracks}), encoding="utf-8")
            failed_video = validate_postbuild.validate_postbuild(
                manifest_path, project, visual_asset_mode="SOURCE_VIDEO_PROVISIONAL"
            )
            self.assertEqual(failed_video["status"], "FAIL")
            tracks[0]["segments"][0]["volume"] = 0.0
            tracks[1]["segments"][0]["volume"] = 0.0
            draft.write_text(json.dumps({"materials": materials, "tracks": tracks}), encoding="utf-8")
            failed_audio = validate_postbuild.validate_postbuild(
                manifest_path, project, visual_asset_mode="SOURCE_VIDEO_PROVISIONAL"
            )
            self.assertEqual(failed_audio["status"], "FAIL")
            tracks[1]["segments"][0]["volume"] = 1.0
            draft.write_text(json.dumps({"materials": materials, "tracks": tracks}), encoding="utf-8")
            passed = validate_postbuild.validate_postbuild(
                manifest_path, project, visual_asset_mode="SOURCE_VIDEO_PROVISIONAL"
            )
            self.assertEqual(passed["status"], "PASS")

    def test_clean_receipt_field_comparison_accepts_equal_and_rejects_drift(self):
        expected = {"status": "PASS", "clean_source_sha256": "a" * 64, "width": 1080}
        self.assertTrue(builder._clean_receipt_fields_match(expected.copy(), expected))
        drifted = expected.copy()
        drifted["width"] = 720
        self.assertFalse(builder._clean_receipt_fields_match(drifted, expected))

    def test_provisional_config_accepts_source_video_without_clean_video(self):
        config = {
            "episode_id": "EP-PROVISIONAL",
            "source_video": "/tmp/source.mp4",
            "visual_asset_mode": "SOURCE_VIDEO_PROVISIONAL",
            "duration_us": 1_000_000,
            "T1": "제목",
            "T2": "부제",
            "state_cues": [{"text": "현재", "start_us": 0, "end_us": 1_000_000}],
            "project_name": "EP-PROVISIONAL",
            "template_zip": "/tmp/root.zip",
            "episode_root": "/tmp/episode",
            "work_root": "/tmp/work",
            "local_capcut_root": "/tmp/capcut",
            "source_identity_path": "/tmp/source_identity.json",
            "approved_timeline_path": "/tmp/timeline.json",
            "design_handoff_path": "/tmp/handoff.json",
            "design_lock_evidence_path": "/tmp/design.json",
            "build_manifest_path": "/tmp/build.json",
        }
        builder._validate_config(config)

    def test_clean_visual_mode_keeps_clean_video_as_the_builder_input(self):
        config = {
            "episode_id": "EP-CLEAN", "clean_video": "/tmp/clean.mp4", "duration_us": 1_000_000,
            "T1": "제목", "T2": "부제", "state_cues": [{"text": "현재", "start_us": 0, "end_us": 1_000_000}],
            "project_name": "EP-CLEAN", "template_zip": "/tmp/root.zip", "episode_root": "/tmp/episode",
            "work_root": "/tmp/work", "local_capcut_root": "/tmp/capcut", "source_identity_path": "/tmp/source_identity.json",
            "approved_timeline_path": "/tmp/timeline.json", "design_handoff_path": "/tmp/handoff.json",
            "design_lock_evidence_path": "/tmp/design.json", "build_manifest_path": "/tmp/build.json",
        }
        builder._validate_config(config)
        self.assertEqual(builder._visual_asset_path(config), Path("/tmp/clean.mp4").resolve())
        self.assertEqual(builder._visual_asset_filename(config), "clean_video.mp4")

    def test_disposable_builder_fixture_inserts_source_video_muted_and_keeps_a10(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "source.mp4"
            subprocess.run([
                "ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-f", "lavfi",
                "-i", "color=c=blue:s=16x16:d=1", "-pix_fmt", "yuv420p", str(source),
            ], check=True)
            project = root / "root"
            (project / "Resources" / "media").mkdir(parents=True)
            (project / "Resources" / "media" / "transparent_center_white_1080x1920.png").write_bytes(b"white")
            materials = []
            tracks = []
            for index in range(12):
                material_id = f"m{index}"
                material = {"id": material_id, "type": "music"}
                if index == 0:
                    material.update({"type": "video", "path": "##_draftpath_placeholder_fixture_##/Resources/media/template.mp4"})
                if index in {3, 6, 7}:
                    material.update({"type": "text", "content": '{"text":"원본","styles":[{"range":[0,2]}]}'})
                materials.append(material)
                tracks.append({"id": f"track-{index}", "segments": [{
                    "id": f"seed-{index}", "material_id": material_id,
                    "target_timerange": {"start": 0, "duration": 1_000_000},
                    "source_timerange": {"start": 0, "duration": 1_000_000},
                }]})
            (project / "draft_content.json").write_text(json.dumps({"duration": 1_000_000, "materials": {"items": materials}, "tracks": tracks}), encoding="utf-8")
            (project / "draft_meta_info.json").write_text(json.dumps({"draft_id": "template-draft"}), encoding="utf-8")
            approved_rows = [
                ("audio-a", "A10", 0, 500_000), ("clip-a", "VIDEO", 0, 500_000),
                ("state", "STATE", 0, 1_000_000), ("t1", "T1", 0, 1_000_000),
                ("t2", "T2", 0, 1_000_000), ("audio-b", "A10", 500_000, 500_000),
                ("clip-b", "VIDEO", 500_000, 500_000),
            ]
            timeline = root / "timeline.json"
            timeline.write_text(json.dumps({"episode_id": "EP-PROVISIONAL", "segments": [
                {"segment_id": segment_id, "role": role, "start": start, "duration": duration, "timeline_order": order}
                for order, (segment_id, role, start, duration) in enumerate(approved_rows)
            ]}), encoding="utf-8")
            config = {
                "episode_id": "EP-PROVISIONAL", "source_video": str(source),
                "visual_asset_mode": "SOURCE_VIDEO_PROVISIONAL", "duration_us": 1_000_000,
                "T1": "제목", "T2": "부제", "state_cues": [{"text": "현재", "start_us": 0, "end_us": 1_000_000, "segment_id": "state"}],
                "approved_timeline_path": str(timeline),
            }
            manifest = {
                "urakkai": {"video_clips": [
                    {"clip_id": "clip-a", "source_range_us": [0, 500_000], "target_range_us": [0, 500_000]},
                    {"clip_id": "clip-b", "source_range_us": [500_000, 1_000_000], "target_range_us": [500_000, 1_000_000]},
                ]},
                "source_audio": [
                    {"clip_id": "clip-a", "mode": "on", "source_range_us": [0, 500_000], "target_range_us": [0, 500_000]},
                    {"clip_id": "clip-b", "mode": "on", "source_range_us": [500_000, 1_000_000], "target_range_us": [500_000, 1_000_000]},
                ],
            }
            builder._normalize_source(project, config, source, manifest)
            content = json.loads((project / "draft_content.json").read_text(encoding="utf-8"))
            video = content["tracks"][0]["segments"]
            a10 = content["tracks"][9]["segments"]
            self.assertEqual([segment["volume"] for segment in video], [0.0, 0.0])
            self.assertEqual(len(a10), 2)
            self.assertEqual([segment["volume"] for segment in a10], [1.0, 1.0])
            material = next(item for item in content["materials"]["items"] if item["id"] == "m0")
            self.assertTrue(material["path"].endswith("Resources/media/source_video.mp4"))


if __name__ == "__main__":
    unittest.main()

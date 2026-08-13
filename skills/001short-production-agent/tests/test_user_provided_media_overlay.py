from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SKILL = Path(__file__).resolve().parents[1]
SCRIPTS = SKILL / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))
if str(Path(__file__).resolve().parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parent))

import build_episode_capcut as builder
import user_provided_media_overlay as overlay
import validate_capcut_project as readback
from test_public_builder_provisional import media, template_archive, write


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


@unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"), "media tools required")
class UserProvidedMediaOverlayTest(unittest.TestCase):
    def _audio(self, root: Path, name: str, seconds: float = 0.2) -> Path:
        path = root / name
        subprocess.run([
            "ffmpeg", "-loglevel", "error", "-f", "lavfi", "-i",
            f"sine=frequency=660:duration={seconds}", "-ar", "48000", "-ac", "1",
            "-c:a", "pcm_s16le", "-y", str(path),
        ], check=True)
        return path

    def _audio_item(self, path: Path, index: int, start_us: int) -> dict:
        return {
            "overlay_id": f"user-audio-{index}",
            "media_kind": "audio",
            "track_index": 15 + index,
            "source_path": str(path),
            "source_sha256": sha(path),
            "measured_duration_us": 200_000,
            "dimensions": {"width": 0, "height": 0},
            "source_range_us": [0, 200_000],
            "target_range_us": [start_us, start_us + 200_000],
        }

    def _image_item(self, path: Path, index: int, start_us: int) -> dict:
        return {
            "overlay_id": f"user-image-{index}", "media_kind": "image",
            "track_index": 15 + index, "source_path": str(path),
            "source_sha256": sha(path), "measured_duration_us": 0,
            "dimensions": {"width": 32, "height": 48},
            "target_range_us": [start_us, start_us + 200_000],
        }

    def _bundle(self, items: list[dict]) -> dict:
        return {
            "schema_version": "001short-user-provided-media-overlay-v1",
            "episode_id": "EP",
            "status": "WAIT_USER_CAPCUT_AUDIO_ADJUSTMENT",
            "user_authority": {
                "evidence": "operator supplied the narration files",
                "exact_text": "User-supplied audio may be stacked as extra layers.",
            },
            "items": items,
        }

    def test_three_user_audio_files_validate_as_extra_tracks(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            items = [
                self._audio_item(self._audio(root, f"tts-{index}.wav"), index, index * 500_000)
                for index in range(3)
            ]
            result = overlay.validate_bundle(
                self._bundle(items), episode_id="EP", timeline_duration_us=2_000_000,
            )
            self.assertEqual(result["status"], "PASS", result)
            self.assertEqual([item["track_index"] for item in result["items"]], [15, 16, 17])
            self.assertTrue(all(item["role"] == "USER_PROVIDED_AUDIO" for item in result["items"]))

    def test_builder_adds_direct_audio_tracks_and_registers_every_material(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source, vocals = media(root)
            archive, _, _ = template_archive(root)
            project = builder._extract_template(archive, root / "project")
            for document_path, payload in builder.iter_primary_draft_documents(project):
                a10_seed = payload["tracks"][builder.TRACK_INDEX["A10"]]["segments"][0]
                a10_seed.setdefault("extra_material_refs", []).append("stale-combination")
                a10_seed["effects"] = [{"binding": {"material_id": "stale-combination"}}]
                payload["materials"].setdefault("audios", []).append({
                    "id": "stale-combination", "type": "combination",
                    "role": "TEMPLATE_ONLY", "desc": "stale template combination",
                })
                write(document_path, payload)
            items = [
                self._audio_item(self._audio(root, f"direct-{index}.wav"), index, index * 500_000)
                for index in range(3)
            ]
            image_path = root / "visual.png"
            subprocess.run([
                "ffmpeg", "-loglevel", "error", "-f", "lavfi", "-i",
                "color=c=red:s=32x48", "-frames:v", "1", "-y", str(image_path),
            ], check=True)
            items.append(self._image_item(image_path, 3, 1_600_000))
            manifest = {
                "schema_version": "001short-build-manifest-v1",
                "episode_id": "EP",
                "visual_asset_mode": "SOURCE_VIDEO_PROVISIONAL",
                "source": {"path": str(source), "sha256": sha(source), "duration_us": 2_000_000},
                "template": {
                    "root_name": "shrt white", "root_zip_path": str(archive),
                    "root_zip_sha256": sha(archive),
                },
                "production_mode": "URAKKAI",
                "urakkai": {
                    "production_type": "URAKKAI", "target_duration_us": 2_000_000,
                    "reorder_required": True, "locked_permutation": ["V2", "V1"],
                    "video_clips": [
                        {"clip_id": "V2", "source_sha256": sha(source), "source_range_us": [1_000_000, 2_000_000], "target_range_us": [0, 1_000_000]},
                        {"clip_id": "V1", "source_sha256": sha(source), "source_range_us": [0, 1_000_000], "target_range_us": [1_000_000, 2_000_000]},
                    ],
                },
                "source_audio": [
                    {"clip_id": "V2", "mode": "on", "source_sha256": sha(source), "source_range_us": [1_000_000, 2_000_000], "target_range_us": [0, 1_000_000]},
                    {"clip_id": "V1", "mode": "on", "source_sha256": sha(source), "source_range_us": [0, 1_000_000], "target_range_us": [1_000_000, 2_000_000]},
                ],
                "user_provided_media_overlay": self._bundle(items),
            }
            rows = [
                {"segment_id": "V2", "timeline_order": 0, "role": "VIDEO", "start": 0, "duration": 1_000_000},
                {"segment_id": "V1", "timeline_order": 1, "role": "VIDEO", "start": 1_000_000, "duration": 1_000_000},
                {"segment_id": "T1", "timeline_order": 2, "role": "T1", "start": 0, "duration": 2_000_000, "text": "title"},
                {"segment_id": "T2", "timeline_order": 3, "role": "T2", "start": 0, "duration": 2_000_000, "text": "subtitle"},
                {"segment_id": "SCREEN_EFFECT", "timeline_order": 4, "role": "SCREEN_EFFECT", "start": 0, "duration": 2_000_000},
                {"segment_id": "SCREEN_WHITE", "timeline_order": 5, "role": "SCREEN_WHITE", "start": 0, "duration": 2_000_000},
                {"segment_id": "A10-1", "timeline_order": 6, "role": "A10", "start": 0, "duration": 1_000_000},
                {"segment_id": "A10-2", "timeline_order": 7, "role": "A10", "start": 1_000_000, "duration": 1_000_000},
            ]
            timeline = root / "timeline.json"
            write(timeline, {"episode_id": "EP", "segments": rows})
            config = {
                "episode_id": "EP", "duration_us": 2_000_000,
                "T1": "title", "T2": "subtitle", "state_cues": [],
                "audio_policy": "A10_REASSEMBLED_SYNC",
                "approved_timeline_path": str(timeline),
                "_visual_input": {"video_input_path": str(source), "resource_name": "source.mp4"},
            }

            builder._normalize_source(project, config, vocals, manifest)
            builder._prepare_cloud_project(
                project, project_name="overlay-fixture", capcut_root=root,
                draft_id="overlay-fixture-id", duration_us=2_000_000,
            )

            content = json.loads((project / "draft_content.json").read_text(encoding="utf-8"))
            meta = json.loads((project / "draft_meta_info.json").read_text(encoding="utf-8"))
            materials = {
                row["id"]: row
                for container in content["materials"].values()
                if isinstance(container, list)
                for row in container
                if isinstance(row, dict) and isinstance(row.get("id"), str)
            }
            self.assertEqual(len(content["tracks"]), 19)
            self.assertTrue(all(row["volume"] == 1.0 for row in content["tracks"][12]["segments"]))
            audio_segments = [
                *content["tracks"][12]["segments"],
                *(track["segments"][0] for track in content["tracks"][15:18]),
            ]
            for segment in audio_segments:
                self.assertEqual(segment["volume"], 1.0)
                ref_types = {
                    materials[ref]["type"] for ref in segment.get("extra_material_refs", [])
                    if ref in materials
                }
                self.assertNotIn("combination", ref_types, segment["id"])
            repaired_ids = {segment["id"] for segment in audio_segments}
            stale_refs = [
                row for row in builder.capcut_model.collect_material_references(content["tracks"])
                if row.get("segment_id") in repaired_ids
                and row.get("material_id") == "stale-combination"
            ]
            self.assertEqual(stale_refs, [])
            check = overlay.validate_project_tracks(
                content["tracks"], content["materials"], project_root=project,
                declared_items=config["user_provided_media_overlay"],
            )
            self.assertEqual(check["status"], "PASS", check)
            shortened = json.loads(json.dumps(content))
            shortened["tracks"][15]["segments"][0]["source_timerange"]["duration"] = 100_000
            shortened_check = overlay.validate_project_tracks(
                shortened["tracks"], shortened["materials"], project_root=project,
                declared_items=config["user_provided_media_overlay"],
            )
            self.assertEqual(shortened_check["status"], "FAIL")
            self.assertIn(
                "USER_MEDIA_OVERLAY_TRACK_UNBOUND",
                {row["code"] for row in shortened_check["errors"]},
            )

            registered = [materials[segment["material_id"]] for segment in audio_segments]
            self.assertTrue(all(row["type"] == "extract_music" for row in registered))
            self.assertTrue(all(row["music_id"] == row["id"] for row in registered))
            self.assertEqual(len({row["local_material_id"] for row in registered}), 4)
            meta_rows = next(row["value"] for row in meta["draft_materials"] if row["type"] == 0)
            self.assertEqual({row["id"] for row in meta_rows}, {row["id"] for row in registered})
            visual_segment = content["tracks"][18]["segments"][0]
            visual_material = materials[visual_segment["material_id"]]
            self.assertEqual(visual_material["role"], "USER_PROVIDED_VISUAL")
            self.assertEqual(visual_material["type"], "video")
            self.assertNotIn(visual_material["id"], {row["id"] for row in meta_rows})

            contract = {
                "track_layout_version": builder.TRACK_LAYOUT,
                "track_layout_extension": overlay.build_track_layout_extension(
                    config["user_provided_media_overlay"]
                ),
                "timeline": [{"role": "VIDEO", "end": 2_000_000}],
                "approved_role_text": {"T1": "title", "T2": "subtitle"},
                "approved_segment_text": {},
            }
            routing_errors = readback.validate_v2_role_routing(
                builder.capcut_model.load_project(project), contract,
            )
            self.assertNotIn(
                "V2_TRACK_LAYOUT_MISMATCH", {row["code"] for row in routing_errors},
                routing_errors,
            )
            self.assertNotIn(
                "USER_MEDIA_OVERLAY_TRACK_UNBOUND", {row["code"] for row in routing_errors},
                routing_errors,
            )

            contract["track_layout_extension"]["items"] = []
            undeclared_errors = readback.validate_v2_role_routing(
                builder.capcut_model.load_project(project), contract,
            )
            self.assertIn(
                "V2_TRACK_LAYOUT_MISMATCH",
                {row["code"] for row in undeclared_errors},
            )

            mirror_path = next((project / "Timelines").glob("*/draft_content.json"))
            mirror = json.loads(mirror_path.read_text(encoding="utf-8"))
            mirror["tracks"].append({
                "id": "undeclared-mirror-track", "segments": [],
            })
            mirror_materials = [
                row for row in builder.capcut_model.iter_materials(mirror["materials"])
                if row.get("role") == "USER_PROVIDED_AUDIO"
            ]
            mirror_materials[0]["type"] = "music"
            write(mirror_path, mirror)

            mirror_errors = readback.validate_primary_document_audio_surfaces(
                project, {
                    **contract,
                    "track_layout_extension": overlay.build_track_layout_extension(
                        config["user_provided_media_overlay"]
                    ),
                    "timeline": [
                        {"role": "VIDEO", "end": 2_000_000},
                        {"role": "A10", "end": 2_000_000},
                    ],
                },
            )
            mirror_codes = {row["code"] for row in mirror_errors}
            self.assertIn("USER_MEDIA_OVERLAY_TRACK_UNBOUND", mirror_codes)
            self.assertIn("AUDIO_MATERIAL_POSTOPEN_REWRITE_INVALID", mirror_codes)

    def test_unbound_sixteenth_track_is_rejected(self):
        tracks = [{"id": f"base-{index}", "segments": []} for index in range(15)]
        tracks.append({"id": "unbound", "segments": [{"id": "extra", "role": "USER_PROVIDED_AUDIO"}]})
        result = overlay.validate_project_tracks(
            tracks, [], project_root=Path.cwd(), declared_items=[],
        )
        self.assertEqual(result["status"], "FAIL")
        self.assertIn("USER_MEDIA_OVERLAY_TRACK_UNBOUND", {row["code"] for row in result["errors"]})

    def test_nested_list_material_container_is_supported(self):
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary)
            media_dir = project / "Resources" / "media"
            media_dir.mkdir(parents=True)
            audio_path = self._audio(media_dir, "nested.wav")
            declared = overlay.validate_bundle(
                self._bundle([self._audio_item(audio_path, 0, 0)]),
                episode_id="EP", timeline_duration_us=1_000_000,
            )["items"]
            segment = {
                "id": declared[0]["segment_id"],
                "material_id": "nested-material",
                "role": "USER_PROVIDED_AUDIO",
                "source_timerange": {"start": 0, "duration": 200_000},
                "target_timerange": {"start": 0, "duration": 200_000},
                "volume": 1.0,
            }
            tracks = [{"id": f"base-{index}", "segments": []} for index in range(15)]
            tracks.append({"id": "declared-overlay", "segments": [segment]})
            material = {
                "id": "nested-material", "type": "extract_music",
                "path": "Resources/media/nested.wav",
            }

            result = overlay.validate_project_tracks(
                tracks, [{"nested": {"audios": [material]}}],
                project_root=project, declared_items=declared,
            )

            self.assertEqual(result["status"], "PASS", result)


if __name__ == "__main__":
    unittest.main()

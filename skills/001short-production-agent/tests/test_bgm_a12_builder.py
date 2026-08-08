import copy
import json
import sys
import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import build_episode_capcut as builder


class BgmA12BuilderTest(unittest.TestCase):
    def _normalize_v2_audio(self, role: str) -> list[dict]:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            project = root / "project"
            (project / "Resources" / "media").mkdir(parents=True)
            clean_video = root / "clean.mp4"
            audio = root / "audio.wav"
            clean_video.write_bytes(b"video")
            audio.write_bytes(b"audio")
            roles = [
                "VIDEO", "SCREEN_EFFECT", "SCREEN_WHITE", "STATE_FLICKER", "STATE_GLITCH",
                "STATE_LASER", "A10_TEXT_WHITE", "A10_TEXT_YELLOW", "A9_TEXT", "T2", "T1",
                "A9", "A10", "A11", "A12",
            ]
            materials = []
            tracks = []
            for index, track_role in enumerate(roles):
                material_id = f"m-{track_role}"
                material = {"id": material_id, "type": "music", "path": "##_draftpath_placeholder_test_##/Resources/media/template.wav"}
                if track_role in {
                    "STATE_FLICKER", "STATE_GLITCH", "STATE_LASER", "A10_TEXT_WHITE",
                    "A10_TEXT_YELLOW", "T1", "T2", "A9_TEXT",
                }:
                    material.update({"type": "text", "content": json.dumps({"text": "old", "styles": [{"range": [0, 3]}]})})
                materials.append(material)
                tracks.append({"segments": [{
                    "id": f"template-{track_role}", "material_id": material_id,
                    "target_timerange": {"start": 0, "duration": 1},
                    "source_timerange": {"start": 0, "duration": 1},
                }] if track_role not in {"SCREEN_EFFECT", "SCREEN_WHITE"} else []})
            payload = {"tracks": tracks, "materials": {"items": materials}}
            document = project / "draft_content.json"
            document.write_text(json.dumps(payload), encoding="utf-8")
            (project / "draft_meta_info.json").write_text(json.dumps({"draft_id": "fixture"}), encoding="utf-8")
            timeline = root / "timeline.json"
            segment_specs = [
                ("state", "STATE", 0, 1_000), ("t1", "T1", 0, 1_000),
                ("t2", "T2", 0, 1_000), ("video", "VIDEO", 0, 1_000),
            ]
            if role == "A9":
                segment_specs = [("a9", "A9", 0, 1_000), ("a9-text", "A9_TEXT", 0, 1_000), *segment_specs]
            elif role == "A11":
                segment_specs.extend([("a11-1", "A11", 100, 100), ("a11-2", "A11", 500, 50)])
            else:
                segment_specs.insert(0, ("a12", "A12", 0, 1_000))
            timeline.write_text(json.dumps({"episode_id": "EP", "segments": [
                {
                    "segment_id": segment_id, "timeline_order": index, "role": segment_role,
                    "start": start, "duration": duration, "source_ref": "source",
                    **({"text": "one"} if segment_role == "T1" else {}),
                    **({"text": "two"} if segment_role == "T2" else {}),
                    **({
                        "text": "cue", "content_type": "SITUATION", "caption_role": "STATE",
                        "state_effect": "FLICKER_RAVE",
                    } if segment_role == "STATE" else {}),
                }
                for index, (segment_id, segment_role, start, duration) in enumerate(segment_specs, start=1)
            ]}), encoding="utf-8")
            config = {
                "episode_id": "EP", "clean_video": str(clean_video), "duration_us": 1_000,
                "approved_timeline_path": str(timeline), "T1": "one", "T2": "two",
                "state_cues": [{"text": "cue", "start_us": 0, "end_us": 1_000}],
                "audio_role": role, "audio_placements": [
                    {"source_range_us": [10, 110], "target_range_us": [100, 200]},
                    {"source_range_us": [200, 250], "target_range_us": [500, 550]},
                ],
            }
            if role == "A9":
                config.update({
                    "audio_role": None, "audio_policy": "TTS_ONLY_MUTE_SOURCE",
                    "tts_cues": [{"cue_id": "cue", "text": "voice", "audio_path": str(audio), "resource_name": "tts.wav", "target_range_us": [0, 1_000]}],
                })
            manifest = {"urakkai": {"video_clips": [{"clip_id": "video", "source_range_us": [0, 1_000], "target_range_us": [0, 1_000]}]}, "source_audio": []}
            with patch.object(builder, "_documents", return_value=[(document, payload)]):
                builder._normalize_source(project, config, audio, manifest)
            return json.loads(document.read_text(encoding="utf-8"))["tracks"]

    def test_normalize_source_readback_mutes_v2_base_tracks_and_keeps_a11_sfx(self):
        tracks = self._normalize_v2_audio("A11")
        self.assertEqual(tracks[0]["segments"][0]["volume"], 0.0)
        self.assertEqual(tracks[11]["segments"], [])
        self.assertEqual(tracks[12]["segments"], [])
        self.assertEqual(
            [(segment["id"], segment["target_timerange"]) for segment in tracks[13]["segments"]],
            [("a11-1", {"start": 100, "duration": 100}), ("a11-2", {"start": 500, "duration": 50})],
        )

    def test_normalize_source_readback_keeps_a12_as_one_full_duration_segment(self):
        tracks = self._normalize_v2_audio("A12")
        self.assertEqual(tracks[0]["segments"][0]["volume"], 0.0)
        self.assertEqual(tracks[11]["segments"], [])
        self.assertEqual(tracks[12]["segments"], [])
        self.assertEqual(len(tracks[14]["segments"]), 1)
        self.assertEqual(tracks[14]["segments"][0]["id"], "a12")
        self.assertEqual(tracks[14]["segments"][0]["role"], "A12")
        self.assertEqual(tracks[14]["segments"][0]["target_timerange"], {"start": 0, "duration": 1_000})
        self.assertEqual(tracks[14]["segments"][0]["source_timerange"], {"start": 0, "duration": 1_000})

    def test_normalize_source_readback_keeps_approved_a9_tts_at_normal_volume(self):
        tracks = self._normalize_v2_audio("A9")
        self.assertEqual(len(tracks[11]["segments"]), 1)
        self.assertEqual(tracks[11]["segments"][0]["role"], "A9")
        self.assertEqual(tracks[11]["segments"][0]["volume"], 1.0)
        self.assertEqual(tracks[11]["segments"][0]["last_nonzero_volume"], 1.0)

    def test_normal_a11_placements_survive_to_track_readback(self):
        self.assertTrue(hasattr(builder, "_populate_audio_placements"))
        template_segment = {
            "id": "template-segment", "material_id": "material-1",
            "target_timerange": {"start": 0, "duration": 1},
            "source_timerange": {"start": 0, "duration": 1},
        }
        material = {"id": "material-1", "type": "music", "path": "old"}
        track = {"segments": []}
        builder._populate_audio_placements(
            track, template_segment, material,
            portable_path="##_draftpath_placeholder_test_##/Resources/media/sfx.wav",
            role="A11",
            placements=[
                {"segment_id": "sfx-1", "source_range_us": [10, 110], "target_range_us": [100, 200]},
                {"segment_id": "sfx-2", "source_range_us": [200, 250], "target_range_us": [500, 550]},
            ],
        )
        self.assertEqual(
            [(row["id"], row["role"], row["target_timerange"], row["source_timerange"])
            for row in track["segments"]],
            [
                ("sfx-1", "A11", {"start": 100, "duration": 100}, {"start": 10, "duration": 100}),
                ("sfx-2", "A11", {"start": 500, "duration": 50}, {"start": 200, "duration": 50}),
            ],
        )
        self.assertEqual(material["role"], "A11")
        self.assertTrue(material["path"].endswith("Resources/media/sfx.wav"))

    def test_populates_one_full_duration_a12_segment_and_material(self):
        self.assertTrue(
            hasattr(builder, "_populate_full_duration_audio"),
            "builder must implement full-duration A12 population",
        )
        template_segment = {
            "id": "template-segment",
            "material_id": "material-1",
            "target_timerange": {"start": 0, "duration": 1},
            "source_timerange": {"start": 0, "duration": 1},
        }
        material = {"id": "material-1", "type": "music", "path": "old"}
        track = {"segments": []}

        builder._populate_full_duration_audio(
            track,
            copy.deepcopy(template_segment),
            material,
            portable_path="##_draftpath_placeholder_test_##/Resources/media/bgm.wav",
            duration_us=15_074_000,
            role="A12",
            segment_id="a12-bgm",
        )

        self.assertEqual(len(track["segments"]), 1)
        segment = track["segments"][0]
        self.assertEqual(segment["id"], "a12-bgm")
        self.assertEqual(segment["role"], "A12")
        self.assertEqual(segment["target_timerange"], {"start": 0, "duration": 15_074_000})
        self.assertEqual(segment["source_timerange"], {"start": 0, "duration": 15_074_000})
        self.assertEqual(material["role"], "A12")
        self.assertEqual(material["duration"], 15_074_000)
        self.assertTrue(material["path"].endswith("Resources/media/bgm.wav"))

    def test_cloud_prepare_creates_mirrors_and_scrubs_windows_cache_paths(self):
        self.assertTrue(hasattr(builder, "_prepare_cloud_project"))
        import json
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            project = Path(td)
            payload = {
                "duration": 1,
                "tracks": [],
                "materials": {
                    "videos": [{"id": "m1", "resource_id": "r1", "path": "C:/cache/effect.bin", "draft_file_path": "C:/old/subdraft/draft_content.json"}]
                },
            }
            (project / "draft_content.json").write_text(json.dumps(payload), encoding="utf-8")
            subdraft = project / "subdraft" / "legacy"
            subdraft.mkdir(parents=True)
            (subdraft / "draft_content.json").write_text(json.dumps(payload), encoding="utf-8")
            timeline = project / "Timelines" / "timeline-1"
            timeline.mkdir(parents=True)
            (timeline / "draft_content.json").write_text(json.dumps(payload), encoding="utf-8")
            meta = {"draft_id": "old", "draft_name": "old"}
            (project / "draft_meta_info.json").write_text(json.dumps(meta), encoding="utf-8")

            builder._prepare_cloud_project(
                project,
                project_name="test-project",
                capcut_root=project.parent,
                draft_id="draft-new",
                duration_us=15_074_000,
            )

            for path in (
                project / "draft_info.json",
                project / "template-2.tmp",
                timeline / "draft_info.json",
                timeline / "template-2.tmp",
            ):
                self.assertTrue(path.is_file(), str(path))
                self.assertNotIn("C:/", path.read_text(encoding="utf-8"))
            updated = json.loads((project / "draft_meta_info.json").read_text(encoding="utf-8"))
            self.assertEqual(updated["draft_id"], "draft-new")
            self.assertEqual(updated["draft_name"], "test-project")
            self.assertEqual(updated["tm_duration"], 15_074_000)
            self.assertFalse((project / "subdraft").exists())


if __name__ == "__main__":
    unittest.main()

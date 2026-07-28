import copy
import sys
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import build_episode_capcut as builder


class BgmA12BuilderTest(unittest.TestCase):
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

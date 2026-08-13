import sys
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import build_episode_capcut as builder


class BgmA12BuilderTest(unittest.TestCase):
    def test_a12_population_helper_is_absent_and_any_segment_is_rejected(self):
        self.assertFalse(hasattr(builder, "_populate_full_duration_audio"))
        with self.assertRaisesRegex(RuntimeError, "A12_RESERVED_EMPTY"):
            builder.assert_a12_empty([{"id": "a12-bgm", "role": "A12"}])
        builder.assert_a12_empty([])

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
            # Existing CapCut combination registrations are authoritative and
            # must survive cloud preparation; deleting them triggers open-time
            # reconstruction from stale seed metadata.
            self.assertTrue((subdraft / "draft_content.json").is_file())


if __name__ == "__main__":
    unittest.main()

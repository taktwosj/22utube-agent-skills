import json
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import validate_capcut_cloud_media as validator


class CapCutCloudMediaTest(unittest.TestCase):
    REFERENCED = "11111111-1111-4111-8111-111111111111"
    OTHER = "22222222-2222-4222-8222-222222222222"

    @staticmethod
    def _write(path: Path, payload: object) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload), encoding="utf-8")

    def _project(self, root: Path) -> Path:
        project = root / "fixture"
        project.mkdir()
        audio = project / "Resources" / "audio" / "speaker.wav"
        audio.parent.mkdir(parents=True)
        audio.write_bytes(b"RIFF")
        payload = {
            "materials": {},
            "tracks": [],
            "combination": {
                "draft_file_path": (
                    f"##_draftpath_placeholder_fixture_##/subdraft/"
                    f"{self.REFERENCED}/draft_content.json"
                )
            },
        }
        for name in ("draft_content.json", "draft_info.json", "template-2.tmp"):
            self._write(project / name, payload)
        self._write(
            project / "draft_meta_info.json",
            {
                "draft_fold_path": str(project.resolve()),
                "draft_root_path": str(project.parent.resolve()),
                "draft_materials": [
                    {"type": 0, "value": [{"file_Path": str(audio.resolve())}]}
                ],
            },
        )
        subdraft = project / "subdraft" / self.REFERENCED
        self._write(subdraft / "draft_content.json", {"materials": {}, "tracks": []})
        self._write(subdraft / "sub_draft_config.json", {})
        (project / "draft_cover.jpg").write_bytes(b"jpg")
        return project

    def test_project_local_metadata_and_referenced_subdraft_pass(self):
        with tempfile.TemporaryDirectory() as td:
            result = validator.validate_project(self._project(Path(td)))

        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["windows_path_files"], [])
        self.assertEqual(result["unreferenced_subdraft_directories"], [])
        self.assertEqual(result["missing_subdraft_directories"], [])

    def test_external_windows_path_and_orphaned_subdraft_fail(self):
        with tempfile.TemporaryDirectory() as td:
            project = self._project(Path(td))
            meta_path = project / "draft_meta_info.json"
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
            meta["cache_path"] = "C:/cache/effect.bin"
            self._write(meta_path, meta)
            orphan = project / "subdraft" / self.OTHER
            self._write(orphan / "draft_content.json", {})

            result = validator.validate_project(project)

        self.assertEqual(result["status"], "FAIL")
        self.assertIn("draft_meta_info.json", result["windows_path_files"])
        self.assertEqual(result["unreferenced_subdraft_directories"], [self.OTHER])

    def test_missing_referenced_subdraft_fails(self):
        with tempfile.TemporaryDirectory() as td:
            project = self._project(Path(td))
            content_path = project / "draft_content.json"
            payload = json.loads(content_path.read_text(encoding="utf-8"))
            payload["missing"] = {
                "draft_file_path": f"subdraft/{self.OTHER}/draft_content.json"
            }
            for name in ("draft_content.json", "draft_info.json", "template-2.tmp"):
                self._write(project / name, payload)

            result = validator.validate_project(project)

        self.assertEqual(result["status"], "FAIL")
        self.assertEqual(result["missing_subdraft_directories"], [self.OTHER])


if __name__ == "__main__":
    unittest.main()

import json
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import apply_capcut_polish_profile as profile
import validate_capcut_polish_profile as validator


def _segment(identifier, material_id, start, duration, role=None):
    value = {"id": identifier, "material_id": material_id, "target_timerange": {"start": start, "duration": duration}}
    if role:
        value["role"] = role
    return value


class CapCutPolishProfileTest(unittest.TestCase):
    def _project(self, root: Path) -> Path:
        payload = {
            "id": "timeline-test", "main_timeline_id": "timeline-test",
            "materials": {
                "videos": [{"id": "v1", "type": "video", "path": "Resources/media/clean_source.mp4"}, {"id": "v2", "type": "video", "path": "Resources/media/clean_source.mp4"}],
                "audios": [{"id": "a9", "type": "audio", "path": "Resources/media/tts_narrator.wav"}, {"id": "a10", "type": "audio", "path": "Resources/media/a10_vocal_stem.m4a"}],
            },
            "tracks": [
                {"segments": [_segment("video-1", "v1", 0, 2_000_000), _segment("video-2", "v2", 2_000_000, 2_000_000)]},
                {"segments": [_segment("narration", "a9", 0, 1_000_000, "A9")]},
                {"segments": [_segment("source", "a10", 0, 4_000_000, "A10")]},
            ],
        }
        (root / "draft_content.json").write_text(json.dumps(payload), encoding="utf-8")
        return root

    def test_applies_and_verifies_every_required_polish_control(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = self._project(Path(tmp))
            receipt = profile.apply_project(project)
            self.assertEqual(receipt["status"], "PASS")
            self.assertEqual(validator.validate_project(project)["status"], "PASS")
            data = json.loads((project / "draft_content.json").read_text(encoding="utf-8"))
            source = data["tracks"][2]["segments"][0]
            self.assertEqual(source["volume"], 0.0)
            self.assertNotIn("vocal_separations", data["materials"])


if __name__ == "__main__":
    unittest.main()

from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "build_top5isu_capcut.py"
spec = importlib.util.spec_from_file_location("build_top5isu_capcut", SCRIPT)
builder = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(builder)


class BuilderInputNormalizationTests(unittest.TestCase):
    def test_subtitle_aliases_and_sub_millisecond_tail_are_normalized(self) -> None:
        cues = [
            {"start_sec": 0.0, "end_sec": 1.0, "text": "첫 자막"},
            {"start_sec": 1.0, "end_sec": 58.063, "text": "마지막 자막"},
        ]
        normalized = builder.normalize_subtitle_cues(cues, duration_us=58_062_854)
        self.assertEqual(normalized[0]["start"], 0.0)
        self.assertEqual(normalized[-1]["end"], 58.062854)
        self.assertEqual(normalized[-1]["text"], "마지막 자막")

    def test_subtitle_tail_over_one_millisecond_is_rejected(self) -> None:
        cues = [{"start": 0.0, "end": 58.065, "text": "초과"}]
        with self.assertRaises(builder.BuildFail):
            builder.normalize_subtitle_cues(cues, duration_us=58_062_854)

    def test_inherited_cloud_identity_is_cleared(self) -> None:
        meta = {
            "cloud_draft_sync": True,
            "cloud_draft_cover": "old-cover",
            "tm_draft_cloud_completed": "123",
            "tm_draft_cloud_entry_id": 123,
            "tm_draft_cloud_modified": 456,
            "tm_draft_cloud_parent_entry_id": 789,
            "tm_draft_cloud_space_id": 111,
            "tm_draft_cloud_user_id": 222,
        }
        cleaned = builder.sanitize_inherited_cloud_identity(meta)
        self.assertFalse(cleaned["cloud_draft_sync"])
        self.assertEqual(cleaned["cloud_draft_cover"], "")
        self.assertEqual(cleaned["tm_draft_cloud_completed"], "0")
        self.assertEqual(cleaned["tm_draft_cloud_entry_id"], 0)
        self.assertEqual(cleaned["tm_draft_cloud_modified"], 0)
        self.assertEqual(cleaned["tm_draft_cloud_parent_entry_id"], -1)
        self.assertEqual(cleaned["tm_draft_cloud_space_id"], 0)
        self.assertEqual(cleaned["tm_draft_cloud_user_id"], 0)


if __name__ == "__main__":
    unittest.main()

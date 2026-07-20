from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from _support import load_source_module_no_bytecode


ROOT = Path(__file__).resolve().parents[1]
VALIDATOR = (
    ROOT
    / "skills"
    / "000short-production-agent"
    / "scripts"
    / "validate_capcut_media_links.py"
)


def write(path: Path, text: str = "ok") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def write_json(path: Path, data: dict) -> None:
    write(path, json.dumps(data, ensure_ascii=False, indent=2) + "\n")


class MediaLinkGateTests(unittest.TestCase):
    def test_active_source_video_must_link_existing_source(self):
        module = load_source_module_no_bytecode("media_link_valid", VALIDATOR)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write(root / "00_source" / "source.mp4", "video")
            write_json(
                root / "50_capcut_project" / "draft_content.json",
                {
                    "active_materials": [
                        {
                            "role": "source_video",
                            "path": "00_source/source.mp4",
                            "active": True,
                            "audio_enabled": False,
                        }
                    ]
                },
            )

            result = module.validate_capcut_media_links(
                root,
                Path("50_capcut_project/draft_content.json"),
                Path("00_source/source.mp4"),
            )

            self.assertEqual(result["capcut_media_links_status"], "PASS")

    def test_missing_active_source_path_fails(self):
        module = load_source_module_no_bytecode("media_link_missing", VALIDATOR)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write(root / "00_source" / "source.mp4", "video")
            write_json(
                root / "50_capcut_project" / "draft_content.json",
                {
                    "active_materials": [
                        {"role": "source_video", "path": "missing.mp4", "active": True}
                    ]
                },
            )

            with self.assertRaisesRegex(module.GateFail, "FAIL_MEDIA_LINK"):
                module.validate_capcut_media_links(
                    root,
                    Path("50_capcut_project/draft_content.json"),
                    Path("00_source/source.mp4"),
                )

    def test_source_video_audio_muted_by_default_except_speaker_quote(self):
        module = load_source_module_no_bytecode("media_link_audio_mute", VALIDATOR)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write(root / "00_source" / "source.mp4", "video")
            draft_path = root / "50_capcut_project" / "draft_content.json"
            write_json(
                draft_path,
                {
                    "active_materials": [
                        {
                            "role": "source_video",
                            "path": "00_source/source.mp4",
                            "active": True,
                            "audio_enabled": True,
                            "caption_type": "tts_narration",
                        }
                    ]
                },
            )

            with self.assertRaisesRegex(module.GateFail, "FAIL_SOURCE_VIDEO_AUDIO_NOT_MUTED"):
                module.validate_capcut_media_links(root, draft_path, Path("00_source/source.mp4"))

            write_json(
                draft_path,
                {
                    "active_materials": [
                        {
                            "role": "source_video",
                            "path": "00_source/source.mp4",
                            "active": True,
                            "audio_enabled": True,
                            "caption_type": "speaker_quote",
                        }
                    ]
                },
            )
            module.validate_capcut_media_links(root, draft_path, Path("00_source/source.mp4"))


if __name__ == "__main__":
    unittest.main()

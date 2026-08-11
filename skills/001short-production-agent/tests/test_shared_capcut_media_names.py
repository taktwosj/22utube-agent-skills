from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path


SKILL = Path(__file__).resolve().parents[1]
SCRIPTS = SKILL / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import prepare_shared_capcut_media as media


class SharedCapCutMediaNamesTest(unittest.TestCase):
    def _write(self, root: Path, relative: str, content: bytes = b"media") -> Path:
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
        return path

    def test_001_maps_shared_sentence_and_vocals_to_legacy_capcut_names(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "episode_media"
            sentence = self._write(root, "sentences/001.wav", b"tts")
            vocals = self._write(root, "vocals.wav", b"voice")
            self._write(root, "source.mp4", b"source")
            receipt = media.prepare_profile(root, "001")
            output = root / "capcut_media" / "001"
            self.assertEqual((output / "tts_01.wav").read_bytes(), sentence.read_bytes())
            self.assertEqual((output / "source_vocals.wav").read_bytes(), vocals.read_bytes())
            self.assertEqual((output / "source.mp4").read_bytes(), b"source")
            self.assertFalse((output / "clean_video.mp4").exists())
            self.assertEqual(receipt["status"], "PASS")

    def test_gunlimbo_keeps_its_existing_names(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "episode_media"
            self._write(root, "scene_01.png", b"scene")
            self._write(root, "narration_final.wav", b"narration")
            receipt = media.prepare_profile(root, "gunlimbo")
            output = root / "capcut_media" / "gunlimbo"
            self.assertEqual((output / "scene_01.png").read_bytes(), b"scene")
            self.assertEqual((output / "narration_final.wav").read_bytes(), b"narration")
            self.assertEqual(receipt["status"], "PASS")

    def test_different_existing_target_stops_without_overwrite(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "episode_media"
            self._write(root, "sentences/001.wav", b"correct")
            target = self._write(root, "capcut_media/001/tts_01.wav", b"different")
            with self.assertRaisesRegex(RuntimeError, "CAPCUT_MEDIA_TARGET_CONFLICT"):
                media.prepare_profile(root, "001")
            self.assertEqual(target.read_bytes(), b"different")


if __name__ == "__main__":
    unittest.main()

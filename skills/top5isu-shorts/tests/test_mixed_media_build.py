from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from PIL import Image

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

from build_top5isu_capcut import (
    collect_visual_media,
    media_dimensions,
    media_kind,
    make_audio_track,
    visual_asset_spec,
)


class MixedMediaBuildTest(unittest.TestCase):
    def test_collect_visual_media_accepts_ordered_png_and_mp4(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            Image.new("RGB", (32, 24), "red").save(root / "scene_01.png")
            subprocess.run(
                [
                    "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
                    "-f", "lavfi", "-i", "color=blue:s=40x30:r=30:d=0.5",
                    "-an", "-c:v", "libx264", "-pix_fmt", "yuv420p",
                    str(root / "scene_02.mp4"),
                ],
                check=True,
            )

            media = collect_visual_media(root)

            self.assertEqual([path.name for path in media], ["scene_01.png", "scene_02.mp4"])
            self.assertEqual(media_kind(media[0]), "photo")
            self.assertEqual(media_kind(media[1]), "video")
            self.assertEqual(media_dimensions(media[0]), (32, 24))
            self.assertEqual(media_dimensions(media[1]), (40, 30))

    def test_visual_asset_spec_preserves_extension_and_mutes_video_audio(self) -> None:
        photo = visual_asset_spec(Path("scene_01.png"), 1)
        video = visual_asset_spec(Path("scene_02.mp4"), 2)

        self.assertEqual(photo, {"filename": "asset_01.png", "type": "photo", "has_audio": False})
        self.assertEqual(video, {"filename": "asset_02.mp4", "type": "video", "has_audio": False})

    def test_make_audio_track_builds_named_bgm_lane(self) -> None:
        track = make_audio_track("A_BGM", "material-1", 2_000_000, 0.16)

        self.assertEqual(track["name"], "A_BGM")
        self.assertEqual(track["type"], "audio")
        self.assertEqual(track["segments"][0]["material_id"], "material-1")
        self.assertEqual(track["segments"][0]["target_timerange"], {"start": 0, "duration": 2_000_000})
        self.assertEqual(track["segments"][0]["volume"], 0.16)


if __name__ == "__main__":
    unittest.main()

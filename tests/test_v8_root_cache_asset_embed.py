# -*- coding: utf-8 -*-
"""근본 캐시 자산 이식이 같은 경로를 두 번 만나도 죽지 않는지 본다.

CapCut 은 근본 폴더를 열 때마다 사본 번호를 다시 매긴다. (6) 이 (7) 이 되면
되돌리기 기록(attachment/patch/*.json)에 남은 절대경로는 접미 없는 옛 이름을
가리켜 파일을 못 찾는다. 그때 빌더는 이름으로 다시 찾는데, 첫 번째 파일을
처리하며 Resources/v8_root_assets/ 에 복사본을 만들어 두면 두 번째 파일에서
후보가 둘이 되어 "없다"고 잘못 판정했다.
"""
from __future__ import annotations

import importlib.util
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BUILDER = ROOT / "skills" / "119-politics-longform-capcut" / "scripts" / "build_politics_v8_project.py"


def load_builder():
    # 빌더는 같은 폴더의 build_politics_card_project 를 부른다. 경로를 먼저 넣는다.
    scripts = str(BUILDER.parent)
    if scripts not in sys.path:
        sys.path.insert(0, scripts)
    spec = importlib.util.spec_from_file_location("build_politics_v8_project", BUILDER)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class V8RootCacheAssetEmbedTests(unittest.TestCase):
    def setUp(self):
        self.builder = load_builder()

    def _stage(self, tmp: Path, stale_path: str, files: int) -> Path:
        """자산 하나를 두고, 그 자산을 가리키는 파일을 files 개 만든다."""
        stage = tmp / "stage"
        (stage / "Resources").mkdir(parents=True)
        (stage / "Resources" / "V8_TEST_VIDEO_C03_10S_1920x1080.mp4").write_bytes(b"v8")
        for index in range(files):
            (stage / f"patch{index}.json").write_text(
                json.dumps({"path": stale_path}, ensure_ascii=False), encoding="utf-8")
        return stage

    def test_same_stale_path_in_two_files_does_not_fail(self):
        import tempfile

        with tempfile.TemporaryDirectory() as raw:
            tmp = Path(raw)
            stale = r"C:\CapCut\P0_ROOT_v8_layout_user_edit\Resources\V8_TEST_VIDEO_C03_10S_1920x1080.mp4"
            stage = self._stage(tmp, stale, files=2)
            final_root = tmp / "final"

            self.builder.embed_root_cache_assets(stage, final_root)

            embedded = stage / "Resources" / "v8_root_assets" / "V8_TEST_VIDEO_C03_10S_1920x1080.mp4"
            self.assertTrue(embedded.is_file(), "자산이 이식되지 않았다")
            for index in range(2):
                document = json.loads((stage / f"patch{index}.json").read_text(encoding="utf-8"))
                self.assertIn("v8_root_assets", document["path"])
                self.assertNotIn("P0_ROOT_v8_layout_user_edit\\Resources", document["path"])

    def test_single_file_still_works(self):
        import tempfile

        with tempfile.TemporaryDirectory() as raw:
            tmp = Path(raw)
            stale = r"C:\CapCut\P0_ROOT_v8_layout_user_edit\Resources\V8_TEST_VIDEO_C03_10S_1920x1080.mp4"
            stage = self._stage(tmp, stale, files=1)
            self.builder.embed_root_cache_assets(stage, tmp / "final")
            self.assertTrue((stage / "Resources" / "v8_root_assets"
                             / "V8_TEST_VIDEO_C03_10S_1920x1080.mp4").is_file())

    def test_truly_missing_asset_still_raises(self):
        import tempfile

        with tempfile.TemporaryDirectory() as raw:
            tmp = Path(raw)
            stage = tmp / "stage"
            (stage / "Resources").mkdir(parents=True)
            (stage / "patch.json").write_text(
                json.dumps({"path": r"C:\CapCut\gone\Resources\NOT_THERE.mp4"}), encoding="utf-8")
            with self.assertRaises(RuntimeError) as caught:
                self.builder.embed_root_cache_assets(stage, tmp / "final")
            self.assertIn("V8_ROOT_CACHE_ASSET_MISSING", str(caught.exception))

    def test_ambiguous_name_still_raises(self):
        """이름이 같은 서로 다른 자산이 둘이면 고를 수 없으므로 그대로 실패해야 한다."""
        import tempfile

        with tempfile.TemporaryDirectory() as raw:
            tmp = Path(raw)
            stage = tmp / "stage"
            (stage / "Resources" / "a").mkdir(parents=True)
            (stage / "Resources" / "b").mkdir(parents=True)
            (stage / "Resources" / "a" / "DUP.mp4").write_bytes(b"a")
            (stage / "Resources" / "b" / "DUP.mp4").write_bytes(b"b")
            (stage / "patch.json").write_text(
                json.dumps({"path": r"C:\CapCut\gone\Resources\DUP.mp4"}), encoding="utf-8")
            with self.assertRaises(RuntimeError):
                self.builder.embed_root_cache_assets(stage, tmp / "final")


if __name__ == "__main__":
    unittest.main()

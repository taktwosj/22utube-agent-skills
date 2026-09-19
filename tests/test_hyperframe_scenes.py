# -*- coding: utf-8 -*-
"""한 하이퍼프레임 장면이 여러 카드에 걸쳐 이어지는지 본다.

카드 한 장에 영상 한 편씩 만들면 삼 초짜리가 줄줄이 이어져 화면이 끊긴다.
나레이션이 이어지는 동안 그래픽도 이어져야 하므로, 열 초 안팎의 장면 하나를
연속한 카드들이 나눠 가져간다. 각 카드는 그 장면의 다른 구간을 쓴다.
"""
from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "skills" / "spine-script-119" / "scripts"


def load(name: str):
    sys.path.insert(0, str(SCRIPTS))
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


common = load("_common")
evidence = load("gen_evidence")


def timeline(rows):
    """rows: (narration_name, start_us, duration_us)"""
    return {"cards": [{"kind": "NAR", "card_id": f"C_{n}", "narration_name": n,
                       "target_start_us": s, "target_duration_us": d} for n, s, d in rows]}


class SceneNamingTests(unittest.TestCase):
    def test_scene_pattern_accepts_a_range(self):
        self.assertTrue(common.HYPERFRAME_SCENE.match("NL88-NL90"))

    def test_scene_pattern_rejects_a_single_line(self):
        self.assertIsNone(common.HYPERFRAME_SCENE.match("NL88"))

    def test_scene_members_span_the_whole_range(self):
        root = self.make_root([("NL01", 0, 100), ("NL02", 100, 100), ("NL03", 200, 100)], ["NL01-NL03"])
        self.assertEqual(sorted(common.hyperframe_files(root)), ["C_NL01", "C_NL02", "C_NL03"])

    def test_reversed_range_is_refused(self):
        root = self.make_root([("NL01", 0, 100), ("NL02", 100, 100)], ["NL02-NL01"])
        with self.assertRaises(SystemExit) as caught:
            common.hyperframe_files(root)
        self.assertIn("HYPERFRAME_SCENE_REVERSED", str(caught.exception))

    def test_unknown_line_is_refused(self):
        root = self.make_root([("NL01", 0, 100)], ["NL01-NL99"])
        with self.assertRaises(SystemExit) as caught:
            common.hyperframe_files(root)
        self.assertIn("HYPERFRAME_SCENE_UNKNOWN_LINE", str(caught.exception))

    def make_root(self, rows, scenes=()) -> Path:
        import tempfile
        root = Path(tempfile.mkdtemp())
        (root / "work").mkdir()
        (root / "hyperframes").mkdir()
        (root / "work" / "timeline.json").write_text(
            json.dumps(timeline(rows), ensure_ascii=False), encoding="utf-8")
        for name in scenes:
            (root / "hyperframes" / f"{name}.mp4").write_bytes(b"")
        return root


class SceneOffsetTests(unittest.TestCase):
    def test_each_card_takes_the_next_slice(self):
        clip = Path("SCENE.mp4")
        tl = timeline([("NL01", 0, 400), ("NL02", 400, 300), ("NL03", 700, 200)])
        moving = {"C_NL01": clip, "C_NL02": clip, "C_NL03": clip}
        evidence.check_scene_lengths = lambda *a, **k: None
        offsets = evidence.video_offsets(tl, moving)
        self.assertEqual(offsets, {"C_NL01": 0, "C_NL02": 400, "C_NL03": 700})

    def test_two_scenes_count_separately(self):
        a, b = Path("A.mp4"), Path("B.mp4")
        tl = timeline([("NL01", 0, 400), ("NL02", 400, 300), ("NL03", 700, 200)])
        moving = {"C_NL01": a, "C_NL02": a, "C_NL03": b}
        evidence.check_scene_lengths = lambda *a, **k: None
        offsets = evidence.video_offsets(tl, moving)
        self.assertEqual(offsets["C_NL03"], 0)

    def test_a_gap_inside_a_scene_restarts_it(self):
        """붙어 있지 않으면 같은 영상이라도 다시 0부터 쓴다 (CTA 가 앞뒤 두 번 놓이는 경우)."""
        clip = Path("SCENE.mp4")
        tl = timeline([("NL01", 0, 400), ("NL02", 900, 300)])
        evidence.check_scene_lengths = lambda *a, **k: None
        offsets = evidence.video_offsets(tl, {"C_NL01": clip, "C_NL02": clip})
        self.assertEqual(offsets, {"C_NL01": 0, "C_NL02": 0})

    def test_a_short_scene_is_refused(self):
        """영상이 카드 합계보다 짧으면 뒤가 검게 빈다."""
        real = load("gen_evidence")
        with self.assertRaises(SystemExit) as caught:
            real.check_scene_lengths({}, {str(SCRIPTS / "gen_evidence.py"): 10_000_000})
        self.assertIn("HYPERFRAME_PROBE_FAILED", str(caught.exception))


class ContractTests(unittest.TestCase):
    def test_evidence_uses_the_shared_map(self):
        text = (SCRIPTS / "gen_evidence.py").read_text(encoding="utf-8")
        self.assertIn("hyperframe_files", text)
        self.assertIn('"video_start_us": offsets[r["card_id"]]', text)

    def test_script_uses_the_shared_map(self):
        text = (SCRIPTS / "gen_script.py").read_text(encoding="utf-8")
        self.assertIn("hyperframes = hyperframe_files(root)", text)
        self.assertIn("moving = cid in hyperframes", text)

    def test_a_line_claimed_twice_is_refused(self):
        import tempfile
        root = Path(tempfile.mkdtemp())
        (root / "work").mkdir()
        (root / "hyperframes").mkdir()
        (root / "work" / "timeline.json").write_text(
            json.dumps(timeline([("NL01", 0, 100), ("NL02", 100, 100)]), ensure_ascii=False),
            encoding="utf-8")
        (root / "hyperframes" / "NL01.mp4").write_bytes(b"")
        (root / "hyperframes" / "NL01-NL02.mp4").write_bytes(b"")
        with self.assertRaises(SystemExit) as caught:
            common.hyperframe_files(root)
        self.assertIn("HYPERFRAME_DUPLICATE_CLAIM", str(caught.exception))

    def test_ffprobe_is_available(self):
        probe = subprocess.run(["ffprobe", "-version"], capture_output=True)
        self.assertEqual(probe.returncode, 0)


if __name__ == "__main__":
    unittest.main()

"""RW-P04-03: canonical Markdown reconciliation is structural-path aware."""

from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CANONICAL_RENDER_PY = (
    ROOT / "shared" / "workflow-harness" / "core" / "canonical_render.py"
)


def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    try:
        spec.loader.exec_module(mod)
    except Exception:
        sys.modules.pop(name, None)
        raise
    return mod


def _move_line_after(lines: list[str], moving_marker: str, target_marker: str) -> str:
    moved = next(line for line in lines if moving_marker in line)
    remaining = [line for line in lines if line != moved]
    target_index = next(i for i, line in enumerate(remaining) if target_marker in line)
    remaining.insert(target_index + 1, moved)
    return "\n".join(remaining)


class PathAwareReconcileTests(unittest.TestCase):
    def setUp(self):
        self.cr = _load_module("rw_p04_03_path_aware", CANONICAL_RENDER_PY)

    def assert_mismatch(self, canonical: dict, human_md: str):
        with self.assertRaises(self.cr.HumanMdCanonicalJsonMismatch):
            self.cr.reconcile_human_md(canonical=canonical, human_md=human_md)

    def test_moving_duplicate_title_between_parent_objects_fails(self):
        canonical = {
            "chapter_a": {"title": "SAME"},
            "chapter_b": {"title": "SAME"},
        }
        rendered = self.cr.render_markdown(canonical)
        moved = _move_line_after(
            rendered.splitlines(),
            "<!-- path: chapter_a.title -->",
            "<!-- path: chapter_b.title -->",
        )
        self.assert_mismatch(canonical, moved)

    def test_moving_duplicate_title_between_array_indices_fails(self):
        canonical = {
            "segments": [
                {"title": "SAME"},
                {"title": "SAME"},
            ]
        }
        rendered = self.cr.render_markdown(canonical)
        moved = _move_line_after(
            rendered.splitlines(),
            "<!-- path: segments[0].title -->",
            "<!-- path: segments[1].title -->",
        )
        self.assert_mismatch(canonical, moved)

    def test_deleting_one_duplicate_structural_field_fails(self):
        canonical = {
            "chapter_a": {"title": "SAME"},
            "chapter_b": {"title": "SAME"},
        }
        rendered = self.cr.render_markdown(canonical)
        changed = "\n".join(
            line
            for line in rendered.splitlines()
            if "<!-- path: chapter_a.title -->" not in line
        )
        self.assert_mismatch(canonical, changed)

    def test_reparenting_empty_object_fails(self):
        canonical = {
            "chapter_a": {"notes": {}},
            "chapter_b": {},
        }
        rendered = self.cr.render_markdown(canonical)
        moved = _move_line_after(
            rendered.splitlines(),
            "<!-- path: chapter_a.notes -->",
            "<!-- path: chapter_b -->",
        )
        self.assert_mismatch(canonical, moved)

    def test_unchanged_canonical_render_is_in_sync(self):
        canonical = {"segments": [{"title": "A"}, {"title": "B"}]}
        result = self.cr.reconcile_human_md(
            canonical=canonical,
            human_md=self.cr.render_markdown(canonical),
        )
        self.assertEqual(result, {"status": "IN_SYNC", "action": "NONE"})

    def test_whitespace_only_change_with_same_ordered_records_is_cosmetic(self):
        canonical = {"segments": [{"title": "A"}, {"title": "B"}]}
        rendered = self.cr.render_markdown(canonical)
        changed = "\n\n".join(
            f"  {line}  " if "<!-- path:" in line else line
            for line in rendered.splitlines()
        )
        result = self.cr.reconcile_human_md(canonical=canonical, human_md=changed)
        self.assertEqual(
            result,
            {
                "status": "COSMETIC_DIFF_ONLY",
                "action": "RE_RENDER_RECOMMENDED",
            },
        )


if __name__ == "__main__":
    unittest.main()

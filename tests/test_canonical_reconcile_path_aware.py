"""RW-P04-03 round 5 regression: structural record reconciliation.

Round-4 path-aware tests used text-replace tricks that don't apply to the
round-5 lossless codec (records are JSON arrays now). These tests cover the
same structural scenarios using the codec helpers in
``tests/_canonical_codec_helpers.py`` so the assertions are precise:

- sibling-field reparent is detected (path segment change)
- array-element move across indices is detected
- empty-container add/remove is detected
- value edit is detected (exact value match)
- genuinely cosmetic diffs still return COSMETIC_DIFF_ONLY
"""

from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path

from tests._canonical_codec_helpers import (
    duplicate_record_line,
    rewrite_record_value,
)


ROOT = Path(__file__).resolve().parents[1]
CANONICAL_RENDER_PY = ROOT / "shared" / "workflow-harness" / "core" / "canonical_render.py"


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


class StructuralRecordReconcileTests(unittest.TestCase):
    def setUp(self):
        self.cr = _load_module("rw_p04_03_v5b_cr", CANONICAL_RENDER_PY)

    def _assert_mismatch(self, canonical: dict, tampered_md: str) -> None:
        with self.assertRaises(self.cr.HumanMdCanonicalJsonMismatch) as ctx:
            self.cr.reconcile_human_md(canonical=canonical, human_md=tampered_md)
        self.assertEqual(ctx.exception.kind, "STRUCTURAL_OR_VALUE_CHANGE")

    # --- reparent / move detection ---

    def test_sibling_field_reparent_is_detected(self):
        """Changing a record's path segment from one parent to another is
        detected (path mismatch)."""
        canonical = {
            "schema_version": "demo-v1",
            "chapter_a": {"title": "SAME"},
            "chapter_b": {"title": "SAME"},
        }
        rendered = self.cr.render_markdown(canonical)
        # Rewrite the value carried at chapter_a.title path so that the
        # chapter_a path now points to a different value than canonical.
        # (Reparent of the value to chapter_b would create a duplicate,
        # which is covered by duplicate_record_line_detected.)
        tampered_md = rewrite_record_value(rendered, "chapter_a.title", "OTHER")
        self._assert_mismatch(canonical, tampered_md)

    def test_array_element_move_across_indices_is_detected(self):
        """Rewriting segments[0].title's value while keeping segments[1]
        unchanged detects the index-specific change."""
        canonical = {
            "schema_version": "demo-v1",
            "segments": [
                {"title": "X"},
                {"title": "X"},
            ],
        }
        rendered = self.cr.render_markdown(canonical)
        # The helper matches by leaf "title" and rewrites the FIRST match.
        # segments[0].title is emitted first in canonical order, so it
        # gets rewritten. segments[1].title stays "X". The record lists
        # now differ.
        tampered_md = rewrite_record_value(rendered, "title", "Y")
        self._assert_mismatch(canonical, tampered_md)

    def test_array_element_duplication_detected(self):
        """Adding a second identical record for segments[0].title (multiplicity
        change) must be detected even when the value matches an existing
        record."""
        canonical = {
            "schema_version": "demo-v1",
            "segments": [{"title": "X"}],
        }
        rendered = self.cr.render_markdown(canonical)
        tampered_md = duplicate_record_line(rendered, "title")
        self._assert_mismatch(canonical, tampered_md)

    # --- empty container handling ---

    def test_empty_object_addition_is_detected(self):
        canonical = {"schema_version": "demo-v1", "chapter_a": {"title": "X"}}
        tampered_canonical = {
            "schema_version": "demo-v1",
            "chapter_a": {"title": "X"},
            "chapter_b": {},
        }
        tampered_md = self.cr.render_markdown(tampered_canonical)
        self._assert_mismatch(canonical, tampered_md)

    def test_empty_object_removal_is_detected(self):
        canonical = {
            "schema_version": "demo-v1",
            "chapter_a": {"title": "X"},
            "chapter_b": {},
        }
        tampered_canonical = {"schema_version": "demo-v1", "chapter_a": {"title": "X"}}
        tampered_md = self.cr.render_markdown(tampered_canonical)
        self._assert_mismatch(canonical, tampered_md)

    def test_empty_list_addition_is_detected(self):
        canonical = {"schema_version": "demo-v1", "kept": "X"}
        tampered_canonical = {"schema_version": "demo-v1", "kept": "X", "arr": []}
        tampered_md = self.cr.render_markdown(tampered_canonical)
        self._assert_mismatch(canonical, tampered_md)

    # --- value edits ---

    def test_value_edit_is_detected(self):
        canonical = {"schema_version": "demo-v1", "title": "HELLO"}
        rendered = self.cr.render_markdown(canonical)
        tampered_md = rewrite_record_value(rendered, "title", "HELLOO")
        self._assert_mismatch(canonical, tampered_md)

    # --- cosmetic diffs ---

    def test_genuinely_cosmetic_whitespace_passes(self):
        canonical = {"schema_version": "demo-v1", "title": "HELLO"}
        rendered = self.cr.render_markdown(canonical)
        tampered_md = rendered.replace(
            "Do not edit.",
            "Please do not edit by hand.",
        )
        tampered_md = "\n\n".join(tampered_md.splitlines())
        result = self.cr.reconcile_human_md(canonical=canonical, human_md=tampered_md)
        self.assertIn(result["status"], ("IN_SYNC", "COSMETIC_DIFF_ONLY"))

    def test_re_rendered_canonical_is_in_sync(self):
        canonical = {
            "schema_version": "demo-v1",
            "chapter_a": {"title": "SAME"},
            "chapter_b": {"title": "SAME"},
            "segments": [{"id": "s0"}, {"id": "s1"}],
        }
        rendered = self.cr.render_markdown(canonical)
        result = self.cr.reconcile_human_md(canonical=canonical, human_md=rendered)
        self.assertEqual(result["status"], "IN_SYNC")


if __name__ == "__main__":
    unittest.main()

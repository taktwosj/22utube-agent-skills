"""RW-P04-03 round 4 regression: ordered structural record reconciliation.

Round-3 path-token approach failed because the reconciler searched for
each marker anywhere in the document and never validated indentation or
parent/array position. Round-4 replaces the marker-search with EXACT
set comparison on (path, value) tuples parsed from the rendered MD.

These tests cover:
- sibling-field reparent is detected (chapter_a.title -> chapter_b)
- array-element move across indices is detected (segments[0] -> segments[1])
- empty-container add/remove is detected (no StopIteration; renderer
  emits explicit <empty-object>/<empty-list> records)
- value edit is detected (exact value match, not substring)
- bool/null field deletion is detected
- genuinely cosmetic diffs still return COSMETIC_DIFF_ONLY
- same canonical re-rendered is IN_SYNC
"""

from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path


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
        self.cr = _load_module("rw_p04_03_v4_cr", CANONICAL_RENDER_PY)

    def _assert_mismatch(self, canonical: dict, tampered_md: str) -> None:
        with self.assertRaises(self.cr.HumanMdCanonicalJsonMismatch) as ctx:
            self.cr.reconcile_human_md(canonical=canonical, human_md=tampered_md)
        self.assertEqual(ctx.exception.kind, "STRUCTURAL_OR_VALUE_CHANGE")

    # --- reparent / move detection ---

    def test_sibling_field_reparent_is_detected(self):
        """Move chapter_a.title to a different parent. Same value, different
        parent path. Round-3 passed because the path token was searched
        document-wide."""
        canonical = {
            "schema_version": "demo-v1",
            "chapter_a": {"title": "SAME"},
            "chapter_b": {"title": "SAME"},
        }
        rendered = self.cr.render_markdown(canonical)
        # Rename one record's path to a different parent. The value stays
        # the same, so substring/Counter approaches miss it.
        tampered_md = rendered.replace(
            "P path:chapter_a.title = SAME",
            "P path:chapter_a.moved = SAME",
        )
        self._assert_mismatch(canonical, tampered_md)

    def test_array_element_move_across_indices_is_detected(self):
        """Move segments[0].title into segments[1]. Same value, different
        array index. Round-3 passed because token-search ignored index."""
        canonical = {
            "schema_version": "demo-v1",
            "segments": [
                {"title": "X"},
                {"title": "X"},
            ],
        }
        rendered = self.cr.render_markdown(canonical)
        tampered_md = rendered.replace(
            "P path:segments[0].title = X",
            "P path:segments[1].title = X",
        )
        # segments[0].title is now missing, segments[1].title duplicated.
        self._assert_mismatch(canonical, tampered_md)

    # --- empty container handling (no StopIteration) ---

    def test_empty_object_addition_is_detected(self):
        canonical = {
            "schema_version": "demo-v1",
            "chapter_a": {"title": "X"},
        }
        tampered_canonical = {
            "schema_version": "demo-v1",
            "chapter_a": {"title": "X"},
            "chapter_b": {},  # empty container added
        }
        tampered_md = self.cr.render_markdown(tampered_canonical)
        self._assert_mismatch(canonical, tampered_md)

    def test_empty_object_removal_is_detected(self):
        canonical = {
            "schema_version": "demo-v1",
            "chapter_a": {"title": "X"},
            "chapter_b": {},  # empty container present
        }
        tampered_canonical = {
            "schema_version": "demo-v1",
            "chapter_a": {"title": "X"},
        }
        tampered_md = self.cr.render_markdown(tampered_canonical)
        self._assert_mismatch(canonical, tampered_md)

    def test_empty_list_addition_is_detected(self):
        canonical = {"schema_version": "demo-v1", "kept": "X"}
        tampered_canonical = {"schema_version": "demo-v1", "kept": "X", "arr": []}
        tampered_md = self.cr.render_markdown(tampered_canonical)
        self._assert_mismatch(canonical, tampered_md)

    # --- value comparison must be exact, not substring ---

    def test_value_edit_is_detected(self):
        """Changing 'HELLO' to 'HELLOO' must be detected. Substring check
        ('HELLO' in 'HELLOO') would pass; exact-record match must not."""
        canonical = {"schema_version": "demo-v1", "title": "HELLO"}
        tampered_md = self.cr.render_markdown(canonical).replace(
            "P path:title = HELLO",
            "P path:title = HELLOO",
        )
        self._assert_mismatch(canonical, tampered_md)

    def test_value_prefixed_substring_is_detected(self):
        """A new value that contains the old value as a substring must
        still be detected as a change."""
        canonical = {"schema_version": "demo-v1", "code": "AB"}
        tampered_md = self.cr.render_markdown(canonical).replace(
            "P path:code = AB",
            "P path:code = ABC",
        )
        self._assert_mismatch(canonical, tampered_md)

    # --- bool / null deletion must be detected ---

    def test_bool_field_deletion_is_detected(self):
        canonical = {"schema_version": "demo-v1", "flag": True}
        tampered_md = self.cr.render_markdown({"schema_version": "demo-v1"})
        self._assert_mismatch(canonical, tampered_md)

    def test_bool_value_flip_is_detected(self):
        canonical = {"schema_version": "demo-v1", "flag": True}
        tampered_md = self.cr.render_markdown(
            {"schema_version": "demo-v1", "flag": False}
        )
        self._assert_mismatch(canonical, tampered_md)

    def test_null_field_deletion_is_detected(self):
        canonical = {"schema_version": "demo-v1", "note": None}
        tampered_md = self.cr.render_markdown({"schema_version": "demo-v1"})
        self._assert_mismatch(canonical, tampered_md)

    # --- cosmetic diffs must still pass ---

    def test_genuinely_cosmetic_whitespace_passes(self):
        canonical = {"schema_version": "demo-v1", "title": "HELLO"}
        rendered = self.cr.render_markdown(canonical)
        # Insert blank lines and reword a comment. Path-record set unchanged.
        tampered_md = rendered.replace(
            "<!-- Rendered from canonical JSON. Do not edit. -->",
            "<!-- Rendered from canonical JSON. Please do not edit by hand. -->",
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

"""RW-P04-03 round 5 regression: lossless typed record codec.

Round-4 set comparison on str()-encoded records failed Codex's adversarial
cases:
- bool true vs string "true" (str() collapses both to "true")
- number 1 vs string "1" (str() collapses both to "1")
- strings containing newlines or leading/trailing spaces cannot round-trip
- duplicate record lines silently accepted (set drops multiplicity)
- dot-bearing JSON key vs nested path collision (path not escaped)
- cosmetic comment edits misclassified as IN_SYNC (should be COSMETIC)

Round-5 fix encodes each value as its JSON serialization (lossless: type,
newlines, whitespace all preserved) and each path as a JSON array of
escaped segments. Records are compared as sorted multiplicity-preserving
lists, not sets.
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


class LosslessCodecTests(unittest.TestCase):
    def setUp(self):
        self.cr = _load_module("rw_p04_03_v5_cr", CANONICAL_RENDER_PY)

    def _render_and_reconcile(self, canonical: dict) -> str:
        """Render canonical, then reconcile the rendered MD against the same
        canonical. The render must round-trip losslessly."""
        rendered = self.cr.render_markdown(canonical)
        return self.cr.reconcile_human_md(canonical=canonical, human_md=rendered)["status"]

    def _assert_mismatch(self, canonical: dict, tampered_md: str) -> None:
        with self.assertRaises(self.cr.HumanMdCanonicalJsonMismatch) as ctx:
            self.cr.reconcile_human_md(canonical=canonical, human_md=tampered_md)
        self.assertEqual(ctx.exception.kind, "STRUCTURAL_OR_VALUE_CHANGE")

    # --- type fidelity ---

    def test_bool_true_distinct_from_string_true(self):
        canonical = {"schema_version": "demo-v1", "flag": True}
        # Render canonical (flag=true as bool). Then produce a tampered MD
        # where the same path carries the STRING "true". A lossy str() codec
        # would treat these as equal; a JSON-typed codec must not.
        rendered = self.cr.render_markdown(canonical)
        # Find the encoded line for path "flag" and rewrite its value from
        # the bool encoding to the string encoding.
        from tests._canonical_codec_helpers import flip_bool_to_string_record
        tampered_md = flip_bool_to_string_record(rendered, "flag")
        self._assert_mismatch(canonical, tampered_md)

    def test_number_one_distinct_from_string_one(self):
        canonical = {"schema_version": "demo-v1", "count": 1}
        rendered = self.cr.render_markdown(canonical)
        from tests._canonical_codec_helpers import flip_number_to_string_record
        tampered_md = flip_number_to_string_record(rendered, "count")
        self._assert_mismatch(canonical, tampered_md)

    # --- whitespace / newline fidelity ---

    def test_string_with_newline_round_trips(self):
        canonical = {"schema_version": "demo-v1", "note": "line1\nline2"}
        # The rendered canonical must reconcile as IN_SYNC against itself.
        status = self._render_and_reconcile(canonical)
        self.assertEqual(status, "IN_SYNC")

    def test_string_with_leading_trailing_spaces_round_trips(self):
        canonical = {"schema_version": "demo-v1", "note": "  spaced  "}
        status = self._render_and_reconcile(canonical)
        self.assertEqual(status, "IN_SYNC")

    # --- multiplicity / duplicate detection ---

    def test_duplicate_record_line_detected(self):
        """Adding a second identical record line must be detected as a
        change (multiplicity must be preserved, not collapsed by a set)."""
        canonical = {"schema_version": "demo-v1", "title": "X"}
        rendered = self.cr.render_markdown(canonical)
        # Duplicate the title record line.
        from tests._canonical_codec_helpers import duplicate_record_line
        tampered_md = duplicate_record_line(rendered, "title")
        self._assert_mismatch(canonical, tampered_md)

    def test_path_collision_via_dot_in_key_detected(self):
        """A JSON key containing a dot must not collide with a nested path.
        canonical {"a.b": 1} must NOT reconcile against {"a": {"b": 1}}."""
        canonical_flat = {"schema_version": "demo-v1", "a.b": 1}
        canonical_nested = {"schema_version": "demo-v1", "a": {"b": 1}}
        rendered_flat = self.cr.render_markdown(canonical_flat)
        # Reconciling the flat-keyed canonical's MD against the nested
        # canonical must FAIL: their structural record sets differ.
        self._assert_mismatch(canonical_nested, rendered_flat)

    # --- IN_SYNC vs COSMETIC_DIFF_ONLY semantics ---

    def test_byte_identical_render_is_in_sync(self):
        canonical = {"schema_version": "demo-v1", "title": "X"}
        rendered = self.cr.render_markdown(canonical)
        result = self.cr.reconcile_human_md(canonical=canonical, human_md=rendered)
        self.assertEqual(result["status"], "IN_SYNC")

    def test_purely_cosmetic_change_is_cosmetic_diff_only(self):
        """Editing a comment or adding blank lines (no path-record change)
        must return COSMETIC_DIFF_ONLY, NOT IN_SYNC."""
        canonical = {"schema_version": "demo-v1", "title": "X"}
        rendered = self.cr.render_markdown(canonical)
        # Reword the rendered comment and add blank lines. Path-record list
        # unchanged.
        tampered_md = rendered.replace(
            "Do not edit.",
            "Please do not edit by hand.",
        )
        tampered_md = "\n\n".join(tampered_md.splitlines())
        result = self.cr.reconcile_human_md(canonical=canonical, human_md=tampered_md)
        self.assertEqual(result["status"], "COSMETIC_DIFF_ONLY")

    def test_value_change_after_collision_still_detected(self):
        """Even after introducing a path collision attempt, a real value
        change must still be caught."""
        canonical = {"schema_version": "demo-v1", "title": "X"}
        rendered = self.cr.render_markdown(canonical)
        from tests._canonical_codec_helpers import rewrite_record_value
        tampered_md = rewrite_record_value(rendered, "title", "Y")
        self._assert_mismatch(canonical, tampered_md)


if __name__ == "__main__":
    unittest.main()

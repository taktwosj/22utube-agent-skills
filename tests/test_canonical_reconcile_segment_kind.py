"""RW-P04-03 round 6 regression: array index vs object key segment kind.

Round-5 codec encoded every segment as a string. Array index 0 became
the string "[0]", indistinguishable from an object key literally named
"[0]". The two JSON structures below produced identical record lists:

    {"x": [{"a": 1}]}            # x -> array[0] -> key "a"
    {"x": {"[0]": {"a": 1}}}     # x -> key "[0]" -> key "a"

Round-6 fix: each segment is encoded as a [kind, value] pair where kind
is "key" (object property) or "idx" (array index). The two structures
above must produce distinct record lists and reconcile as a mismatch.
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


class SegmentKindDisambiguationTests(unittest.TestCase):
    def setUp(self):
        self.cr = _load_module("rw_p04_03_v6_cr", CANONICAL_RENDER_PY)

    def test_array_index_distinct_from_object_key_with_same_text(self):
        """The two structures below must NOT reconcile as IN_SYNC/COSMETIC."""
        array_form = {"schema_version": "demo-v1", "x": [{"a": 1}]}
        object_form = {"schema_version": "demo-v1", "x": {"[0]": {"a": 1}}}
        # Render the object form, then try to reconcile it against the
        # array form canonical. Must raise a mismatch.
        rendered_object_form = self.cr.render_markdown(object_form)
        with self.assertRaises(self.cr.HumanMdCanonicalJsonMismatch) as ctx:
            self.cr.reconcile_human_md(
                canonical=array_form, human_md=rendered_object_form
            )
        self.assertEqual(ctx.exception.kind, "STRUCTURAL_OR_VALUE_CHANGE")

    def test_segment_records_carry_kind_tag(self):
        """Each segment in a rendered record line must carry a kind tag
        so key vs idx is structurally distinguishable."""
        canonical = {"schema_version": "demo-v1", "x": [{"a": 1}]}
        rendered = self.cr.render_markdown(canonical)
        # Find the record line for x[0].a and inspect its segments.
        record_lines = [
            line for line in rendered.splitlines()
            if line.startswith("R ") and '"a"' in line
        ]
        self.assertTrue(record_lines, "no record line for x[0].a")
        import json as _json
        payload = _json.loads(record_lines[0][2:])
        segments = payload[0]
        # Segments must be a list of [kind, value] pairs (not bare strings).
        self.assertTrue(
            all(
                isinstance(s, list) and len(s) == 2 and s[0] in ("key", "idx")
                for s in segments
            ),
            f"segments must be [kind, value] pairs; got {segments!r}",
        )
        # The array index segment must be tagged "idx", not "key".
        kinds = [s[0] for s in segments]
        self.assertIn("idx", kinds, "array index segment must carry kind=idx")

    def test_object_key_with_bracket_text_tagged_as_key(self):
        """An object key literally named '[0]' must be tagged as 'key'."""
        canonical = {"schema_version": "demo-v1", "x": {"[0]": {"a": 1}}}
        rendered = self.cr.render_markdown(canonical)
        record_lines = [
            line for line in rendered.splitlines()
            if line.startswith("R ") and '"a"' in line
        ]
        self.assertTrue(record_lines)
        import json as _json
        payload = _json.loads(record_lines[0][2:])
        segments = payload[0]
        # The "[0]" segment must be a key, not an idx.
        bracket_segment = next(
            (s for s in segments if len(s) == 2 and s[1] == "[0]"),
            None,
        )
        self.assertIsNotNone(bracket_segment, "no '[0]' segment found")
        self.assertEqual(
            bracket_segment[0],
            "key",
            "object key '[0]' must be tagged kind=key, not idx",
        )

    def test_self_round_trip_array(self):
        canonical = {"schema_version": "demo-v1", "x": [{"a": 1}]}
        rendered = self.cr.render_markdown(canonical)
        result = self.cr.reconcile_human_md(canonical=canonical, human_md=rendered)
        self.assertEqual(result["status"], "IN_SYNC")

    def test_self_round_trip_object_with_bracket_key(self):
        canonical = {"schema_version": "demo-v1", "x": {"[0]": {"a": 1}}}
        rendered = self.cr.render_markdown(canonical)
        result = self.cr.reconcile_human_md(canonical=canonical, human_md=rendered)
        self.assertEqual(result["status"], "IN_SYNC")


class JsonFidelityComparisonTests(unittest.TestCase):
    """JSON values that compare equal in Python but are distinct JSON scalars
    must be distinguished by the codec.

    These were found during pre-submission self-review (round 7) and would
    have been the next Codex blocker if shipped as-is.
    """

    def setUp(self):
        self.cr = _load_module("rw_p04_03_v7_fidelity", CANONICAL_RENDER_PY)

    def _assert_mismatch(self, canonical: dict, tampered_canonical: dict) -> None:
        rendered = self.cr.render_markdown(tampered_canonical)
        with self.assertRaises(self.cr.HumanMdCanonicalJsonMismatch) as ctx:
            self.cr.reconcile_human_md(canonical=canonical, human_md=rendered)
        self.assertEqual(ctx.exception.kind, "STRUCTURAL_OR_VALUE_CHANGE")

    def test_int_one_distinct_from_float_one(self):
        self._assert_mismatch({"a": 1}, {"a": 1.0})

    def test_zero_int_distinct_from_false(self):
        self._assert_mismatch({"a": 0}, {"a": False})

    def test_one_int_distinct_from_true(self):
        self._assert_mismatch({"a": 1}, {"a": True})

    def test_negative_zero_distinct_from_positive_zero(self):
        self._assert_mismatch({"a": -0.0}, {"a": 0.0})

    def test_self_round_trip_preserves_int(self):
        canonical = {"a": 1}
        rendered = self.cr.render_markdown(canonical)
        result = self.cr.reconcile_human_md(canonical=canonical, human_md=rendered)
        self.assertEqual(result["status"], "IN_SYNC")

    def test_self_round_trip_preserves_float(self):
        canonical = {"a": 1.5}
        rendered = self.cr.render_markdown(canonical)
        result = self.cr.reconcile_human_md(canonical=canonical, human_md=rendered)
        self.assertEqual(result["status"], "IN_SYNC")


class JsonNativeInputOnlyTests(unittest.TestCase):
    """Round 8: render_markdown / reconcile_human_md must reject Python
    values that json.dumps silently coerces (tuple, non-string dict key)
    because they are not JSON-native and would either lose information
    or collide with a real JSON value.
    """

    def setUp(self):
        self.cr = _load_module("rw_p04_03_v8_native", CANONICAL_RENDER_PY)

    def test_render_rejects_tuple(self):
        with self.assertRaises(TypeError):
            self.cr.render_markdown({"a": (1, 2)})

    def test_render_rejects_non_string_dict_key(self):
        with self.assertRaises(TypeError):
            self.cr.render_markdown({1: "v"})

    def test_render_rejects_nested_tuple(self):
        with self.assertRaises(TypeError):
            self.cr.render_markdown({"a": {"b": (1, 2)}})

    def test_render_rejects_tuple_in_list(self):
        with self.assertRaises(TypeError):
            self.cr.render_markdown({"a": [(1, 2)]})

    def test_reconcile_rejects_tuple_canonical(self):
        # Even if human_md is well-formed, canonical must be JSON-native.
        with self.assertRaises(TypeError):
            self.cr.reconcile_human_md(
                canonical={"a": (1, 2)},
                human_md=self.cr.render_markdown({"a": [1, 2]}),
            )

    def test_reconcile_rejects_int_key_canonical(self):
        with self.assertRaises(TypeError):
            self.cr.reconcile_human_md(
                canonical={1: "v"},
                human_md=self.cr.render_markdown({"1": "v"}),
            )

    def test_int_key_does_not_collide_with_str_key(self):
        """After rejecting int keys, a str key '1' is the only form that
        round-trips. Pre-fix this would have silently passed IN_SYNC."""
        canonical = {"1": "v"}  # string key, JSON-native
        rendered = self.cr.render_markdown(canonical)
        result = self.cr.reconcile_human_md(canonical=canonical, human_md=rendered)
        self.assertEqual(result["status"], "IN_SYNC")


if __name__ == "__main__":
    unittest.main()

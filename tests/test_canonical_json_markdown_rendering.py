"""P04 canonical JSON -> human MD rendering tests (RED first).

V2 design section 37: machine JSON is canonical; human MD is rendered from
it. The two are not edited independently. A human MD edit requires an
explicit import/reconcile step. Silent dual editing is forbidden and must
raise HUMAN_MD_CANONICAL_JSON_MISMATCH.

The renderer must be deterministic and must not use an LLM (section 44.2).
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


class CanonicalRenderPresenceTests(unittest.TestCase):
    def test_canonical_render_module_exists(self):
        self.assertTrue(CANONICAL_RENDER_PY.exists(), "canonical_render.py missing")


class CanonicalRenderTests(unittest.TestCase):
    def setUp(self):
        if not CANONICAL_RENDER_PY.exists():
            self.skipTest("canonical_render.py not yet implemented (RED)")
        self.cr = _load_module("p04_canonical_render", CANONICAL_RENDER_PY)

    def test_deterministic_formatter_uses_no_llm(self):
        """Rendering the same canonical JSON twice must yield byte-identical
        MD output (no timestamps, no nondeterminism)."""
        canonical = {
            "schema_version": "design-blueprint-v1",
            "episode_id": "SHT-20260720-01",
            "hook": "공을 힘껏 걷어찬다",
            "scenes": [
                {"id": "seg-001", "source_order": 1, "role": "speaker_quote"},
                {"id": "seg-002", "source_order": 2, "role": "situation_description"},
            ],
        }
        md1 = self.cr.render_markdown(canonical)
        md2 = self.cr.render_markdown(canonical)
        self.assertEqual(md1, md2)
        # Output must contain canonical fields.
        self.assertIn("SHT-20260720-01", md1)
        self.assertIn("공을 힘껏 걷어찬다", md1)

    def test_human_md_canonical_json_mismatch_blocks(self):
        """If a hand-edited MD disagrees with the canonical JSON projection,
        reconciliation must raise HUMAN_MD_CANONICAL_JSON_MISMATCH."""
        canonical = {
            "schema_version": "design-blueprint-v1",
            "episode_id": "SHT-20260720-01",
            "hook": "ORIGINAL_HOOK",
        }
        canonical_md = self.cr.render_markdown(canonical)
        # Tamper: simulate a human edit that diverges.
        tampered_md = canonical_md.replace("ORIGINAL_HOOK", "EDITED_HOOK")
        with self.assertRaises(self.cr.HumanMdCanonicalJsonMismatch) as ctx:
            self.cr.reconcile_human_md(canonical=canonical, human_md=tampered_md)
        self.assertIn("HUMAN_MD_CANONICAL_JSON_MISMATCH", str(ctx.exception))

    def test_render_markdown_rejects_non_serializable_input(self):
        with self.assertRaises(Exception):
            self.cr.render_markdown({"oops": object()})


if __name__ == "__main__":
    unittest.main()

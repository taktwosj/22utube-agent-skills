"""RW-P05-01 regression: generated core must compile and import cleanly.

Prior bug: sync_shared_workflow_harness.py kept per-module
`from __future__ import annotations` lines, so the bundled file had future
imports mid-file (illegal). The bundle emitted PASS for byte-identity but
could not be imported as Python.

These tests verify:
- generated core compiles (py_compile)
- generated core imports
- each P05/P06 lane adapter that depends on _import_core() can load
"""

from __future__ import annotations

import importlib.util
import py_compile
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

GENERATED_CORES = [
    ROOT / "skills" / "00-tikitaka" / "scripts" / "_generated" / "workflow_harness_core.py",
    ROOT / "skills" / "000short-production-agent" / "scripts" / "_generated" / "workflow_harness_core.py",
    ROOT / "skills" / "111-politics-longform" / "scripts" / "_generated" / "workflow_harness_core.py",
]

LANE_ADAPTERS_USING_CORE = [
    ROOT / "skills" / "00-tikitaka" / "scripts" / "validate_stage_gate.py",
    ROOT / "skills" / "00-tikitaka" / "scripts" / "workflow_runner.py",
    ROOT / "skills" / "00-tikitaka" / "scripts" / "render_design_blueprint.py",
    ROOT / "skills" / "00-tikitaka" / "scripts" / "validate_analysis_cache.py",
    ROOT / "skills" / "00-tikitaka" / "scripts" / "build_external_prompt.py",
    ROOT / "skills" / "000short-production-agent" / "scripts" / "validate_stage_gate.py",
    ROOT / "skills" / "000short-production-agent" / "scripts" / "workflow_runner.py",
    ROOT / "skills" / "111-politics-longform" / "scripts" / "build_external_prompt.py",
]


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


class GeneratedCoreCompilesTests(unittest.TestCase):
    def test_every_generated_core_compiles(self):
        for core in GENERATED_CORES:
            with self.subTest(core=core.name):
                py_compile.compile(str(core), doraise=True)

    def test_every_generated_core_imports(self):
        for i, core in enumerate(GENERATED_CORES):
            with self.subTest(core=core.name):
                mod = _load_module(f"gen_core_{i}_{core.stem}", core)
                # Sanity: the generated core must expose the validate_gate
                # function from the canonical gate_validation module.
                self.assertTrue(hasattr(mod, "validate_gate"))

    def test_no_mid_file_future_import_in_generated_core(self):
        for core in GENERATED_CORES:
            with self.subTest(core=core.name):
                text = core.read_text(encoding="utf-8")
                lines = text.splitlines()
                # Find the first non-empty, non-comment, non-docstring line.
                future_lines = [
                    i for i, line in enumerate(lines)
                    if line.strip().startswith("from __future__ import")
                ]
                self.assertLessEqual(
                    len(future_lines),
                    1,
                    f"{core.name} must have at most one future import (the bundle header)",
                )
                if future_lines:
                    # The single future import must be near the top (before
                    # any canonical module body).
                    first_module_marker = next(
                        (i for i, line in enumerate(lines)
                         if line.startswith("# === BEGIN CANONICAL MODULE")),
                        len(lines),
                    )
                    self.assertLess(
                        future_lines[0],
                        first_module_marker,
                        f"{core.name}: future import must precede the first canonical module body",
                    )


class LaneAdapterImportTests(unittest.TestCase):
    """RW-P05-01 requires that every lane adapter that calls _import_core()
    can actually be imported as a Python module."""

    def test_every_lane_adapter_imports(self):
        for adapter in LANE_ADAPTERS_USING_CORE:
            with self.subTest(adapter=adapter.name):
                # Just importing the module triggers _import_core() paths
                # only when functions are called, but we still want to be
                # sure the module-level code (including REPO_ROOT resolution
                # and any decorators) executes.
                mod = _load_module(f"adapter_{adapter.stem}_{id(adapter)}", adapter)
                self.assertTrue(hasattr(mod, "REPO_ROOT"))


if __name__ == "__main__":
    unittest.main()

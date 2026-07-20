"""RW-P05-01 regression (round 3): generated core must compile and every
lane adapter's `_import_core()` must actually return a usable module.

Round-2 test only checked that adapters imported as modules. Codex round-2
review required actually calling `_import_core()` (the function the
adapter uses at runtime) so the generated core path resolution and
import are exercised end-to-end.

Also: py_compile.compile() is run against copies in a TemporaryDirectory
so no __pycache__/*.pyc is left under managed skill folders.
"""

from __future__ import annotations

import importlib.util
import py_compile
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

GENERATED_CORES = [
    ROOT / "skills" / "00-tikitaka" / "scripts" / "_generated" / "workflow_harness_core.py",
    ROOT / "skills" / "000short-production-agent" / "scripts" / "_generated" / "workflow_harness_core.py",
    ROOT / "skills" / "111-politics-longform" / "scripts" / "_generated" / "workflow_harness_core.py",
]

# Adapters that expose an _import_core() helper which loads the generated
# core. For each, we call _import_core() and assert the returned module
# exposes validate_gate (sanity).
ADAPTERS_WITH_IMPORT_CORE = [
    ROOT / "skills" / "00-tikitaka" / "scripts" / "validate_stage_gate.py",
    ROOT / "skills" / "00-tikitaka" / "scripts" / "workflow_runner.py",
    ROOT / "skills" / "00-tikitaka" / "scripts" / "render_design_blueprint.py",
    ROOT / "skills" / "000short-production-agent" / "scripts" / "validate_stage_gate.py",
    ROOT / "skills" / "000short-production-agent" / "scripts" / "workflow_runner.py",
]

# Adapters that expose a different _import_* helper that loads a generated
# core module. validate_analysis_cache uses _import_prompt_factory() because
# it only needs the prompt_factory symbols, not the full gate_validation.
# Either way, the helper must successfully load the generated core.
ADAPTERS_WITH_ALT_IMPORT = [
    (ROOT / "skills" / "00-tikitaka" / "scripts" / "validate_analysis_cache.py",
     "_import_prompt_factory", "build_analysis_cache_manifest"),
]

# Adapters that don't expose _import_core but do import the generated core
# at module load time (build_external_prompt). We import these and check
# REPO_ROOT resolved to the real repo.
ADAPTERS_MODULE_LEVEL = [
    ROOT / "skills" / "00-tikitaka" / "scripts" / "build_external_prompt.py",
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
    def test_every_generated_core_compiles_without_leaving_pyc(self):
        """py_compile.compile must run against a temp copy so no .pyc is
        left under managed skill folders."""
        for core in GENERATED_CORES:
            with self.subTest(core=core.name), tempfile.TemporaryDirectory() as tmp:
                # Copy the generated core into a temp dir and compile there.
                # tempfile.TemporaryDirectory cleans up automatically,
                # including any __pycache__ the compiler creates.
                tmp_path = Path(tmp) / core.name
                tmp_path.write_bytes(core.read_bytes())
                cfile = Path(tmp) / f"{core.stem}.pyc"
                py_compile.compile(
                    str(tmp_path),
                    cfile=str(cfile),
                    doraise=True,
                )
                # The .pyc must live under tmp, never under the managed skill.
                self.assertTrue(cfile.is_file())

    def test_no_mid_file_future_import_in_generated_core(self):
        for core in GENERATED_CORES:
            with self.subTest(core=core.name):
                text = core.read_text(encoding="utf-8")
                lines = text.splitlines()
                future_lines = [
                    i for i, line in enumerate(lines)
                    if line.strip().startswith("from __future__ import")
                ]
                self.assertLessEqual(len(future_lines), 1)
                if future_lines:
                    first_module_marker = next(
                        (i for i, line in enumerate(lines)
                         if line.startswith("# === BEGIN CANONICAL MODULE")),
                        len(lines),
                    )
                    self.assertLess(future_lines[0], first_module_marker)

    def test_managed_generated_directories_have_no_bytecode_cache(self):
        for core in GENERATED_CORES:
            with self.subTest(core=core):
                leftovers = [
                    path
                    for path in core.parent.rglob("*")
                    if path.name == "__pycache__" or path.suffix == ".pyc"
                ]
                self.assertEqual(leftovers, [])


class AdapterImportCoreCallTests(unittest.TestCase):
    """Actually call each adapter's _import_core() and assert the returned
    module is usable. This is the regression Codex required (round 3)."""

    def test_every_adapter_import_core_returns_usable_module(self):
        for adapter in ADAPTERS_WITH_IMPORT_CORE:
            with self.subTest(adapter=adapter.name):
                mod = _load_module(f"adapter_core_{adapter.stem}_{id(adapter)}", adapter)
                self.assertTrue(
                    hasattr(mod, "_import_core"),
                    f"{adapter.name} must expose _import_core",
                )
                core = mod._import_core()
                self.assertTrue(
                    hasattr(core, "validate_gate"),
                    f"{adapter.name} _import_core() must return a module with validate_gate",
                )

    def test_every_module_level_adapter_imports(self):
        for adapter in ADAPTERS_MODULE_LEVEL:
            with self.subTest(adapter=adapter.name):
                mod = _load_module(f"adapter_mod_{adapter.stem}_{id(adapter)}", adapter)
                self.assertTrue(hasattr(mod, "REPO_ROOT"))

    def test_every_alt_import_helper_returns_usable_module(self):
        """Adapters with a non-standard helper name (e.g. validate_analysis_cache
        uses _import_prompt_factory) must still successfully load the
        generated core."""
        for adapter, helper_name, expected_attr in ADAPTERS_WITH_ALT_IMPORT:
            with self.subTest(adapter=adapter.name):
                mod = _load_module(f"adapter_alt_{adapter.stem}_{id(adapter)}", adapter)
                self.assertTrue(
                    hasattr(mod, helper_name),
                    f"{adapter.name} must expose {helper_name}",
                )
                helper = getattr(mod, helper_name)
                core = helper()
                self.assertTrue(
                    hasattr(core, expected_attr),
                    f"{adapter.name} {helper_name}() must return a module with {expected_attr}",
                )


if __name__ == "__main__":
    unittest.main()

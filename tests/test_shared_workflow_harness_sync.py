"""P03 sync_shared_workflow_harness tests.

Asserts that the sync script deterministically regenerates byte-identical
copies of workflow_harness_core.py into each of the three skills, that
the generated file carries a source version + SHA header, and that the
verify script confirms hash equality.
"""

from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SYNC_PY = ROOT / "scripts" / "sync_shared_workflow_harness.py"
VERIFY_PY = ROOT / "scripts" / "verify_shared_workflow_harness.py"

GENERATED_TARGETS = [
    ROOT / "skills" / "00-tikitaka" / "scripts" / "_generated" / "workflow_harness_core.py",
    ROOT / "skills" / "000short-production-agent" / "scripts" / "_generated" / "workflow_harness_core.py",
    ROOT / "skills" / "111-politics-longform" / "scripts" / "_generated" / "workflow_harness_core.py",
]
GENERATED_VERSION_TARGETS = [
    ROOT / "skills" / "00-tikitaka" / "scripts" / "_generated" / "WORKFLOW_HARNESS_VERSION",
    ROOT / "skills" / "000short-production-agent" / "scripts" / "_generated" / "WORKFLOW_HARNESS_VERSION",
    ROOT / "skills" / "111-politics-longform" / "scripts" / "_generated" / "WORKFLOW_HARNESS_VERSION",
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


class SyncScriptPresenceTests(unittest.TestCase):
    def test_sync_script_exists(self):
        self.assertTrue(SYNC_PY.exists(), "sync_shared_workflow_harness.py missing")

    def test_verify_script_exists(self):
        self.assertTrue(VERIFY_PY.exists(), "verify_shared_workflow_harness.py missing")


class GeneratedCoreByteIdenticalTests(unittest.TestCase):
    def setUp(self):
        if not SYNC_PY.exists():
            self.skipTest("sync script not yet implemented (RED)")

    def test_generated_common_core_hashes_match(self):
        """After sync, all three skills' workflow_harness_core.py must be
        byte-identical (NORM-008)."""
        sync = _load_module("p03_sync", SYNC_PY)
        sync.sync_all()
        contents = [p.read_bytes() for p in GENERATED_TARGETS]
        # All three must exist.
        self.assertTrue(all(c for c in contents))
        # All three must be identical.
        self.assertEqual(len({c for c in contents}), 1)

    def test_generated_files_have_source_version_and_sha_header(self):
        sync = _load_module("p03_sync_header", SYNC_PY)
        sync.sync_all()
        for path in GENERATED_TARGETS:
            text = path.read_text(encoding="utf-8")
            self.assertIn("WORKFLOW_HARNESS_SOURCE_VERSION", text)
            self.assertIn("WORKFLOW_HARNESS_SOURCE_SHA256", text)
            self.assertIn("DO NOT EDIT", text)

    def test_generated_version_files_match_canonical(self):
        sync = _load_module("p03_sync_version", SYNC_PY)
        sync.sync_all()
        versions = [p.read_text(encoding="utf-8").strip() for p in GENERATED_VERSION_TARGETS]
        canonical = (ROOT / "shared" / "workflow-harness" / "VERSION").read_text(encoding="utf-8").strip()
        self.assertTrue(all(v == canonical for v in versions))


class VerifyScriptTests(unittest.TestCase):
    def setUp(self):
        if not VERIFY_PY.exists():
            self.skipTest("verify script not yet implemented (RED)")

    def test_verify_returns_pass_after_sync(self):
        sync = _load_module("p03_verify_sync", SYNC_PY)
        sync.sync_all()
        verify = _load_module("p03_verify", VERIFY_PY)
        result = verify.verify_all()
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["generated_core_hashes_match"], True)


if __name__ == "__main__":
    unittest.main()

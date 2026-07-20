"""RW-P04-01 regression tests: lane adapter REPO_ROOT resolution.

Prior bug: adapters used parents[4] which points outside the repository
to the worktree parent directory. The fix is parents[3] (scripts/<skill>/
skills/<repo>).

These tests execute the adapter modules directly (no argparse) and verify
that REPO_ROOT resolves to the actual repository root, identified by the
manifests/skill-set.json marker with repo_name=22utube-agent-skills.
"""

from __future__ import annotations

import importlib.util
import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MARKER = ROOT / "manifests" / "skill-set.json"

ADAPTERS = [
    ROOT / "skills" / "00-tikitaka" / "scripts" / "build_external_prompt.py",
    ROOT / "skills" / "00-tikitaka" / "scripts" / "render_design_blueprint.py",
    ROOT / "skills" / "00-tikitaka" / "scripts" / "validate_analysis_cache.py",
    ROOT / "skills" / "00-tikitaka" / "scripts" / "validate_stage_gate.py",
    ROOT / "skills" / "00-tikitaka" / "scripts" / "workflow_runner.py",
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


class AdapterRepoRootTests(unittest.TestCase):
    def setUp(self):
        self.assertTrue(MARKER.exists(), "repo marker missing")
        self.marker_data = json.loads(MARKER.read_text(encoding="utf-8"))
        self.assertEqual(
            self.marker_data["repo_name"], "22utube-agent-skills"
        )

    def test_no_adapter_uses_parents_4(self):
        """parents[4] points outside the repo and must not appear in any
        adapter's REPO_ROOT resolution."""
        for adapter in ADAPTERS:
            text = adapter.read_text(encoding="utf-8")
            self.assertNotIn(
                "parents[4]",
                text,
                f"{adapter} still uses parents[4] (RW-P04-01)",
            )

    def test_every_adapter_resolves_repo_root_inside_repository(self):
        for adapter in ADAPTERS:
            mod = _load_module(f"adapter_{adapter.stem}_{id(adapter)}", adapter)
            repo_root = Path(mod.REPO_ROOT)
            self.assertTrue(
                (repo_root / "manifests" / "skill-set.json").exists(),
                f"{adapter.name}: REPO_ROOT={repo_root} is outside the repository",
            )
            self.assertEqual(
                repo_root.resolve(),
                ROOT.resolve(),
                f"{adapter.name}: REPO_ROOT={repo_root} != {ROOT}",
            )


if __name__ == "__main__":
    unittest.main()

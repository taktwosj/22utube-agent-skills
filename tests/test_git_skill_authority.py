from __future__ import annotations

import importlib.util
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock


REPO_ROOT = Path(__file__).resolve().parents[1]
SKIL_DOWN = REPO_ROOT / "skills" / "skil-down" / "scripts" / "skil_down.py"
FORBIDDEN_TOKENS = ("codex_skills_source", "skills_sync", "codex_skills")


def load_skil_down():
    spec = importlib.util.spec_from_file_location("skil_down", SKIL_DOWN)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def is_allowed_reference(relative_path: str, line: str) -> bool:
    if relative_path.startswith("skills/00-tikitaka/reports/"):
        return True
    if relative_path.startswith("docs/superpowers/"):
        return True
    if relative_path in {"scripts/verify.sh", "scripts/verify.ps1"}:
        return True
    if relative_path == "skills/skil-down/scripts/skil_down.py":
        return "FORBIDDEN_SOURCE_PARTS" in line
    if relative_path == "skills/skil-down/SKILL.md":
        return "FORBIDDEN:" in line or "Forbidden legacy source/mirror folders" in line
    return False


class GitSkillAuthorityTests(unittest.TestCase):
    def test_default_candidates_do_not_use_onedrive_mirrors(self):
        module = load_skil_down()
        with tempfile.TemporaryDirectory() as tmp:
            env = {
                "OneDrive": str(Path(tmp) / "OneDrive"),
                "OneDriveCommercial": str(Path(tmp) / "OneDriveCommercial"),
                "USERPROFILE": str(Path(tmp) / "user"),
            }
            with mock.patch.dict(os.environ, env, clear=False):
                candidates = module.candidate_source_paths()
        bad = [
            str(path)
            for path in candidates
            if any(part in module.FORBIDDEN_SOURCE_PARTS for part in path.parts)
        ]
        self.assertEqual(bad, [])

    def test_explicit_legacy_source_is_rejected(self):
        module = load_skil_down()
        with tempfile.TemporaryDirectory() as tmp:
            legacy = Path(tmp) / "OneDrive" / "22utube" / "11utube" / "codex_skills_source"
            (legacy / "demo").mkdir(parents=True)
            (legacy / "demo" / "SKILL.md").write_text(
                "---\nname: demo\ndescription: Use when testing\n---\n# Demo\n",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(SystemExit, "forbidden"):
                module.materialize_source(str(legacy), Path(tmp) / "materialized")

    def test_active_workflow_text_has_no_legacy_mirror_paths(self):
        scan_roots = ["scripts", "skills", "docs"]
        violations: list[str] = []
        files: list[Path] = []
        for root_name in scan_roots:
            files.extend(path for path in (REPO_ROOT / root_name).rglob("*") if path.is_file())
        files.append(REPO_ROOT / "README.md")
        for path in files:
            if not path.is_file() or "__pycache__" in path.parts:
                continue
            try:
                lines = path.read_text(encoding="utf-8").splitlines()
            except UnicodeDecodeError:
                continue
            relative = path.relative_to(REPO_ROOT).as_posix()
            for index, line in enumerate(lines, start=1):
                if not any(token in line for token in FORBIDDEN_TOKENS):
                    continue
                if is_allowed_reference(relative, line):
                    continue
                violations.append(f"{relative}:{index}")
        self.assertEqual(violations, [])


if __name__ == "__main__":
    unittest.main()

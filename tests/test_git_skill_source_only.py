from __future__ import annotations

import unittest
from pathlib import Path

from _support import load_source_module_no_bytecode


ROOT = Path(__file__).resolve().parents[1]
SKIL_DOWN = ROOT / "skills" / "skil-down"
SKIL_DOWN_SCRIPT = SKIL_DOWN / "scripts" / "skil_down.py"


class GitSkillSourceOnlyTests(unittest.TestCase):
    def test_skil_down_no_longer_discovers_onedrive_skill_sources(self):
        module = load_source_module_no_bytecode("skil_down_git_source_only", SKIL_DOWN_SCRIPT)

        candidates = [str(path).replace("\\", "/") for path in module.candidate_source_paths()]

        self.assertTrue(
            any(path.endswith("/agent-skills/skills") for path in candidates),
            "skil-down must still discover the Git skill source",
        )
        retired_source = "codex_" + "skills_source"
        retired_sync = "skills_" + "sync"
        self.assertFalse(
            any(retired_source in path or retired_sync in path for path in candidates),
            "skil-down must not auto-discover retired shared-source paths",
        )

    def test_active_docs_do_not_name_onedrive_as_skill_source_or_cache(self):
        checked_files = [
            ROOT / "docs" / "migration-from-onedrive.md",
            ROOT / "docs" / "verification-status.md",
            SKIL_DOWN / "SKILL.md",
            SKIL_DOWN_SCRIPT,
        ]
        forbidden = [
            "codex_" + "skills_source",
            "skills_" + "sync",
            "Legacy " + "OneDrive cache",
            "OneDrive " + "paths",
            "OneDrive " + "skill",
        ]

        for path in checked_files:
            text = path.read_text(encoding="utf-8")
            for token in forbidden:
                with self.subTest(path=path.relative_to(ROOT), token=token):
                    self.assertNotIn(token, text)


if __name__ == "__main__":
    unittest.main()

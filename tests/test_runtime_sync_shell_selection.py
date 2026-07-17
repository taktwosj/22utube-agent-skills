from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class RuntimeSyncShellSelectionTests(unittest.TestCase):
    def test_bash_auto_sync_prefers_pwsh_before_windows_powershell(self):
        text = (ROOT / "scripts" / "auto_sync_runtime_skills.sh").read_text(encoding="utf-8")

        self.assertIn("pwsh.exe", text)
        self.assertLess(
            text.index("pwsh.exe"),
            text.index("powershell.exe"),
            "bash hook auto-sync should prefer pwsh.exe before legacy powershell.exe",
        )

    def test_bash_auto_sync_places_lock_in_git_common_directory(self):
        text = (ROOT / "scripts" / "auto_sync_runtime_skills.sh").read_text(encoding="utf-8")

        self.assertIn("git rev-parse --git-common-dir", text)
        self.assertIn(
            'LOCK_FILE="$GIT_COMMON_DIR/22utube-skill-auto-sync.lock"',
            text,
        )
        self.assertNotIn(
            'LOCK_FILE="$REPO_ROOT/.git/22utube-skill-auto-sync.lock"',
            text,
        )

    def test_update_ps1_uses_selected_powershell_executable(self):
        text = (ROOT / "scripts" / "update.ps1").read_text(encoding="utf-8")

        self.assertIn("$powerShellExe", text)
        self.assertNotIn("\npowershell @installArgs", text)
        self.assertNotIn("\npowershell @verifyArgs", text)


if __name__ == "__main__":
    unittest.main()

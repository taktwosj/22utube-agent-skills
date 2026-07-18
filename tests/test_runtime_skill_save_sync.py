import json
import os
from pathlib import Path
import subprocess
import unittest


ROOT = Path(__file__).resolve().parents[1]
SYNC_SCRIPT = ROOT / "scripts" / "sync_changed_runtime_skills.ps1"
WATCH_SCRIPT = ROOT / "scripts" / "watch_runtime_skills.ps1"
INSTALL_WATCHER_SCRIPT = ROOT / "scripts" / "install_runtime_skill_watcher.ps1"


def run_powershell(script: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            "powershell",
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(script),
            *args,
        ],
        cwd=ROOT,
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        check=False,
        env={**os.environ, "PYTHONUTF8": "1"},
    )


def result_payload(stdout: str) -> dict:
    prefix = "SYNC_RESULT_JSON="
    lines = [line for line in stdout.splitlines() if line.startswith(prefix)]
    if not lines:
        raise AssertionError(f"missing {prefix!r} in output:\n{stdout}")
    return json.loads(lines[-1][len(prefix) :])


class RuntimeSkillSaveSyncTests(unittest.TestCase):
    def test_changed_skill_path_selects_only_that_skill_even_when_repo_is_dirty(self):
        changed = ROOT / "skills" / "00-tikitaka" / "SKILL.md"
        result = run_powershell(
            SYNC_SCRIPT,
            "-ChangedPath",
            str(changed),
            "-DryRun",
        )

        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        payload = result_payload(result.stdout)
        self.assertEqual(payload["status"], "DRYRUN")
        self.assertEqual(payload["skills"], ["00-tikitaka"])
        self.assertEqual(payload["targets"], ["codex", "claude", "hermes"])
        self.assertNotIn("dirty worktree", result.stdout.lower())

    def test_path_outside_skills_is_ignored(self):
        changed = ROOT / "README.md"
        result = run_powershell(
            SYNC_SCRIPT,
            "-ChangedPath",
            str(changed),
            "-DryRun",
        )

        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        payload = result_payload(result.stdout)
        self.assertEqual(payload["status"], "NO_MANAGED_SKILL_CHANGE")
        self.assertEqual(payload["skills"], [])

    def test_watcher_is_recursive_debounced_and_calls_focused_sync(self):
        text = WATCH_SCRIPT.read_text(encoding="utf-8")

        self.assertIn("System.IO.FileSystemWatcher", text)
        self.assertRegex(text, r"IncludeSubdirectories\s*=\s*\$true")
        self.assertIn("DebounceMilliseconds", text)
        self.assertIn("sync_changed_runtime_skills.ps1", text)
        self.assertNotIn("git commit", text.lower())
        self.assertNotIn("git push", text.lower())

    def test_installer_registers_hidden_logon_task_and_starts_it(self):
        text = INSTALL_WATCHER_SCRIPT.read_text(encoding="utf-8")

        self.assertIn("22utube Skill Runtime Save Sync", text)
        self.assertIn("New-ScheduledTaskTrigger -AtLogOn", text)
        self.assertIn("-WindowStyle Hidden", text)
        self.assertIn("Register-ScheduledTask", text)
        self.assertIn("Start-ScheduledTask", text)


if __name__ == "__main__":
    unittest.main()

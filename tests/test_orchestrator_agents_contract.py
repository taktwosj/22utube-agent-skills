from __future__ import annotations

import json
import os
import shutil
import unittest
import subprocess
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FACTORY_ROOT = ROOT.parent.parent if ROOT.parent.name == "worktrees" else ROOT.parent
POWERSHELL = shutil.which("pwsh") or shutil.which("powershell")


def write_managed_skill(factory: Path, skill_name: str = "demo-skill") -> Path:
    repo = factory / "agent-skills"
    source = repo / "skills" / skill_name
    source.mkdir(parents=True)
    (source / "SKILL.md").write_text("managed-source", encoding="utf-8")
    manifests = repo / "manifests"
    manifests.mkdir(parents=True, exist_ok=True)
    (manifests / "skill-set.json").write_text(
        json.dumps(
            {
                "skills": [
                    {
                        "name": skill_name,
                        "enabled": True,
                        "targets": ["codex", "claude", "hermes"],
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    return source


class OrchestratorAgentsContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if POWERSHELL is None:
            raise unittest.SkipTest("PowerShell is not installed")
        cls.old_test_override = os.environ.get("AGENT_SKILLS_TEST_RUNTIME_OVERRIDE")
        os.environ["AGENT_SKILLS_TEST_RUNTIME_OVERRIDE"] = "1"

    @classmethod
    def tearDownClass(cls):
        if cls.old_test_override is None:
            os.environ.pop("AGENT_SKILLS_TEST_RUNTIME_OVERRIDE", None)
        else:
            os.environ["AGENT_SKILLS_TEST_RUNTIME_OVERRIDE"] = cls.old_test_override

    def test_test_harness_discovers_cross_platform_powershell(self):
        text = Path(__file__).read_text(encoding="utf-8")

        self.assertIn('shutil.which("pwsh") or shutil.which("powershell")', text)
        self.assertNotIn('"power' + 'shell.exe"', text)

    def test_repo_agents_keeps_compact_orchestrator_and_verified_release_contract(self):
        agents_path = ROOT / "AGENTS.md"
        self.assertTrue(agents_path.is_file(), "repo-root AGENTS.md must exist")

        text = agents_path.read_text(encoding="utf-8")
        lines = text.splitlines()
        self.assertLessEqual(len(lines), 200, "repo-root AGENTS.md must stay compact")

        for section in range(1, 13):
            self.assertIn(f"## {section}.", text)

        self.assertIn("동일 Scope에는 작업자 한 명만 배정한다.", text)
        self.assertIn("`$1caveman + $task-owner`", text)
        self.assertIn("commit·push", text)
        self.assertIn(r"<factory-root>\agent-skills-runtime\releases", text)
        self.assertIn("Codex", text)
        self.assertIn("Claude", text)
        self.assertIn("Hermes", text)
        self.assertIn("backup", text.lower())
        self.assertIn("manifest", text.lower())
        self.assertIn("READY", text)
        self.assertIn("verified cache", text)
        self.assertIn("system/plugin", text)

    def test_link_helper_dry_run_reports_paths_without_replacing_target(self):
        script = ROOT / "scripts" / "link-managed-skill.ps1"
        with tempfile.TemporaryDirectory() as temp_dir:
            temp = Path(temp_dir)
            factory = temp / "factory"
            source = write_managed_skill(factory)

            runtime = temp / "runtime-skills"
            destination = runtime / "demo-skill"
            destination.mkdir(parents=True)
            marker = destination / "keep.txt"
            marker.write_text("unchanged", encoding="utf-8")

            completed = subprocess.run(
                [
                    POWERSHELL,
                    "-NoProfile",
                    "-ExecutionPolicy",
                    "Bypass",
                    "-File",
                    str(script),
                    "-DevOnly",
                    "-FactoryRoot",
                    str(factory),
                    "-SkillName",
                    "demo-skill",
                    "-Target",
                    "codex",
                    "-RuntimeRoot",
                    str(runtime),
                    "-AllowTestRuntimeRoot",
                    "-DryRun",
                ],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
            )

            self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
            self.assertIn(f"DRYRUN SOURCE {source.resolve()}", completed.stdout)
            self.assertIn(f"DRYRUN DESTINATION {destination.resolve()}", completed.stdout)
            self.assertIn("DRYRUN BACKUP ", completed.stdout)
            self.assertEqual(marker.read_text(encoding="utf-8"), "unchanged")

    def test_link_helper_backs_up_then_links_and_verifies_readback(self):
        script = ROOT / "scripts" / "link-managed-skill.ps1"
        with tempfile.TemporaryDirectory() as temp_dir:
            temp = Path(temp_dir)
            factory = temp / "factory"
            source = write_managed_skill(factory)
            self_check = source / "checks" / "verify.ps1"
            self_check.parent.mkdir()
            self_check.write_text('Write-Output "fixture-self-check"\n', encoding="utf-8")

            runtime = temp / "runtime-skills"
            destination = runtime / "demo-skill"
            destination.mkdir(parents=True)
            (destination / "keep.txt").write_text("legacy", encoding="utf-8")
            backup_root = temp / "backups"

            completed = subprocess.run(
                [
                    POWERSHELL,
                    "-NoProfile",
                    "-ExecutionPolicy",
                    "Bypass",
                    "-File",
                    str(script),
                    "-DevOnly",
                    "-FactoryRoot",
                    str(factory),
                    "-SkillName",
                    "demo-skill",
                    "-Target",
                    "codex",
                    "-RuntimeRoot",
                    str(runtime),
                    "-AllowTestRuntimeRoot",
                    "-BackupRoot",
                    str(backup_root),
                    "-SelfCheckRelativePath",
                    "checks/verify.ps1",
                ],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
            )

            self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
            backup_lines = [line for line in completed.stdout.splitlines() if line.startswith("BACKUP ")]
            self.assertEqual(len(backup_lines), 1, completed.stdout)
            self.assertLess(completed.stdout.index("BACKUP "), completed.stdout.index("LINKED "))
            self.assertLess(completed.stdout.index("LINKED "), completed.stdout.index("READBACK "))
            self.assertIn("HASH PASS algorithm=SHA256", completed.stdout)
            self.assertIn("fixture-self-check", completed.stdout)
            self.assertIn("SELF_CHECK PASS checks/verify.ps1", completed.stdout)
            self.assertIn("VERIFY PASS", completed.stdout)

            backups = list(backup_root.glob("demo-skill_*"))
            self.assertEqual(len(backups), 1)
            self.assertEqual((backups[0] / "keep.txt").read_text(encoding="utf-8"), "legacy")
            self.assertEqual(destination.resolve(), source.resolve())
            self.assertEqual((destination / "SKILL.md").read_text(encoding="utf-8"), "managed-source")

    def test_factory_router_points_to_managed_skills_and_001_onedrive_root(self):
        text = (FACTORY_ROOT / "AGENTS.md").read_text(encoding="utf-8")

        self.assertIn(r"<factory-root>\agent-skills\skills", text)
        self.assertIn(r"<factory-root>\0000shrt", text)
        self.assertNotIn("OneDrive is for lightweight archive and handoff data.", text)

    def test_link_helper_refuses_repo_skill_not_owned_by_manifest(self):
        script = ROOT / "scripts" / "link-managed-skill.ps1"
        with tempfile.TemporaryDirectory() as temp_dir:
            temp = Path(temp_dir)
            factory = temp / "factory"
            write_managed_skill(factory, "owned-skill")
            unowned = factory / "agent-skills" / "skills" / "unowned-skill"
            unowned.mkdir(parents=True)
            (unowned / "SKILL.md").write_text("unowned", encoding="utf-8")

            completed = subprocess.run(
                [
                    POWERSHELL,
                    "-NoProfile",
                    "-ExecutionPolicy",
                    "Bypass",
                    "-File",
                    str(script),
                    "-DevOnly",
                    "-FactoryRoot",
                    str(factory),
                    "-SkillName",
                    "unowned-skill",
                    "-Target",
                    "codex",
                    "-RuntimeRoot",
                    str(temp / "runtime-skills"),
                    "-AllowTestRuntimeRoot",
                    "-DryRun",
                ],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
            )

            self.assertNotEqual(completed.returncode, 0)
            self.assertIn("not enabled for target codex", completed.stdout + completed.stderr)

    def test_link_helper_refuses_runtime_owned_system_name_and_plugin_path(self):
        script = ROOT / "scripts" / "link-managed-skill.ps1"
        with tempfile.TemporaryDirectory() as temp_dir:
            temp = Path(temp_dir)
            factory = temp / "factory"
            write_managed_skill(factory, "skill-creator")

            protected_name = subprocess.run(
                [
                    POWERSHELL,
                    "-NoProfile",
                    "-ExecutionPolicy",
                    "Bypass",
                    "-File",
                    str(script),
                    "-DevOnly",
                    "-FactoryRoot",
                    str(factory),
                    "-SkillName",
                    "skill-creator",
                    "-Target",
                    "codex",
                    "-RuntimeRoot",
                    str(temp / "runtime-skills"),
                    "-AllowTestRuntimeRoot",
                    "-DryRun",
                ],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
            )
            self.assertNotEqual(protected_name.returncode, 0)
            self.assertIn("runtime-owned system/plugin skill name", protected_name.stdout + protected_name.stderr)

            write_managed_skill(factory, "demo-skill")
            protected_path = subprocess.run(
                [
                    POWERSHELL,
                    "-NoProfile",
                    "-ExecutionPolicy",
                    "Bypass",
                    "-File",
                    str(script),
                    "-DevOnly",
                    "-FactoryRoot",
                    str(factory),
                    "-SkillName",
                    "demo-skill",
                    "-Target",
                    "codex",
                    "-RuntimeRoot",
                    str(temp / "runtime-skills" / "plugins" / "cache"),
                    "-AllowTestRuntimeRoot",
                    "-DryRun",
                ],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
            )
            self.assertNotEqual(protected_path.returncode, 0)
            self.assertIn("runtime-owned system/plugin path", protected_path.stdout + protected_path.stderr)

    def test_readme_documents_verified_release_cli(self):
        text = (ROOT / "README.md").read_text(encoding="utf-8")

        self.assertIn("scripts/skill_release.py publish", text)
        self.assertIn("scripts/skill_release.py activate", text)
        self.assertIn("scripts/skill_release.py verify", text)
        self.assertIn("local verified cache", text)
        self.assertIn("development-only", text)

    def test_link_helper_is_blocked_for_production_without_dev_switch(self):
        script = ROOT / "scripts" / "link-managed-skill.ps1"
        with tempfile.TemporaryDirectory() as temp_dir:
            temp = Path(temp_dir)
            factory = temp / "factory"
            write_managed_skill(factory)
            environment = dict(os.environ)
            environment.pop("AGENT_SKILLS_TEST_RUNTIME_OVERRIDE", None)

            completed = subprocess.run(
                [
                    POWERSHELL,
                    "-NoProfile",
                    "-ExecutionPolicy",
                    "Bypass",
                    "-File",
                    str(script),
                    "-FactoryRoot",
                    str(factory),
                    "-SkillName",
                    "demo-skill",
                    "-Target",
                    "codex",
                    "-DryRun",
                ],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                env=environment,
            )

            self.assertNotEqual(completed.returncode, 0)
            self.assertIn("Production direct repo links are disabled", completed.stdout + completed.stderr)

    def test_runtime_root_override_requires_switch_and_test_environment(self):
        if POWERSHELL is None:
            self.skipTest("PowerShell is not installed")
        script = ROOT / "scripts" / "link-managed-skill.ps1"
        with tempfile.TemporaryDirectory() as temp_dir:
            temp = Path(temp_dir)
            factory = temp / "factory"
            write_managed_skill(factory)
            completed = subprocess.run(
                [
                    POWERSHELL,
                    "-NoProfile",
                    "-ExecutionPolicy",
                    "Bypass",
                    "-File",
                    str(script),
                    "-DevOnly",
                    "-FactoryRoot",
                    str(factory),
                    "-SkillName",
                    "demo-skill",
                    "-Target",
                    "codex",
                    "-RuntimeRoot",
                    str(temp / "runtime-skills"),
                    "-DryRun",
                ],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
            )

            self.assertNotEqual(completed.returncode, 0)
            self.assertIn("test-only", completed.stdout + completed.stderr)

            env_without_guard = dict(os.environ)
            env_without_guard.pop("AGENT_SKILLS_TEST_RUNTIME_OVERRIDE", None)
            missing_environment_guard = subprocess.run(
                [
                    POWERSHELL,
                    "-NoProfile",
                    "-ExecutionPolicy",
                    "Bypass",
                    "-File",
                    str(script),
                    "-DevOnly",
                    "-FactoryRoot",
                    str(factory),
                    "-SkillName",
                    "demo-skill",
                    "-Target",
                    "codex",
                    "-RuntimeRoot",
                    str(temp / "runtime-skills"),
                    "-AllowTestRuntimeRoot",
                    "-DryRun",
                ],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                env=env_without_guard,
            )

            self.assertNotEqual(missing_environment_guard.returncode, 0)
            self.assertIn(
                "test-only",
                missing_environment_guard.stdout + missing_environment_guard.stderr,
            )

    def test_dev_link_helper_refuses_official_default_runtime_root(self):
        script = ROOT / "scripts" / "link-managed-skill.ps1"
        with tempfile.TemporaryDirectory() as temp_dir:
            factory = Path(temp_dir) / "factory"
            write_managed_skill(factory)
            default_runtime = Path.home() / ".codex" / "skills"

            completed = subprocess.run(
                [
                    POWERSHELL,
                    "-NoProfile",
                    "-ExecutionPolicy",
                    "Bypass",
                    "-File",
                    str(script),
                    "-DevOnly",
                    "-FactoryRoot",
                    str(factory),
                    "-SkillName",
                    "demo-skill",
                    "-Target",
                    "codex",
                    "-RuntimeRoot",
                    str(default_runtime),
                    "-AllowTestRuntimeRoot",
                    "-DryRun",
                ],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
            )

            self.assertNotEqual(completed.returncode, 0)
            self.assertIn("Official/default runtime root is forbidden", completed.stdout + completed.stderr)

    def test_dev_link_helper_refuses_nested_official_runtime_and_backup_paths(self):
        script = ROOT / "scripts" / "link-managed-skill.ps1"
        with tempfile.TemporaryDirectory() as temp_dir:
            temp = Path(temp_dir)
            factory = temp / "factory"
            write_managed_skill(factory)
            official_codex = Path.home() / ".codex" / "skills"
            commands = [
                [
                    "-RuntimeRoot", str(official_codex / "isolated-test"),
                    "-BackupRoot", str(temp / "backups"),
                ],
                [
                    "-RuntimeRoot", str(temp / "runtime"),
                    "-BackupRoot", str(official_codex / "backups" / "isolated-test"),
                ],
            ]
            for extra in commands:
                with self.subTest(extra=extra):
                    completed = subprocess.run(
                        [
                            POWERSHELL,
                            "-NoProfile",
                            "-ExecutionPolicy",
                            "Bypass",
                            "-File",
                            str(script),
                            "-DevOnly",
                            "-FactoryRoot",
                            str(factory),
                            "-SkillName",
                            "demo-skill",
                            "-Target",
                            "codex",
                            *extra,
                            "-AllowTestRuntimeRoot",
                            "-DryRun",
                        ],
                        capture_output=True,
                        text=True,
                        encoding="utf-8",
                        errors="replace",
                    )

                    self.assertNotEqual(completed.returncode, 0)
                    self.assertIn("official runtime root", (completed.stdout + completed.stderr).lower())

    def test_verifier_accepts_manifest_owned_link_without_marker(self):
        helper = ROOT / "scripts" / "link-managed-skill.ps1"
        with tempfile.TemporaryDirectory() as temp_dir:
            temp = Path(temp_dir)
            factory = temp / "factory"
            repo = factory / "agent-skills"
            source = write_managed_skill(factory)
            (source / "SKILL.md").write_text(
                "---\nname: demo-skill\ndescription: Use when testing a managed runtime link.\n---\n",
                encoding="utf-8",
            )
            self_check = source / "scripts" / "self-check.ps1"
            self_check.parent.mkdir()
            self_check.write_text('Write-Output "verify-self-check"\n', encoding="utf-8")

            runtime = temp / "runtime-skills"
            backup = temp / "backups"
            manifests = repo / "manifests"
            skill_set = json.loads((manifests / "skill-set.json").read_text(encoding="utf-8"))
            skill_set["repo_name"] = "22utube-agent-skills"
            (manifests / "skill-set.json").write_text(json.dumps(skill_set), encoding="utf-8")
            (manifests / "targets.json").write_text(
                json.dumps(
                    {
                        "targets": {
                            "codex": {
                                "path": str(runtime),
                                "layout": "flat",
                                "backup_path": str(backup),
                                "state_file": ".managed.json",
                            }
                        }
                    }
                ),
                encoding="utf-8",
            )
            scripts = repo / "scripts"
            scripts.mkdir(exist_ok=True)
            verifier = scripts / "verify.ps1"
            shutil.copy2(ROOT / "scripts" / "verify.ps1", verifier)
            tests = repo / "tests"
            tests.mkdir()
            (tests / "test_smoke.py").write_text(
                "import unittest\n\n\nclass Smoke(unittest.TestCase):\n"
                "    def test_smoke(self):\n        self.assertTrue(True)\n",
                encoding="utf-8",
            )

            linked = subprocess.run(
                [
                    POWERSHELL,
                    "-NoProfile",
                    "-ExecutionPolicy",
                    "Bypass",
                    "-File",
                    str(helper),
                    "-DevOnly",
                    "-FactoryRoot",
                    str(factory),
                    "-SkillName",
                    "demo-skill",
                    "-Target",
                    "codex",
                    "-RuntimeRoot",
                    str(runtime),
                    "-AllowTestRuntimeRoot",
                    "-BackupRoot",
                    str(backup),
                ],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
            )
            self.assertEqual(linked.returncode, 0, linked.stdout + linked.stderr)

            verified = subprocess.run(
                [
                    POWERSHELL,
                    "-NoProfile",
                    "-ExecutionPolicy",
                    "Bypass",
                    "-File",
                    str(verifier),
                    "-Target",
                    "codex",
                ],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1", "PYTHONUTF8": "1"},
            )

            self.assertEqual(verified.returncode, 0, verified.stdout + verified.stderr)
            self.assertIn("LINK PASS target=codex skill=demo-skill", verified.stdout)
            self.assertIn("SELF_CHECK PASS target=codex skill=demo-skill", verified.stdout)
            self.assertNotIn("missing managed marker", verified.stdout)


if __name__ == "__main__":
    unittest.main()

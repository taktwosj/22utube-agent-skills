from __future__ import annotations

import hashlib
import json
import os
import stat
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from scripts import skill_release


ROOT = Path(__file__).resolve().parents[1]
CLI = ROOT / "scripts" / "skill_release.py"
EXPECTED_SHARED_SKILLS = [
    "001short-production-agent",
    "119-politics-longform-capcut",
    "1caveman",
    "222mara",
    "naver-blog-posting",
    "top5isu-shorts",
]


def run(*args: str, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    command_env = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1", "PYTHONUTF8": "1"}
    if env:
        command_env.update(env)
    return subprocess.run(
        [sys.executable, "-B", str(CLI), *args],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=command_env,
    )


def create_repo(root: Path, skills: tuple[str, ...] = ("demo-skill",)) -> tuple[Path, str]:
    repo = root / "agent-skills"
    targets = {
        "codex": {"path": "$HOME/.codex/skills", "layout": "flat", "backup_path": "$HOME/.codex/skills_backups"},
        "claude": {"path": "$HOME/.claude/skills", "layout": "flat", "backup_path": "$HOME/.claude/skills_backups"},
        "hermes": {
            "path": "$HOME/.hermes/skills",
            "windows_path": "$LOCALAPPDATA/Hermes/skills",
            "layout": "category",
            "default_category": "22utube",
            "backup_path": "$HOME/.hermes/skills_backups",
            "windows_backup_path": "$LOCALAPPDATA/Hermes/skills_backups",
        },
    }
    manifest_skills = []
    for name in skills:
        skill = repo / "skills" / name
        skill.mkdir(parents=True)
        (skill / "SKILL.md").write_text(
            f"---\nname: {name}\ndescription: Fixture.\n---\n", encoding="utf-8"
        )
        (skill / "asset.txt").write_text(f"payload:{name}\n", encoding="utf-8")
        manifest_skills.append(
            {"name": name, "category": "22utube", "targets": ["codex", "claude", "hermes"], "enabled": True}
        )
    manifests = repo / "manifests"
    manifests.mkdir(parents=True)
    (manifests / "skill-set.json").write_text(
        json.dumps({"repo_name": "22utube-agent-skills", "skills": manifest_skills}), encoding="utf-8"
    )
    (manifests / "targets.json").write_text(json.dumps({"targets": targets}), encoding="utf-8")
    subprocess.run(["git", "init", "-q", str(repo)], check=True)
    subprocess.run(["git", "-C", str(repo), "config", "user.name", "Fixture"], check=True)
    subprocess.run(["git", "-C", str(repo), "config", "user.email", "fixture@example.invalid"], check=True)
    subprocess.run(["git", "-C", str(repo), "add", "."], check=True)
    subprocess.run(["git", "-C", str(repo), "commit", "-q", "-m", "fixture"], check=True)
    commit = subprocess.run(
        ["git", "-C", str(repo), "rev-parse", "HEAD"], check=True, capture_output=True, text=True
    ).stdout.strip()
    return repo, commit


def publish_fixture(temp: Path, skills: tuple[str, ...] = ("demo-skill",)) -> tuple[Path, Path, str]:
    repo, commit = create_repo(temp, skills)
    release_root = temp / "onedrive-runtime"
    completed = run(
        "publish",
        "--repo-root",
        str(repo),
        "--release-root",
        str(release_root),
        env={"AGENT_SKILLS_TEST_ROOT_OVERRIDE": "1"},
    )
    if completed.returncode != 0:
        raise AssertionError(completed.stdout + completed.stderr)
    return repo, release_root, commit


def commit_repo(repo: Path, message: str) -> str:
    subprocess.run(["git", "-C", str(repo), "add", "."], check=True)
    subprocess.run(["git", "-C", str(repo), "commit", "-q", "-m", message], check=True)
    return subprocess.run(
        ["git", "-C", str(repo), "rev-parse", "HEAD"], check=True, capture_output=True, text=True
    ).stdout.strip()


def runtime_arguments(temp: Path) -> list[str]:
    return [
        "--runtime-root",
        f"codex={temp / 'codex'}",
        "--runtime-root",
        f"claude={temp / 'claude'}",
        "--runtime-root",
        f"hermes={temp / 'hermes'}",
    ]


def make_tree_writable(root: Path) -> None:
    if not root.exists():
        return
    for path in sorted(root.rglob("*"), key=lambda item: len(item.parts), reverse=True):
        if path.is_symlink():
            continue
        try:
            path.chmod(path.stat().st_mode | stat.S_IWRITE | stat.S_IWUSR)
        except OSError:
            pass
    try:
        root.chmod(root.stat().st_mode | stat.S_IWRITE | stat.S_IWUSR)
    except OSError:
        pass


class ReleasePreflightTests(unittest.TestCase):
    def test_main_manifest_preflight_accepts_six_enabled_shared_skills(self):
        skills, targets = skill_release.enabled_skills(ROOT)
        skill_release.semantic_preflight(skills, targets)
        self.assertEqual([item["name"] for item in skills], EXPECTED_SHARED_SKILLS)


class VerifiedSkillReleaseTests(unittest.TestCase):
    def test_publish_creates_commit_pinned_immutable_release(self):
        with tempfile.TemporaryDirectory() as temporary:
            temp = Path(temporary)
            repo, commit = create_repo(temp)
            release_root = temp / "onedrive-runtime"

            completed = run(
                "publish",
                "--repo-root",
                str(repo),
                "--release-root",
                str(release_root),
                env={"AGENT_SKILLS_TEST_ROOT_OVERRIDE": "1"},
            )

            self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
            release = release_root / "releases" / commit
            manifest_bytes = (release / "manifest.json").read_bytes()
            manifest = json.loads(manifest_bytes)
            self.assertEqual(manifest["release_id"], commit)
            self.assertEqual(manifest["source_commit"], commit)
            self.assertEqual(manifest["file_count"], 2)
            self.assertEqual(
                (release / "READY").read_text(encoding="utf-8").strip(), hashlib.sha256(manifest_bytes).hexdigest()
            )
            self.assertEqual(json.loads((release_root / "active.json").read_text(encoding="utf-8"))["release_id"], commit)
            self.assertTrue((release / "skills" / "demo-skill" / "SKILL.md").is_file())

    def test_publish_refuses_dirty_repository(self):
        with tempfile.TemporaryDirectory() as temporary:
            temp = Path(temporary)
            repo, _ = create_repo(temp)
            (repo / "dirty.txt").write_text("dirty", encoding="utf-8")
            release_root = temp / "onedrive-runtime"

            completed = run(
                "publish", "--repo-root", str(repo), "--release-root", str(release_root),
                env={"AGENT_SKILLS_TEST_ROOT_OVERRIDE": "1"},
            )

            self.assertNotEqual(completed.returncode, 0)
            self.assertIn("dirty repository", completed.stderr)
            self.assertFalse(release_root.exists())

    def test_publish_uses_exact_head_snapshot_and_is_deterministic_for_same_commit(self):
        with tempfile.TemporaryDirectory() as temporary:
            temp = Path(temporary)
            repo, _ = create_repo(temp)
            (repo / ".gitignore").write_text("ignored.txt\n", encoding="utf-8")
            commit = commit_repo(repo, "ignore generated bytes")
            ignored = repo / "skills" / "demo-skill" / "ignored.txt"
            ignored.write_text("must never publish\n", encoding="utf-8")
            release_root = temp / "runtime"
            command = (
                "publish", "--repo-root", str(repo), "--release-root", str(release_root)
            )

            first = run(*command, env={"AGENT_SKILLS_TEST_ROOT_OVERRIDE": "1"})
            self.assertEqual(first.returncode, 0, first.stdout + first.stderr)
            release = release_root / "releases" / commit
            manifest_before = (release / "manifest.json").read_bytes()
            active_before = (release_root / "active.json").read_bytes()
            manifest = json.loads(manifest_before)
            self.assertNotIn("skills/demo-skill/ignored.txt", {entry["path"] for entry in manifest["files"]})
            self.assertFalse((release / "skills" / "demo-skill" / "ignored.txt").exists())

            second = run(*command, env={"AGENT_SKILLS_TEST_ROOT_OVERRIDE": "1"})
            self.assertEqual(second.returncode, 0, second.stdout + second.stderr)
            self.assertEqual((release / "manifest.json").read_bytes(), manifest_before)
            self.assertEqual((release_root / "active.json").read_bytes(), active_before)

    def test_root_override_requires_explicit_test_guard(self):
        with tempfile.TemporaryDirectory() as temporary:
            temp = Path(temporary)
            repo, _ = create_repo(temp)
            environment = dict(os.environ)
            environment.pop("AGENT_SKILLS_TEST_ROOT_OVERRIDE", None)

            completed = run(
                "publish", "--repo-root", str(repo), "--release-root", str(temp / "runtime"), env=environment
            )

            self.assertNotEqual(completed.returncode, 0)
            self.assertIn("test-only root overrides require", completed.stderr)
            self.assertFalse((temp / "runtime").exists())

    def test_activate_refuses_tampered_release(self):
        with tempfile.TemporaryDirectory() as temporary:
            temp = Path(temporary)
            _, release_root, commit = publish_fixture(temp)
            (release_root / "releases" / commit / "skills" / "demo-skill" / "asset.txt").write_text(
                "tampered", encoding="utf-8"
            )

            completed = run(
                "activate", "--release-root", str(release_root), "--cache-root", str(temp / "cache"),
                *runtime_arguments(temp), env={"AGENT_SKILLS_TEST_ROOT_OVERRIDE": "1"},
            )

            self.assertNotEqual(completed.returncode, 0)
            self.assertIn("hash mismatch", completed.stderr)
            self.assertFalse((temp / "cache").exists())

    def test_activate_refuses_unlisted_release_file(self):
        with tempfile.TemporaryDirectory() as temporary:
            temp = Path(temporary)
            _, release_root, commit = publish_fixture(temp)
            (release_root / "releases" / commit / "skills" / "demo-skill" / "unlisted.txt").write_text(
                "not in manifest", encoding="utf-8"
            )

            completed = run(
                "activate", "--release-root", str(release_root), "--cache-root", str(temp / "cache"),
                *runtime_arguments(temp), env={"AGENT_SKILLS_TEST_ROOT_OVERRIDE": "1"},
            )

            self.assertNotEqual(completed.returncode, 0)
            self.assertIn("unlisted release files", completed.stderr)

    def test_activate_refuses_partial_active_release(self):
        with tempfile.TemporaryDirectory() as temporary:
            temp = Path(temporary)
            _, release_root, commit = publish_fixture(temp)
            (release_root / "releases" / commit / "READY").unlink()

            completed = run(
                "activate", "--release-root", str(release_root), "--cache-root", str(temp / "cache"),
                *runtime_arguments(temp), env={"AGENT_SKILLS_TEST_ROOT_OVERRIDE": "1"},
            )

            self.assertNotEqual(completed.returncode, 0)
            self.assertIn("partial release", completed.stderr)

    def test_activation_and_verify_link_all_targets_to_local_cache(self):
        with tempfile.TemporaryDirectory() as temporary:
            temp = Path(temporary)
            repo, release_root, commit = publish_fixture(temp)
            cache_root = temp / "cache"
            arguments = [
                "--release-root", str(release_root), "--cache-root", str(cache_root),
                *runtime_arguments(temp),
            ]

            activated = run("activate", *arguments, env={"AGENT_SKILLS_TEST_ROOT_OVERRIDE": "1"})
            self.assertEqual(activated.returncode, 0, activated.stdout + activated.stderr)
            verified = run("verify", "--cache-root", str(cache_root), *runtime_arguments(temp), env={"AGENT_SKILLS_TEST_ROOT_OVERRIDE": "1"})
            self.assertEqual(verified.returncode, 0, verified.stdout + verified.stderr)

            expected = (cache_root / "releases" / commit / "skills" / "demo-skill").resolve()
            destinations = [
                temp / "codex" / "demo-skill",
                temp / "claude" / "demo-skill",
                temp / "hermes" / "22utube" / "demo-skill",
            ]
            for destination in destinations:
                self.assertEqual(destination.resolve(), expected)
                self.assertNotEqual(destination.resolve(), (repo / "skills" / "demo-skill").resolve())
                self.assertFalse(str(destination.resolve()).startswith(str(release_root.resolve())))

    def test_local_cache_has_verified_immutable_seal_and_blocks_tampered_reactivation(self):
        with tempfile.TemporaryDirectory() as temporary:
            temp = Path(temporary)
            _, release_root, commit = publish_fixture(temp)
            cache_root = temp / "cache"
            arguments = [
                "--release-root", str(release_root), "--cache-root", str(cache_root),
                *runtime_arguments(temp),
            ]
            activated = run("activate", *arguments, env={"AGENT_SKILLS_TEST_ROOT_OVERRIDE": "1"})
            self.assertEqual(activated.returncode, 0, activated.stdout + activated.stderr)
            local_release = cache_root / "releases" / commit
            manifest_sha = hashlib.sha256((local_release / "manifest.json").read_bytes()).hexdigest()
            self.assertEqual((local_release / "IMMUTABLE").read_text(encoding="utf-8").strip(), manifest_sha)
            self.assertFalse((release_root / "releases" / commit / "IMMUTABLE").exists())

            asset = local_release / "skills" / "demo-skill" / "asset.txt"
            mutation_blocked = False
            try:
                asset.write_text("tampered local cache\n", encoding="utf-8")
            except OSError:
                mutation_blocked = True

            try:
                if mutation_blocked:
                    verified = run(
                        "verify", "--cache-root", str(cache_root), *runtime_arguments(temp),
                        env={"AGENT_SKILLS_TEST_ROOT_OVERRIDE": "1"},
                    )
                    self.assertEqual(verified.returncode, 0, verified.stdout + verified.stderr)
                else:
                    rejected = run("activate", *arguments, env={"AGENT_SKILLS_TEST_ROOT_OVERRIDE": "1"})
                    self.assertNotEqual(rejected.returncode, 0)
                    self.assertIn("hash mismatch", rejected.stderr)
            finally:
                make_tree_writable(cache_root)

    def test_activation_backs_up_existing_runtime_destination(self):
        with tempfile.TemporaryDirectory() as temporary:
            temp = Path(temporary)
            _, release_root, _ = publish_fixture(temp)
            destination = temp / "codex" / "demo-skill"
            destination.mkdir(parents=True)
            (destination / "legacy.txt").write_text("keep", encoding="utf-8")
            backup_root = temp / "codex-backups"

            activated = run(
                "activate", "--release-root", str(release_root), "--cache-root", str(temp / "cache"),
                "--target", "codex", "--runtime-root", f"codex={temp / 'codex'}",
                "--backup-root", f"codex={backup_root}", env={"AGENT_SKILLS_TEST_ROOT_OVERRIDE": "1"},
            )

            self.assertEqual(activated.returncode, 0, activated.stdout + activated.stderr)
            backups = list(backup_root.glob("demo-skill_*"))
            self.assertEqual(len(backups), 1)
            self.assertEqual((backups[0] / "legacy.txt").read_text(encoding="utf-8"), "keep")
            self.assertTrue((destination / "SKILL.md").is_file())

    def test_activation_failure_rolls_back_all_links_and_keeps_previous_active(self):
        with tempfile.TemporaryDirectory() as temporary:
            temp = Path(temporary)
            repo, release_root, old_commit = publish_fixture(temp, ("alpha-skill", "beta-skill"))
            cache_root = temp / "cache"
            arguments = [
                "--release-root", str(release_root), "--cache-root", str(cache_root),
                *runtime_arguments(temp),
            ]
            first = run("activate", *arguments, env={"AGENT_SKILLS_TEST_ROOT_OVERRIDE": "1"})
            self.assertEqual(first.returncode, 0, first.stdout + first.stderr)

            (repo / "skills" / "alpha-skill" / "asset.txt").write_text("new alpha\n", encoding="utf-8")
            (repo / "skills" / "beta-skill" / "asset.txt").write_text("new beta\n", encoding="utf-8")
            new_commit = commit_repo(repo, "new release")
            published = run(
                "publish", "--repo-root", str(repo), "--release-root", str(release_root),
                env={"AGENT_SKILLS_TEST_ROOT_OVERRIDE": "1"},
            )
            self.assertEqual(published.returncode, 0, published.stdout + published.stderr)

            failed = run(
                "activate", *arguments,
                env={"AGENT_SKILLS_TEST_ROOT_OVERRIDE": "1", "AGENT_SKILLS_TEST_FAIL_LINK_AFTER": "1"},
            )

            self.assertNotEqual(failed.returncode, 0)
            self.assertIn("induced runtime link failure", failed.stderr)
            local_active = json.loads((cache_root / "active.json").read_text(encoding="utf-8"))
            self.assertEqual(local_active["release_id"], old_commit)
            self.assertNotEqual(local_active["release_id"], new_commit)
            old_release = (cache_root / "releases" / old_commit / "skills").resolve()
            for root in (temp / "codex", temp / "claude", temp / "hermes" / "22utube"):
                for skill in ("alpha-skill", "beta-skill"):
                    destination = root / skill
                    self.assertTrue(str(destination.resolve()).startswith(str(old_release)))

    def test_protected_skill_is_refused(self):
        with tempfile.TemporaryDirectory() as temporary:
            temp = Path(temporary)
            repo, _ = create_repo(temp, ("skill-creator",))

            completed = run(
                "publish", "--repo-root", str(repo), "--release-root", str(temp / "runtime"),
                env={"AGENT_SKILLS_TEST_ROOT_OVERRIDE": "1"},
            )

            self.assertNotEqual(completed.returncode, 0)
            self.assertIn("protected system/plugin skill name", completed.stderr)

    def test_protected_release_path_is_refused(self):
        with tempfile.TemporaryDirectory() as temporary:
            temp = Path(temporary)
            repo, _ = create_repo(temp)

            completed = run(
                "publish", "--repo-root", str(repo), "--release-root", str(temp / "plugins" / "runtime"),
                env={"AGENT_SKILLS_TEST_ROOT_OVERRIDE": "1"},
            )

            self.assertNotEqual(completed.returncode, 0)
            self.assertIn("protected system/plugin path", completed.stderr)

    def test_publish_semantic_preflight_rejects_invalid_target_contracts(self):
        cases = {
            "unsupported target": lambda skills, targets: skills["skills"][0].update(targets=["missing"]),
            "invalid layout": lambda skills, targets: targets["targets"]["codex"].update(layout="nested"),
            "missing default_category": lambda skills, targets: targets["targets"]["hermes"].pop("default_category"),
            "protected target path": lambda skills, targets: targets["targets"]["codex"].update(
                path="$HOME/.codex/plugins/skills"
            ),
        }
        for expected, mutate in cases.items():
            with self.subTest(expected=expected), tempfile.TemporaryDirectory() as temporary:
                temp = Path(temporary)
                repo, _ = create_repo(temp)
                skill_set_path = repo / "manifests" / "skill-set.json"
                targets_path = repo / "manifests" / "targets.json"
                skill_set = json.loads(skill_set_path.read_text(encoding="utf-8"))
                targets = json.loads(targets_path.read_text(encoding="utf-8"))
                mutate(skill_set, targets)
                skill_set_path.write_text(json.dumps(skill_set), encoding="utf-8")
                targets_path.write_text(json.dumps(targets), encoding="utf-8")
                commit_repo(repo, expected)
                release_root = temp / "runtime"

                completed = run(
                    "publish", "--repo-root", str(repo), "--release-root", str(release_root),
                    env={"AGENT_SKILLS_TEST_ROOT_OVERRIDE": "1"},
                )

                self.assertNotEqual(completed.returncode, 0)
                self.assertIn(expected, completed.stderr)
                self.assertFalse((release_root / "active.json").exists())

    def test_publish_preflight_requires_supported_target_and_universal_path(self):
        def add_unknown_target(skills: dict, targets: dict) -> None:
            targets["targets"]["future"] = {
                "path": "$HOME/.future/skills",
                "layout": "flat",
                "backup_path": "$HOME/.future/backups",
            }
            skills["skills"][0]["targets"] = ["future"]

        def remove_path(skills: dict, targets: dict) -> None:
            targets["targets"]["codex"].pop("path")

        def keep_windows_path_only(skills: dict, targets: dict) -> None:
            targets["targets"]["codex"]["windows_path"] = "$LOCALAPPDATA/Codex/skills"
            targets["targets"]["codex"].pop("path")

        cases = {
            "unsupported target": add_unknown_target,
            "universal path is missing": remove_path,
            "windows path cannot replace universal path": keep_windows_path_only,
        }
        for expected, mutate in cases.items():
            with self.subTest(expected=expected), tempfile.TemporaryDirectory() as temporary:
                temp = Path(temporary)
                repo, _ = create_repo(temp)
                skill_set_path = repo / "manifests" / "skill-set.json"
                targets_path = repo / "manifests" / "targets.json"
                skill_set = json.loads(skill_set_path.read_text(encoding="utf-8"))
                targets = json.loads(targets_path.read_text(encoding="utf-8"))
                mutate(skill_set, targets)
                skill_set_path.write_text(json.dumps(skill_set), encoding="utf-8")
                targets_path.write_text(json.dumps(targets), encoding="utf-8")
                commit_repo(repo, expected)

                completed = run(
                    "publish", "--repo-root", str(repo), "--release-root", str(temp / "runtime"),
                    env={"AGENT_SKILLS_TEST_ROOT_OVERRIDE": "1"},
                )

                self.assertNotEqual(completed.returncode, 0)
                self.assertIn(expected, completed.stderr)

    def test_dry_run_makes_no_mutation(self):
        with tempfile.TemporaryDirectory() as temporary:
            temp = Path(temporary)
            repo, _ = create_repo(temp)
            release_root = temp / "runtime"
            published = run(
                "publish", "--repo-root", str(repo), "--release-root", str(release_root), "--dry-run",
                env={"AGENT_SKILLS_TEST_ROOT_OVERRIDE": "1"},
            )
            self.assertEqual(published.returncode, 0, published.stdout + published.stderr)
            self.assertFalse(release_root.exists())

            _, release_root, _ = publish_fixture(temp / "real")
            activated = run(
                "activate", "--release-root", str(release_root), "--cache-root", str(temp / "cache"),
                *runtime_arguments(temp), "--dry-run", env={"AGENT_SKILLS_TEST_ROOT_OVERRIDE": "1"},
            )
            self.assertEqual(activated.returncode, 0, activated.stdout + activated.stderr)
            self.assertFalse((temp / "cache").exists())
            self.assertFalse((temp / "codex").exists())

    def test_existing_immutable_release_with_different_valid_manifest_is_refused(self):
        with tempfile.TemporaryDirectory() as temporary:
            temp = Path(temporary)
            repo, release_root, commit = publish_fixture(temp)
            release = release_root / "releases" / commit
            manifest_path = release / "manifest.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["unexpected"] = "different-but-valid"
            manifest_data = (json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")
            manifest_path.write_bytes(manifest_data)
            (release / "READY").write_text(hashlib.sha256(manifest_data).hexdigest() + "\n", encoding="utf-8")

            completed = run(
                "publish", "--repo-root", str(repo), "--release-root", str(release_root),
                env={"AGENT_SKILLS_TEST_ROOT_OVERRIDE": "1"},
            )

            self.assertNotEqual(completed.returncode, 0)
            self.assertIn("immutable release already exists with different content", completed.stderr)


if __name__ == "__main__":
    unittest.main()

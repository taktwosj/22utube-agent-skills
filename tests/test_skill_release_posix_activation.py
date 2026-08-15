from __future__ import annotations

import os
import stat
import tempfile
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from scripts import skill_release


RELEASE_ID = "a" * 40


def write_published_release(release_root: Path) -> tuple[Path, str]:
    release = release_root / "releases" / RELEASE_ID
    skill = release / "skills" / "demo-skill"
    skill.mkdir(parents=True)
    (skill / "SKILL.md").write_text(
        "---\nname: demo-skill\ndescription: Fixture.\n---\n", encoding="utf-8"
    )
    skills = [{"name": "demo-skill", "category": "22utube", "targets": ["codex"]}]
    manifest = {
        "schema_version": 1,
        "release_id": RELEASE_ID,
        "source_commit": RELEASE_ID,
        "skills": skills,
        "targets": {
            "codex": {
                "path": "$HOME/.codex/skills",
                "layout": "flat",
                "backup_path": "$HOME/.codex/skills_backups",
            }
        },
        "files": skill_release.payload_entries(release, skills),
        "file_count": 1,
    }
    manifest_data = skill_release.json_bytes(manifest)
    manifest_sha = skill_release.sha256_bytes(manifest_data)
    (release / "manifest.json").write_bytes(manifest_data)
    (release / "READY").write_text(manifest_sha + "\n", encoding="utf-8")
    (release_root / "active.json").write_bytes(
        skill_release.json_bytes(
            {"schema_version": 1, "release_id": RELEASE_ID, "manifest_sha256": manifest_sha}
        )
    )
    return release, manifest_sha


def activation_args(temp: Path, release_root: Path, cache_root: Path) -> SimpleNamespace:
    return SimpleNamespace(
        release_root=str(release_root),
        cache_root=str(cache_root),
        runtime_root=[f"codex={temp / 'codex'}"],
        backup_root=[f"codex={temp / 'codex-backups'}"],
        target="codex",
        dry_run=False,
    )


def seal_like_posix(release: Path, manifest_sha: str) -> None:
    (release / "IMMUTABLE").write_text(manifest_sha + "\n", encoding="utf-8")
    files = sorted(
        (path for path in release.rglob("*") if path.is_file()), key=lambda path: len(path.parts), reverse=True
    )
    directories = sorted(
        (path for path in release.rglob("*") if path.is_dir()), key=lambda path: len(path.parts), reverse=True
    )
    for path in files:
        path.chmod(path.stat().st_mode & ~0o222)
    for path in directories + [release]:
        path.chmod(path.stat().st_mode & ~0o222)


class PosixActivationPromotionTests(unittest.TestCase):
    def test_activate_promotes_across_parents_before_posix_immutable_seal(self):
        with tempfile.TemporaryDirectory() as temporary:
            temp = Path(temporary)
            release_root = temp / "publisher"
            cache_root = temp / "cache"
            write_published_release(release_root)
            real_replace = os.replace
            cross_parent_source_modes: list[int] = []

            def replace_with_posix_directory_rule(source: os.PathLike[str], destination: os.PathLike[str]) -> None:
                source_path = Path(source)
                destination_path = Path(destination)
                if source_path.is_dir() and source_path.parent != destination_path.parent:
                    source_mode = stat.S_IMODE(source_path.stat().st_mode)
                    cross_parent_source_modes.append(source_mode)
                    if not source_mode & stat.S_IWUSR:
                        raise PermissionError(13, "Permission denied", str(source_path))
                real_replace(source_path, destination_path)

            try:
                with (
                    patch.dict(os.environ, {skill_release.TEST_OVERRIDE_ENV: "1"}),
                    patch.object(skill_release, "make_local_release_immutable", side_effect=seal_like_posix),
                    patch.object(skill_release.os, "replace", side_effect=replace_with_posix_directory_rule),
                ):
                    skill_release.activate(activation_args(temp, release_root, cache_root))

                self.assertTrue(cross_parent_source_modes)
                self.assertTrue(cross_parent_source_modes[0] & stat.S_IWUSR)
                local_release = cache_root / "releases" / RELEASE_ID
                skill_release.verify_release_directory(local_release, require_immutable=True)
                self.assertEqual(list((cache_root / ".staging").iterdir()), [])
            finally:
                skill_release.remove_link_or_directory(temp / "codex" / "demo-skill")
                skill_release.make_tree_writable_for_cleanup(temp)

    def test_activate_removes_promoted_release_when_immutable_seal_fails(self):
        with tempfile.TemporaryDirectory() as temporary:
            temp = Path(temporary)
            release_root = temp / "publisher"
            cache_root = temp / "cache"
            write_published_release(release_root)

            def seal_then_fail(release: Path, manifest_sha: str) -> None:
                seal_like_posix(release, manifest_sha)
                raise RuntimeError("induced immutable seal failure")

            local_release = cache_root / "releases" / RELEASE_ID
            try:
                with (
                    patch.dict(os.environ, {skill_release.TEST_OVERRIDE_ENV: "1"}),
                    patch.object(skill_release, "make_local_release_immutable", side_effect=seal_then_fail),
                ):
                    with self.assertRaisesRegex(RuntimeError, "induced immutable seal failure"):
                        skill_release.activate(activation_args(temp, release_root, cache_root))

                self.assertFalse(local_release.exists())
                self.assertEqual(list((cache_root / ".staging").iterdir()), [])
                self.assertFalse((temp / "codex" / "demo-skill").exists())
            finally:
                skill_release.make_tree_writable_for_cleanup(temp)

    def test_activate_reuses_existing_immutable_release_without_staging_residue(self):
        with tempfile.TemporaryDirectory() as temporary:
            temp = Path(temporary)
            release_root = temp / "publisher"
            cache_root = temp / "cache"
            _, manifest_sha = write_published_release(release_root)
            args = activation_args(temp, release_root, cache_root)

            try:
                with patch.dict(os.environ, {skill_release.TEST_OVERRIDE_ENV: "1"}):
                    skill_release.activate(args)
                    skill_release.activate(args)

                local_release = cache_root / "releases" / RELEASE_ID
                skill_release.verify_release_directory(local_release, manifest_sha, require_immutable=True)
                self.assertEqual(list((cache_root / ".staging").iterdir()), [])
                self.assertEqual(list((temp / "codex-backups").glob("demo-skill_*")), [])
            finally:
                skill_release.remove_link_or_directory(temp / "codex" / "demo-skill")
                skill_release.make_tree_writable_for_cleanup(temp)


if __name__ == "__main__":
    unittest.main()

#!/usr/bin/env python3
"""Offline integrity and scope verifier for this handoff package."""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

PACKAGE = Path(__file__).resolve().parents[1]
REPO = PACKAGE.parents[2]
HANDOFF = PACKAGE / "handoff.json"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def fail(message: str) -> None:
    print(f"HANDOFF_VERIFY_FAIL: {message}", file=sys.stderr)
    raise SystemExit(1)


def main() -> None:
    try:
        data = json.loads(HANDOFF.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        fail(f"invalid handoff.json: {error}")

    if data.get("schema_version") != "22utube.hyperframes-windows-unicode-handoff.v1":
        fail("unexpected schema_version")

    for artifact in data.get("artifacts", []):
        relative = artifact.get("path")
        expected = artifact.get("sha256")
        if not isinstance(relative, str) or not isinstance(expected, str):
            fail("artifact missing path or sha256")
        file_path = PACKAGE / relative
        if not file_path.is_file():
            fail(f"missing artifact: {relative}")
        actual = sha256(file_path)
        if actual != expected:
            fail(f"sha mismatch for {relative}: {actual}")

    changed = subprocess.run(
        ["git", "-C", str(REPO), "diff", "--name-only", "origin/main...HEAD"],
        capture_output=True,
        text=True,
        check=True,
    ).stdout.splitlines()
    package_prefix = f"docs/handoffs/{PACKAGE.name}/"
    unexpected = [path for path in changed if not path.startswith(package_prefix)]
    if unexpected:
        fail(f"branch changes outside handoff package: {unexpected}")

    if not changed:
        fail("no branch changes found")

    print(
        "HANDOFF_VERIFY_PASS "
        f"branch={data['repository']['branch']} "
        f"artifacts={len(data['artifacts'])} "
        f"changed_paths={len(changed)}"
    )


if __name__ == "__main__":
    main()

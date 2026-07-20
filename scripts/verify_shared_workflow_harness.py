"""Verify that the three vendored workflow harness core copies are present
and byte-identical, and that they were regenerated from the current
canonical source.

Does NOT regenerate; for regeneration use sync_shared_workflow_harness.py.
"""

from __future__ import annotations

import argparse
import hashlib
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SHARED_CORE_DIR = REPO_ROOT / "shared" / "workflow-harness" / "core"
SHARED_VERSION_FILE = REPO_ROOT / "shared" / "workflow-harness" / "VERSION"

CORE_MODULE_ORDER = [
    "ledger.py",
    "state_projection.py",
    "legacy_compat.py",
    "gate_validation.py",
    "cost_guard.py",
    "context_manifest.py",
    "runner_policy.py",
    "effect_policy.py",
    "canonical_render.py",
    "prompt_factory.py",
]

TARGET_SKILLS = [
    "00-tikitaka",
    "000short-production-agent",
    "111-politics-longform",
]


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _canonical_aggregate_sha() -> str:
    h = hashlib.sha256()
    for name in CORE_MODULE_ORDER:
        h.update(_read(SHARED_CORE_DIR / name).encode("utf-8"))
    return h.hexdigest().upper()


def verify_all(repo_root: Path | None = None) -> dict:
    root = Path(repo_root) if repo_root else REPO_ROOT
    skills_root = root / "skills"
    generated_paths = [
        skills_root / skill / "scripts" / "_generated" / "workflow_harness_core.py"
        for skill in TARGET_SKILLS
    ]

    missing = [str(p) for p in generated_paths if not p.exists()]
    if missing:
        return {
            "status": "FAIL",
            "reason": "GENERATED_CORE_MISSING",
            "missing": missing,
            "generated_core_hashes_match": False,
        }

    contents = [p.read_bytes() for p in generated_paths]
    byte_identical = len({c for c in contents}) == 1

    canonical_version = _read(SHARED_VERSION_FILE).strip()
    version_paths = [
        skills_root / skill / "scripts" / "_generated" / "WORKFLOW_HARNESS_VERSION"
        for skill in TARGET_SKILLS
    ]
    version_mismatch = [
        str(p)
        for p, c in zip(version_paths, contents)
        if p.exists() and p.read_text(encoding="utf-8").strip() != canonical_version
    ]

    return {
        "status": "PASS" if (byte_identical and not version_mismatch) else "FAIL",
        "generated_core_hashes_match": byte_identical,
        "version_mismatch": version_mismatch,
        "canonical_version": canonical_version,
        "canonical_source_sha256": _canonical_aggregate_sha(),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Verify vendored workflow harness core copies match canonical source."
    )
    parser.add_argument("--repo-root", type=Path, default=REPO_ROOT)
    args = parser.parse_args(argv)
    result = verify_all(repo_root=args.repo_root)
    print(result["status"])
    for k, v in result.items():
        if k != "status":
            print(f"  {k}: {v}")
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())

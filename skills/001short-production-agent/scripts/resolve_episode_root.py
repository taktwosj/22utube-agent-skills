#!/usr/bin/env python3
"""Resolve the canonical OneDrive episode root for 001 Shorts."""

from __future__ import annotations

import argparse
import re
from pathlib import Path


EPISODE_NAME = re.compile(r"^\d{6}_[A-Za-z0-9][A-Za-z0-9._-]*_[A-Za-z0-9][A-Za-z0-9_-]*$")


def resolve_episode_root(factory_root: Path, episode_name: str) -> Path:
    if not isinstance(episode_name, str) or not EPISODE_NAME.fullmatch(episode_name):
        raise ValueError("EPISODE_ROOT_NAME_INVALID")
    factory = Path(factory_root).resolve()
    if factory.name != "22factory_20260628":
        raise ValueError("FACTORY_ROOT_INVALID")
    root = factory / "0000shrt" / episode_name
    try:
        root.resolve().relative_to((factory / "0000shrt").resolve())
    except ValueError as exc:
        raise ValueError("EPISODE_ROOT_OUT_OF_0000SHRT") from exc
    return root.resolve()


def required_episode_paths(episode_root: Path) -> dict[str, Path]:
    root = Path(episode_root)
    return {
        "source_media": root / "00_input" / "source.mp4",
        "source_intake_receipt": root / "00_input" / "source_intake_receipt.json",
        "source_identity": root / "00_input" / "source_identity.json",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--factory-root", type=Path, required=True)
    parser.add_argument("--episode-name", required=True)
    args = parser.parse_args()
    root = resolve_episode_root(args.factory_root, args.episode_name)
    print(root)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

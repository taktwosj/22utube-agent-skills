#!/usr/bin/env python3
"""Resolve the 112 episode visual profile without changing the V3 default."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


SKILL_DIR = Path(__file__).resolve().parent.parent
V3_PATH = SKILL_DIR / "assets" / "political-documentary-defaults.json"
V4_PATH = SKILL_DIR / "assets" / "political-documentary-v4.json"
V3_ID = "politics_documentary_broadcast_v3"
V4_ID = "politics_documentary_broadcast_v4"


def resolve_profile(requested_profile: str | None) -> tuple[str, Path]:
    normalized = (requested_profile or "").strip()
    if normalized in {"", V3_ID}:
        return V3_ID, V3_PATH
    if normalized == V4_ID:
        return V4_ID, V4_PATH
    raise ValueError(f"UNSUPPORTED_VISUAL_PROFILE:{normalized}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--profile")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    try:
        profile_id, path = resolve_profile(args.profile)
    except ValueError as exc:
        parser.error(str(exc))
    result = {
        "profile_id": profile_id,
        "profile_path": str(path),
        "is_default": profile_id == V3_ID,
        "rollback_profile_id": V3_ID,
    }
    print(json.dumps(result, ensure_ascii=False) if args.json else str(path))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

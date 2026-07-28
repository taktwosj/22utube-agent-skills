#!/usr/bin/env python3
"""Create a self-contained top5isu episode workspace."""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path


class GateFail(Exception):
    pass


DIRECTORIES = (
    "00_source",
    "10_analysis",
    "20_script",
    "30_audio",
    "40_assets",
    "50_capcut_project",
    "90_reports",
)


def route_profile(prompt: str) -> str:
    normalized = re.sub(r"\s+", "", prompt).lower()
    top_tokens = ("top5", "탑5", "탑파이브", "순위", "랭킹", "5위부터1위")
    gunlimbo_tokens = ("군림보", "gunlimbo")
    top5 = any(token in normalized for token in top_tokens)
    gunlimbo = any(token in normalized for token in gunlimbo_tokens)
    if top5 == gunlimbo:
        raise GateFail("WAIT_USER_PROFILE: choose exactly one of top5 or gunlimbo")
    return "top5" if top5 else "gunlimbo"


def validate_episode_id(value: str) -> str:
    value = value.strip()
    if not value or value in {".", ".."} or "/" in value or "\\" in value:
        raise GateFail("FAIL_TOP5ISU_EPISODE_ID: use a non-empty folder-safe id")
    return value


def create_episode(root: Path, episode_id: str, style_profile: str) -> Path:
    if style_profile not in {"top5", "gunlimbo"}:
        raise GateFail("WAIT_USER_PROFILE: style_profile must be top5 or gunlimbo")
    episode_id = validate_episode_id(episode_id)
    root = Path(root).expanduser().resolve()
    episode = root / episode_id
    episode.mkdir(parents=True, exist_ok=False)
    for name in DIRECTORIES:
        (episode / name).mkdir()
    state = {
        "skill": "top5isu-shorts",
        "standalone_factory": True,
        "external_skill_handoff": "forbidden",
        "style_profile": style_profile,
        "template_profile": "top5isu_v2_top55",
        "writer_backend": "chatgpt_browser",
        "browser_profile": "openclaw",
        "writer_reasoning_label": "높음",
        "stage": "INTAKE",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "directories": list(DIRECTORIES),
    }
    (episode / "top5isu_episode_state.json").write_text(
        json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return episode


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("root")
    parser.add_argument("episode_id")
    parser.add_argument("prompt")
    args = parser.parse_args()
    try:
        profile = route_profile(args.prompt)
        episode = create_episode(Path(args.root), args.episode_id, profile)
    except (GateFail, FileExistsError, OSError) as exc:
        print(str(exc))
        return 1
    print(json.dumps({"status": "CREATED", "episode": str(episode), "style_profile": profile}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

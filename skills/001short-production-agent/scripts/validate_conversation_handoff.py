#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any, Dict, List


SCHEMA_VERSION = "001short-session-handoff-v1"
OWNER_SKILL = "001short-production-agent"
LANE = "general_shorts_production"
FORBIDDEN_KEYS = {
    "api_key",
    "apikey",
    "access_token",
    "refresh_token",
    "bot_token",
    "token",
    "cookie",
    "cookies",
    "password",
    "oauth",
    "oauth_token",
    "session_id",
    "conversation_id",
    "secret",
    "credential",
    "credentials",
}


def read_json(path: Path) -> Dict[str, Any]:
    value = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("HANDOFF_JSON_OBJECT_REQUIRED")
    return value


def _normalized_key(value: Any) -> str:
    return re.sub(r"[^a-z0-9]+", "_", str(value).lower()).strip("_")


def _secret_key_paths(value: Any, prefix: str = "") -> List[str]:
    found: List[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            key_text = str(key)
            path = f"{prefix}.{key_text}" if prefix else key_text
            if _normalized_key(key_text) in FORBIDDEN_KEYS:
                found.append(path)
            found.extend(_secret_key_paths(child, path))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            path = f"{prefix}[{index}]" if prefix else f"[{index}]"
            found.extend(_secret_key_paths(child, path))
    return found


def validate_handoff(handoff: Dict[str, Any]) -> List[str]:
    errors: List[str] = []
    if not isinstance(handoff, dict):
        return ["HANDOFF_JSON_OBJECT_REQUIRED"]
    if handoff.get("schema_version") != SCHEMA_VERSION:
        errors.append("HANDOFF_SCHEMA_VERSION_INVALID")
    if handoff.get("owner_skill") != OWNER_SKILL:
        errors.append("HANDOFF_OWNER_SKILL_INVALID")
    if handoff.get("lane") != LANE:
        errors.append("HANDOFF_LANE_INVALID")
    if not isinstance(handoff.get("resume_requested"), bool):
        errors.append("HANDOFF_RESUME_FLAG_INVALID")
    episode_id = handoff.get("episode_id")
    if episode_id is not None and (not isinstance(episode_id, str) or not episode_id.strip()):
        errors.append("HANDOFF_EPISODE_ID_INVALID")
    if handoff.get("resume_requested") is True and not (isinstance(episode_id, str) and episode_id.strip()):
        errors.append("HANDOFF_EPISODE_ID_REQUIRED")
    for field in ("request_scope", "next_action"):
        value = handoff.get(field)
        if not isinstance(value, str) or not value.strip():
            errors.append(f"HANDOFF_FIELD_REQUIRED:{field}")
    for path in _secret_key_paths(handoff):
        errors.append(f"HANDOFF_SECRET_MATERIAL_FORBIDDEN:{path}")
    return errors


def safe_summary(handoff: Dict[str, Any], env_file_exists: bool) -> Dict[str, Any]:
    errors = validate_handoff(handoff)
    summary: Dict[str, Any] = {
        "status": "PASS" if not errors else "FAIL",
        "owner_skill": handoff.get("owner_skill"),
        "lane": handoff.get("lane"),
        "resume_requested": handoff.get("resume_requested"),
        "episode_id": handoff.get("episode_id"),
        "request_scope": handoff.get("request_scope"),
        "next_action": handoff.get("next_action"),
        "env_file_exists": bool(env_file_exists),
    }
    if errors:
        summary["errors"] = errors
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate a safe 001short /new session handoff")
    parser.add_argument("--handoff", type=Path, required=True)
    parser.add_argument("--env-file", type=Path, default=Path.home() / ".hermes" / ".env")
    args = parser.parse_args()
    try:
        handoff = read_json(args.handoff)
        summary = safe_summary(handoff, args.env_file.expanduser().is_file())
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        summary = {"status": "FAIL", "errors": [str(exc)]}
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0 if summary.get("status") == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())

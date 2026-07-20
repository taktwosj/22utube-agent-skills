#!/usr/bin/env python3
"""Validate T1/T2 top title rows cover the full project duration."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


class GateFail(Exception):
    pass


def load_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(data, dict):
        raise GateFail("top title json root must be object")
    return data


def number(value: Any, label: str) -> float:
    try:
        return float(value)
    except (TypeError, ValueError) as exc:
        raise GateFail(f"FAIL_TOP_TITLE_DURATION: {label} must be numeric") from exc


def find_track(data: dict[str, Any], track_id: str) -> dict[str, Any]:
    tracks = data.get("fixed_tracks") or data.get("tracks") or []
    if not isinstance(tracks, list):
        raise GateFail("FAIL_TOP_TITLE_DURATION: fixed_tracks must be array")
    for track in tracks:
        if isinstance(track, dict) and track.get("track_id") == track_id:
            return track
    raise GateFail(f"FAIL_TOP_TITLE_DURATION: {track_id} missing")


def validate_top_title_full_duration(data: dict[str, Any]) -> dict[str, Any]:
    project_duration = number(data.get("project_duration_sec"), "project_duration_sec")
    for track_id, role in (("T1", "top_title_1"), ("T2", "top_title_2")):
        track = find_track(data, track_id)
        if track.get("role") != role:
            raise GateFail(f"FAIL_TOP_TITLE_DURATION: {track_id} role must be {role}")
        start = number(track.get("start_sec", track.get("start", 0)), f"{track_id}.start_sec")
        end = number(track.get("end_sec", track.get("end")), f"{track_id}.end_sec")
        if abs(start) > 0.001 or abs(end - project_duration) > 0.001:
            raise GateFail(f"FAIL_TOP_TITLE_DURATION: {track_id} must span full project duration")
    return {"top_title_full_duration_status": "PASS"}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("json_path")
    args = parser.parse_args()
    try:
        result = validate_top_title_full_duration(load_json(Path(args.json_path)))
    except GateFail as exc:
        print(str(exc))
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

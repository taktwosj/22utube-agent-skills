from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from common import read_json, result, sha256_file, write_json
from schema_runtime import validate_schema


SKILL_ROOT = Path(__file__).resolve().parents[1]
PLAN_SCHEMA = SKILL_ROOT / "schemas" / "executable_production_plan.schema.json"
APPROVED_TIMELINE_SCHEMA = SKILL_ROOT / "schemas" / "approved_timeline.schema.json"
STATE_ANCHOR = {
    "FLICKER_RAVE": "STATE_EFFECT_1",
    "GLITCH_SHAKE": "STATE_EFFECT_2",
    "LASER_CUT": "STATE_EFFECT_3",
}
SFX_SEED = {"TRANSITION": 1, "REVERSAL": 2, "WOW": 3}
FULL_DURATION_ANCHORS = ("SCREEN_EFFECT", "SCREEN_WHITE")


def _valid_range(value: Any) -> bool:
    return (
        isinstance(value, list)
        and len(value) == 2
        and all(isinstance(item, int) and not isinstance(item, bool) for item in value)
        and 0 <= value[0] < value[1]
    )


def _range(row: dict[str, Any], total_duration_us: int) -> list[int]:
    start = row.get("start")
    duration = row.get("duration")
    if (
        not isinstance(start, int)
        or isinstance(start, bool)
        or not isinstance(duration, int)
        or isinstance(duration, bool)
        or start < 0
        or duration <= 0
        or start + duration > total_duration_us
    ):
        raise ValueError(f"APPROVED_TIMELINE_RANGE_INVALID:{row.get('segment_id')}")
    return [start, start + duration]


def _placement(row: dict[str, Any], total_duration_us: int, primary_speaker_id: str) -> dict[str, Any]:
    placement_id = row.get("segment_id")
    role = row.get("role")
    if not isinstance(placement_id, str) or not placement_id:
        raise ValueError("APPROVED_TIMELINE_SEGMENT_ID_INVALID")
    target_range = _range(row, total_duration_us)
    placement: dict[str, Any] = {
        "placement_id": placement_id,
        "anchor": role,
        "operation": "replace_text_preserve_style",
        "target_range_us": target_range,
    }
    if role == "VIDEO":
        source_range = row.get("source_range_us")
        asset_key = row.get("asset_key")
        if not _valid_range(source_range) or not isinstance(asset_key, str):
            raise ValueError(f"APPROVED_TIMELINE_VIDEO_BINDING_INVALID:{placement_id}")
        placement.update(
            operation="replace_media_and_range",
            asset_key=asset_key,
            source_range_us=source_range,
            volume=0,
        )
    elif role in {"T1", "T2", "A9_TEXT"}:
        text = row.get("text")
        if not isinstance(text, str) or not text.strip():
            raise ValueError(f"APPROVED_TIMELINE_TEXT_INVALID:{placement_id}")
        placement["text"] = text
    elif role == "SPEAKER":
        speaker_id = row.get("speaker_id")
        text = row.get("text")
        if not isinstance(text, str) or not text.strip():
            raise ValueError(f"APPROVED_TIMELINE_TEXT_INVALID:{placement_id}")
        placement["speaker_id"] = speaker_id if isinstance(speaker_id, str) else "UNASSIGNED"
        placement["text"] = text
        if not isinstance(speaker_id, str) or not speaker_id or speaker_id == "UNASSIGNED":
            placement.update(anchor="A10_TEXT_UNASSIGNED", operation="omit", speaker_route="UNASSIGNED")
        elif speaker_id == primary_speaker_id:
            placement.update(anchor="A10_TEXT_WHITE", speaker_route="WHITE")
        else:
            placement.update(anchor="A10_TEXT_YELLOW", speaker_route="YELLOW")
    elif role == "STATE":
        effect = row.get("state_effect")
        text = row.get("text")
        if effect not in STATE_ANCHOR:
            raise ValueError(f"APPROVED_TIMELINE_STATE_EFFECT_INVALID:{placement_id}")
        if not isinstance(text, str) or not text.strip():
            raise ValueError(f"APPROVED_TIMELINE_TEXT_INVALID:{placement_id}")
        placement.update(anchor=STATE_ANCHOR[effect], state_effect=effect, text=text)
    elif role == "A11_SFX":
        kind = row.get("sfx_kind")
        if kind not in SFX_SEED:
            raise ValueError(f"APPROVED_TIMELINE_SFX_INVALID:{placement_id}")
        placement.update(
            anchor="A11_SFX",
            operation="clone_template_segment",
            sfx_kind=kind,
            sfx_seed=SFX_SEED[kind],
            volume=1,
        )
    elif role in {"A9", "A10", "A12"}:
        asset_key = row.get("asset_key")
        source_range = row.get("source_range_us")
        if not isinstance(asset_key, str) or not _valid_range(source_range):
            raise ValueError(f"APPROVED_TIMELINE_AUDIO_BINDING_INVALID:{placement_id}")
        volume = row.get("volume", 1)
        if not isinstance(volume, (int, float)) or isinstance(volume, bool) or volume < 0:
            raise ValueError(f"APPROVED_TIMELINE_AUDIO_VOLUME_INVALID:{placement_id}")
        placement.update(
            operation="replace_media_and_range",
            asset_key=asset_key,
            source_range_us=source_range,
            volume=volume,
        )
    else:
        raise ValueError(f"APPROVED_TIMELINE_ROLE_INVALID:{placement_id}:{role}")
    return placement


def compile_plan(approved_timeline: dict[str, Any]) -> dict[str, Any]:
    if approved_timeline.get("schema_version") != "approved-timeline-v2":
        raise ValueError("APPROVED_TIMELINE_V2_REQUIRED")
    episode_id = approved_timeline.get("episode_id")
    total_duration_us = approved_timeline.get("total_duration_us")
    primary_speaker_id = approved_timeline.get("primary_speaker_id")
    if not isinstance(episode_id, str) or not episode_id:
        raise ValueError("APPROVED_TIMELINE_EPISODE_INVALID")
    if not isinstance(total_duration_us, int) or isinstance(total_duration_us, bool) or total_duration_us <= 0:
        raise ValueError("APPROVED_TIMELINE_DURATION_INVALID")
    if not isinstance(primary_speaker_id, str) or not primary_speaker_id:
        raise ValueError("APPROVED_TIMELINE_PRIMARY_SPEAKER_INVALID")
    rows = approved_timeline.get("segments")
    if not isinstance(rows, list) or not rows:
        raise ValueError("APPROVED_TIMELINE_SEGMENTS_INVALID")
    segment_ids = [row.get("segment_id") for row in rows if isinstance(row, dict)]
    seen_ids: set[str] = set()
    for segment_id in segment_ids:
        if isinstance(segment_id, str) and segment_id in seen_ids:
            raise ValueError(f"APPROVED_TIMELINE_DUPLICATE_SEGMENT_ID:{segment_id}")
        if isinstance(segment_id, str):
            seen_ids.add(segment_id)

    placements = [_placement(row, total_duration_us, primary_speaker_id) for row in rows]
    lane_policies = approved_timeline.get("lane_policies")
    if not isinstance(lane_policies, dict):
        raise ValueError("APPROVED_TIMELINE_LANE_POLICIES_INVALID")
    for lane in ("VIDEO", "A9", "A10"):
        policy = lane_policies.get(lane)
        if not isinstance(policy, dict):
            raise ValueError(f"APPROVED_TIMELINE_LANE_POLICY_MISSING:{lane}")
        lane_rows = sorted(
            [row for row in placements if row["anchor"] == lane],
            key=lambda row: row["target_range_us"],
        )
        if not lane_rows and lane != "VIDEO":
            continue
        cursor = 0
        for row in lane_rows:
            start, end = row["target_range_us"]
            if start > cursor and policy.get("allow_gaps") is not True:
                raise ValueError(f"APPROVED_TIMELINE_LANE_GAP:{lane}:{cursor}:{start}")
            if start < cursor and policy.get("allow_overlaps") is not True:
                raise ValueError(f"APPROVED_TIMELINE_LANE_OVERLAP:{lane}:{start}:{cursor}")
            cursor = max(cursor, end)
        if cursor < total_duration_us and policy.get("allow_gaps") is not True:
            raise ValueError(
                f"APPROVED_TIMELINE_LANE_GAP:{lane}:{cursor}:{total_duration_us}"
            )
    titles = {placement["anchor"]: placement for placement in placements if placement["anchor"] in {"T1", "T2"}}
    for title in ("T1", "T2"):
        if title not in titles or titles[title]["target_range_us"] != [0, total_duration_us]:
            raise ValueError(f"APPROVED_TIMELINE_FIXED_TITLE_INVALID:{title}")
    for anchor in FULL_DURATION_ANCHORS:
        placements.append(
            {
                "placement_id": f"{anchor}_FIXED",
                "anchor": anchor,
                "operation": "extend_seed_full_duration",
                "target_range_us": [0, total_duration_us],
            }
        )
    for anchor in ("A9", "A10"):
        if not any(placement["anchor"] == anchor for placement in placements):
            placements.append(
                {
                    "placement_id": f"{anchor}_SEED",
                    "anchor": anchor,
                    "operation": "preserve_muted_seed",
                    "target_range_us": [0, min(total_duration_us, 716_666)],
                    "volume": 0,
                }
            )

    placements.sort(key=lambda row: (row["target_range_us"][0], row["placement_id"]))
    state_rows = sorted(
        [row for row in placements if row["anchor"].startswith("STATE_EFFECT_")],
        key=lambda row: row["target_range_us"],
    )
    for previous, current in zip(state_rows, state_rows[1:]):
        if previous["target_range_us"][1] > current["target_range_us"][0]:
            raise ValueError(f"APPROVED_TIMELINE_STATE_OVERLAP:{previous['placement_id']}:{current['placement_id']}")

    video_ids = [row["placement_id"] for row in placements if row["anchor"] == "VIDEO"]
    original_order = approved_timeline.get("original_order")
    if not isinstance(original_order, list) or not original_order:
        original_order = list(video_ids)
    return {
        "schema_version": "001short-production-plan-v2",
        "episode_id": episode_id,
        "root_profile": approved_timeline.get("root_profile", "shrt_white_base_v2"),
        "project_name": approved_timeline.get("project_name", episode_id),
        "production_mode": approved_timeline.get("production_mode", "URAKKAI"),
        "audio_policy": approved_timeline.get("audio_policy", "V2_TRACK_MIX"),
        "visual_asset_mode": approved_timeline.get("visual_asset_mode", "VMAKE_CLEAN"),
        "total_duration_us": total_duration_us,
        "primary_speaker_id": primary_speaker_id,
        "lane_policies": lane_policies,
        "original_order": original_order,
        "order_signature": [row["placement_id"] for row in placements],
        "timeline": [
            {
                "segment_key": row["placement_id"],
                "target_range_us": row["target_range_us"],
                "placements": [row],
            }
            for row in placements
        ],
    }


def compile_file(approved_timeline_path: Path, output_path: Path) -> dict[str, Any]:
    try:
        approved_timeline = read_json(approved_timeline_path)
        approved_errors = validate_schema(
            approved_timeline, read_json(APPROVED_TIMELINE_SCHEMA)
        )
        if approved_errors:
            return result([{"code": "APPROVED_TIMELINE_SCHEMA", "detail": approved_errors}])
        plan = compile_plan(approved_timeline)
        schema_errors = validate_schema(plan, read_json(PLAN_SCHEMA))
        if schema_errors:
            return result([{"code": "PRODUCTION_PLAN_SCHEMA", "detail": schema_errors}])
        write_json(output_path, plan)
    except (OSError, TypeError, ValueError) as exc:
        return result([{"code": "PRODUCTION_PLAN_COMPILE", "detail": str(exc)}])
    return result([], {"output_path": str(output_path.resolve()), "output_sha256": sha256_file(output_path)})


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--approved-timeline", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    payload = compile_file(args.approved_timeline, args.output)
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if payload["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())

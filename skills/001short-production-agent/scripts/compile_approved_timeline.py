from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

from common import read_json, result, sha256_file, write_json
from schema_runtime import validate_schema


SKILL_ROOT = Path(__file__).resolve().parents[1]
SCHEMA = SKILL_ROOT / "schemas" / "approved_timeline.schema.json"
PRODUCTION_ROLES = ("STATE", "A9", "A9_TEXT", "T1", "T2")


def _target_range(value: object, *, segment_key: str, role: str) -> tuple[int, int]:
    if (
        not isinstance(value, list)
        or len(value) != 2
        or not all(isinstance(item, int) and not isinstance(item, bool) for item in value)
        or value[0] < 0
        or value[1] <= value[0]
    ):
        raise ValueError(f"APPROVED_TIMELINE_RANGE_INVALID:{segment_key}:{role}")
    return value[0], value[1]


def _row_id(role: str, segment_key: str, occurrence: int) -> str:
    if role in {"T1", "T2"} and segment_key == "GLOBAL_TITLES":
        base = f"{role}_FIXED"
    else:
        base = f"{role}_{segment_key}"
    return base if occurrence == 1 else f"{base}_{occurrence:02d}"


def _compile(timeline: dict, plan: dict) -> dict:
    if timeline.get("episode_id") != plan.get("episode_id"):
        raise ValueError("APPROVED_TIMELINE_EPISODE_MISMATCH")
    total_duration = plan.get("total_duration_us")
    if not isinstance(total_duration, int) or isinstance(total_duration, bool) or total_duration <= 0:
        raise ValueError("APPROVED_TIMELINE_DURATION_INVALID")

    existing = timeline.get("segments")
    if not isinstance(existing, list) or not existing:
        raise ValueError("APPROVED_TIMELINE_SEGMENTS_INVALID")
    preserved = [row for row in existing if isinstance(row, dict) and row.get("role") not in PRODUCTION_ROLES]
    source_refs = [row.get("source_ref") for row in preserved if isinstance(row.get("source_ref"), str) and row["source_ref"]]
    if not source_refs:
        raise ValueError("APPROVED_TIMELINE_SOURCE_REF_MISSING")
    default_source_ref = source_refs[0]
    source_ref_by_segment = {
        row.get("segment_id"): row.get("source_ref")
        for row in preserved
        if isinstance(row.get("segment_id"), str) and isinstance(row.get("source_ref"), str)
    }

    role_rows: list[dict] = []
    occurrences: Counter[tuple[str, str]] = Counter()
    plan_timeline = plan.get("timeline")
    if not isinstance(plan_timeline, list) or not plan_timeline:
        raise ValueError("APPROVED_TIMELINE_PLAN_INVALID")
    for plan_row in plan_timeline:
        if not isinstance(plan_row, dict) or not isinstance(plan_row.get("segment_key"), str):
            raise ValueError("APPROVED_TIMELINE_PLAN_INVALID")
        segment_key = plan_row["segment_key"]
        placements = plan_row.get("placements")
        if not isinstance(placements, list):
            raise ValueError(f"APPROVED_TIMELINE_PLACEMENTS_INVALID:{segment_key}")
        for placement in placements:
            if not isinstance(placement, dict) or placement.get("anchor") not in PRODUCTION_ROLES:
                continue
            role = placement["anchor"]
            start, end = _target_range(placement.get("target_range_us"), segment_key=segment_key, role=role)
            if role in {"T1", "T2"} and (start != 0 or end != total_duration):
                raise ValueError(f"APPROVED_TIMELINE_FIXED_TITLE_RANGE_INVALID:{role}")
            key = (role, segment_key)
            occurrences[key] += 1
            role_rows.append(
                {
                    "segment_id": _row_id(role, segment_key, occurrences[key]),
                    "timeline_order": 0,
                    "role": role,
                    "start": start,
                    "duration": end - start,
                    "source_ref": source_ref_by_segment.get(segment_key, default_source_ref),
                }
            )

    observed_roles = {row["role"] for row in role_rows}
    missing_roles = [role for role in PRODUCTION_ROLES if role not in observed_roles]
    if missing_roles:
        raise ValueError(f"APPROVED_TIMELINE_ROLE_MISSING:{','.join(missing_roles)}")

    compiled = dict(timeline)
    ordered = sorted([*preserved, *role_rows], key=lambda row: (row["start"], row["segment_id"]))
    for index, row in enumerate(ordered, start=1):
        row["timeline_order"] = index
    compiled["segments"] = ordered
    return compiled


def compile_timeline(timeline_path: Path, production_plan_path: Path, output_path: Path) -> dict:
    try:
        timeline = read_json(Path(timeline_path))
        plan = read_json(Path(production_plan_path))
        compiled = _compile(timeline, plan)
        schema_errors = validate_schema(compiled, read_json(SCHEMA))
        if schema_errors:
            return result([{"code": "APPROVED_TIMELINE_SCHEMA", "detail": schema_errors}])
        write_json(Path(output_path), compiled)
    except (OSError, TypeError, ValueError) as exc:
        return result([{"code": "APPROVED_TIMELINE_COMPILE", "detail": str(exc)}])
    return result(
        [],
        {
            "output_path": str(Path(output_path).resolve()),
            "output_sha256": sha256_file(Path(output_path)),
            "production_roles": sorted({row["role"] for row in compiled["segments"] if row["role"] in PRODUCTION_ROLES}),
        },
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--timeline", type=Path, required=True)
    parser.add_argument("--production-plan", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    payload = compile_timeline(args.timeline, args.production_plan, args.output)
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if payload["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())

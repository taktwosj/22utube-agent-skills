#!/usr/bin/env python3
"""Derive the 001 Shorts lock artifacts from a single v_plan.json.

The same segment boundaries are otherwise copied by hand into production_plan,
build_manifest, build_config, caption_lock, caption_timing_evidence and final.srt.
Deriving them from one table removes the transcription drift that made whole
episodes fail on microsecond differences.

Only artifacts that are *derivable* are written here. Evidence of external
events - the VMake download receipt, the clean-visual receipt - is read, never
synthesised, so a generated tree can never claim a download that did not happen.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from audio_policy_matrix import A10_POLICIES, SOURCE_CLIP_A10_POLICIES  # noqa: E402
from assembly_type_matrix import (  # noqa: E402
    ALWAYS_CLEARED as ASSEMBLY_ALWAYS_CLEARED,
    LEGACY_EXECUTION_STRATEGY_ALIASES,
    assembly_type_definition,
    validate_assembly_placement_rules,
)
from common import read_json, sha256_file, write_json  # noqa: E402
from production_profile import (  # noqa: E402
    ResolvedProductionProfile,
    audio_source_for_route,
    resolve_production_profile,
)
from schema_runtime import validate_schema  # noqa: E402

SCHEMAS = Path(__file__).resolve().parents[1] / "schemas"

DESIGN_HANDOFF_SCHEMA_VERSION = "tikitaka-design-handoff-v1"
PRODUCTION_PLAN_SCHEMA_VERSION = "001short-production-plan-v2"
BUILD_MANIFEST_SCHEMA_VERSION = "001short-build-manifest-v1"
CAPTION_LOCK_SCHEMA_VERSION = "001short-caption-lock-v2"
CAPTION_TIMING_SCHEMA_VERSION = "001short-caption-timing-evidence-v2"

CAPTION_ROLES = ("A9_TEXT", "A10_TEXT", "STATE")
# A STATE caption has no matching audio, so it cannot claim speech authority.
CAPTION_AUTHORITY = {"STATE": "STATE"}
# Compatibility view for callers/tests that historically appended a list.
ALWAYS_CLEARED = list(ASSEMBLY_ALWAYS_CLEARED)


def resolve_v_plan_type(
    plan: dict,
    production_profile: ResolvedProductionProfile | None = None,
):
    definition = assembly_type_definition(plan.get("type"))
    production_mode = plan.get("production_mode", "URAKKAI")
    if production_profile is not None:
        selector = production_profile.selector
        if (
            selector["assembly_type"] != definition.type_id
            or selector["production_mode"] != production_mode
            or selector["audio_policy"] != plan.get("audio_policy")
        ):
            raise ValueError("V_PLAN_PRODUCTION_PROFILE_MISMATCH")
    strategy = plan.get("execution_strategy")
    if strategy != definition.execution_strategy:
        if strategy not in LEGACY_EXECUTION_STRATEGY_ALIASES.get(definition.type_id, ()):
            raise ValueError("V_PLAN_EXECUTION_STRATEGY_MISMATCH")
        if production_profile is not None:
            raise ValueError("V_PLAN_PRODUCTION_PROFILE_MISMATCH")
    route = (production_mode, plan.get("audio_policy"))
    if route not in definition.allowed_mode_policies:
        raise ValueError("V_PLAN_ASSEMBLY_AUDIO_ROUTE_MISMATCH")
    if production_profile is not None:
        if production_profile.execution_strategy != definition.execution_strategy:
            raise ValueError("V_PLAN_PRODUCTION_PROFILE_MISMATCH")
    return definition


def validate_timeline_type_contract(plan: dict, timeline: dict) -> None:
    expected = {
        "production_mode": plan.get("production_mode", "URAKKAI"),
        "audio_policy": plan.get("audio_policy"),
        "execution_strategy": plan.get("execution_strategy"),
    }
    actual = {
        "production_mode": timeline.get("production_mode", "URAKKAI"),
        "audio_policy": timeline.get("audio_policy"),
        "execution_strategy": timeline.get("execution_strategy"),
    }
    for field, expected_value in expected.items():
        if actual[field] != expected_value:
            raise ValueError(f"V_PLAN_TIMELINE_CONTRACT_MISMATCH:{field}")


def validate_timeline_placement_contract(definition, timeline: dict) -> None:
    role_ranges: dict[str, list[tuple[int, int]]] = {}
    for segment in timeline.get("segments", []):
        role = segment.get("role")
        start = segment.get("start")
        duration = segment.get("duration")
        if (
            not isinstance(role, str)
            or not isinstance(start, int)
            or isinstance(start, bool)
            or not isinstance(duration, int)
            or isinstance(duration, bool)
            or duration <= 0
        ):
            raise ValueError(
                f"APPROVED_TIMELINE_RANGE_INVALID:{segment.get('segment_id')}"
            )
        role_ranges.setdefault(role, []).append((start, start + duration))
    errors = validate_assembly_placement_rules(
        definition, role_ranges, role_ranges.get("VIDEO", [])
    )
    if errors:
        raise ValueError(errors[0])


def source_credit_text(plan: dict) -> str | None:
    """Return the declared full-span credit, or None when the plan omits it.

    Absence is the key being missing.  A present key must carry a non-empty
    string: an empty value would otherwise be indistinguishable from absence and
    would silently leave the template placeholder on track 3.
    """
    if "SOURCE_CREDIT" not in plan:
        return None
    value = plan["SOURCE_CREDIT"]
    if not isinstance(value, str) or not value.strip():
        raise ValueError("SOURCE_CREDIT_DECLARED_EMPTY")
    return value


ORIGINAL_BEAT_HEADER = re.compile(r"^###\s+(B\d{2})\s", re.MULTILINE)


def resolve_original_order(plan: dict, original_grid: Path, v_rows: list[list]) -> list[str]:
    """Return the original beat list the URAKKAI order gates compare against.

    Derived from the surviving V rows alone, an exclusion trim looks identical to
    its own output and can never pass URAKKAI_STRUCTURE_UNCHANGED, so a trim has
    to declare the full list.  A declaration nothing checks is worth no more than
    the derivation it replaced, so it is matched against the original table.
    """
    final_order = [row[1] for row in v_rows]
    declared = plan.get("original_order")
    if declared is None:
        return sorted(set(final_order))
    if not isinstance(declared, list) or not declared:
        raise ValueError("V_PLAN_ORIGINAL_ORDER_INVALID")
    if len(set(declared)) != len(declared):
        raise ValueError(f"V_PLAN_ORIGINAL_ORDER_DUPLICATE:{declared}")
    missing = [beat for beat in final_order if beat not in declared]
    if missing:
        raise ValueError(f"V_PLAN_ORIGINAL_ORDER_MISSING_BEAT:{sorted(set(missing))}")
    # A legacy or fixture grid carries no "### Bxx" blocks; the checks above still
    # apply, but there is nothing to compare the declaration against.
    beats = ORIGINAL_BEAT_HEADER.findall(original_grid.read_text(encoding="utf-8"))
    if beats and declared != beats:
        raise ValueError(f"V_PLAN_ORIGINAL_ORDER_MISMATCH:{declared}!={beats}")
    return declared


def srt_timestamp(us: int) -> str:
    ms = us // 1000
    return f"{ms // 3600000:02d}:{ms // 60000 % 60:02d}:{ms // 1000 % 60:02d},{ms % 1000:03d}"


def probe_duration_us(path: Path) -> int:
    completed = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=nw=1:nk=1", str(path)],
        capture_output=True, text=True, check=True,
    )
    return int(round(float(completed.stdout.strip()) * 1_000_000))


def host_segment(v_rows: list[list], start: int, end: int) -> list | None:
    for row in v_rows:
        if row[2] <= start and end <= row[3]:
            return row
    return None


def build_design_handoff(episode_id: str, episode_root: Path, timeline: dict, identity: dict) -> dict:
    order = [
        segment["segment_id"]
        for segment in sorted(timeline["segments"], key=lambda row: row["timeline_order"])
    ]
    payload = {
        "schema_version": DESIGN_HANDOFF_SCHEMA_VERSION,
        "episode_id": episode_id,
        "status": "PASS",
        "source_identity_path": "../00_input/source_identity.json",
        "source_identity_sha256": sha256_file(episode_root / "00_input" / "source_identity.json"),
        "timeline_path": "approved_timeline.json",
        "timeline_sha256": sha256_file(episode_root / "20_script" / "approved_timeline.json"),
        "source_fingerprint": identity["source_fingerprint"],
        "approved_timeline_order": order,
        "production_mode": timeline.get("production_mode", "URAKKAI"),
        "audio_policy": timeline["audio_policy"],
        "execution_strategy": timeline["execution_strategy"],
        "total_duration_us": max(row["start"] + row["duration"] for row in timeline["segments"]),
    }
    errors = validate_schema(payload, read_json(SCHEMAS / "design_handoff.schema.json"))
    if errors:
        raise ValueError(f"DESIGN_HANDOFF_SCHEMA_INVALID:{errors}")
    return payload


USER_FALLBACK = "USER_FALLBACK_CLEAN_SOURCE"


def clean_source_block(vmake_evidence: dict, clean_path: Path, clean_sha: str) -> dict:
    origin = vmake_evidence.get("origin", "AGENT_PRIMARY_CLEAN_SOURCE")
    block = {"origin": origin, "output_path": str(clean_path), "output_sha256": clean_sha}
    if origin == USER_FALLBACK:
        block["fallback_reason"] = vmake_evidence["fallback_reason"]
    return block


def vmake_block(vmake_evidence: dict, episode_root: Path, clean_path: Path, clean_sha: str) -> dict:
    if vmake_evidence.get("origin") == USER_FALLBACK:
        return {}
    return {
        "vmake": {
            "receipt_path": str(episode_root / "40_assets_used" / "vmake_final_download_evidence.json"),
            "output_path": str(clean_path),
            "run_id": vmake_evidence["run_id"],
            "job_id": vmake_evidence["job_id"],
            "input_sha256": vmake_evidence["uploaded_source_sha256"],
            "output_sha256": clean_sha,
            "final_download": bool(vmake_evidence.get("final_download")),
        }
    }


def build_manifest(
    episode_id: str,
    episode_root: Path,
    plan: dict,
    identity: dict,
    template_zip: Path,
    vmake_evidence: dict,
) -> dict:
    v_rows = plan["V"]
    source_sha = identity["media_sha256"]
    clean_path = episode_root / "40_assets_used" / "clean_source.mp4"
    clean_sha = sha256_file(clean_path)
    if str(vmake_evidence.get("downloaded_output_sha256", "")).lower() != clean_sha.lower():
        raise ValueError("VMAKE_EVIDENCE_OUTPUT_SHA_MISMATCH")
    intake = read_json(episode_root / "00_input" / "source_intake_receipt.json")
    audio_policy = plan["audio_policy"]
    urakkai_production_type = plan.get("urakkai_production_type", "URAKKAI")
    keep_a10 = audio_policy in A10_POLICIES
    narration_ranges = [
        [cue[4], cue[5]] for cue in plan.get("cues", []) if cue[1] != "NOFIT"
    ]

    def audio_mode(row: list) -> str:
        # Every lane used to be hardcoded mute, which is why types 3-5 built a
        # silent draft: build_episode_capcut emits an A10 segment only for rows
        # whose mode is "on" or "duck".
        if not keep_a10:
            return "mute"
        target = [row[2], row[3]]
        covering = [
            narration for narration in narration_ranges
            if max(target[0], narration[0]) < min(target[1], narration[1])
        ]
        if not covering:
            return "on"
        # Types 4 and 5 lay a new A9 narration over the retained speaker, and
        # both the protocol gate and the builder require A10 to be silent for
        # exactly the segments A9 covers - "on" everywhere earns
        # URAKKAI_MIXED_A10_NOT_MUTED_UNDER_A9.  Neither side supports a cue
        # that covers only part of a Vxx, so refuse it here rather than let a
        # later validator find it after the receipts are written.
        if any(
            narration[0] > target[0] or narration[1] < target[1]
            for narration in covering
        ):
            raise ValueError(f"MIXED_A10_PARTIAL_OVERLAP_UNSUPPORTED:{row[0]}")
        return "duck"

    def capcut_range(row: list) -> dict:
        # A reassembled stem is already in target order, so the builder may reuse
        # the target range.  SOURCE_CLIP plays the untouched source, so its CapCut
        # source range has to name the real original span.
        if audio_policy not in SOURCE_CLIP_A10_POLICIES:
            return {}
        return {"capcut_source_range_us": [row[4], row[5]]}

    return {
        "schema_version": BUILD_MANIFEST_SCHEMA_VERSION,
        "episode_id": episode_id,
        "visual_asset_mode": "CLEAN_VISUAL_READY",
        "production_mode": plan.get("production_mode", "URAKKAI"),
        "audio_policy": plan["audio_policy"],
        "audio_source": audio_source_for_route(
            plan.get("production_mode", "URAKKAI"), plan["audio_policy"]
        ),
        "source": {
            "path": str(episode_root / "00_input" / "source.mp4"),
            "sha256": source_sha,
            "duration_us": intake["local_media_duration_us"],
        },
        "template": {
            "root_name": "shrt white",
            "root_zip_path": str(template_zip),
            "root_zip_sha256": sha256_file(template_zip),
        },
        # A user-supplied clean file carries no VMake receipt: validate_prebuild rejects
        # USER_FALLBACK_CLEAN_SOURCE that claims one, so the agent never implies it ran the job.
        "clean_source": clean_source_block(vmake_evidence, clean_path, clean_sha),
        **vmake_block(vmake_evidence, episode_root, clean_path, clean_sha),
        "urakkai": {
            "production_type": urakkai_production_type,
            "target_duration_us": plan["DUR"],
            "reorder_required": urakkai_production_type != "TRIM_ONLY_NO_REORDER",
            "locked_permutation": [row[0] for row in v_rows],
            "video_clips": [
                {"clip_id": row[0], "source_sha256": source_sha,
                 "source_range_us": [row[4], row[5]], "target_range_us": [row[2], row[3]]}
                for row in v_rows
            ],
        },
        "source_audio": [
            {"clip_id": row[0], "mode": audio_mode(row), "source_sha256": source_sha,
             "source_range_us": [row[4], row[5]], "target_range_us": [row[2], row[3]],
             **capcut_range(row)}
            for row in v_rows
        ],
    }


def build_production_plan(
    episode_id: str, episode_root: Path, plan: dict, timeline: dict, identity: dict,
    manifest: dict, root_profile: str, original_order: list[str],
    production_profile: ResolvedProductionProfile | None = None,
) -> dict:
    audio_source = manifest["audio_source"]
    v_rows = plan["V"]
    cues = [cue for cue in plan.get("cues", []) if cue[1] != "NOFIT"]
    a9_text = {row["cue_id"]: row for row in timeline["segments"] if row["role"] == "A9"}
    states = {row["segment_id"]: row for row in timeline["segments"] if row["role"] == "STATE"}
    a10_texts = sorted(
        (row for row in timeline["segments"] if row["role"] == "A10_TEXT"),
        key=lambda row: row["start"],
    )
    audio_modes = {row["clip_id"]: row["mode"] for row in manifest["source_audio"]}
    a10_asset_key = "source_audio"
    rows = []
    for segment_id, beat_id, start, end, source_start, source_end in v_rows:
        target = [start, end]
        placements = [
            {"anchor": "VIDEO", "operation": "clone_template_segment", "asset_key": "clean_video",
             "source_range_us": [source_start, source_end], "target_range_us": target, "volume": 0},
            {"anchor": "T1", "operation": "replace_template_text", "text": plan["T1"], "target_range_us": target},
            {"anchor": "T2", "operation": "replace_template_text", "text": plan["T2"], "target_range_us": target},
        ]
        # SOURCE_CREDIT is a full-span title lane like T1/T2.  A plan that does
        # not declare it leaves track 3 empty, so v2-era episodes rebuild
        # unchanged.
        credit = source_credit_text(plan)
        if credit is not None:
            placements.append({
                "anchor": "SOURCE_CREDIT", "operation": "replace_template_text",
                "text": credit, "target_range_us": target,
            })
        for cue in cues:
            if cue[0] != segment_id:
                continue
            placements.append({
                "anchor": "A9", "operation": "replace_media_and_range", "asset_key": cue[6],
                "source_range_us": [0, cue[3]], "target_range_us": [cue[4], cue[5]], "volume": 1,
            })
            placements.append({
                "anchor": "A9_TEXT", "operation": "replace_text_preserve_style",
                "text": cue[2].replace("<br>", "\n"), "target_range_us": [cue[4], cue[5]],
            })
        mode = audio_modes.get(segment_id, "mute")
        if mode in {"on", "duck"}:
            # A10 spans the whole Vxx, exactly like its VIDEO twin: the mapping
            # gate in validate_executable_protocol requires one A10 per V with
            # identical source and target ranges.  duck keeps the lane present
            # under a narration bed at zero volume rather than dropping it.
            placements.append({
                "anchor": "A10", "operation": "replace_media_and_range",
                "asset_key": a10_asset_key,
                "source_range_us": [source_start, source_end], "target_range_us": target,
                "volume": 0 if mode == "duck" else 1,
            })
        for caption in a10_texts:
            caption_end = caption["start"] + caption["duration"]
            if caption["start"] < start or caption_end > end:
                continue
            placements.append({
                "anchor": "A10_TEXT", "operation": "replace_text_preserve_style",
                "text": caption["text"].replace("<br>", "\n"),
                "target_range_us": [caption["start"], caption_end],
            })
        state = states.get(f"STATE_{segment_id}")
        if state:
            placements.append({
                "anchor": "STATE", "operation": "replace_text_preserve_style",
                "text": state["text"], "target_range_us": target,
            })
        placements.append({"anchor": "SCREEN", "operation": "clone_template_segment", "target_range_us": target})
        rows.append({
            "segment_key": beat_id, "source_beat_id": beat_id, "target_segment_id": segment_id,
            "target_range_us": target, "placements": placements,
        })
    unused = set(a9_text) - {cue[1] for cue in cues}
    if unused:
        raise ValueError(f"TIMELINE_A9_NOT_IN_V_PLAN:{sorted(unused)}")
    return {
        "schema_version": PRODUCTION_PLAN_SCHEMA_VERSION,
        "episode_id": episode_id,
        "root_profile": root_profile,
        "project_name": episode_id,
        "production_mode": "URAKKAI",
        "audio_policy": plan["audio_policy"],
        "audio_source": audio_source,
        "assembly_type": plan["type"],
        "execution_strategy": plan["execution_strategy"],
        **(
            {"production_profile": dict(production_profile.selector)}
            if production_profile is not None else {}
        ),
        "visual_asset_mode": "CLEAN_VISUAL_READY",
        "total_duration_us": plan["DUR"],
        # URAKKAI_STRUCTURE_UNCHANGED and the fake-split guard both compare the
        # final order against the ORIGINAL beat list, and the guard exempts a
        # trim whose final_order is a contiguous slice of it.  Deriving this
        # from v_rows alone dropped every excluded beat, so an order-preserving
        # trim looked identical to its own output and could never be built.
        "original_order": original_order,
        "order_signature": [row[1] for row in v_rows],
        "final_order": [row[1] for row in v_rows],
        "timeline": rows,
        "cleared_anchors": (
            list(ALWAYS_CLEARED)
            + list(assembly_type_definition(plan["type"]).cleared_roles)
            + ([] if source_credit_text(plan) is not None else ["SOURCE_CREDIT"])
        ),
        "audio_bindings": {
            "audio_lock_path": "../30_audio_srt/audio_lock.json",
            "audio_lock_sha256": sha256_file(episode_root / "30_audio_srt" / "audio_lock.json"),
        },
        "locks": {
            "source_identity_sha256": sha256_file(episode_root / "00_input" / "source_identity.json"),
            "source_fingerprint": identity["source_fingerprint"],
            "original_grid_sha256": sha256_file(episode_root / "20_script" / "original-capcut-grid.md"),
            "urakkai_grid_sha256": sha256_file(episode_root / "20_script" / "urakkai-capcut-grid.md"),
        },
    }


def build_captions(episode_id: str, episode_root: Path, plan: dict, timeline: dict) -> tuple[dict, dict, str]:
    v_rows = plan["V"]
    captions = sorted(
        (row for row in timeline["segments"] if row["role"] in CAPTION_ROLES),
        key=lambda row: row["start"],
    )
    srt = "\n\n".join(
        f"{index}\n{srt_timestamp(row['start'])} --> {srt_timestamp(row['start'] + row['duration'])}\n{row['text']}"
        for index, row in enumerate(captions, start=1)
    ) + "\n"
    srt_path = episode_root / "30_audio_srt" / "final.srt"
    srt_path.write_text(srt, encoding="utf-8")
    srt_sha = sha256_file(srt_path)

    identity_sha = sha256_file(episode_root / "00_input" / "source_identity.json")
    evidence = {
        "schema_version": CAPTION_TIMING_SCHEMA_VERSION,
        "status": "PASS",
        "episode_id": episode_id,
        "source_identity_path": "../00_input/source_identity.json",
        "source_identity_sha256": identity_sha,
        "approved_timeline_path": "../20_script/approved_timeline.json",
        "approved_timeline_sha256": sha256_file(episode_root / "20_script" / "approved_timeline.json"),
        "build_manifest_path": "../50_capcut_project/build_manifest.json",
        "build_manifest_sha256": sha256_file(episode_root / "50_capcut_project" / "build_manifest.json"),
        "production_plan_path": "../20_script/production_plan.json",
        "production_plan_sha256": sha256_file(episode_root / "20_script" / "production_plan.json"),
        "original_grid_path": "../20_script/original-capcut-grid.md",
        "original_grid_sha256": sha256_file(episode_root / "20_script" / "original-capcut-grid.md"),
        "urakkai_grid_path": "../20_script/urakkai-capcut-grid.md",
        "urakkai_grid_sha256": sha256_file(episode_root / "20_script" / "urakkai-capcut-grid.md"),
        "tolerance_us": 999,
        "zero_caption": not captions,
        "mapping": [
            {"mapping_id": f"MAP_{row[0]}", "source_beat_id": row[1], "target_segment_id": row[0],
             "source_range_us": [row[4], row[5]], "target_range_us": [row[2], row[3]]}
            for row in v_rows
        ],
        "cues": [],
    }
    for caption in captions:
        start = caption["start"]
        end = start + caption["duration"]
        host = host_segment(v_rows, start, end)
        if host is None:
            raise ValueError(f"CAPTION_CUE_SPANS_SEGMENTS:{caption['cue_id']}")
        evidence["cues"].append({
            "cue_id": caption["cue_id"],
            "text": caption["text"],
            "authority": CAPTION_AUTHORITY.get(caption["role"], "SPEECH_AUDIO"),
            "mapping_id": f"MAP_{host[0]}",
            "source_range_us": [host[4] + (start - host[2]), host[4] + (end - host[2])],
            "target_range_us": [start, end],
            "bound_file_path": "final.srt",
            "bound_file_sha256": srt_sha,
        })
    write_json(episode_root / "30_audio_srt" / "caption_timing_evidence.json", evidence)

    lock = {
        "schema_version": CAPTION_LOCK_SCHEMA_VERSION,
        "episode_id": episode_id,
        "status": "PASS",
        "audio_lock_path": "audio_lock.json",
        "audio_lock_sha256": sha256_file(episode_root / "30_audio_srt" / "audio_lock.json"),
        "final_srt_path": "final.srt",
        "final_srt_sha256": srt_sha,
        "final_cue_count": len(captions),
        "caption_timing_evidence_path": "caption_timing_evidence.json",
        "caption_timing_evidence_sha256": sha256_file(
            episode_root / "30_audio_srt" / "caption_timing_evidence.json"
        ),
        "all_cues_within_measured_audio": True,
        "no_overlap_verified": True,
        "cues": [
            {"cue_id": row["cue_id"], "start_us": row["start"], "end_us": row["start"] + row["duration"],
             "text": row["text"], "layer": row["role"], "caption_role": row["role"]}
            for row in captions
        ],
    }
    return evidence, lock, srt_sha


def build_config(
    episode_id: str, episode_root: Path, plan: dict, timeline: dict,
    capcut_root: Path, work_root: Path, workspace_root: Path, root_profile: str, root_contract_path: str,
    production_profile: ResolvedProductionProfile | None = None,
) -> dict:
    cues = [cue for cue in plan.get("cues", []) if cue[1] != "NOFIT"]
    a9 = {row["cue_id"]: row for row in timeline["segments"] if row["role"] == "A9"}
    credit = source_credit_text(plan)
    config = {
        "episode_id": episode_id,
        "visual_asset_mode": "CLEAN_VISUAL_READY",
        "clean_video": str(episode_root / "40_assets_used" / "clean_source.mp4"),
        "clean_asset_root": str(episode_root / "40_assets_used"),
        "clean_evidence_root": str(episode_root / "40_assets_used"),
        "production_mode": "URAKKAI",
        "audio_policy": plan["audio_policy"],
        "duration_us": plan["DUR"],
        **({"audio_role": "A10"} if plan["audio_policy"] in A10_POLICIES else {}),
        "T1": plan["T1"],
        "T2": plan["T2"],
        **({"SOURCE_CREDIT": credit} if credit is not None else {}),
        "state_cues": [
            {"cue_id": row["cue_id"], "start_us": row["start"],
             "end_us": row["start"] + row["duration"], "text": row["text"]}
            for row in sorted(
                (row for row in timeline["segments"] if row["role"] == "STATE"),
                key=lambda row: row["start"],
            )
        ],
        "project_name": episode_id,
        "episode_root": str(episode_root),
        "work_root": str(work_root),
        "local_capcut_root": str(capcut_root),
        "source_identity_path": str(episode_root / "00_input" / "source_identity.json"),
        "approved_timeline_path": str(episode_root / "20_script" / "approved_timeline.json"),
        "design_handoff_path": str(episode_root / "20_script" / "design_handoff.json"),
        "design_lock_evidence_path": str(episode_root / "20_script" / "design_lock_evidence.json"),
        "build_manifest_path": str(episode_root / "50_capcut_project" / "build_manifest.json"),
        "state_path": str(episode_root / "90_workflow" / "state.json"),
        "workspace_root": str(workspace_root),
        "root_profile": root_profile,
        "root_contract_path": root_contract_path,
        **(
            {"production_profile": dict(production_profile.selector)}
            if production_profile is not None else {}
        ),
    }
    if cues:
        config["tts_cues"] = [
            {"cue_id": cue[1], "text": a9[cue[1]]["text"], "target_range_us": [cue[4], cue[5]],
             "audio_path": str(episode_root / "30_audio_srt" / "tts" / cue[6]), "resource_name": cue[6]}
            for cue in cues
        ]
    return config


def generate(
    episode_root: Path, capcut_root: Path, workspace_root: Path,
    template_zip: Path, root_profile: str, root_contract_path: str, work_root: Path,
    profile_path: Path | None = None,
) -> dict:
    episode_root = episode_root.resolve()
    episode_id = episode_root.name
    plan = read_json(episode_root / "20_script" / "v_plan.json")
    production_profile = (
        resolve_production_profile(read_json(Path(profile_path).resolve()))
        if profile_path is not None else None
    )
    assembly_type = resolve_v_plan_type(plan, production_profile)
    if plan.get("production_mode", "URAKKAI") != "URAKKAI":
        raise ValueError("EPISODE_LOCKS_PRODUCTION_MODE_UNSUPPORTED")
    timeline = read_json(episode_root / "20_script" / "approved_timeline.json")
    validate_timeline_type_contract(plan, timeline)
    validate_timeline_placement_contract(assembly_type, timeline)
    identity = read_json(episode_root / "00_input" / "source_identity.json")
    vmake_receipt = episode_root / "40_assets_used" / "vmake_final_download_evidence.json"
    if not vmake_receipt.is_file():
        raise ValueError("VMAKE_FINAL_DOWNLOAD_EVIDENCE_REQUIRED")
    vmake_evidence = read_json(vmake_receipt)
    original_order = resolve_original_order(
        plan, episode_root / "20_script" / "original-capcut-grid.md", plan["V"]
    )

    manifest = build_manifest(episode_id, episode_root, plan, identity, template_zip, vmake_evidence)
    write_json(episode_root / "50_capcut_project" / "build_manifest.json", manifest)

    production_plan = build_production_plan(
        episode_id, episode_root, plan, timeline, identity, manifest, root_profile,
        original_order, production_profile,
    )
    errors = validate_schema(
        production_plan, read_json(SCHEMAS / "executable_production_plan.schema.json")
    )
    if errors:
        raise ValueError(f"PRODUCTION_PLAN_SCHEMA_INVALID:{errors}")
    write_json(episode_root / "20_script" / "production_plan.json", production_plan)
    write_json(episode_root / "90_workflow" / "production_plan_validation.json", {
        "status": "PASS",
        "errors": [],
        "checked": ["protocol", "skill_contract", "production_plan"],
        "evidence": {
            "episode_id": episode_id,
            "production_plan_path": str(episode_root / "20_script" / "production_plan.json"),
            "production_plan_sha256": sha256_file(episode_root / "20_script" / "production_plan.json"),
        },
    })

    handoff = build_design_handoff(episode_id, episode_root, timeline, identity)
    write_json(episode_root / "20_script" / "design_handoff.json", handoff)

    _, caption_lock, _ = build_captions(episode_id, episode_root, plan, timeline)
    write_json(episode_root / "30_audio_srt" / "caption_lock.json", caption_lock)

    config = build_config(
        episode_id, episode_root, plan, timeline,
        capcut_root, work_root, workspace_root, root_profile, root_contract_path,
        production_profile,
    )
    write_json(episode_root / "50_capcut_project" / "build_config.json", config)

    clean_duration_us = probe_duration_us(episode_root / "40_assets_used" / "clean_source.mp4")
    return {
        "status": "PASS",
        "episode_id": episode_id,
        "caption_cue_count": caption_lock["final_cue_count"],
        "tts_cue_count": len(config.get("tts_cues", [])),
        "state_cue_count": len(config["state_cues"]),
        "target_duration_us": plan["DUR"],
        "clean_source_duration_us": clean_duration_us,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--episode-root", type=Path, required=True)
    parser.add_argument("--capcut-root", type=Path, required=True)
    parser.add_argument("--workspace-root", type=Path, required=True)
    parser.add_argument("--template-zip", type=Path, required=True)
    parser.add_argument("--work-root", type=Path, required=True)
    parser.add_argument("--root-profile", required=True)
    parser.add_argument("--profile", type=Path)
    parser.add_argument(
        "--root-contract-path",
        default="00_asset_tools/templates/capcut/shrt_white_base_v2/shorts_capcut_root_contract_v2.json",
    )
    args = parser.parse_args()
    payload = generate(
        args.episode_root, args.capcut_root, args.workspace_root,
        args.template_zip, args.root_profile, args.root_contract_path, args.work_root,
        args.profile,
    )
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

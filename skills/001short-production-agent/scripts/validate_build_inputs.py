from __future__ import annotations

from pathlib import Path

from common import read_json, resolved_declared_path, result, sha256_file
from schema_runtime import validate_schema
from validate_audio_caption import validate_audio_caption


SKILL_ROOT = Path(__file__).resolve().parents[1]
BUILD_SCHEMA = SKILL_ROOT / "schemas" / "build_contract.schema.json"
TIMELINE_SCHEMA = SKILL_ROOT / "schemas" / "approved_timeline.schema.json"
DESIGN_LOCK_SCHEMA = SKILL_ROOT / "schemas" / "design_lock_evidence.schema.json"


def validate_build_inputs(
    caption_lock_path: Path,
    srt_path: Path,
    build_contract_path: Path,
    timeline_path: Path,
) -> dict:
    caption_lock_path = Path(caption_lock_path).resolve()
    srt_path = Path(srt_path).resolve()
    build_contract_path = Path(build_contract_path).resolve()
    timeline_path = Path(timeline_path).resolve()
    try:
        caption = read_json(caption_lock_path)
        contract = read_json(build_contract_path)
        timeline = read_json(timeline_path)
    except (OSError, ValueError, TypeError) as exc:
        return result([{"code": "BUILD_INPUTS_INPUT_INVALID", "detail": str(exc)}])
    errors: list[dict] = []
    if schema_errors := validate_schema(contract, read_json(BUILD_SCHEMA)):
        errors.append({"code": "BUILD_INPUTS_BUILD_CONTRACT_SCHEMA", "detail": schema_errors})
    if schema_errors := validate_schema(timeline, read_json(TIMELINE_SCHEMA)):
        errors.append({"code": "BUILD_INPUTS_TIMELINE_SCHEMA", "detail": schema_errors})
    if errors:
        return result(errors)
    required_links = (
        "approved_timeline_path",
        "approved_timeline_sha256",
        "audio_lock_path",
        "audio_lock_sha256",
        "caption_lock_path",
        "caption_lock_sha256",
        "final_srt_path",
        "final_srt_sha256",
    )
    if any(not contract.get(field) for field in required_links):
        errors.append({"code": "BUILD_INPUTS_BUILD_CONTRACT_LINKS_MISSING"})
        return result(errors)
    audio_lock = Path(contract["audio_lock_path"]).resolve()
    audio_caption_result = validate_audio_caption(audio_lock, caption_lock_path)
    errors.extend(audio_caption_result.get("errors", []))
    if audio_caption_result.get("status") != "PASS":
        return result(errors)
    if resolved_declared_path(caption_lock_path, caption["audio_lock_path"]) != audio_lock:
        errors.append({"code": "BUILD_INPUTS_AUDIO_LOCK_PATH_MISMATCH"})
    if not audio_lock.is_file() or sha256_file(audio_lock) != contract["audio_lock_sha256"]:
        errors.append({"code": "BUILD_INPUTS_AUDIO_LOCK_SHA_MISMATCH"})
    if Path(contract["caption_lock_path"]).resolve() != caption_lock_path or sha256_file(caption_lock_path) != contract["caption_lock_sha256"]:
        errors.append({"code": "BUILD_INPUTS_CAPTION_LOCK_SHA_MISMATCH"})
    if Path(contract["final_srt_path"]).resolve() != srt_path or not srt_path.is_file() or sha256_file(srt_path) != contract["final_srt_sha256"] or sha256_file(srt_path) != caption["final_srt_sha256"]:
        errors.append({"code": "BUILD_INPUTS_SRT_SHA_MISMATCH"})
    if Path(contract["approved_timeline_path"]).resolve() != timeline_path or sha256_file(timeline_path) != contract["approved_timeline_sha256"]:
        errors.append({"code": "BUILD_INPUTS_TIMELINE_SHA_MISMATCH"})
    design_lock_evidence = Path(contract["design_lock_evidence_path"]).resolve()
    design_lock = None
    if not design_lock_evidence.is_file() or sha256_file(design_lock_evidence) != contract["design_lock_evidence_sha256"]:
        errors.append({"code": "BUILD_INPUTS_DESIGN_LOCK_EVIDENCE_SHA_MISMATCH"})
    else:
        try:
            design_lock = read_json(design_lock_evidence)
        except (OSError, ValueError, TypeError) as exc:
            errors.append({"code": "BUILD_INPUTS_DESIGN_LOCK_EVIDENCE_INVALID", "detail": str(exc)})
        else:
            if schema_errors := validate_schema(design_lock, read_json(DESIGN_LOCK_SCHEMA)):
                errors.append({"code": "BUILD_INPUTS_DESIGN_LOCK_EVIDENCE_INVALID", "detail": schema_errors})
                design_lock = None
    episode_ids = {
        "build_contract": contract["episode_id"],
        "caption_lock": caption["episode_id"],
        "approved_timeline": timeline["episode_id"],
    }
    if design_lock is not None:
        episode_ids["design_lock_evidence"] = design_lock["episode_id"]
    if len(set(episode_ids.values())) != 1:
        errors.append({"code": "BUILD_INPUTS_EPISODE_ID_MISMATCH", "episode_ids": episode_ids})
    srt_cue_texts = {
        cue.get("text")
        for cue in caption.get("cues", [])
        if isinstance(cue, dict) and isinstance(cue.get("text"), str)
    }
    approved_text = contract.get("approved_text", [])
    for cue_text in srt_cue_texts:
        if cue_text not in approved_text:
            errors.append({"code": "BUILD_INPUTS_SUBTITLE_TEXT_NOT_IN_SRT", "text": cue_text})
            break
    approved_rows = timeline.get("segments", [])
    contract_rows = contract.get("timeline", [])
    approved_by_id = {row.get("segment_id"): row for row in approved_rows}
    contract_by_id = {row.get("segment_id"): row for row in contract_rows}
    locked_cue_ids = {row.get("cue_id") for row in caption.get("cues", [])}
    binding_cue_ids = {row.get("cue_id") for row in contract.get("caption_bindings", [])}
    if locked_cue_ids != binding_cue_ids or len(contract.get("caption_bindings", [])) != len(binding_cue_ids):
        errors.append({"code": "BUILD_INPUTS_CAPTION_BINDING_SET_MISMATCH"})
    # user_provided_media_overlay segments are appended to the built contract
    # (segment_id "USER_MEDIA::<overlay_id>") but are never part of the
    # locked approved_timeline.json - they're bound separately from
    # build_manifest. Only allow that specific, prefixed extra; any other
    # discrepancy still fails as a real mismatch.
    overlay_only_ids = {
        segment_id for segment_id in contract_by_id
        if segment_id not in approved_by_id
        and isinstance(segment_id, str) and segment_id.startswith("USER_MEDIA::")
    }
    if set(approved_by_id) != set(contract.get("approved_actual_order", [])) - overlay_only_ids:
        errors.append({"code": "BUILD_INPUTS_TIMELINE_ORDER_MISMATCH"})
    if set(approved_by_id) != set(contract_by_id) - overlay_only_ids:
        errors.append({"code": "BUILD_INPUTS_TIMELINE_CONTENT_MISMATCH"})
    else:
        for segment_id, approved in approved_by_id.items():
            planned = contract_by_id[segment_id]
            if any(approved.get(field) != planned.get(field) for field in ("segment_id", "role", "start", "duration")):
                errors.append({"code": "BUILD_INPUTS_TIMELINE_CONTENT_MISMATCH", "segment_id": approved.get("segment_id")})
    if errors:
        return result(errors)
    return result(
        [],
        {
            "episode_id": contract["episode_id"],
            "audio_lock_path": str(audio_lock),
            "audio_lock_sha256": sha256_file(audio_lock),
            "caption_lock_path": str(caption_lock_path),
            "caption_lock_sha256": sha256_file(caption_lock_path),
            "final_srt_path": str(srt_path),
            "final_srt_sha256": sha256_file(srt_path),
            "approved_timeline_path": str(timeline_path),
            "approved_timeline_sha256": sha256_file(timeline_path),
        },
    )

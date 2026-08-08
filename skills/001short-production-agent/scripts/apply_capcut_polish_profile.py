"""Apply the approved, repeatable CapCut polish profile to a closed draft.

This stores user-approved settings only.  It does not judge VMake or image quality.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import uuid
from pathlib import Path


W_FLASH = {
    "category_id": "100000", "category_name": "", "duration": 500000,
    "effect_id": "6724845376098013708", "is_ai_transition": False,
    "is_overlap": False, "name": "W Flash", "platform": "all",
    "request_id": "", "resource_id": "6724845376098013708",
    "source_platform": 1, "task_id": "", "third_resource_id": "6724845376098013708",
    "type": "transition", "video_path": "",
    "role": "SCREEN_EFFECT", "desc": "001short approved W Flash transition",
}


def _id(seed: str) -> str:
    return str(uuid.uuid5(uuid.NAMESPACE_URL, f"001short-polish/{seed}"))


def _read(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"JSON_OBJECT_REQUIRED:{path}")
    return value


def _write(path: Path, value: dict) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _content_documents(project: Path) -> list[Path]:
    root = _read(project / "draft_content.json")
    timeline_id = str(root.get("main_timeline_id") or root.get("id") or "")
    if not timeline_id:
        raise ValueError("MAIN_TIMELINE_ID_MISSING")
    candidates = [
        project / "draft_content.json", project / "draft_info.json", project / "template-2.tmp",
        *(project / "Timelines" / timeline_id / name for name in
          ("draft_content.json", "draft_info.json", "template-2.tmp", "template.json")),
    ]
    paths = []
    for path in candidates:
        try:
            value = _read(path)
        except (OSError, ValueError, json.JSONDecodeError):
            continue
        if isinstance(value.get("tracks"), list) and isinstance(value.get("materials"), dict):
            paths.append(path)
    return sorted(set(paths))


def _material_index(materials: dict) -> dict[str, tuple[str, dict]]:
    return {
        row["id"]: (group, row)
        for group, rows in materials.items() if isinstance(rows, list)
        for row in rows if isinstance(row, dict) and isinstance(row.get("id"), str)
    }


def _ensure_ref_material(materials: dict, segment: dict, group: str, kind: str, data: dict) -> dict:
    materials.setdefault(group, [])
    index = _material_index(materials)
    refs = segment.setdefault("extra_material_refs", [])
    row = next((index[ref][1] for ref in refs if ref in index and index[ref][0] == group
                and index[ref][1].get("type") == kind), None)
    if row is None:
        row = {
            "id": _id(f"{segment.get('id')}/{group}/{kind}"), "type": kind,
            "role": segment.get("role", "SCREEN_EFFECT"),
            "desc": f"001short approved {kind}",
        }
        materials[group].append(row)
        refs.append(row["id"])
    row.setdefault("role", segment.get("role", "SCREEN_EFFECT"))
    row.setdefault("desc", f"001short approved {kind}")
    row.update(data)
    return row


def _ensure_effect(materials: dict, segment: dict, effect_type: str, value: float) -> None:
    _ensure_ref_material(materials, segment, "effects", effect_type, {
        "effect_id": "7501974767453474064", "resource_id": "7501974767453474064",
        "value": value, "visible": True, "apply_target_type": 0,
        "platform": "all", "source_platform": 1,
    })


def _ensure_transition(materials: dict, segment: dict) -> None:
    materials.setdefault("transitions", [])
    index = _material_index(materials)
    refs = segment.setdefault("extra_material_refs", [])
    row = next((index[ref][1] for ref in refs if ref in index and index[ref][0] == "transitions"), None)
    if row is None:
        row = {**W_FLASH, "id": _id(f"{segment.get('id')}/transition")}
        materials["transitions"].append(row)
        refs.append(row["id"])
    keep_id = row["id"]
    row.clear(); row.update({**W_FLASH, "id": keep_id})


def _ensure_loudness(materials: dict, segment: dict, material: dict) -> None:
    _ensure_ref_material(materials, segment, "loudnesses", "loudness", {
        "enable": True, "file_id": Path(str(material.get("path", "audio"))).stem,
        "loudness_param": None, "target_loudness": -14.0,
        "time_range": dict(segment.get("target_timerange", {})),
    })


def _remove_vocal_retain_metadata(materials: dict, segment: dict) -> None:
    index = _material_index(materials)
    refs = segment.get("extra_material_refs", [])
    if not isinstance(refs, list):
        return
    removed = {
        ref for ref in refs
        if ref in index and index[ref][0] == "vocal_separations"
        and index[ref][1].get("type") == "vocal_separation"
    }
    if not removed:
        return
    segment["extra_material_refs"] = [ref for ref in refs if ref not in removed]
    still_referenced = {
        ref for track in materials.get("_tracks_for_ref_scan", []) if isinstance(track, dict)
        for row in track.get("segments", []) if isinstance(row, dict)
        for ref in row.get("extra_material_refs", []) if isinstance(ref, str)
    }
    rows = materials.get("vocal_separations", [])
    if isinstance(rows, list):
        materials["vocal_separations"] = [
            row for row in rows
            if not (row.get("id") in removed and row.get("id") not in still_referenced)
        ]


def _range(segment: dict) -> tuple[int, int]:
    value = segment.get("target_timerange", {})
    start = int(value.get("start", 0))
    return start, start + int(value.get("duration", 0))


def _apply(value: dict) -> dict[str, int]:
    materials = value["materials"]
    # Legacy profiles wrote a CapCut-only vocal-retain marker. It is not an
    # audio separator, so remove it while preserving actual A10 media.
    materials["_tracks_for_ref_scan"] = value["tracks"]
    index = _material_index(materials)
    a9_ranges: list[tuple[int, int]] = []
    videos: list[tuple[dict, dict]] = []
    audio: list[tuple[dict, dict, bool]] = []
    for track in value["tracks"]:
        for segment in track.get("segments", []):
            material = index.get(segment.get("material_id"), ("", {}))[1]
            name = Path(str(material.get("path", ""))).name.casefold()
            is_a9 = segment.get("role") == "A9" or "tts_narrator" in name
            is_source = segment.get("role") in {"A10", "A11"} or any(
                token in name for token in ("source_audio", "a10_vocal_stem")
            )
            if is_a9:
                a9_ranges.append(_range(segment))
            if material.get("type") == "video":
                videos.append((segment, material))
            if material.get("type") in {"audio", "music", "extract_music"}:
                audio.append((segment, material, is_source))
    for order, (segment, material) in enumerate(videos):
        material.setdefault("video_algorithm", {})["quality_enhance"] = {"level": 3, "from": "multi_track"}
        _ensure_effect(materials, segment, "smart_color_adjust", 0.42 if order % 2 == 0 else 0.47)
        _ensure_effect(materials, segment, "sharpen", 0.50)
        _ensure_effect(materials, segment, "clear", 0.50)
        if order < len(videos) - 1:
            _ensure_transition(materials, segment)
    for segment, material, is_source in audio:
        _ensure_loudness(materials, segment, material)
        if is_source:
            start, end = _range(segment)
            segment["volume"] = 0.0 if any(start < a9_end and a9_start < end for a9_start, a9_end in a9_ranges) else 1.0
            _remove_vocal_retain_metadata(materials, segment)
    materials.pop("_tracks_for_ref_scan", None)
    return {"video_segments": len(videos), "audio_segments": len(audio), "a9_ranges": len(a9_ranges)}


def apply_project(project: Path) -> dict:
    project = Path(project).resolve()
    documents = _content_documents(project)
    if not documents:
        raise ValueError("CAPCUT_CONTENT_DOCUMENTS_MISSING")
    changed, counts = [], {"video_segments": 0, "audio_segments": 0, "a9_ranges": 0}
    for path in documents:
        value = _read(path)
        result = _apply(value)
        _write(path, value)
        for key, amount in result.items():
            counts[key] += amount
        changed.append({"path": str(path), "sha256": hashlib.sha256(path.read_bytes()).hexdigest()})
    return {"status": "PASS", "profile": "001short-capcut-polish-v3", "project": str(project), "documents": changed, **counts}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", type=Path, required=True)
    parser.add_argument("--receipt", type=Path, required=True)
    args = parser.parse_args()
    receipt = apply_project(args.project)
    args.receipt.parent.mkdir(parents=True, exist_ok=True)
    _write(args.receipt, receipt)
    print(json.dumps(receipt, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

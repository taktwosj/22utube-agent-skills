from __future__ import annotations

import argparse
import json
import shutil
import subprocess
from pathlib import Path

from common import sha256_file, write_json
from validate_vocal_stem import validate_vocal_stem


def _capcut_open() -> bool:
    completed = subprocess.run(
        ["tasklist", "/fo", "csv", "/nh"], capture_output=True, text=True, check=False
    )
    names = completed.stdout.casefold()
    return "capcut.exe" in names or "lveditor.exe" in names


def _load(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise RuntimeError("DRAFT_CONTENT_INVALID")
    return value


def _material_rows(materials: object) -> list[dict]:
    if not isinstance(materials, dict):
        return []
    rows: list[dict] = []
    for value in materials.values():
        if isinstance(value, list):
            rows.extend(row for row in value if isinstance(row, dict))
    return rows


def rebind(draft: Path, manifest_path: Path, *, dry_run: bool) -> dict:
    if _capcut_open():
        raise RuntimeError("CAPCUT_PROCESS_OPEN")
    draft = draft.resolve()
    content_path = draft / "draft_content.json"
    media_root = draft / "Resources" / "media"
    if not content_path.is_file() or not media_root.is_dir():
        raise RuntimeError("DRAFT_LAYOUT_INVALID")

    stem = validate_vocal_stem(manifest_path)
    if stem["status"] != "PASS":
        raise RuntimeError(f"VOCAL_STEM_INVALID:{stem['errors']}")
    manifest = _load(manifest_path.resolve())
    vocals = Path(stem["evidence"]["a10_audio_path"]).resolve()
    duration_us = int(manifest["vocals_duration_us"])

    payload = _load(content_path)
    tracks = payload.get("tracks")
    if not isinstance(tracks, list):
        raise RuntimeError("DRAFT_TRACKS_INVALID")
    audio_tracks = [track for track in tracks if isinstance(track, dict) and track.get("type") == "audio" and track.get("segments")]
    if len(audio_tracks) != 1:
        raise RuntimeError("EXISTING_DRAFT_AUDIO_TRACK_AMBIGUOUS")
    audio_segments = audio_tracks[0]["segments"]
    if not all(isinstance(segment, dict) for segment in audio_segments):
        raise RuntimeError("EXISTING_DRAFT_AUDIO_SEGMENT_INVALID")
    material_ids = {segment.get("material_id") for segment in audio_segments}
    if len(material_ids) != 1 or not isinstance(next(iter(material_ids)), str):
        raise RuntimeError("EXISTING_DRAFT_AUDIO_MATERIAL_AMBIGUOUS")
    material_id = next(iter(material_ids))
    max_source_end = max(
        int(segment["source_timerange"]["start"]) + int(segment["source_timerange"]["duration"])
        for segment in audio_segments
    )
    if duration_us + 100_000 < max_source_end:
        raise RuntimeError("VOCAL_STEM_TOO_SHORT_FOR_EXISTING_A10")

    rows = [row for row in _material_rows(payload.get("materials")) if row.get("id") == material_id]
    if not rows or not all(isinstance(row.get("path"), str) and "/Resources/media/" in row["path"] for row in rows):
        raise RuntimeError("EXISTING_DRAFT_AUDIO_MATERIAL_NOT_PORTABLE")
    prefix = rows[0]["path"].split("/Resources/media/", 1)[0]
    portable_path = f"{prefix}/Resources/media/source_vocals.wav"
    destination = media_root / "source_vocals.wav"
    if destination.exists() and sha256_file(destination) != sha256_file(vocals):
        raise RuntimeError("EXISTING_STEM_DESTINATION_CONFLICT")
    backup = draft / "draft_content.pre_vocal_stem.json"
    receipt = draft / "vocal_stem_rebind_receipt.json"
    if backup.exists() or receipt.exists():
        raise RuntimeError("EXISTING_VOCAL_STEM_REBIND_EVIDENCE")

    for row in rows:
        row["name"] = "source_vocals.wav"
        row["path"] = portable_path
        row["duration"] = duration_us
        row["role"] = "A10"
        row["desc"] = "001short production A10 Demucs vocal stem"
    for segment in audio_segments:
        segment["role"] = "A10"
    if dry_run:
        return {
            "status": "DRY_RUN_PASS",
            "audio_segments": len(audio_segments),
            "material_id": material_id,
            "vocals": str(vocals),
            "portable_path": portable_path,
            "max_source_end_us": max_source_end,
            "vocals_duration_us": duration_us,
        }

    shutil.copy2(content_path, backup)
    if not destination.exists():
        shutil.copy2(vocals, destination)
    write_json(content_path, payload)
    observed = _load(content_path)
    observed_tracks = [track for track in observed["tracks"] if track.get("type") == "audio" and track.get("segments")]
    observed_segments = observed_tracks[0]["segments"] if len(observed_tracks) == 1 else []
    observed_rows = [row for row in _material_rows(observed.get("materials")) if row.get("id") == material_id]
    if (
        len(observed_segments) != len(audio_segments)
        or any(segment.get("role") != "A10" for segment in observed_segments)
        or not observed_rows
        or any(row.get("path") != portable_path or row.get("role") != "A10" for row in observed_rows)
        or sha256_file(destination) != sha256_file(vocals)
    ):
        raise RuntimeError("VOCAL_STEM_REBIND_READBACK_FAILED")
    receipt_payload = {
        "status": "STEM_REBOUND_NOT_GUI_VERIFIED",
        "draft_content_backup": str(backup),
        "draft_content_sha256_before": sha256_file(backup),
        "draft_content_sha256_after": sha256_file(content_path),
        "vocal_stem_manifest": str(manifest_path.resolve()),
        "vocal_stem_manifest_sha256": sha256_file(manifest_path.resolve()),
        "a10_audio_path": str(destination),
        "a10_audio_sha256": sha256_file(destination),
        "a10_segment_count": len(observed_segments),
        "a12_policy": "EMPTY",
        "next_gate": "WAIT_CAPCUT_GUI_REOPEN_PREVIEW",
    }
    write_json(receipt, receipt_payload)
    return receipt_payload


def main() -> int:
    parser = argparse.ArgumentParser(description="Replace one existing portable A10 source-audio material with a validated Demucs vocal stem.")
    parser.add_argument("--draft", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    try:
        output = rebind(args.draft, args.manifest, dry_run=args.dry_run)
    except (OSError, RuntimeError, KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
        print(json.dumps({"status": "FAIL", "error": str(exc)}, ensure_ascii=False))
        return 1
    print(json.dumps(output, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

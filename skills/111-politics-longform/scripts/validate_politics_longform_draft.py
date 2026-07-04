#!/usr/bin/env python3
"""Validate a politics-longform CapCut draft copied from jungchilong."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
from pathlib import Path
from typing import Any

from scan_forbidden_capcut_refs import scan_tree


MEDIA_EXTENSIONS = (".mp4", ".mov", ".m4v", ".mkv", ".wav", ".mp3", ".aac", ".m4a")
OLD_ACTIVE_PATTERNS = [
    re.compile(r"YP007", re.IGNORECASE),
    re.compile(r"YP005", re.IGNORECASE),
    re.compile(r"YM007", re.IGNORECASE),
    re.compile(r"YP_ROH_YSM_.*정치롱폼기본", re.IGNORECASE),
    re.compile(r"정치롱폼기준(?:[_\\/\-]|$)", re.IGNORECASE),
    re.compile(r"capcut_drafts[\\/]+YP_", re.IGNORECASE),
]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def collect_strings(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        out: list[str] = []
        for item in value:
            out.extend(collect_strings(item))
        return out
    if isinstance(value, dict):
        out: list[str] = []
        for item in value.values():
            out.extend(collect_strings(item))
        return out
    return []


def looks_like_media_path(text: str) -> bool:
    low = text.lower()
    return any(ext in low for ext in MEDIA_EXTENSIONS)


def normalize_path(text: str) -> str:
    return text.replace("\\", "/")


def resolve_path(text: str, draft: Path) -> Path | None:
    cleaned = text.strip().strip('"')
    if cleaned.startswith("file://"):
        cleaned = cleaned[7:]
    if re.match(r"^[A-Za-z]:[\\/]", cleaned):
        return Path(cleaned)
    if cleaned.startswith("/") or cleaned.startswith("\\\\"):
        return Path(cleaned)
    if looks_like_media_path(cleaned):
        return draft / cleaned
    return None


def material_paths(draft_json: dict[str, Any]) -> dict[str, list[str]]:
    mapping: dict[str, list[str]] = {}
    for material in draft_json.get("materials", {}).get("videos", []):
        mid = material.get("id")
        if not isinstance(mid, str):
            continue
        paths = [s for s in collect_strings(material) if looks_like_media_path(s)]
        mapping[mid] = paths
    return mapping


def active_video_material_ids(draft_json: dict[str, Any]) -> list[str]:
    ids: list[str] = []
    for track in draft_json.get("tracks", []):
        if track.get("type") != "video":
            continue
        for seg in track.get("segments", []):
            for key in ("material_id", "materialID"):
                value = seg.get(key)
                if isinstance(value, str):
                    ids.append(value)
            refs = seg.get("extra_material_refs")
            if isinstance(refs, list):
                ids.extend([x for x in refs if isinstance(x, str)])
    return ids


def load_manifest_paths(manifest: Path | None) -> set[str]:
    if not manifest or not manifest.exists():
        return set()
    try:
        data = json.loads(manifest.read_text(encoding="utf-8"))
    except Exception:
        return set()
    return {normalize_path(s).lower() for s in collect_strings(data) if looks_like_media_path(s)}


def validate_draft(draft: Path, manifest: Path | None = None, require_locked_clips: bool = False) -> dict[str, Any]:
    result: dict[str, Any] = {
        "status": "PASS",
        "draft": str(draft),
        "errors": [],
        "warnings": [],
        "gates": {},
    }

    def error(code: str, detail: str, path: str | Path = "") -> None:
        result["errors"].append({"code": code, "path": str(path), "detail": detail})

    def warn(code: str, detail: str, path: str | Path = "") -> None:
        result["warnings"].append({"code": code, "path": str(path), "detail": detail})

    if not draft.exists():
        error("MISSING_DRAFT", "draft folder does not exist", draft)
        result["status"] = "FAIL"
        return result

    scan = scan_tree(draft)
    result["gates"]["episode_draft_clean_copy"] = scan["status"]
    result["scan"] = scan
    if scan["status"] != "PASS":
        error("FAIL_EPISODE_DRAFT_DIRTY_COPY", "dirty copy scan failed")

    root_content = draft / "draft_content.json"
    root_tmp = draft / "template-2.tmp"
    mirror_files = [root_content, root_tmp]
    mirror_files.extend(draft.glob("Timelines/*/draft_content.json"))
    mirror_files.extend(draft.glob("Timelines/*/template-2.tmp"))
    missing = [p for p in mirror_files if not p.exists()]
    if missing:
        for path in missing:
            error("MISSING_JSON_MIRROR", "required CapCut JSON mirror missing", path)
    else:
        hashes = {str(p): sha256(p) for p in mirror_files}
        result["mirror_hashes"] = hashes
        if len(set(hashes.values())) != 1:
            error("FAIL_JSON_MIRROR_MD5", "draft_content/template-2/Timelines mirrors differ")
        else:
            result["gates"]["json_mirror_md5"] = "PASS"

    try:
        draft_json = json.loads(root_content.read_text(encoding="utf-8"))
    except Exception as exc:
        error("JSON_PARSE_FAILED", str(exc), root_content)
        draft_json = {}

    id_to_paths = material_paths(draft_json)
    active_ids = active_video_material_ids(draft_json)
    result["active_video_material_ids"] = active_ids
    active_paths: list[str] = []
    for mid in active_ids:
        active_paths.extend(id_to_paths.get(mid, []))
    result["active_video_paths"] = active_paths

    if not active_ids:
        error("NO_ACTIVE_VIDEO_TRACK", "no active video material ids found")
    if not active_paths:
        error("NO_ACTIVE_VIDEO_PATHS", "active video materials do not expose media paths")

    allowed = load_manifest_paths(manifest)
    for raw in active_paths:
        normalized = normalize_path(raw)
        for pattern in OLD_ACTIVE_PATTERNS:
            if pattern.search(normalized):
                error("OLD_ACTIVE_MEDIA_REF", f"active media matched {pattern.pattern}", raw)
                break
        resolved = resolve_path(raw, draft)
        if resolved and not resolved.exists():
            if re.match(r"^[A-Za-z]:[\\/]", raw) or raw.startswith(("/", "\\\\")):
                error("ACTIVE_MEDIA_MISSING", "active media path does not exist", raw)
            else:
                warn("ACTIVE_MEDIA_UNRESOLVED", "active media path could not be resolved as local file", raw)
        if require_locked_clips and raw.lower().endswith(".mp4") and not raw.lower().endswith("_locked.mp4"):
            if "subscribe" not in raw.lower() and "placeholder" not in raw.lower():
                error("ACTIVE_MEDIA_NOT_LOCKED_CLIP", "episode video track should use *_locked.mp4", raw)
        if allowed and not any(normalized.lower().endswith(p.split("/")[-1]) for p in allowed):
            warn("ACTIVE_MEDIA_NOT_IN_MANIFEST", "active media not listed in source manifest by filename", raw)

    cache_roots = []
    cache_roots.extend([p for p in draft.glob("{*}/materials") if p.exists()])
    cache_roots.extend([p for p in draft.glob("{*}/Resources") if p.exists()])
    cache_roots.extend([p for p in draft.glob("{*}/common_attachment") if p.exists()])
    cache_roots.extend([draft / "Resources", draft / "common_attachment", draft / "subdraft"])
    cache_media: list[str] = []
    cache_errors = 0
    for root in cache_roots:
        if not root.exists():
            continue
        for path in root.rglob("*"):
            if path.is_file() and looks_like_media_path(path.name):
                cache_media.append(str(path))
                for pattern in OLD_ACTIVE_PATTERNS:
                    if pattern.search(normalize_path(str(path))):
                        cache_errors += 1
                        error("CACHE_FOLDER_OLD_REFERENCE", f"cache media matched {pattern.pattern}", path)
    result["cache_media_count"] = len(cache_media)
    result["gates"]["cache_folder_scan"] = "PASS" if cache_errors == 0 else "FAIL"

    if result["errors"]:
        result["status"] = "FAIL"
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--draft", required=True)
    parser.add_argument("--manifest")
    parser.add_argument("--require-locked-clips", action="store_true")
    args = parser.parse_args()

    result = validate_draft(
        Path(args.draft),
        Path(args.manifest) if args.manifest else None,
        require_locked_clips=args.require_locked_clips,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    os.environ.setdefault("PYTHONUTF8", "1")
    sys.exit(main())

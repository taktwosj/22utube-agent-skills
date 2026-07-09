#!/usr/bin/env python3
"""Validate active CapCut media links for source-derived Shorts drafts."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


class GateFail(Exception):
    pass


SOURCE_VIDEO_ROLES = {"source_video", "V8", "source_clip"}


def load_json(path: Path, label: str) -> dict[str, Any]:
    if not path.exists():
        raise GateFail(f"FAIL_MEDIA_LINK: {label} missing: {path}")
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(data, dict):
        raise GateFail(f"FAIL_MEDIA_LINK: {label} root must be object")
    return data


def as_path(root: Path, raw_path: str | Path) -> Path:
    path = Path(raw_path)
    return path if path.is_absolute() else root / path


def material_path(material: dict[str, Any]) -> str:
    for key in ("path", "local_path", "file_path", "material_path"):
        value = material.get(key)
        if isinstance(value, str) and value.strip():
            return value
    return ""


def active_materials(data: dict[str, Any]) -> list[dict[str, Any]]:
    materials = data.get("active_materials")
    if isinstance(materials, list):
        return [item for item in materials if isinstance(item, dict)]
    result: list[dict[str, Any]] = []
    materials_root = data.get("materials")
    if isinstance(materials_root, dict):
        for value in materials_root.values():
            if isinstance(value, list):
                result.extend(item for item in value if isinstance(item, dict))
    return result


def is_source_video_material(material: dict[str, Any]) -> bool:
    role = str(material.get("role") or material.get("track_id") or material.get("track") or "")
    return role in SOURCE_VIDEO_ROLES or material.get("is_source_video") is True


def validate_capcut_media_links(
    root: Path,
    draft_content_path: Path,
    source_path: Path,
    virtual_store_path: Path | None = None,
) -> dict[str, Any]:
    root = Path(root)
    source_path = as_path(root, source_path)
    if not source_path.exists():
        raise GateFail(f"FAIL_MEDIA_LINK: source media missing: {source_path}")
    draft = load_json(as_path(root, draft_content_path), "draft_content.json")
    if virtual_store_path is not None and as_path(root, virtual_store_path).exists():
        load_json(as_path(root, virtual_store_path), "draft_virtual_store.json")

    materials = active_materials(draft)
    if not materials:
        raise GateFail("FAIL_MEDIA_LINK: active materials missing")

    source_linked = False
    for material in materials:
        if not material.get("active", True):
            continue
        raw_path = material_path(material)
        if not raw_path:
            raise GateFail("FAIL_MEDIA_LINK: active material path missing")
        resolved = as_path(root, raw_path)
        if not resolved.exists():
            raise GateFail(f"FAIL_MEDIA_LINK: active material path missing on disk: {resolved}")
        if str(resolved.resolve()).lower() == str(source_path.resolve()).lower():
            source_linked = True
        placeholder = str(material.get("placeholder") or material.get("placeholder_id") or "")
        if placeholder or "placeholder" in raw_path.lower():
            raise GateFail("FAIL_PLACEHOLDER_MEDIA_ACTIVE: template placeholder media is active")
        if is_source_video_material(material):
            caption_type = str(material.get("caption_type") or material.get("audio_policy") or "")
            audio_enabled = material.get("audio_enabled", material.get("source_video_audio_enabled", False))
            speaker_allowed = (
                caption_type == "speaker_quote"
                or str(material.get("audio_policy") or "") in {"speaker_source", "source_audio_on"}
            )
            if audio_enabled is True and not speaker_allowed:
                raise GateFail(
                    "FAIL_SOURCE_VIDEO_AUDIO_NOT_MUTED: source-video embedded audio must be muted by default"
                )

    if not source_linked:
        raise GateFail("FAIL_MEDIA_LINK: active source video does not point to source media")
    return {"capcut_media_links_status": "PASS", "source_media_path": str(source_path)}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--draft-content", default="50_capcut_project/draft_content.json")
    parser.add_argument("--source", default="00_source/source.mp4")
    parser.add_argument("--virtual-store", default="")
    args = parser.parse_args()
    try:
        result = validate_capcut_media_links(
            Path(args.root),
            Path(args.draft_content),
            Path(args.source),
            Path(args.virtual_store) if args.virtual_store else None,
        )
    except GateFail as exc:
        print(str(exc))
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

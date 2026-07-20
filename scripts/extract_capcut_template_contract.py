"""Extract a CapCut template slot contract from a pinned CapCut draft archive.

This is a deterministic extractor: it reads the real draft_content.json and
timeline metadata from a ZIP archive and emits a contract manifest with the
actual slot values (no EXTRACT_FROM_ROOT placeholders, no example numbers).

Usage:
    python scripts/extract_capcut_template_contract.py \
        --archive <archive.zip> \
        --template-id <template_id> \
        --manifest <existing_manifest_or_empty> \
        --output <contract.json>

The extractor never opens CapCut, never mutates the local CapCut user data,
and never makes external calls. SHRTJUNGCHI GUI restore state is recorded as
NOT_RUN by callers; this script only reads the archive.

Slot value extraction covers the CapCut draft_content.json schema:
- materials.texts[*] -> font_size, alignment, text_alpha (opacity),
  initial_scale, font_resource_id, font_path, text_color, line_max_width,
  background_* (text box geometry), global_alpha
- tracks[*] (text) -> segment.transform (x, y, scale_x, scale_y, rotation)
  and segment.clip (start/end timing), render_index, layer ordering
- tracks[*] (video/audio/effect) -> layer order and material role hints
- materials.videos/audios/images -> file path, source duration, media fingerprint

Material classification policy is encoded per-template in the contract config.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import zipfile
from pathlib import Path
from typing import Any


# Classification policy: which template materials are reusable, which must be
# replaced, which are reference-only, and which must never appear in output.
# Per NORM-002/NORM-006 and section 41.5 of the V2 design doc.
DEFAULT_CLASSIFICATION = {
    # Shrt white must keep its internal transparent PNG and must not reference
    # any Cache/onlineMaterial.
    "shrt_white_base_v1": {
        "fixed_reusable_substrings": [
            "Resources/media/transparent_center_white_1080x1920.png",
        ],
        "replace_required_keywords": ["test.mp4", "placeholder"],
        "reference_only_keywords": [],
        "forbidden_in_output_substrings": [
            "Cache/onlineMaterial",
            "/Cache/onlineMaterial",
        ],
    },
    "jungchilong_base_v3_intro15": {
        "fixed_reusable_substrings": [],
        "replace_required_keywords": ["test.mp4", "placeholder"],
        "reference_only_keywords": [],
        "forbidden_in_output_substrings": [
            "Cache/onlineMaterial",
            "/Cache/onlineMaterial",
        ],
    },
    "shrtjungchi_base_v1": {
        "fixed_reusable_substrings": [],
        "replace_required_keywords": ["test.mp4", "placeholder"],
        "reference_only_keywords": [],
        "forbidden_in_output_substrings": [
            "Cache/onlineMaterial",
            "/Cache/onlineMaterial",
        ],
    },
}

# Locked text slot fields. These must not change between the pinned root and
# any episode clone. (V2 design section 39, 41.)
LOCKED_TEXT_FIELDS = [
    "transform_x",
    "transform_y",
    "scale_x",
    "scale_y",
    "rotation",
    "font_resource_id",
    "font_size",
    "initial_scale",
    "alignment",
    "global_alpha",
    "line_max_width",
    "layer_index",
    "track_order",
]

LOCKED_MEDIA_FIELDS = [
    "layer_index",
    "track_order",
    "source_duration_us",
    "media_fingerprint",
]


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest().upper()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


def _draft_root_name(archive_path: Path) -> str:
    """The top-level folder name inside the CapCut draft archive."""
    with zipfile.ZipFile(archive_path) as zf:
        names = zf.namelist()
    roots = sorted({n.split("/", 1)[0] for n in names if "/" in n})
    if len(roots) != 1:
        raise ValueError(
            f"STOP_TEMPLATE_ARCHIVE_STRUCTURE_AMBIGUOUS roots={roots}"
        )
    return roots[0]


def _load_draft_content(archive_path: Path, root: str) -> dict:
    with zipfile.ZipFile(archive_path) as zf:
        data = zf.read(f"{root}/draft_content.json")
    return json.loads(data.decode("utf-8"))


def _load_timeline_mirror(archive_path: Path, root: str) -> dict | None:
    """Some archives ship a top-level timeline_layout.json mirror."""
    path = f"{root}/timeline_layout.json"
    with zipfile.ZipFile(archive_path) as zf:
        if path in zf.namelist():
            return json.loads(zf.read(path).decode("utf-8"))
    return None


def _parse_text_content(raw: str) -> dict:
    """The text material 'content' field is itself a JSON string."""
    if not raw:
        return {}
    try:
        return json.loads(raw)
    except (ValueError, TypeError):
        return {"raw": raw}


def _clip_transform(segment: dict) -> dict:
    """CapCut draft_content schema: position/scale/rotation live inside
    segment.clip as {transform:{x,y}, scale:{x,y}, rotation, alpha}.
    Older export variants occasionally used a flat 6-tuple 'transform'; we
    support both so the extractor stays robust to the pinned archives."""
    clip = segment.get("clip") or {}
    if isinstance(clip, dict):
        transform = clip.get("transform") or {}
        scale = clip.get("scale") or {}
        return {
            "transform_x": float(transform.get("x", 0.0)),
            "transform_y": float(transform.get("y", 0.0)),
            "scale_x": float(scale.get("x", 1.0)),
            "scale_y": float(scale.get("y", 1.0)),
            "rotation": float(clip.get("rotation", 0.0)),
            "alpha": float(clip.get("alpha", 1.0)),
        }
    flat = segment.get("transform", [0.0, 0.0, 1.0, 1.0, 0.0, 0.0])
    return {
        "transform_x": float(flat[0]) if len(flat) > 0 else 0.0,
        "transform_y": float(flat[1]) if len(flat) > 1 else 0.0,
        "scale_x": float(flat[2]) if len(flat) > 2 else 1.0,
        "scale_y": float(flat[3]) if len(flat) > 3 else 1.0,
        "rotation": float(flat[4]) if len(flat) > 4 else 0.0,
        "alpha": 1.0,
    }


def _extract_text_slot(
    text_material: dict,
    track_index: int,
    segment: dict,
    layer_index: int,
) -> dict:
    content = _parse_text_content(text_material.get("content", ""))
    tx_values = _clip_transform(segment)
    clip = segment.get("clip") or {}
    slot = {
        "slot_id": text_material.get("id", ""),
        "material_role": "TEXT",
        "visible_text_role": content.get("text", ""),
        "layer_index": layer_index,
        "track_order": track_index,
        "transform_x": tx_values["transform_x"],
        "transform_y": tx_values["transform_y"],
        "scale_x": tx_values["scale_x"],
        "scale_y": tx_values["scale_y"],
        "rotation": tx_values["rotation"],
        "alpha": tx_values["alpha"],
        "font_resource_id": text_material.get("font_resource_id", ""),
        "font_path": text_material.get("font_path", ""),
        "font_size": text_material.get("font_size", 0.0),
        "initial_scale": text_material.get("initial_scale", 1.0),
        "alignment": text_material.get("alignment", 0),
        "text_color": text_material.get("text_color", ""),
        "global_alpha": text_material.get("global_alpha", 1.0),
        "text_alpha": text_material.get("text_alpha", 1.0),
        "line_max_width": text_material.get("line_max_width", 0.0),
        "background_style": text_material.get("background_style", 0),
        "background_width": text_material.get("background_width", 0.0),
        "background_height": text_material.get("background_height", 0.0),
        "background_round_radius": text_material.get(
            "background_round_radius", 0.0
        ),
        "target_timerange": segment.get("target_timerange"),
        "render_index": segment.get("render_index"),
        "locked_fields": list(LOCKED_TEXT_FIELDS),
    }
    return slot


def _extract_media_slot(
    material: dict,
    track_index: int,
    segment: dict,
    layer_index: int,
    role: str,
) -> dict:
    clip = segment.get("clip") or {}
    target_timerange = segment.get("target_timerange") or {}
    tx_values = _clip_transform(segment)
    return {
        "slot_id": material.get("id", ""),
        "material_role": role,
        "layer_index": layer_index,
        "track_order": track_index,
        "source_duration_us": material.get("duration", 0),
        "media_fingerprint": material.get("md5", "")
        or material.get("source_platform", ""),
        "file_path": material.get("path", "") or material.get("source", ""),
        "clip_start": target_timerange.get("start", 0),
        "clip_duration": target_timerange.get("duration", 0),
        "transform_x": tx_values["transform_x"],
        "transform_y": tx_values["transform_y"],
        "scale_x": tx_values["scale_x"],
        "scale_y": tx_values["scale_y"],
        "rotation": tx_values["rotation"],
        "alpha": tx_values["alpha"],
        "render_index": segment.get("render_index"),
        "locked_fields": list(LOCKED_MEDIA_FIELDS),
    }


def _classify_material(
    file_path: str,
    policy: dict,
) -> str:
    p = file_path or ""
    low = p.lower()
    for sub in policy.get("forbidden_in_output_substrings", []):
        if sub.lower() in low:
            return "FORBIDDEN_IN_OUTPUT"
    for sub in policy.get("fixed_reusable_substrings", []):
        if sub.lower() in low:
            return "FIXED_REUSABLE"
    for kw in policy.get("reference_only_keywords", []):
        if kw.lower() in low:
            return "REFERENCE_ONLY"
    for kw in policy.get("replace_required_keywords", []):
        if kw.lower() in low:
            return "REPLACE_REQUIRED"
    return "REPLACE_REQUIRED"


def extract_contract(
    archive_path: Path,
    template_id: str,
    template_display_name: str,
    gui_restore_state: str = "NOT_RUN",
    existing_manifest: dict | None = None,
) -> dict:
    if not archive_path.exists():
        raise FileNotFoundError(f"STOP_TEMPLATE_ARCHIVE_MISSING: {archive_path}")

    archive_hash = sha256_file(archive_path)
    root = _draft_root_name(archive_path)
    draft_content = _load_draft_content(archive_path, root)
    timeline_mirror = _load_timeline_mirror(archive_path, root)

    policy = DEFAULT_CLASSIFICATION.get(template_id, DEFAULT_CLASSIFICATION["shrt_white_base_v1"])

    # Build material lookup tables.
    materials = draft_content.get("materials", {})
    text_mats = {m.get("id"): m for m in materials.get("texts", [])}
    video_mats = {m.get("id"): m for m in materials.get("videos", [])}
    audio_mats = {m.get("id"): m for m in materials.get("audios", [])}
    image_mats = {m.get("id"): m for m in materials.get("images", [])}
    effect_mats = {m.get("id"): m for m in materials.get("effects", [])}

    slots: list[dict] = []
    material_classifications: dict[str, str] = {}
    forbidden_hits: list[dict] = []
    required_internal_asset_present = False

    # Walk tracks in order. Layer index = reverse of track order (CapCut:
    # higher track index renders on top).
    tracks = draft_content.get("tracks", [])
    n_tracks = len(tracks)
    for track_index, track in enumerate(tracks):
        ttype = track.get("type", "")
        layer_index = n_tracks - 1 - track_index
        for segment in track.get("segments", []):
            # CapCut draft_content schema: segments reference materials via
            # 'material_id'. Some older exports used 'target_material_id';
            # we accept both for robustness against the pinned archives.
            mat_id = (
                segment.get("material_id")
                or segment.get("target_material_id")
                or ""
            )
            if ttype == "text" and mat_id in text_mats:
                slot = _extract_text_slot(
                    text_mats[mat_id], track_index, segment, layer_index
                )
                slots.append(slot)
            elif ttype == "video" and mat_id in video_mats:
                mat = video_mats[mat_id]
                role = "VIDEO"
                slot = _extract_media_slot(
                    mat, track_index, segment, layer_index, role
                )
                slots.append(slot)
                fp = mat.get("path", "") or mat.get("source", "")
                cls = _classify_material(fp, policy)
                material_classifications[fp] = cls
                if cls == "FORBIDDEN_IN_OUTPUT":
                    forbidden_hits.append(
                        {"path": fp, "slot_id": mat.get("id", ""), "reason": cls}
                    )
            elif ttype == "audio" and mat_id in audio_mats:
                mat = audio_mats[mat_id]
                slot = _extract_media_slot(
                    mat, track_index, segment, layer_index, "AUDIO"
                )
                slots.append(slot)
                fp = mat.get("path", "") or mat.get("source", "")
                material_classifications[fp] = _classify_material(fp, policy)
            elif ttype == "effect" and mat_id in effect_mats:
                mat = effect_mats[mat_id]
                slot = _extract_media_slot(
                    mat, track_index, segment, layer_index, "EFFECT"
                )
                slots.append(slot)
            elif ttype in {"image", "sticker"} and mat_id in image_mats:
                mat = image_mats[mat_id]
                slot = _extract_media_slot(
                    mat, track_index, segment, layer_index, "IMAGE"
                )
                slots.append(slot)

    # Check required internal asset for shrt white.
    required_internal_asset = None
    if template_id == "shrt_white_base_v1":
        required_internal_asset = (
            "Resources/media/transparent_center_white_1080x1920.png"
        )
        with zipfile.ZipFile(archive_path) as zf:
            names = zf.namelist()
            required_internal_asset_present = any(
                required_internal_asset in n for n in names
            )
        # Also reject Cache/onlineMaterial references anywhere in materials.
        for collection in ("videos", "audios", "images"):
            for m in materials.get(collection, []):
                fp = m.get("path", "") or m.get("source", "")
                if fp and "Cache/onlineMaterial" in fp:
                    forbidden_hits.append(
                        {
                            "path": fp,
                            "slot_id": m.get("id", ""),
                            "reason": "CACHE_ONLINE_MATERIAL_REFERENCE",
                        }
                    )

    contract = {
        "schema_version": "capcut-template-contract-v1",
        "template_id": template_id,
        "template_display_name": template_display_name,
        "capcut_root_project_name": root,
        "extraction_source": {
            "archive_path": str(archive_path),
            "archive_sha256": archive_hash,
            "draft_root_inside_archive": root,
            "draft_content_entry": f"{root}/draft_content.json",
            "timeline_mirror_entry": (
                f"{root}/timeline_layout.json" if timeline_mirror else None
            ),
            "extractor": "scripts/extract_capcut_template_contract.py",
        },
        "gui_restore_state": gui_restore_state,
        "archive_integrity": "PASS_ARCHIVE_STRUCTURE_ONLY",
        "required_internal_asset": required_internal_asset,
        "required_internal_asset_present": required_internal_asset_present,
        "cache_online_material_referenced": bool(forbidden_hits),
        "forbidden_hits": forbidden_hits,
        "slots": slots,
        "material_classifications": material_classifications,
        "locked_fields_policy": {
            "text": LOCKED_TEXT_FIELDS,
            "media": LOCKED_MEDIA_FIELDS,
        },
    }
    if existing_manifest:
        contract["source_manifest_digest"] = {
            "manifest_sha256": sha256_bytes(
                json.dumps(existing_manifest, sort_keys=True).encode("utf-8")
            ),
        }
    return contract


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Extract a CapCut template slot contract from a pinned archive."
    )
    parser.add_argument("--archive", required=True, type=Path)
    parser.add_argument("--template-id", required=True)
    parser.add_argument("--template-display-name", required=True)
    parser.add_argument("--manifest", type=Path, default=None)
    parser.add_argument(
        "--gui-restore-state",
        default="NOT_RUN",
        choices=["NOT_RUN", "PASS", "FAIL"],
    )
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args(argv)

    existing = None
    if args.manifest and args.manifest.exists():
        existing = json.loads(args.manifest.read_text(encoding="utf-8"))

    contract = extract_contract(
        archive_path=args.archive,
        template_id=args.template_id,
        template_display_name=args.template_display_name,
        gui_restore_state=args.gui_restore_state,
        existing_manifest=existing,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(contract, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(f"WROTE {args.output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

"""Verify the deterministic parts of the approved Shorts polish profile."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from apply_capcut_polish_profile import _content_documents, _material_index, _range


def _refs(index: dict, segment: dict, group: str) -> list[dict]:
    return [index[ref][1] for ref in segment.get("extra_material_refs", [])
            if ref in index and index[ref][0] == group]


def validate_project(project: Path) -> dict:
    docs = _content_documents(Path(project))
    if not docs:
        return {"status": "FAIL", "errors": [{"code": "CAPCUT_CONTENT_DOCUMENTS_MISSING"}]}
    errors = []
    for path in docs:
        value = json.loads(path.read_text(encoding="utf-8"))
        index = _material_index(value["materials"])
        videos, a9_ranges, audio = [], [], []
        for track in value["tracks"]:
            for segment in track.get("segments", []):
                material = index.get(segment.get("material_id"), ("", {}))[1]
                name = Path(str(material.get("path", ""))).name.casefold()
                if segment.get("role") == "A9" or "tts_narrator" in name:
                    a9_ranges.append(_range(segment))
                if material.get("type") == "video":
                    videos.append((segment, material))
                if material.get("type") in {"audio", "music", "extract_music"}:
                    audio.append((segment, material, segment.get("role") in {"A10", "A11"} or "source_audio" in name))
        for order, (segment, material) in enumerate(videos):
            if material.get("video_algorithm", {}).get("quality_enhance", {}).get("level") != 3:
                errors.append({"code": "POLISH_AI_HD_MISSING", "segment": segment.get("id")})
            effects = {row.get("type"): row.get("value") for row in _refs(index, segment, "effects")}
            expected_color = 0.42 if order % 2 == 0 else 0.47
            if effects.get("smart_color_adjust") != expected_color or effects.get("sharpen") != 0.5 or effects.get("clear") != 0.5:
                errors.append({"code": "POLISH_VIDEO_ADJUSTMENT_MISSING", "segment": segment.get("id")})
            if order < len(videos) - 1 and not any(row.get("name") == "W Flash" for row in _refs(index, segment, "transitions")):
                errors.append({"code": "POLISH_W_FLASH_MISSING", "segment": segment.get("id")})
        for segment, material, is_source in audio:
            loudness = _refs(index, segment, "loudnesses")
            if not any(row.get("enable") is True and row.get("target_loudness") == -14.0 for row in loudness):
                errors.append({"code": "POLISH_LOUDNESS_MISSING", "segment": segment.get("id")})
            if is_source:
                start, end = _range(segment)
                expected_volume = 0.0 if any(start < b and a < end for a, b in a9_ranges) else 1.0
                if segment.get("volume") != expected_volume:
                    errors.append({"code": "POLISH_NARRATION_MUTE_MISSING", "segment": segment.get("id")})
                if _refs(index, segment, "vocal_separations"):
                    errors.append({"code": "POLISH_CAPCUT_VOCAL_METADATA_FORBIDDEN", "segment": segment.get("id")})
    return {"status": "PASS" if not errors else "FAIL", "errors": errors, "profile": "001short-capcut-polish-v3"}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", type=Path, required=True)
    args = parser.parse_args()
    result = validate_project(args.project)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())

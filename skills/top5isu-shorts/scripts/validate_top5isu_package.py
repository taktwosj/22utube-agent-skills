#!/usr/bin/env python3
"""Validate a portable top5isu root-template package."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import zipfile
from pathlib import Path, PurePosixPath
from typing import Any


class GateFail(Exception):
    pass


EXPECTED_TRACKS_V1 = ["IMAGE_EFFECT_PRESETS", "TTS", "T2", "T1", "LOGO"]
EXPECTED_TRACKS_V2 = ["IMAGE_EFFECT_PRESETS", "FRAME", "LOGO", "TTS_TEXT", "SOURCE_TEXT", "T2", "T1"]
HIGH_IMPACT_EFFECTS = {"불꽃 회오리", "불꽃 스와이프", "불꽃 마법"}


def fail(code: str, detail: str) -> None:
    raise GateFail(f"{code}: {detail}")


def read_object(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(data, dict):
        fail("FAIL_TOP5ISU_PORTABLE_PACKAGE", f"object required: {path.name}")
    return data


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def validate_top5isu_package(template_dir: Path) -> dict[str, Any]:
    template_dir = Path(template_dir)
    manifest_path = template_dir / "template_manifest.json"
    if not manifest_path.is_file():
        fail("FAIL_TOP5ISU_ARCHIVE_INTEGRITY", "template_manifest.json missing")
    manifest = read_object(manifest_path)
    archive_file = str(manifest.get("archive_file") or "")
    if not archive_file or Path(archive_file).name != archive_file or ".." in archive_file:
        fail("FAIL_TOP5ISU_PORTABLE_PACKAGE", "archive_file must be relative basename")
    archive = template_dir / archive_file
    if not archive.is_file():
        fail("FAIL_TOP5ISU_ARCHIVE_INTEGRITY", "archive missing")
    measured_sha = sha256(archive)
    if measured_sha.lower() != str(manifest.get("archive_sha256") or "").lower():
        fail("FAIL_TOP5ISU_ARCHIVE_INTEGRITY", "archive SHA256 mismatch")

    try:
        handle = zipfile.ZipFile(archive)
    except zipfile.BadZipFile as exc:
        fail("FAIL_TOP5ISU_ARCHIVE_INTEGRITY", str(exc))
    with handle as zf:
        bad_member = zf.testzip()
        if bad_member:
            fail("FAIL_TOP5ISU_ARCHIVE_INTEGRITY", f"corrupt member: {bad_member}")
        names = [name for name in zf.namelist() if not name.endswith("/")]
        expected_count = manifest.get("packaged_file_count")
        if not isinstance(expected_count, int) or len(names) != expected_count:
            fail("FAIL_TOP5ISU_ARCHIVE_INTEGRITY", "packaged_file_count mismatch")
        for name in names:
            pure = PurePosixPath(name)
            if pure.is_absolute() or ".." in pure.parts or re.match(r"^[A-Za-z]:", name):
                fail("FAIL_TOP5ISU_PORTABLE_PACKAGE", f"unsafe archive member: {name}")
            if name.lower().endswith(".bak"):
                fail("FAIL_TOP5ISU_PORTABLE_PACKAGE", f".bak present: {name}")
            if "top55_sample_image" in name.lower():
                fail("FAIL_TOP5ISU_SAMPLE_MEDIA", f"legacy stock sample present: {name}")
        profile = str(manifest.get("template_profile") or "")
        if profile == "top5isu_v2_top55":
            expected_tracks = EXPECTED_TRACKS_V2
        else:
            expected_tracks = EXPECTED_TRACKS_V1

        required = {
            "top5isu/draft_content.json",
            "top5isu/draft_meta_info.json",
            "top5isu/Resources/media/jungboitsu.png",
        }
        if profile == "top5isu_v2_top55":
            required.add("top5isu/Resources/media/transparent_center_black_1080x1920.png")
        missing = sorted(required - set(names))
        if missing:
            fail("FAIL_TOP5ISU_PORTABLE_PACKAGE", f"missing members: {missing}")

        for name in names:
            # Bundled CapCut effect metadata can retain vendor build-machine
            # paths. It is inert resource provenance, not an episode media
            # link. Portability checks apply to project control files.
            if name.startswith("top5isu/Resources/effects/"):
                continue
            if not name.lower().endswith((".json", ".tmp", ".md", ".txt")):
                continue
            try:
                text = zf.read(name).decode("utf-8")
            except (UnicodeDecodeError, KeyError):
                continue
            lowered = text.lower()
            if "coltsfoot flowers in spring" in lowered or "7339228024233086209" in text:
                fail("FAIL_TOP5ISU_SAMPLE_MEDIA", f"legacy stock identity present: {name}")
            mac_user_path = "/" + "Users" + r"/[^/]+/"
            if re.search(r"C:[/\\]Users[/\\]", text, re.I) or re.search(mac_user_path, text):
                fail("FAIL_TOP5ISU_PORTABLE_PACKAGE", f"foreign user path: {name}")

        content = json.loads(zf.read("top5isu/draft_content.json").decode("utf-8"))
        tracks = content.get("tracks") or []
        track_names = [track.get("name") for track in tracks]
        if track_names != expected_tracks:
            fail("FAIL_TOP5ISU_TRACK_MAPPING", f"unexpected tracks: {track_names}")
        canvas = content.get("canvas_config") or {}
        if canvas.get("width") != 1080 or canvas.get("height") != 1920:
            fail("FAIL_TOP5ISU_PORTABLE_PACKAGE", "canvas must be 1080x1920")
        duration = content.get("duration")
        image_segments = tracks[0].get("segments") or []
        if profile == "top5isu_v2_top55":
            if len(image_segments) != 4:
                fail("FAIL_TOP5ISU_TRACK_MAPPING", "four TOP55 animation prototype segments required")
            if "top5isu/key_value.json" in names:
                key_value = json.loads(zf.read("top5isu/key_value.json").decode("utf-8"))
                if key_value:
                    fail("FAIL_TOP5ISU_MATERIAL_CACHE", "root key_value.json must be empty")
            video_lookup = {
                str(item.get("id")): item
                for item in ((content.get("materials") or {}).get("videos") or [])
                if isinstance(item, dict)
            }
            prototype_material_ids: list[str] = []
            for segment in image_segments:
                material = video_lookup.get(str(segment.get("material_id"))) or {}
                external_id = str(material.get("material_id") or "")
                if not external_id:
                    fail("FAIL_TOP5ISU_MATERIAL_IDENTITY", "prototype material_id missing")
                prototype_material_ids.append(external_id)
                if material.get("source") != 0 or material.get("source_platform") != 0:
                    fail("FAIL_TOP5ISU_MATERIAL_IDENTITY", "prototype must be local media")
                if material.get("category_name") or material.get("is_copyright"):
                    fail("FAIL_TOP5ISU_MATERIAL_IDENTITY", "prototype retains stock metadata")
            if len(set(prototype_material_ids)) != len(prototype_material_ids):
                fail("FAIL_TOP5ISU_MATERIAL_IDENTITY", "prototype material_ids must be unique")
            text_lookup = {
                str(item.get("id")): item
                for item in ((content.get("materials") or {}).get("texts") or [])
                if isinstance(item, dict)
            }
            locked_colors = {
                "T1": "#f1ff00",
                "T2": "#f1ff00",
                "TTS_TEXT": "#ffffff",
                "SOURCE_TEXT": "#ffffff",
            }
            tracks_by_name = {str(track.get("name")): track for track in tracks}
            for track_name, expected_color in locked_colors.items():
                for segment in (tracks_by_name.get(track_name) or {}).get("segments") or []:
                    material = text_lookup.get(str(segment.get("material_id"))) or {}
                    if str(material.get("text_color") or "").lower() != expected_color:
                        fail(
                            "FAIL_TOP5ISU_TEXT_COLOR_LOCK",
                            f"{track_name} must use {expected_color}",
                        )
            animation_lookup = {
                str(item.get("id")): item
                for item in ((content.get("materials") or {}).get("material_animations") or [])
                if isinstance(item, dict)
            }
            image_animation_names: list[str] = []
            for segment in image_segments:
                names_for_segment: list[str] = []
                for ref in segment.get("extra_material_refs") or []:
                    for animation in (animation_lookup.get(str(ref)) or {}).get("animations") or []:
                        name = str(animation.get("name") or "").strip()
                        if name:
                            names_for_segment.append(name)
                if len(names_for_segment) != 1:
                    fail(
                        "FAIL_TOP5ISU_IMAGE_TRANSITION_REQUIRED",
                        f"each prototype image requires exactly one animation; got {names_for_segment}",
                    )
                image_animation_names.append(names_for_segment[0])
            strong_count = sum(name in HIGH_IMPACT_EFFECTS for name in image_animation_names)
            minimum = int(manifest.get("high_impact_effect_required_count_min") or 1)
            maximum = int(manifest.get("high_impact_effect_required_count_max") or 2)
            if not minimum <= strong_count <= maximum:
                fail(
                    "FAIL_TOP5ISU_HIGH_IMPACT_EFFECT",
                    f"high-impact fire animation count must be {minimum}..{maximum}; got {strong_count}",
                )
            frame_segments = tracks[1].get("segments") or []
            logo_segments = tracks[2].get("segments") or []
            for label, segments in (("frame", frame_segments), ("logo", logo_segments)):
                observed = ((segments[0].get("target_timerange") or {}).get("duration")) if segments else None
                if not duration or observed != duration:
                    fail("FAIL_TOP5ISU_LOGO_DURATION", f"{label} must span project duration")
        else:
            if len(image_segments) != 7:
                fail("FAIL_TOP5ISU_TRACK_MAPPING", "seven image-effect segments required")
            for segment in image_segments:
                y_value = (((segment.get("clip") or {}).get("transform") or {}).get("y"))
                if y_value != -0.15625:
                    fail("FAIL_TOP5ISU_COORDINATE_LOCK", f"image JSON y must be -0.15625; got {y_value!r}")
            image_animation_names = []
            strong_count = 0
            logo_segments = tracks[-1].get("segments") or []
        logo_duration = ((logo_segments[0].get("target_timerange") or {}).get("duration")) if logo_segments else None
        if not duration or logo_duration != duration:
            fail("FAIL_TOP5ISU_LOGO_DURATION", "logo must span project duration")

    return {
        "top5isu_package_status": "PASS",
        "template_profile": profile or "top5isu_v1",
        "archive_sha256": measured_sha,
        "packaged_file_count": expected_count,
        "tracks": list(expected_tracks),
        "image_animation_names": image_animation_names,
        "high_impact_effect_segments": strong_count,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("template_dir")
    args = parser.parse_args()
    try:
        result = validate_top5isu_package(Path(args.template_dir))
    except (GateFail, OSError, json.JSONDecodeError) as exc:
        print(str(exc))
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

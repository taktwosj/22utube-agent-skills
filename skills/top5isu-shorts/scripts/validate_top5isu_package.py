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


EXPECTED_TRACKS = ["IMAGE_EFFECT_PRESETS", "TTS", "T2", "T1", "LOGO"]


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
        required = {
            "top5isu/draft_content.json",
            "top5isu/draft_meta_info.json",
            "top5isu/Resources/media/jungboitsu.png",
        }
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
            mac_user_path = "/" + "Users" + r"/[^/]+/"
            if re.search(r"C:[/\\]Users[/\\]", text, re.I) or re.search(mac_user_path, text):
                fail("FAIL_TOP5ISU_PORTABLE_PACKAGE", f"foreign user path: {name}")

        content = json.loads(zf.read("top5isu/draft_content.json").decode("utf-8"))
        tracks = content.get("tracks") or []
        track_names = [track.get("name") for track in tracks]
        if track_names != EXPECTED_TRACKS:
            fail("FAIL_TOP5ISU_TRACK_MAPPING", f"unexpected tracks: {track_names}")
        if len(tracks[0].get("segments") or []) != 7:
            fail("FAIL_TOP5ISU_TRACK_MAPPING", "seven image-effect segments required")
        canvas = content.get("canvas_config") or {}
        if canvas.get("width") != 1080 or canvas.get("height") != 1920:
            fail("FAIL_TOP5ISU_PORTABLE_PACKAGE", "canvas must be 1080x1920")
        for segment in tracks[0].get("segments") or []:
            y_value = (((segment.get("clip") or {}).get("transform") or {}).get("y"))
            if y_value != -0.15625:
                fail("FAIL_TOP5ISU_COORDINATE_LOCK", f"image JSON y must be -0.15625; got {y_value!r}")
        duration = content.get("duration")
        logo_segments = tracks[-1].get("segments") or []
        logo_duration = ((logo_segments[0].get("target_timerange") or {}).get("duration")) if logo_segments else None
        if not duration or logo_duration != duration:
            fail("FAIL_TOP5ISU_LOGO_DURATION", "logo must span project duration")

    return {
        "top5isu_package_status": "PASS",
        "archive_sha256": measured_sha,
        "packaged_file_count": expected_count,
        "tracks": list(EXPECTED_TRACKS),
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

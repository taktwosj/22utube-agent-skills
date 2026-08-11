#!/usr/bin/env python3
"""Prepare profile-specific CapCut media folders from shared episode media.

The common media folder keeps semantic production names. A profile folder adds
only compatibility names that an existing CapCut draft consumes. It never
substitutes source.mp4 for clean_video.mp4 or overwrites a target.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
from pathlib import Path


PROFILES = {"001", "gunlimbo"}
PASSTHROUGH_FILES = (
    "narration_final.wav",
    "subtitles_display.srt",
    "vocals.wav",
    "no_vocals.wav",
    "source.mp4",
    "clean_video.mp4",
)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _shared_files(media_root: Path) -> list[Path]:
    files = [media_root / name for name in PASSTHROUGH_FILES]
    files.extend(path for path in media_root.glob("scene_*") if path.is_file())
    sentences = media_root / "sentences"
    if sentences.is_dir():
        files.extend(path for path in sorted(sentences.glob("*.wav")) if path.is_file())
    return sorted((path for path in files if path.is_file()), key=lambda path: path.as_posix())


def _profile_mappings(media_root: Path, profile: str) -> list[tuple[Path, Path]]:
    mappings = [(source, source.relative_to(media_root)) for source in _shared_files(media_root)]
    if profile == "001":
        sentence_root = media_root / "sentences"
        if sentence_root.is_dir():
            for sentence in sorted(sentence_root.glob("*.wav")):
                try:
                    number = int(sentence.stem)
                except ValueError:
                    continue
                mappings.append((sentence, Path(f"tts_{number:02d}.wav")))
        vocals = media_root / "vocals.wav"
        if vocals.is_file():
            mappings.append((vocals, Path("source_vocals.wav")))
    return mappings


def _assert_safe_target(source: Path, target: Path) -> None:
    if not target.exists():
        return
    if not target.is_file() or _sha256(source) != _sha256(target):
        raise RuntimeError(f"CAPCUT_MEDIA_TARGET_CONFLICT:{target}")


def _link_or_copy(source: Path, target: Path) -> str:
    if target.exists():
        return "existing"
    target.parent.mkdir(parents=True, exist_ok=True)
    try:
        os.link(source, target)
        return "hardlink"
    except OSError:
        shutil.copy2(source, target)
        return "copy"


def prepare_profile(media_root: Path, profile: str) -> dict:
    """Create `{media_root}/capcut_media/{profile}` without changing the source."""
    media_root = Path(media_root).resolve()
    if profile not in PROFILES:
        raise RuntimeError(f"CAPCUT_MEDIA_PROFILE_UNKNOWN:{profile}")
    if not media_root.is_dir():
        raise RuntimeError(f"CAPCUT_MEDIA_ROOT_MISSING:{media_root}")

    destination_root = media_root / "capcut_media" / profile
    seen_targets: dict[Path, Path] = {}
    for source, relative_target in _profile_mappings(media_root, profile):
        target = destination_root / relative_target
        previous = seen_targets.get(target)
        if previous is not None and _sha256(previous) != _sha256(source):
            raise RuntimeError(f"CAPCUT_MEDIA_MAPPING_AMBIGUOUS:{relative_target}")
        seen_targets[target] = source
        _assert_safe_target(source, target)

    entries = []
    for target, source in sorted(seen_targets.items(), key=lambda row: row[0].as_posix()):
        method = _link_or_copy(source, target)
        entries.append({
            "from": source.relative_to(media_root).as_posix(),
            "to": target.relative_to(destination_root).as_posix(),
            "sha256": _sha256(source),
            "method": method,
        })
    receipt = {
        "schema_version": "shared-capcut-media-v1",
        "status": "PASS",
        "profile": profile,
        "media_root": str(media_root),
        "prepared_media_folder": str(destination_root),
        "mappings": [{"from": row["from"], "to": row["to"]} for row in entries],
        "entries": entries,
        "missing": [],
        "invariants": [
            "source.mp4 is never substituted for clean_video.mp4",
            "existing different target files stop with CAPCUT_MEDIA_TARGET_CONFLICT",
            "gunlimbo root and track contract are not modified",
        ],
    }
    destination_root.mkdir(parents=True, exist_ok=True)
    (destination_root / "media_name_mapping.json").write_text(
        json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--media-root", required=True, type=Path)
    parser.add_argument("--profile", required=True, choices=sorted(PROFILES))
    args = parser.parse_args()
    print(json.dumps(prepare_profile(args.media_root, args.profile), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

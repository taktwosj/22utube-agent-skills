#!/usr/bin/env python3
"""Run full-source vocal isolation before any gunlimbo Q-clip cutting."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
from pathlib import Path
from typing import Any


class VocalIsolationFail(Exception):
    pass


def preserve_executable_path(path: Path) -> Path:
    """Keep a venv launcher symlink intact instead of resolving to system Python."""
    expanded = Path(path).expanduser()
    return expanded if expanded.is_absolute() else expanded.absolute()


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def media_duration(path: Path) -> float:
    raw = subprocess.check_output(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "json", str(path)],
        text=True,
    )
    return float(json.loads(raw)["format"]["duration"])


def build_demucs_command(
    python_executable: Path,
    full_source_wav: Path,
    demucs_output: Path,
    model: str,
) -> list[str]:
    return [
        str(python_executable),
        "-m",
        "demucs",
        "--two-stems",
        "vocals",
        "-n",
        model,
        "--out",
        str(demucs_output),
        str(full_source_wav),
    ]


def build_manifest(
    source_media: Path,
    vocals_path: Path,
    no_vocals_path: Path,
    model: str,
    source_duration_sec: float,
    vocals_duration_sec: float,
) -> dict[str, Any]:
    method = "demucs_htdemucs_ft" if model == "htdemucs_ft" else "demucs_two_stems"
    return {
        "status": "WAIT_VOCAL_ISOLATION_REVIEW",
        "source_media": str(source_media),
        "source_media_sha256": sha256(source_media),
        "source_duration_sec": round(source_duration_sec, 6),
        "vocals_path": str(vocals_path),
        "vocals_sha256": sha256(vocals_path),
        "vocals_duration_sec": round(vocals_duration_sec, 6),
        "no_vocals_path": str(no_vocals_path),
        "no_vocals_sha256": sha256(no_vocals_path),
        "source_vocal_isolation": {
            "policy": "REQUIRED_WHEN_MIXED_AUDIO",
            "status": "WAIT_REVIEW",
            "method": method,
            "model": model,
            "processed_before_speaker_clip_cut": True,
            "q_clips_source": "vocals_stem",
            "original_video_audio_muted": True,
            "residual_music_review": "WAIT_REVIEW",
            "voice_artifact_review": "WAIT_REVIEW",
        },
    }


def prepare_source_vocals(
    source_media: Path,
    output_dir: Path,
    python_executable: Path,
    model: str = "htdemucs_ft",
    overwrite: bool = False,
) -> dict[str, Any]:
    source_media = Path(source_media).expanduser().resolve()
    output_dir = Path(output_dir).expanduser().resolve()
    python_executable = preserve_executable_path(python_executable)
    if not source_media.is_file():
        raise VocalIsolationFail(f"source media missing: {source_media}")
    if re.match(r"^Q\d+([_.-]|$)", source_media.name, re.I):
        raise VocalIsolationFail("quote fragments are forbidden; provide the complete original source")
    if not python_executable.is_file():
        raise VocalIsolationFail(f"Demucs Python missing: {python_executable}")
    if output_dir.exists():
        if not overwrite:
            raise VocalIsolationFail(f"output exists: {output_dir}")
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True)

    full_source_wav = output_dir / "full_source.wav"
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-hide_banner",
            "-loglevel",
            "error",
            "-i",
            str(source_media),
            "-vn",
            "-ar",
            "44100",
            "-ac",
            "2",
            "-c:a",
            "pcm_s16le",
            str(full_source_wav),
        ],
        check=True,
    )
    demucs_root = output_dir / "demucs_work"
    subprocess.run(
        build_demucs_command(python_executable, full_source_wav, demucs_root, model),
        check=True,
    )
    stem_root = demucs_root / model / full_source_wav.stem
    generated_vocals = stem_root / "vocals.wav"
    generated_no_vocals = stem_root / "no_vocals.wav"
    if not generated_vocals.is_file() or not generated_no_vocals.is_file():
        raise VocalIsolationFail("Demucs stems missing after separation")
    vocals = output_dir / "vocals.wav"
    no_vocals = output_dir / "no_vocals.wav"
    shutil.copy2(generated_vocals, vocals)
    shutil.copy2(generated_no_vocals, no_vocals)

    source_duration = media_duration(source_media)
    vocals_duration = media_duration(vocals)
    if abs(source_duration - vocals_duration) > 0.5:
        raise VocalIsolationFail("vocals stem duration differs from source by more than 0.5 seconds")
    manifest = build_manifest(
        source_media,
        vocals,
        no_vocals,
        model,
        source_duration,
        vocals_duration,
    )
    (output_dir / "isolation_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("source_media")
    parser.add_argument("output_dir")
    parser.add_argument("--python", required=True, dest="python_executable")
    parser.add_argument("--model", default="htdemucs_ft")
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()
    try:
        manifest = prepare_source_vocals(
            Path(args.source_media),
            Path(args.output_dir),
            Path(args.python_executable),
            model=args.model,
            overwrite=args.overwrite,
        )
    except (VocalIsolationFail, OSError, ValueError, json.JSONDecodeError, subprocess.CalledProcessError) as exc:
        print(f"WAIT_VOCAL_ISOLATION: {exc}")
        return 1
    print(
        json.dumps(
            {
                "status": manifest["status"],
                "source_media": manifest["source_media"],
                "vocals_path": manifest["vocals_path"],
                "no_vocals_path": manifest["no_vocals_path"],
                "review_required": True,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Prepare a full-source Demucs vocal stem for Tikitaka source analysis."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any


class GateFail(Exception):
    pass


MANIFEST_RELATIVE_PATH = Path("10_analysis/source_voice_separation.json")
SOURCE_AUDIO_RELATIVE_PATH = Path("10_analysis/audio/full_source_audio.wav")
VOCALS_RELATIVE_PATH = Path("10_analysis/audio/vocals.wav")
ALLOWED_CONFIRMATION_SOURCES = {"user", "source_evidence", "no_audio_stream"}
DURATION_TOLERANCE_SEC = 0.25
SAMPLE_RATE_HZ = 48000


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def resolve_episode_path(root: Path, raw_path: Path | str) -> Path:
    root = root.resolve()
    candidate = Path(raw_path)
    resolved = candidate.resolve() if candidate.is_absolute() else (root / candidate).resolve()
    try:
        resolved.relative_to(root)
    except ValueError as exc:
        raise GateFail("WAIT_SOURCE_VOICE_SEPARATION: path escapes episode root") from exc
    return resolved


def run_command(command: list[str], fail_token: str) -> subprocess.CompletedProcess[str]:
    try:
        completed = subprocess.run(
            command,
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=1800,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired) as exc:
        raise GateFail(f"{fail_token}: {exc}") from exc
    if completed.returncode != 0:
        detail = completed.stderr.strip().splitlines()
        message = detail[-1] if detail else f"exit={completed.returncode}"
        raise GateFail(f"{fail_token}: {message}")
    return completed


def probe_media(path: Path, ffprobe: str) -> dict[str, Any]:
    completed = run_command(
        [
            ffprobe,
            "-v",
            "error",
            "-show_entries",
            "format=duration:stream=codec_type,sample_rate,channels",
            "-of",
            "json",
            str(path),
        ],
        "WAIT_SOURCE_VOICE_SEPARATION",
    )
    try:
        payload = json.loads(completed.stdout)
        duration_sec = float(payload.get("format", {}).get("duration"))
    except (TypeError, ValueError, json.JSONDecodeError) as exc:
        raise GateFail("WAIT_SOURCE_VOICE_SEPARATION: ffprobe duration missing") from exc
    streams = payload.get("streams")
    if not isinstance(streams, list):
        raise GateFail("WAIT_SOURCE_VOICE_SEPARATION: ffprobe streams missing")
    audio_streams = [
        stream
        for stream in streams
        if isinstance(stream, dict) and stream.get("codec_type") == "audio"
    ]
    sample_rate_hz = 0
    channels = 0
    if audio_streams:
        try:
            sample_rate_hz = int(audio_streams[0].get("sample_rate") or 0)
            channels = int(audio_streams[0].get("channels") or 0)
        except (TypeError, ValueError) as exc:
            raise GateFail("WAIT_SOURCE_VOICE_SEPARATION: invalid audio stream metadata") from exc
    if duration_sec <= 0:
        raise GateFail("WAIT_SOURCE_VOICE_SEPARATION: source duration must be positive")
    return {
        "duration_sec": duration_sec,
        "has_audio_stream": bool(audio_streams),
        "sample_rate_hz": sample_rate_hz,
        "channels": channels,
    }


def write_manifest(root: Path, payload: dict[str, Any]) -> dict[str, Any]:
    path = root / MANIFEST_RELATIVE_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return payload


def skip_manifest(
    root: Path,
    source_path: Path,
    *,
    confirmation_source: str,
) -> dict[str, Any]:
    payload = {
        "gate_name": "SOURCE_VOICE_SEPARATION_GATE",
        "status": "NOT_REQUIRED_NO_SOURCE_SPEECH",
        "owner_skill": "00-tikitaka",
        "source_fingerprint_sha256": sha256_file(source_path),
        "no_source_speech_confirmed": True,
        "confirmation_source": confirmation_source,
        "source_voice_music_removed": False,
        "no_vocals_used": False,
        "created_by": "prepare_source_voice.py",
    }
    return write_manifest(root, payload)


def prepare_source_voice(
    root: Path,
    source: Path,
    *,
    model: str = "htdemucs",
    no_source_speech_confirmed: bool = False,
    confirmation_source: str = "",
) -> dict[str, Any]:
    """Create full-source audio, Demucs vocals, and the bound gate manifest."""

    root = Path(root).resolve()
    source_path = resolve_episode_path(root, source)
    if not source_path.is_file() or source_path.stat().st_size <= 0:
        raise GateFail(f"WAIT_SOURCE_VOICE_SEPARATION: source media missing: {source_path}")

    if no_source_speech_confirmed:
        if confirmation_source not in {"user", "source_evidence"}:
            raise GateFail(
                "WAIT_SOURCE_VOICE_SEPARATION: confirmed skip requires "
                "confirmation_source=user|source_evidence"
            )
        return skip_manifest(
            root,
            source_path,
            confirmation_source=confirmation_source,
        )

    ffprobe = shutil.which("ffprobe")
    if not ffprobe:
        raise GateFail("WAIT_FFPROBE_AVAILABLE: ffprobe not found")
    source_probe = probe_media(source_path, ffprobe)
    if not source_probe["has_audio_stream"]:
        return skip_manifest(
            root,
            source_path,
            confirmation_source="no_audio_stream",
        )

    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        raise GateFail("WAIT_FFMPEG_AVAILABLE: ffmpeg not found")
    if importlib.util.find_spec("demucs") is None:
        raise GateFail("WAIT_DEMUCS_AVAILABLE: Python demucs module not found")

    source_audio_path = root / SOURCE_AUDIO_RELATIVE_PATH
    vocals_path = root / VOCALS_RELATIVE_PATH
    source_audio_path.parent.mkdir(parents=True, exist_ok=True)

    run_command(
        [
            ffmpeg,
            "-y",
            "-i",
            str(source_path),
            "-vn",
            "-ac",
            "2",
            "-ar",
            str(SAMPLE_RATE_HZ),
            "-c:a",
            "pcm_s24le",
            str(source_audio_path),
        ],
        "WAIT_SOURCE_VOICE_SEPARATION",
    )
    if not source_audio_path.is_file() or source_audio_path.stat().st_size <= 0:
        raise GateFail("WAIT_SOURCE_VOICE_SEPARATION: full source audio was not created")

    with tempfile.TemporaryDirectory(
        prefix="demucs-",
        dir=str(source_audio_path.parent),
    ) as temporary:
        temporary_root = Path(temporary)
        run_command(
            [
                sys.executable,
                "-m",
                "demucs.separate",
                "-n",
                model,
                "--two-stems",
                "vocals",
                "-o",
                str(temporary_root),
                str(source_audio_path),
            ],
            "WAIT_SOURCE_VOICE_SEPARATION",
        )
        demucs_vocals = (
            temporary_root
            / model
            / source_audio_path.stem
            / "vocals.wav"
        )
        if not demucs_vocals.is_file() or demucs_vocals.stat().st_size <= 0:
            raise GateFail("WAIT_SOURCE_VOICE_SEPARATION: Demucs vocals.wav missing")
        run_command(
            [
                ffmpeg,
                "-y",
                "-i",
                str(demucs_vocals),
                "-ac",
                "2",
                "-ar",
                str(SAMPLE_RATE_HZ),
                "-c:a",
                "pcm_s24le",
                str(vocals_path),
            ],
            "WAIT_SOURCE_VOICE_SEPARATION",
        )

    if not vocals_path.is_file() or vocals_path.stat().st_size <= 0:
        raise GateFail("WAIT_SOURCE_VOICE_SEPARATION: stable vocals.wav missing")

    source_audio_probe = probe_media(source_audio_path, ffprobe)
    vocals_probe = probe_media(vocals_path, ffprobe)
    durations = (
        float(source_probe["duration_sec"]),
        float(source_audio_probe["duration_sec"]),
        float(vocals_probe["duration_sec"]),
    )
    if max(durations) - min(durations) > DURATION_TOLERANCE_SEC:
        raise GateFail(
            "WAIT_SOURCE_VOICE_DURATION_PARITY: source, full audio, and vocals duration mismatch"
        )
    if (
        source_audio_probe["sample_rate_hz"] != SAMPLE_RATE_HZ
        or vocals_probe["sample_rate_hz"] != SAMPLE_RATE_HZ
    ):
        raise GateFail("WAIT_SOURCE_VOICE_SEPARATION: stable WAV sample rate must be 48000")

    source_audio_sha256 = sha256_file(source_audio_path)
    payload = {
        "gate_name": "SOURCE_VOICE_SEPARATION_GATE",
        "status": "PASS",
        "owner_skill": "00-tikitaka",
        "source_fingerprint_sha256": sha256_file(source_path),
        "separation_engine": "demucs",
        "separation_model": model,
        "separation_scope": "FULL_SOURCE_AUDIO",
        "source_audio_path": SOURCE_AUDIO_RELATIVE_PATH.as_posix(),
        "source_audio_sha256": source_audio_sha256,
        "demucs_input_sha256": source_audio_sha256,
        "vocals_path": VOCALS_RELATIVE_PATH.as_posix(),
        "vocals_sha256": sha256_file(vocals_path),
        "source_duration_sec": source_probe["duration_sec"],
        "source_audio_duration_sec": source_audio_probe["duration_sec"],
        "vocals_duration_sec": vocals_probe["duration_sec"],
        "duration_tolerance_sec": DURATION_TOLERANCE_SEC,
        "sample_rate_hz": SAMPLE_RATE_HZ,
        "channels": vocals_probe["channels"],
        "source_voice_music_removed": True,
        "q_segment_source": VOCALS_RELATIVE_PATH.as_posix(),
        "no_vocals_used": False,
        "created_by": "prepare_source_voice.py",
    }
    return write_manifest(root, payload)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--source", default="00_source/source.mp4")
    parser.add_argument("--model", default="htdemucs")
    parser.add_argument("--no-source-speech-confirmed", action="store_true")
    parser.add_argument(
        "--confirmation-source",
        choices=sorted(ALLOWED_CONFIRMATION_SOURCES - {"no_audio_stream"}),
        default="",
    )
    args = parser.parse_args()
    try:
        result = prepare_source_voice(
            Path(args.root),
            Path(args.source),
            model=args.model,
            no_source_speech_confirmed=args.no_source_speech_confirmed,
            confirmation_source=args.confirmation_source,
        )
    except GateFail as exc:
        print(str(exc))
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

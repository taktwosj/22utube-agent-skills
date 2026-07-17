#!/usr/bin/env python3
"""Validate full-source Demucs vocal separation evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
import wave
from pathlib import Path
from typing import Any


class GateFail(Exception):
    pass


MANIFEST_RELATIVE_PATH = Path("10_analysis/source_voice_separation.json")
LOCK_RELATIVE_PATH = Path("10_analysis/source_identity_lock.json")
PASS_STATUS = "PASS"
SKIP_STATUS = "NOT_REQUIRED_NO_SOURCE_SPEECH"
ALLOWED_CONFIRMATION_SOURCES = {"user", "source_evidence", "no_audio_stream"}
EXPECTED_SOURCE_AUDIO_PATH = "10_analysis/audio/full_source_audio.wav"
EXPECTED_VOCALS_PATH = "10_analysis/audio/vocals.wav"


def load_json(path: Path, label: str) -> dict[str, Any]:
    if not path.is_file():
        raise GateFail(f"WAIT_SOURCE_VOICE_SEPARATION: {label} missing: {path}")
    try:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError as exc:
        raise GateFail(f"WAIT_SOURCE_VOICE_SEPARATION: {label} parse failed") from exc
    if not isinstance(data, dict):
        raise GateFail(f"WAIT_SOURCE_VOICE_SEPARATION: {label} root must be object")
    return data


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def relative_artifact(root: Path, raw_path: Any, field: str) -> Path:
    value = str(raw_path or "").strip()
    path = Path(value)
    if not value or path.is_absolute():
        raise GateFail(
            f"WAIT_SOURCE_VOICE_SEPARATION: {field} must be an episode-root-relative path"
        )
    resolved = (root / path).resolve()
    try:
        resolved.relative_to(root)
    except ValueError as exc:
        raise GateFail(f"WAIT_SOURCE_VOICE_SEPARATION: {field} escapes episode root") from exc
    if not resolved.is_file() or resolved.stat().st_size <= 0:
        raise GateFail(f"WAIT_SOURCE_VOICE_SEPARATION: {field} missing: {resolved}")
    return resolved


def wav_metadata(path: Path) -> dict[str, Any]:
    try:
        with wave.open(str(path), "rb") as handle:
            sample_rate_hz = handle.getframerate()
            frames = handle.getnframes()
            channels = handle.getnchannels()
    except (wave.Error, EOFError) as exc:
        raise GateFail(f"WAIT_SOURCE_VOICE_SEPARATION: invalid WAV: {path}") from exc
    if sample_rate_hz <= 0 or frames <= 0:
        raise GateFail(f"WAIT_SOURCE_VOICE_SEPARATION: empty WAV: {path}")
    return {
        "sample_rate_hz": sample_rate_hz,
        "channels": channels,
        "duration_sec": frames / sample_rate_hz,
    }


def require_number(data: dict[str, Any], field: str) -> float:
    value = data.get(field)
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise GateFail(f"WAIT_SOURCE_VOICE_SEPARATION: {field} must be numeric")
    return float(value)


def validate_source_voice_separation(
    root: Path,
    manifest_path: Path | None = None,
) -> dict[str, Any]:
    root = Path(root).resolve()
    manifest_file = (
        root / MANIFEST_RELATIVE_PATH
        if manifest_path is None
        else (
            Path(manifest_path)
            if Path(manifest_path).is_absolute()
            else root / Path(manifest_path)
        )
    )
    manifest = load_json(manifest_file, "source_voice_separation.json")
    if manifest.get("gate_name") != "SOURCE_VOICE_SEPARATION_GATE":
        raise GateFail("WAIT_SOURCE_VOICE_SEPARATION: gate_name mismatch")
    if manifest.get("owner_skill") != "00-tikitaka":
        raise GateFail("WAIT_SOURCE_VOICE_SEPARATION: owner_skill must be 00-tikitaka")

    lock = load_json(root / LOCK_RELATIVE_PATH, "source_identity_lock.json")
    expected_source_sha = str(lock.get("sha256") or "").lower()
    actual_source_sha = str(manifest.get("source_fingerprint_sha256") or "").lower()
    if not expected_source_sha or actual_source_sha != expected_source_sha:
        raise GateFail("WAIT_SOURCE_VOICE_HASH_BINDING: source fingerprint mismatch")

    status = str(manifest.get("status") or "")
    if status == SKIP_STATUS:
        if manifest.get("no_source_speech_confirmed") is not True:
            raise GateFail("WAIT_SOURCE_VOICE_SEPARATION: no-speech skip is not confirmed")
        if manifest.get("confirmation_source") not in ALLOWED_CONFIRMATION_SOURCES:
            raise GateFail("WAIT_SOURCE_VOICE_SEPARATION: invalid no-speech confirmation source")
        if manifest.get("source_voice_music_removed") is not False:
            raise GateFail("WAIT_SOURCE_VOICE_SEPARATION: skipped separation cannot claim removal")
        if manifest.get("no_vocals_used") is not False:
            raise GateFail("WAIT_SOURCE_VOICE_SEPARATION: no_vocals_used must be false")
        return {
            "source_voice_separation_status": SKIP_STATUS,
            "source_voice_manifest_path": str(manifest_file),
            "source_voice_vocals_path": "",
        }
    if status != PASS_STATUS:
        raise GateFail("WAIT_SOURCE_VOICE_SEPARATION: status must be PASS or valid skip")

    expected_values = {
        "separation_engine": "demucs",
        "separation_scope": "FULL_SOURCE_AUDIO",
        "source_audio_path": EXPECTED_SOURCE_AUDIO_PATH,
        "vocals_path": EXPECTED_VOCALS_PATH,
        "q_segment_source": EXPECTED_VOCALS_PATH,
        "sample_rate_hz": 48000,
        "source_voice_music_removed": True,
        "no_vocals_used": False,
        "created_by": "prepare_source_voice.py",
    }
    for field, expected in expected_values.items():
        if manifest.get(field) != expected:
            raise GateFail(
                f"WAIT_SOURCE_VOICE_SEPARATION: {field} must be {expected!r}"
            )

    source_audio_path = relative_artifact(
        root,
        manifest.get("source_audio_path"),
        "source_audio_path",
    )
    vocals_path = relative_artifact(root, manifest.get("vocals_path"), "vocals_path")
    actual_source_audio_sha = sha256_file(source_audio_path)
    actual_vocals_sha = sha256_file(vocals_path)
    if str(manifest.get("source_audio_sha256") or "").lower() != actual_source_audio_sha:
        raise GateFail("WAIT_SOURCE_VOICE_HASH_BINDING: source audio hash mismatch")
    if str(manifest.get("demucs_input_sha256") or "").lower() != actual_source_audio_sha:
        raise GateFail("WAIT_SOURCE_VOICE_HASH_BINDING: Demucs input hash mismatch")
    if str(manifest.get("vocals_sha256") or "").lower() != actual_vocals_sha:
        raise GateFail("WAIT_SOURCE_VOICE_HASH_BINDING: vocals hash mismatch")

    source_audio = wav_metadata(source_audio_path)
    vocals = wav_metadata(vocals_path)
    if (
        source_audio["sample_rate_hz"] != 48000
        or vocals["sample_rate_hz"] != 48000
    ):
        raise GateFail("WAIT_SOURCE_VOICE_SEPARATION: WAV sample rate must be 48000")

    tolerance = require_number(manifest, "duration_tolerance_sec")
    if tolerance < 0 or tolerance > 0.25:
        raise GateFail("WAIT_SOURCE_VOICE_DURATION_PARITY: tolerance must be 0..0.25")
    declared_source = require_number(manifest, "source_duration_sec")
    declared_source_audio = require_number(manifest, "source_audio_duration_sec")
    declared_vocals = require_number(manifest, "vocals_duration_sec")
    observed = (
        declared_source,
        declared_source_audio,
        declared_vocals,
        source_audio["duration_sec"],
        vocals["duration_sec"],
    )
    if max(observed) - min(observed) > tolerance:
        raise GateFail("WAIT_SOURCE_VOICE_DURATION_PARITY: duration mismatch")

    return {
        "source_voice_separation_status": PASS_STATUS,
        "source_voice_manifest_path": str(manifest_file),
        "source_voice_source_audio_path": str(source_audio_path),
        "source_voice_vocals_path": str(vocals_path),
        "source_voice_vocals_sha256": actual_vocals_sha,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--manifest", default=str(MANIFEST_RELATIVE_PATH))
    args = parser.parse_args()
    try:
        result = validate_source_voice_separation(
            Path(args.root),
            Path(args.manifest),
        )
    except GateFail as exc:
        print(str(exc))
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

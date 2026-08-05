from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from common import sha256_file, write_json


SKILL_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MODEL = "htdemucs"


def _run(command: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, capture_output=True, text=True, check=False)


def _demucs_version(command: list[str]) -> str | None:
    probe = (
        "import tempfile; from pathlib import Path; import torch, torchaudio, demucs; "
        "d=tempfile.TemporaryDirectory(); p=Path(d.name)/'probe.wav'; "
        "torchaudio.save(str(p), torch.zeros(1, 8), 8000); assert p.is_file(); "
        "print(getattr(demucs, '__version__', 'unknown'))"
    )
    completed = _run(command + ["-c", probe])
    return completed.stdout.strip() if completed.returncode == 0 else None


def find_demucs_python(explicit: str | None = None) -> tuple[list[str] | None, str | None]:
    candidates: list[list[str]] = []
    if explicit:
        candidates.append([explicit])
    candidates.append([sys.executable])
    if sys.platform == "win32":
        candidates.extend([["py", "-3.12"], ["py", "-3.11"]])
    seen: set[tuple[str, ...]] = set()
    for command in candidates:
        key = tuple(command)
        if key in seen:
            continue
        seen.add(key)
        version = _demucs_version(command)
        if version is not None:
            return command, version
    return None, None


def _probe_audio(path: Path) -> tuple[int, str]:
    completed = _run([
        "ffprobe", "-v", "error", "-select_streams", "a:0",
        "-show_entries", "stream=codec_name:format=duration", "-of", "json", str(path),
    ])
    try:
        payload = json.loads(completed.stdout)
        duration_us = round(float(payload["format"]["duration"]) * 1_000_000)
        codec = str(payload["streams"][0]["codec_name"])
    except (IndexError, KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
        raise RuntimeError("AUDIO_PROBE_FAILED") from exc
    if completed.returncode != 0 or duration_us <= 0 or not codec:
        raise RuntimeError("AUDIO_PROBE_FAILED")
    return duration_us, codec


def _wait_payload() -> dict:
    command, _ = find_demucs_python()
    return {
        "status": "PASS" if command else "WAIT_DEMUCS_RUNTIME",
        "engine": "demucs",
        "model": DEFAULT_MODEL,
        "python_command": command or [],
        "install_hint": "Install Demucs in Python 3.12 or 3.11, then rerun this command.",
    }


def separate(source: Path, output_dir: Path, episode_id: str, *, model: str, python: str | None) -> dict:
    source = source.resolve()
    output_dir = output_dir.resolve()
    if not source.is_file():
        raise RuntimeError("SOURCE_AUDIO_INPUT_MISSING")
    if output_dir.exists() and any(output_dir.iterdir()):
        raise RuntimeError("VOCAL_STEM_OUTPUT_EXISTS")
    command, demucs_version = find_demucs_python(python)
    if command is None:
        return _wait_payload()
    if shutil.which("ffmpeg") is None or shutil.which("ffprobe") is None:
        raise RuntimeError("MEDIA_TOOL_MISSING:ffmpeg/ffprobe")

    output_dir.mkdir(parents=True, exist_ok=True)
    source_duration_us, _ = _probe_audio(source)
    with tempfile.TemporaryDirectory(prefix="001short-demucs-", dir=str(output_dir.parent)) as temp_root:
        temporary = Path(temp_root)
        extracted = temporary / "source_audio.wav"
        extracted_result = _run([
            "ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", str(source),
            "-map", "0:a:0", "-vn", "-ac", "2", "-ar", "44100", "-c:a", "pcm_s16le", str(extracted),
        ])
        if extracted_result.returncode != 0 or not extracted.is_file():
            raise RuntimeError("SOURCE_AUDIO_EXTRACT_FAILED")
        demucs_root = temporary / "demucs"
        separated = _run(command + [
            "-m", "demucs.separate", "--two-stems", "vocals", "-n", model,
            "--out", str(demucs_root), str(extracted),
        ])
        demucs_output = demucs_root / model / extracted.stem
        raw_vocals = demucs_output / "vocals.wav"
        raw_residual = demucs_output / "no_vocals.wav"
        if separated.returncode != 0 or not raw_vocals.is_file() or not raw_residual.is_file():
            detail = (separated.stderr or separated.stdout).strip()[-1000:]
            raise RuntimeError(f"DEMUCS_SEPARATION_FAILED:{detail}")
        vocals = output_dir / "vocals.wav"
        residual = output_dir / "no_vocals.wav"
        for raw, target in ((raw_vocals, vocals), (raw_residual, residual)):
            normalized = _run([
                "ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", str(raw),
                "-ac", "1", "-ar", "48000", "-c:a", "pcm_s16le", str(target),
            ])
            if normalized.returncode != 0 or not target.is_file():
                raise RuntimeError("VOCAL_STEM_NORMALIZATION_FAILED")

    vocals_duration_us, vocals_codec = _probe_audio(vocals)
    residual_duration_us, residual_codec = _probe_audio(residual)
    if abs(vocals_duration_us - source_duration_us) > 100_000:
        raise RuntimeError("VOCAL_STEM_DURATION_MISMATCH")
    manifest = {
        "schema_version": "001short-vocal-stem-manifest-v1",
        "status": "STEM_GENERATED",
        "episode_id": episode_id,
        "source_path": str(source),
        "source_sha256": sha256_file(source),
        "source_duration_us": source_duration_us,
        "separator": {
            "engine": "demucs",
            "model": model,
            "version": demucs_version,
            "python_executable": " ".join(command),
        },
        "vocals_path": "vocals.wav",
        "vocals_sha256": sha256_file(vocals),
        "vocals_duration_us": vocals_duration_us,
        "vocals_codec": vocals_codec,
        "vocals_ffprobe_verified": True,
        "residual_reference_path": "no_vocals.wav",
        "residual_reference_sha256": sha256_file(residual),
        "residual_duration_us": residual_duration_us,
        "residual_codec": residual_codec,
        "capcut_audio_role": "A10",
        "capcut_allowed_audio_path": "vocals.wav",
        "a12_policy": "EMPTY",
        "human_listen_qc_required": True,
        "automatic_claim_limit": "The generated stem proves a separator ran; a listen check still decides audible residual music.",
    }
    manifest_path = output_dir / "vocal_stem_manifest.json"
    write_json(manifest_path, manifest)
    return {
        "status": "STEM_GENERATED",
        "manifest_path": str(manifest_path),
        "vocals_path": str(vocals),
        "capcut_audio_role": "A10",
        "a12_policy": "EMPTY",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate an actual Demucs vocal stem for 001short A10.")
    parser.add_argument("--preflight", action="store_true")
    parser.add_argument("--source", type=Path)
    parser.add_argument("--out-dir", type=Path)
    parser.add_argument("--episode-id")
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--separator-python")
    args = parser.parse_args()
    if args.preflight:
        payload = _wait_payload()
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0 if payload["status"] == "PASS" else 2
    if not args.source or not args.out_dir or not args.episode_id:
        parser.error("--source, --out-dir, and --episode-id are required unless --preflight is used")
    try:
        payload = separate(args.source, args.out_dir, args.episode_id, model=args.model, python=args.separator_python)
    except RuntimeError as exc:
        payload = {"status": "FAIL", "errors": [str(exc)]}
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 1
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if payload["status"] == "STEM_GENERATED" else 2


if __name__ == "__main__":
    raise SystemExit(main())

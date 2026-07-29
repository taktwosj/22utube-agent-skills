#!/usr/bin/env python3
"""Build a V4 voice bus and final master with measured FFmpeg loudnorm receipts."""

from __future__ import annotations

import argparse
import json
import math
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_DIR = SCRIPT_DIR.parent
DEFAULT_PROFILE = SKILL_DIR / "assets" / "political-documentary-v4.json"
LOUDNORM_OBJECT_RE = re.compile(r'\{\s*"input_i".*?\}', re.DOTALL)


class AudioBuildError(RuntimeError):
    """Raised when FFmpeg or a V4 audio contract fails."""


def run_command(command: list[str]) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    if result.returncode != 0:
        rendered = " ".join(command)
        raise AudioBuildError(
            f"COMMAND_FAILED:{rendered}\n{result.stdout}\n{result.stderr}".strip()
        )
    return result


def finite_number(value: Any, field: str) -> float:
    try:
        parsed = float(value)
    except (TypeError, ValueError) as exc:
        raise AudioBuildError(f"INVALID_LOUDNESS_VALUE:{field}:{value}") from exc
    if not math.isfinite(parsed):
        raise AudioBuildError(f"NONFINITE_LOUDNESS_VALUE:{field}:{value}")
    return parsed


def parse_loudnorm_output(stderr: str) -> dict[str, Any]:
    candidates = LOUDNORM_OBJECT_RE.findall(stderr)
    if not candidates:
        raise AudioBuildError("LOUDNORM_JSON_NOT_FOUND")
    try:
        return json.loads(candidates[-1])
    except json.JSONDecodeError as exc:
        raise AudioBuildError(f"LOUDNORM_JSON_INVALID:{exc}") from exc


def normalized_stats(raw: dict[str, Any]) -> dict[str, float]:
    return {
        "integrated_lufs": finite_number(raw.get("input_i"), "input_i"),
        "true_peak_dbtp": finite_number(raw.get("input_tp"), "input_tp"),
        "lra_lu": finite_number(raw.get("input_lra"), "input_lra"),
        "threshold_lufs": finite_number(raw.get("input_thresh"), "input_thresh"),
        "target_offset_db": finite_number(raw.get("target_offset"), "target_offset"),
    }


def measure_loudness(
    media_path: Path,
    ffmpeg: str,
    target_i: float = -14.0,
    target_tp: float = -1.0,
    target_lra: float = 11.0,
) -> tuple[dict[str, float], dict[str, Any]]:
    filter_value = (
        f"loudnorm=I={target_i}:TP={target_tp}:LRA={target_lra}:"
        "print_format=json"
    )
    result = run_command(
        [
            ffmpeg,
            "-hide_banner",
            "-nostats",
            "-i",
            str(media_path),
            "-vn",
            "-af",
            filter_value,
            "-f",
            "null",
            os.devnull,
        ]
    )
    raw = parse_loudnorm_output(result.stderr)
    return normalized_stats(raw), raw


def loudnorm_2pass(
    input_path: Path,
    output_path: Path,
    ffmpeg: str,
    target_i: float,
    target_tp: float,
    target_lra: float,
) -> dict[str, Any]:
    input_stats, pass1_raw = measure_loudness(
        input_path, ffmpeg, target_i, target_tp, target_lra
    )
    second_filter = (
        f"loudnorm=I={target_i}:TP={target_tp}:LRA={target_lra}:"
        f"measured_I={input_stats['integrated_lufs']}:"
        f"measured_TP={input_stats['true_peak_dbtp']}:"
        f"measured_LRA={input_stats['lra_lu']}:"
        f"measured_thresh={input_stats['threshold_lufs']}:"
        f"offset={input_stats['target_offset_db']}:"
        "linear=true:print_format=json"
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    result = run_command(
        [
            ffmpeg,
            "-y",
            "-hide_banner",
            "-nostats",
            "-i",
            str(input_path),
            "-vn",
            "-af",
            second_filter,
            "-ar",
            "48000",
            "-ac",
            "2",
            "-c:a",
            "pcm_s24le",
            str(output_path),
        ]
    )
    pass2_raw = parse_loudnorm_output(result.stderr)
    output_stats, verification_raw = measure_loudness(
        output_path, ffmpeg, target_i, target_tp, target_lra
    )
    return {
        "input": input_stats,
        "output": output_stats,
        "applied_gain_db": round(
            output_stats["integrated_lufs"] - input_stats["integrated_lufs"], 3
        ),
        "ffmpeg_pass1": pass1_raw,
        "ffmpeg_pass2": pass2_raw,
        "verification": verification_raw,
    }


def assess_normalized_audio(
    receipt: dict[str, Any],
    target_i: float,
    target_tp: float,
    target_lra: float,
    lufs_tolerance: float,
    max_abs_gain_db: float,
) -> list[str]:
    errors: list[str] = []
    output = receipt["output"]
    gain = abs(float(receipt["applied_gain_db"]))
    if gain > max_abs_gain_db:
        errors.append(
            f"GAIN_OUTLIER:{receipt['applied_gain_db']:.3f}dB>{max_abs_gain_db:.3f}dB"
        )
    if abs(output["integrated_lufs"] - target_i) > lufs_tolerance:
        errors.append(
            "INTEGRATED_LUFS_OUT_OF_RANGE:"
            f"{output['integrated_lufs']:.3f}:target={target_i}:tol={lufs_tolerance}"
        )
    if output["true_peak_dbtp"] > target_tp + 0.1:
        errors.append(
            f"TRUE_PEAK_OUT_OF_RANGE:{output['true_peak_dbtp']:.3f}>{target_tp:.3f}"
        )
    if output["lra_lu"] > target_lra + 0.1:
        errors.append(f"LRA_OUT_OF_RANGE:{output['lra_lu']:.3f}>{target_lra:.3f}")
    return errors


def condition_peak_limited_speech(
    input_path: Path,
    output_path: Path,
    ffmpeg: str,
) -> None:
    """Reduce speech crest factor only when TP prevents the LUFS target."""
    run_command(
        [
            ffmpeg,
            "-y",
            "-hide_banner",
            "-nostats",
            "-i",
            str(input_path),
            "-vn",
            "-af",
            "acompressor=threshold=0.12:ratio=3:attack=15:release=200:makeup=2",
            "-ar",
            "48000",
            "-ac",
            "2",
            "-c:a",
            "pcm_s24le",
            str(output_path),
        ]
    )


def resolve_plan_path(plan_path: Path, value: str) -> Path:
    candidate = Path(value)
    if not candidate.is_absolute():
        candidate = plan_path.parent / candidate
    return candidate.resolve()


def assemble_voice_bus(
    clips: list[dict[str, Any]],
    duration_ms: int,
    output_path: Path,
    ffmpeg: str,
) -> None:
    if not clips:
        raise AudioBuildError("VOICE_CLIPS_EMPTY")
    duration_s = duration_ms / 1000.0
    command = [ffmpeg, "-y", "-hide_banner", "-nostats"]
    filters: list[str] = []
    for index, clip in enumerate(clips):
        command.extend(["-i", str(clip["normalized_path"])])
        start_ms = int(clip["start_ms"])
        filters.append(
            f"[{index}:a]aformat=sample_rates=48000:channel_layouts=stereo,"
            f"adelay={start_ms}:all=1,apad=whole_dur={duration_s:.3f},"
            f"atrim=duration={duration_s:.3f}[voice{index}]"
        )
    labels = "".join(f"[voice{index}]" for index in range(len(clips)))
    filters.append(
        f"{labels}amix=inputs={len(clips)}:duration=longest:normalize=0,"
        f"atrim=duration={duration_s:.3f}[voice_bus]"
    )
    command.extend(
        [
            "-filter_complex",
            ";".join(filters),
            "-map",
            "[voice_bus]",
            "-ar",
            "48000",
            "-ac",
            "2",
            "-c:a",
            "pcm_s24le",
            str(output_path),
        ]
    )
    run_command(command)


def mix_with_ducked_bgm(
    voice_bus: Path,
    bgm_path: Path | None,
    duration_ms: int,
    output_path: Path,
    ffmpeg: str,
    bgm_gain_db: float,
    duck: dict[str, Any],
) -> None:
    duration_s = duration_ms / 1000.0
    if bgm_path is None:
        run_command(
            [
                ffmpeg,
                "-y",
                "-hide_banner",
                "-nostats",
                "-i",
                str(voice_bus),
                "-af",
                f"atrim=duration={duration_s:.3f}",
                "-ar",
                "48000",
                "-ac",
                "2",
                "-c:a",
                "pcm_s24le",
                str(output_path),
            ]
        )
        return

    threshold = float(duck.get("threshold", 0.025))
    ratio = float(duck.get("ratio", 8.0))
    attack = float(duck.get("attack_ms", 20.0))
    release = float(duck.get("release_ms", 320.0))
    filters = (
        f"[1:a]aformat=sample_rates=48000:channel_layouts=stereo,"
        f"volume={bgm_gain_db}dB,apad=whole_dur={duration_s:.3f},"
        f"atrim=duration={duration_s:.3f}[bgm_bed];"
        f"[bgm_bed][0:a]sidechaincompress=threshold={threshold}:ratio={ratio}:"
        f"attack={attack}:release={release}[ducked_bgm];"
        f"[0:a][ducked_bgm]amix=inputs=2:duration=first:normalize=0,"
        f"atrim=duration={duration_s:.3f}[premaster]"
    )
    run_command(
        [
            ffmpeg,
            "-y",
            "-hide_banner",
            "-nostats",
            "-i",
            str(voice_bus),
            "-stream_loop",
            "-1",
            "-i",
            str(bgm_path),
            "-filter_complex",
            filters,
            "-map",
            "[premaster]",
            "-ar",
            "48000",
            "-ac",
            "2",
            "-c:a",
            "pcm_s24le",
            str(output_path),
        ]
    )


def load_json_object(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise AudioBuildError(f"JSON_ROOT_NOT_OBJECT:{path}")
    return value


def build_audio(
    plan_path: Path,
    output_dir: Path,
    profile_path: Path,
    ffmpeg: str,
) -> dict[str, Any]:
    if shutil.which(ffmpeg) is None:
        raise AudioBuildError(f"FFMPEG_NOT_FOUND:{ffmpeg}")
    plan = load_json_object(plan_path)
    profile = load_json_object(profile_path)
    if profile.get("profile_id") != "politics_documentary_broadcast_v4":
        raise AudioBuildError("V4_PROFILE_REQUIRED")
    settings = profile["audio"]
    target_i = float(settings["integrated_lufs"])
    target_tp = float(settings["true_peak_dbtp_max"])
    target_lra = float(settings["lra_max"])
    clip_tolerance = float(settings["clip_lufs_tolerance"])
    final_tolerance = float(settings["final_lufs_tolerance"])
    max_abs_gain_db = float(settings["max_abs_gain_db"])
    final_encode_headroom_db = float(settings.get("final_encode_headroom_db", -0.2))
    duration_ms = int(plan["duration_ms"])
    output_dir.mkdir(parents=True, exist_ok=True)
    normalized_dir = output_dir / "normalized_clips"
    normalized_dir.mkdir(parents=True, exist_ok=True)

    manifest: dict[str, Any] = {
        "schema_version": "politics_audio_loudness_manifest_v4",
        "profile_id": profile["profile_id"],
        "target": {
            "integrated_lufs": target_i,
            "true_peak_dbtp_max": target_tp,
            "lra_lu_max": target_lra,
            "clip_lufs_tolerance": clip_tolerance,
            "final_lufs_tolerance": final_tolerance,
            "max_abs_gain_db": max_abs_gain_db,
            "final_encode_headroom_db": final_encode_headroom_db,
        },
        "duration_ms": duration_ms,
        "voice_clips": [],
        "mix": {
            "voice_bus_normalized_first": True,
            "bgm_normalized_to_minus_14_lufs": False,
            "sfx_normalized_to_minus_14_lufs": False,
            "bgm_ducking_applied": False,
        },
        "errors": [],
        "gate": "FAIL_AUDIO_GAIN_OUTLIER",
    }

    prepared_clips: list[dict[str, Any]] = []
    allowed_roles = set(settings["voice_roles"])
    for clip in plan.get("voice_clips", []):
        clip_id = str(clip["id"])
        role = str(clip["role"])
        if role not in allowed_roles:
            raise AudioBuildError(f"UNSUPPORTED_VOICE_ROLE:{clip_id}:{role}")
        source_path = resolve_plan_path(plan_path, str(clip["path"]))
        if not source_path.is_file():
            raise AudioBuildError(f"VOICE_CLIP_NOT_FOUND:{clip_id}:{source_path}")
        normalized_path = normalized_dir / f"{clip_id}.wav"
        receipt = loudnorm_2pass(
            source_path,
            normalized_path,
            ffmpeg,
            target_i,
            target_tp,
            target_lra,
        )
        errors = assess_normalized_audio(
            receipt,
            target_i,
            target_tp,
            target_lra,
            clip_tolerance,
            max_abs_gain_db,
        )
        integrated_only = errors and all(
            error.startswith("INTEGRATED_LUFS_OUT_OF_RANGE") for error in errors
        )
        peak_limited = receipt["output"]["true_peak_dbtp"] >= target_tp - 0.1
        if integrated_only and peak_limited:
            conditioned_path = normalized_dir / f"{clip_id}.conditioned.wav"
            condition_peak_limited_speech(source_path, conditioned_path, ffmpeg)
            conditioned_receipt = loudnorm_2pass(
                conditioned_path,
                normalized_path,
                ffmpeg,
                target_i,
                target_tp,
                target_lra,
            )
            conditioned_receipt["conditioning"] = {
                "applied": True,
                "reason": "TRUE_PEAK_PREVENTED_INTEGRATED_TARGET",
                "filter": "acompressor",
                "conditioned_input": conditioned_receipt["input"],
            }
            conditioned_receipt["input"] = receipt["input"]
            conditioned_receipt["applied_gain_db"] = round(
                conditioned_receipt["output"]["integrated_lufs"]
                - receipt["input"]["integrated_lufs"],
                3,
            )
            receipt = conditioned_receipt
            errors = assess_normalized_audio(
                receipt,
                target_i,
                target_tp,
                target_lra,
                clip_tolerance,
                max_abs_gain_db,
            )
        start_ms = int(clip["start_ms"])
        entry = {
            "id": clip_id,
            "role": role,
            "source_path": str(source_path),
            "normalized_path": str(normalized_path.resolve()),
            "start_ms": start_ms,
            "normalization": "ffmpeg_loudnorm_2pass",
            **receipt,
            "status": "PASS" if not errors else "FAIL_AUDIO_GAIN_OUTLIER",
            "errors": errors,
        }
        manifest["voice_clips"].append(entry)
        manifest["errors"].extend(f"{clip_id}:{error}" for error in errors)
        prepared_clips.append(
            {
                "id": clip_id,
                "start_ms": start_ms,
                "normalized_path": normalized_path,
            }
        )

    voice_bus = output_dir / "voice_bus.wav"
    assemble_voice_bus(prepared_clips, duration_ms, voice_bus, ffmpeg)
    voice_bus_stats, voice_bus_raw = measure_loudness(
        voice_bus, ffmpeg, target_i, target_tp, target_lra
    )
    manifest["voice_bus"] = {
        "path": str(voice_bus.resolve()),
        "measurement": voice_bus_stats,
        "ffmpeg_measurement": voice_bus_raw,
    }

    bgm_path: Path | None = None
    bgm_gain_db = -24.0
    duck: dict[str, Any] = {}
    if plan.get("bgm"):
        bgm = plan["bgm"]
        bgm_path = resolve_plan_path(plan_path, str(bgm["path"]))
        if not bgm_path.is_file():
            raise AudioBuildError(f"BGM_NOT_FOUND:{bgm_path}")
        bgm_gain_db = float(bgm.get("gain_db", -24.0))
        duck = dict(bgm.get("ducking", {}))
        bgm_stats, bgm_raw = measure_loudness(
            bgm_path, ffmpeg, target_i, target_tp, target_lra
        )
        manifest["mix"].update(
            {
                "bgm_path": str(bgm_path),
                "bgm_input_measurement": bgm_stats,
                "bgm_ffmpeg_measurement": bgm_raw,
                "bgm_gain_db": bgm_gain_db,
                "bgm_ducking_applied": True,
                "ducking": duck,
            }
        )

    premaster = output_dir / "premaster.wav"
    mix_with_ducked_bgm(
        voice_bus,
        bgm_path,
        duration_ms,
        premaster,
        ffmpeg,
        bgm_gain_db,
        duck,
    )
    final_master = output_dir / "final_master.wav"
    run_command(
        [
            ffmpeg,
            "-y",
            "-hide_banner",
            "-nostats",
            "-i",
            str(premaster),
            "-af",
            f"volume={final_encode_headroom_db}dB",
            "-ar",
            "48000",
            "-ac",
            "2",
            "-c:a",
            "pcm_s24le",
            str(final_master),
        ]
    )
    premaster_stats, premaster_raw = measure_loudness(
        premaster, ffmpeg, target_i, target_tp, target_lra
    )
    final_stats, final_raw = measure_loudness(
        final_master, ffmpeg, target_i, target_tp, target_lra
    )
    final_receipt = {
        "input": premaster_stats,
        "output": final_stats,
        "applied_gain_db": final_encode_headroom_db,
        "normalization": "voice_bus_2pass_then_bgm_ducking_encode_headroom",
        "premaster_measurement": premaster_raw,
        "verification": final_raw,
    }
    final_errors = assess_normalized_audio(
        final_receipt,
        target_i,
        target_tp,
        target_lra,
        final_tolerance,
        max_abs_gain_db,
    )
    manifest["final_master"] = {
        "path": str(final_master.resolve()),
        "premaster_path": str(premaster.resolve()),
        **final_receipt,
        "status": "PASS" if not final_errors else "FAIL_AUDIO_GAIN_OUTLIER",
        "errors": final_errors,
    }
    manifest["errors"].extend(f"final_master:{error}" for error in final_errors)
    if not manifest["errors"]:
        manifest["gate"] = "PASS_AUDIO_LOUDNESS_NORMALIZATION"

    manifest_path = output_dir / "audio_loudness_manifest_v4.json"
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    manifest["manifest_path"] = str(manifest_path.resolve())
    return manifest


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Normalize V4 voice clips, duck BGM, and measure the final master."
    )
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--profile", type=Path, default=DEFAULT_PROFILE)
    parser.add_argument("--ffmpeg", default="ffmpeg")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    try:
        manifest = build_audio(
            args.plan.resolve(),
            args.output_dir.resolve(),
            args.profile.resolve(),
            args.ffmpeg,
        )
    except (AudioBuildError, OSError, KeyError, ValueError, json.JSONDecodeError) as exc:
        print(f"FAIL_AUDIO_GAIN_OUTLIER:{exc}", file=sys.stderr)
        return 2
    print(manifest["gate"])
    print(manifest["manifest_path"])
    return 0 if manifest["gate"] == "PASS_AUDIO_LOUDNESS_NORMALIZATION" else 3


if __name__ == "__main__":
    raise SystemExit(main())

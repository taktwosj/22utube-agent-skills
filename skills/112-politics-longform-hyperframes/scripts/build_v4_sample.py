#!/usr/bin/env python3
"""Create a disposable V4 HyperFrames project with real audio/video fixtures."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_DIR = SCRIPT_DIR.parent
EXAMPLE_DIR = SKILL_DIR / "examples" / "v4-validation-project"
V3_PROFILE = SKILL_DIR / "assets" / "political-documentary-defaults.json"
V4_PROFILE = SKILL_DIR / "assets" / "political-documentary-v4.json"
V3_ID = "politics_documentary_broadcast_v3"
V4_ID = "politics_documentary_broadcast_v4"

sys.path.insert(0, str(SCRIPT_DIR))
from normalize_v4_audio import AudioBuildError, build_audio  # noqa: E402
from resolve_visual_profile import resolve_profile  # noqa: E402


class SampleBuildError(RuntimeError):
    """Raised when the disposable validation project cannot be built safely."""


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def run(command: list[str]) -> None:
    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    if result.returncode != 0:
        raise SampleBuildError(
            f"COMMAND_FAILED:{' '.join(command)}\n{result.stdout}\n{result.stderr}".strip()
        )


def require_new_or_empty_directory(path: Path) -> None:
    if path.exists() and any(path.iterdir()):
        raise SampleBuildError(f"OUTPUT_DIRECTORY_NOT_EMPTY:{path}")
    path.mkdir(parents=True, exist_ok=True)


def generate_speech_fixture(
    ffmpeg: str,
    output_path: Path,
    text: str,
    voice: str,
    gain_db: float,
) -> None:
    source = f"flite=text='{text}':voice={voice}"
    run(
        [
            ffmpeg,
            "-y",
            "-hide_banner",
            "-nostats",
            "-f",
            "lavfi",
            "-i",
            source,
            "-af",
            f"volume={gain_db}dB,apad=pad_dur=0.25",
            "-ar",
            "48000",
            "-ac",
            "2",
            "-c:a",
            "pcm_s24le",
            str(output_path),
        ]
    )


def generate_bgm_fixture(ffmpeg: str, output_path: Path, duration_s: float) -> None:
    run(
        [
            ffmpeg,
            "-y",
            "-hide_banner",
            "-nostats",
            "-f",
            "lavfi",
            "-i",
            f"sine=frequency=96:duration={duration_s}:sample_rate=48000",
            "-f",
            "lavfi",
            "-i",
            f"sine=frequency=144:duration={duration_s}:sample_rate=48000",
            "-filter_complex",
            "[0:a]volume=0.18[a0];[1:a]volume=0.07[a1];"
            f"[a0][a1]amix=inputs=2:normalize=0,afade=t=in:st=0:d=0.8,"
            f"afade=t=out:st={duration_s - 0.8}:d=0.8[bgm]",
            "-map",
            "[bgm]",
            "-ar",
            "48000",
            "-ac",
            "2",
            "-c:a",
            "pcm_s24le",
            str(output_path),
        ]
    )


def generate_source_video(ffmpeg: str, output_path: Path) -> None:
    video_filter = (
        "drawgrid=width=96:height=72:thickness=1:color=0x2f6570@0.22,"
        "drawbox=x=80:y=70:w=1120:h=580:color=0x07131f@0.52:t=fill,"
        "drawbox=x=84:y=74:w=1112:h=572:color=0x2d727b@0.42:t=3,"
        "drawbox=x=520:y=410:w=280:h=170:color=0x183947@0.96:t=fill,"
        "drawbox=x=554:y=250:w=212:h=200:color=0x2d4f5d@0.92:t=fill,"
        "drawbox=x=80:y=610:w=1120:h=40:color=0x25e6d3@0.18:t=fill,"
        "vignette=PI/5,format=yuv420p"
    )
    run(
        [
            ffmpeg,
            "-y",
            "-hide_banner",
            "-nostats",
            "-f",
            "lavfi",
            "-i",
            "color=c=0x102a3a:s=1280x720:r=30:d=2.9",
            "-vf",
            video_filter,
            "-an",
            "-c:v",
            "libx264",
            "-preset",
            "veryfast",
            "-crf",
            "18",
            "-pix_fmt",
            "yuv420p",
            "-movflags",
            "+faststart",
            str(output_path),
        ]
    )


def write_json(path: Path, value: dict[str, Any]) -> None:
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def inline_timeline(project_dir: Path) -> None:
    index_path = project_dir / "index.html"
    timeline_path = project_dir / "src" / "timeline.js"
    marker = "/*__INLINE_V4_TIMELINE__*/"
    index_text = index_path.read_text(encoding="utf-8")
    if marker not in index_text:
        raise SampleBuildError("INLINE_TIMELINE_MARKER_MISSING")
    timeline_text = " ".join(
        line.strip()
        for line in timeline_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    )
    index_path.write_text(
        index_text.replace(marker, timeline_text), encoding="utf-8"
    )


def build_sample(output_dir: Path, requested_profile: str, ffmpeg: str) -> dict[str, Any]:
    profile_id, profile_path = resolve_profile(requested_profile)
    if profile_id != V4_ID:
        raise SampleBuildError(
            f"V4_EXPLICIT_OPT_IN_REQUIRED:selected={profile_id}:default={V3_ID}"
        )
    if shutil.which(ffmpeg) is None:
        raise SampleBuildError(f"FFMPEG_NOT_FOUND:{ffmpeg}")
    require_new_or_empty_directory(output_dir)
    shutil.copytree(EXAMPLE_DIR, output_dir, dirs_exist_ok=True)
    inline_timeline(output_dir)

    profile_copy = output_dir / "assets" / "profile" / profile_path.name
    profile_copy.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(profile_path, profile_copy)

    fixture_dir = output_dir / "assets" / "fixture"
    source_dir = output_dir / "assets" / "source"
    fixture_dir.mkdir(parents=True, exist_ok=True)
    source_dir.mkdir(parents=True, exist_ok=True)
    fixtures = [
        ("fact.wav", "The official record is confirmed.", "slt", -8.0),
        ("claim.wav", "This allegation remains unverified.", "kal", -3.0),
        ("conclusion.wav", "Independent review is the alternative.", "slt", -11.0),
        ("source_speech.wav", "The source statement matches the public record.", "kal", -6.0),
    ]
    for filename, phrase, voice, gain_db in fixtures:
        generate_speech_fixture(
            ffmpeg, fixture_dir / filename, phrase, voice, gain_db
        )
    generate_bgm_fixture(ffmpeg, fixture_dir / "bgm.wav", 21.5)
    generate_source_video(ffmpeg, source_dir / "source-video.mp4")

    srt_path = output_dir / "source_semantic_sample.srt"
    srt_path.write_text(
        "1\n00:00:02,800 --> 00:00:04,500\n공식 기록이 첫 번째 시간축을 확정합니다.\n\n"
        "2\n00:00:04,700 --> 00:00:06,400\n이 주장은 아직 확인되지 않았습니다.\n\n"
        "3\n00:00:06,700 --> 00:00:08,200\n독립 검증 절차가 대안입니다.\n\n"
        "4\n00:00:08,800 --> 00:00:10,600\n핵심 발언을 원본 영상과 대조합니다.\n",
        encoding="utf-8",
    )

    audio_plan = {
        "schema_version": "politics_audio_plan_v4",
        "duration_ms": 21500,
        "voice_clips": [
            {
                "id": "tts_fact",
                "role": "TTS",
                "path": "assets/fixture/fact.wav",
                "start_ms": 2800,
            },
            {
                "id": "tts_claim",
                "role": "TTS",
                "path": "assets/fixture/claim.wav",
                "start_ms": 4700,
            },
            {
                "id": "tts_conclusion",
                "role": "TTS",
                "path": "assets/fixture/conclusion.wav",
                "start_ms": 6700,
            },
            {
                "id": "source_speech",
                "role": "SOURCE_SPEECH",
                "path": "assets/fixture/source_speech.wav",
                "start_ms": 8800,
            },
        ],
        "bgm": {
            "path": "assets/fixture/bgm.wav",
            "gain_db": -24.0,
            "normalize_to_minus_14_lufs": False,
            "ducking": {
                "threshold": 0.025,
                "ratio": 8.0,
                "attack_ms": 20,
                "release_ms": 320,
            },
        },
        "sfx": {
            "normalize_to_minus_14_lufs": False,
        },
    }
    audio_plan_path = output_dir / "audio_plan_v4.json"
    write_json(audio_plan_path, audio_plan)
    audio_manifest = build_audio(
        audio_plan_path,
        output_dir / "assets" / "audio",
        V4_PROFILE,
        ffmpeg,
    )
    if audio_manifest["gate"] != "PASS_AUDIO_LOUDNESS_NORMALIZATION":
        raise SampleBuildError(audio_manifest["gate"])

    timeline_path = output_dir / "visual_timeline_v4.json"
    build_manifest = {
        "schema_version": "politics_hyperframes_build_manifest_v4",
        "profile_id": V4_ID,
        "profile_sha256": sha256_file(profile_path),
        "profile_copy": str(profile_copy.relative_to(output_dir)).replace("\\", "/"),
        "profile_selection": "explicit_user_opt_in",
        "rollback_profile_id": V3_ID,
        "rollback_profile_sha256": sha256_file(V3_PROFILE),
        "v3_profile_modified": False,
        "template_lock_modified": False,
        "visual_timeline_sha256": sha256_file(timeline_path),
        "source_video_sha256": sha256_file(source_dir / "source-video.mp4"),
        "source_srt_sha256": sha256_file(srt_path),
        "audio_manifest": str(
            Path(audio_manifest["manifest_path"]).relative_to(output_dir)
        ).replace("\\", "/"),
        "audio_gate": audio_manifest["gate"],
        "required_gates": [
            "PASS_CHAPTER_ACTIVE_STATE",
            "PASS_SEMANTIC_VISUAL_SYNC",
            "PASS_SOURCE_VIDEO_FOCUS_LINES",
            "PASS_AUDIO_LOUDNESS_NORMALIZATION",
        ],
    }
    build_manifest_path = output_dir / "build_manifest_v4.json"
    write_json(build_manifest_path, build_manifest)
    return {
        "status": "V4_SAMPLE_PROJECT_READY",
        "project": str(output_dir),
        "build_manifest": str(build_manifest_path),
        "audio_gate": audio_manifest["gate"],
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--profile", default=V3_ID)
    parser.add_argument("--ffmpeg", default="ffmpeg")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        result = build_sample(
            args.output.resolve(), str(args.profile), str(args.ffmpeg)
        )
    except (
        SampleBuildError,
        AudioBuildError,
        OSError,
        ValueError,
        KeyError,
        json.JSONDecodeError,
    ) as exc:
        print(f"V4_SAMPLE_BUILD_FAIL:{exc}", file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Validate V4 gates from rendered pixels and measured render audio."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any, Callable

from PIL import Image, ImageChops, ImageStat


SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_DIR = SCRIPT_DIR.parent
DEFAULT_PROFILE = SKILL_DIR / "assets" / "political-documentary-v4.json"
sys.path.insert(0, str(SCRIPT_DIR))
from normalize_v4_audio import AudioBuildError, measure_loudness  # noqa: E402


class EvidenceError(RuntimeError):
    """Raised when render evidence cannot be inspected."""


def run(command: list[str]) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    if result.returncode != 0:
        raise EvidenceError(
            f"COMMAND_FAILED:{' '.join(command)}\n{result.stdout}\n{result.stderr}".strip()
        )
    return result


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise EvidenceError(f"JSON_ROOT_NOT_OBJECT:{path}")
    return value


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def probe_render(render_path: Path, ffprobe: str) -> dict[str, Any]:
    result = run(
        [
            ffprobe,
            "-v",
            "error",
            "-show_entries",
            "format=duration:stream=index,codec_type,codec_name,width,height,sample_rate,channels",
            "-of",
            "json",
            str(render_path),
        ]
    )
    return json.loads(result.stdout)


def extract_frame(
    render_path: Path,
    time_ms: int,
    output_path: Path,
    ffmpeg: str,
) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    run(
        [
            ffmpeg,
            "-y",
            "-hide_banner",
            "-nostats",
            "-ss",
            f"{time_ms / 1000.0:.3f}",
            "-i",
            str(render_path),
            "-frames:v",
            "1",
            "-vf",
            "scale=1920:1080",
            str(output_path),
        ]
    )
    with Image.open(output_path) as image:
        if image.size != (1920, 1080):
            raise EvidenceError(f"FRAME_SIZE_INVALID:{output_path}:{image.size}")


def crop_box(values: list[int]) -> tuple[int, int, int, int]:
    x, y, width, height = (int(value) for value in values)
    return x, y, x + width, y + height


def image_pixels(image: Image.Image):
    flattened = getattr(image, "get_flattened_data", None)
    return flattened() if flattened is not None else image.getdata()


def pixel_score(
    image: Image.Image,
    region: list[int],
    predicate: Callable[[int, int, int], bool],
) -> int:
    rgb = image.convert("RGB").crop(crop_box(region))
    return sum(
        1 for red, green, blue in image_pixels(rgb) if predicate(red, green, blue)
    )


def cyan_predicate(red: int, green: int, blue: int) -> bool:
    return green >= 150 and blue >= 125 and red <= 130 and green >= red * 1.25


def orange_predicate(red: int, green: int, blue: int) -> bool:
    return red >= 175 and 75 <= green <= 195 and blue <= 135 and red >= green * 1.12


def green_predicate(red: int, green: int, blue: int) -> bool:
    return green >= 140 and red <= 135 and blue <= 155 and green >= red * 1.18


def image_difference_ratio(
    first: Image.Image,
    second: Image.Image,
    region: list[int],
    threshold: int = 24,
) -> float:
    first_crop = first.convert("RGB").crop(crop_box(region))
    second_crop = second.convert("RGB").crop(crop_box(region))
    difference = ImageChops.difference(first_crop, second_crop)
    pixels = list(image_pixels(difference))
    if not pixels:
        return 0.0
    changed = sum(1 for red, green, blue in pixels if max(red, green, blue) >= threshold)
    return changed / len(pixels)


def mean_luminance(image: Image.Image, region: list[int]) -> float:
    crop = image.convert("L").crop(crop_box(region))
    return float(ImageStat.Stat(crop).mean[0])


def verify_chapters(
    timeline: dict[str, Any],
    render_path: Path,
    frame_dir: Path,
    ffmpeg: str,
) -> tuple[list[dict[str, Any]], list[str]]:
    errors: list[str] = []
    evidence: list[dict[str, Any]] = []
    regions = timeline["chapter_box_regions"]
    hashes: set[str] = set()
    for chapter in timeline["chapters"]:
        chapter_id = str(chapter["chapter_id"])
        time_ms = int(chapter["active_frame_ms"])
        frame_path = frame_dir / f"chapter_{chapter_id}_current_{time_ms}ms.png"
        extract_frame(render_path, time_ms, frame_path, ffmpeg)
        with Image.open(frame_path) as image:
            scores = {
                key: pixel_score(image, values, cyan_predicate)
                for key, values in regions.items()
            }
        expected = scores[chapter_id]
        others = [score for key, score in scores.items() if key != chapter_id]
        if expected < 400:
            errors.append(f"CHAPTER_{chapter_id}_CYAN_SCORE_LOW:{expected}")
        if others and expected <= max(others) * 1.2:
            errors.append(
                f"CHAPTER_{chapter_id}_NOT_DOMINANT:{expected}:others={scores}"
            )
        frame_hash = sha256_file(frame_path)
        hashes.add(frame_hash)
        evidence.append(
            {
                "chapter_id": chapter_id,
                "time_ms": time_ms,
                "frame": str(frame_path.resolve()),
                "sha256": frame_hash,
                "cyan_scores": scores,
            }
        )
    if len(hashes) != 4:
        errors.append(f"CHAPTER_FRAME_HASHES_NOT_UNIQUE:{len(hashes)}")
    return evidence, errors


def verify_semantic_sync(
    timeline: dict[str, Any],
    render_path: Path,
    frame_dir: Path,
    ffmpeg: str,
) -> tuple[list[dict[str, Any]], list[str]]:
    errors: list[str] = []
    evidence: list[dict[str, Any]] = []
    predicates: dict[str, Callable[[int, int, int], bool]] = {
        "verified_fact": cyan_predicate,
        "allegation_unverified": orange_predicate,
        "conclusion_alternative": green_predicate,
    }
    base_path = frame_dir / "semantic_base_2600ms.png"
    after_path = frame_dir / "semantic_after_8350ms.png"
    extract_frame(render_path, 2600, base_path, ffmpeg)
    extract_frame(render_path, 8350, after_path, ffmpeg)
    hashes: set[str] = set()
    events = timeline["semantic_events"]
    with Image.open(base_path) as base_image, Image.open(after_path) as after_image:
        for event in events:
            event_id = str(event["id"])
            role = str(event["semantic_role"])
            time_ms = int(event["evidence_frame_ms"])
            sync_delta = abs(int(event["start_ms"]) - int(event["srt_start_ms"]))
            if sync_delta > int(timeline["sync_tolerance_ms"]):
                errors.append(f"SEMANTIC_SYNC_OUT_OF_RANGE:{event_id}:{sync_delta}ms")
            frame_path = frame_dir / f"semantic_{event_id}_{time_ms}ms.png"
            extract_frame(render_path, time_ms, frame_path, ffmpeg)
            predicate = predicates.get(role)
            if predicate is None:
                errors.append(f"SEMANTIC_ROLE_UNSUPPORTED:{event_id}:{role}")
                continue
            with Image.open(frame_path) as image:
                active_score = pixel_score(image, event["region"], predicate)
                base_score = pixel_score(base_image, event["region"], predicate)
                active_luminance = mean_luminance(image, event["region"])
                base_luminance = mean_luminance(base_image, event["region"])
            if active_score < max(240, base_score * 2.2):
                errors.append(
                    f"SEMANTIC_ACTIVE_COLOR_LOW:{event_id}:active={active_score}:base={base_score}"
                )
            if active_luminance <= base_luminance + 2.0:
                errors.append(
                    f"SEMANTIC_ACTIVE_LUMINANCE_LOW:{event_id}:"
                    f"active={active_luminance:.3f}:base={base_luminance:.3f}"
                )
            frame_hash = sha256_file(frame_path)
            hashes.add(frame_hash)
            evidence.append(
                {
                    "id": event_id,
                    "semantic_role": role,
                    "start_ms": int(event["start_ms"]),
                    "srt_start_ms": int(event["srt_start_ms"]),
                    "sync_delta_ms": sync_delta,
                    "time_ms": time_ms,
                    "frame": str(frame_path.resolve()),
                    "sha256": frame_hash,
                    "active_color_score": active_score,
                    "base_color_score": base_score,
                    "active_luminance": round(active_luminance, 3),
                    "base_luminance": round(base_luminance, 3),
                }
            )

        conclusion = next(
            event for event in events if event["semantic_role"] == "conclusion_alternative"
        )
        active_entry = next(
            entry for entry in evidence if entry["semantic_role"] == "conclusion_alternative"
        )
        after_score = pixel_score(after_image, conclusion["region"], green_predicate)
        if after_score >= active_entry["active_color_score"] * 0.82:
            errors.append(
                "LAST_ELEMENT_HELD_ACTIVE:"
                f"active={active_entry['active_color_score']}:after={after_score}"
            )
    if len(hashes) != len(events):
        errors.append(f"SEMANTIC_FRAME_HASHES_NOT_UNIQUE:{len(hashes)}")
    return evidence, errors


def verify_focus_lines(
    timeline: dict[str, Any],
    render_path: Path,
    project_dir: Path,
    frame_dir: Path,
    ffmpeg: str,
) -> tuple[dict[str, Any], list[str]]:
    errors: list[str] = []
    event = timeline["focus_events"][0]
    paths: dict[str, Path] = {}
    for label in ("before", "during", "after"):
        time_ms = int(event[f"{label}_frame_ms"])
        frame_path = frame_dir / f"focus_{label}_{time_ms}ms.png"
        extract_frame(render_path, time_ms, frame_path, ffmpeg)
        paths[label] = frame_path
    with (
        Image.open(paths["before"]) as before,
        Image.open(paths["during"]) as during,
        Image.open(paths["after"]) as after,
    ):
        during_before = image_difference_ratio(
            during, before, event["focus_region"], threshold=26
        )
        during_after = image_difference_ratio(
            during, after, event["focus_region"], threshold=26
        )
        before_after = image_difference_ratio(
            before, after, event["focus_region"], threshold=26
        )
        protected_diffs = {
            name: image_difference_ratio(during, before, region, threshold=26)
            for name, region in event["protected_regions"].items()
        }
    if during_before < 0.001:
        errors.append(f"FOCUS_LINES_NOT_VISIBLE:{during_before:.6f}")
    if during_after < 0.001:
        errors.append(f"FOCUS_LINES_NOT_GONE_AFTER:{during_after:.6f}")
    if during_before > 0.16:
        errors.append(f"FOCUS_OVERLAY_TOO_DENSE:{during_before:.6f}")
    if before_after > 0.012:
        errors.append(f"FOCUS_BASE_CHANGED_TOO_MUCH:{before_after:.6f}")
    for name, ratio in protected_diffs.items():
        if ratio > 0.012:
            errors.append(f"FOCUS_PROTECTED_REGION_OCCLUDED:{name}:{ratio:.6f}")
    enter_ms = int(event["enter_end_ms"]) - int(event["start_ms"])
    visible_ms = int(event["end_ms"]) - int(event["enter_end_ms"])
    if enter_ms != 200:
        errors.append(f"FOCUS_ENTER_DURATION_INVALID:{enter_ms}")
    if not 600 <= visible_ms <= 1200:
        errors.append(f"FOCUS_FADE_DURATION_INVALID:{visible_ms}")
    html = (project_dir / "index.html").read_text(encoding="utf-8")
    if '<svg\n              id="source-focus-lines"' not in html and 'id="source-focus-lines"' not in html:
        errors.append("FOCUS_SVG_NOT_FOUND")
    if "source-focus-lines" in html and "<rect" in html.split("source-focus-lines", 1)[1].split("</svg>", 1)[0]:
        errors.append("FOCUS_OPAQUE_RECT_FORBIDDEN")
    evidence = {
        "id": event["id"],
        "enter_ms": enter_ms,
        "fade_ms": visible_ms,
        "frames": {
            label: {
                "time_ms": int(event[f"{label}_frame_ms"]),
                "path": str(path.resolve()),
                "sha256": sha256_file(path),
            }
            for label, path in paths.items()
        },
        "pixel_difference": {
            "during_vs_before": round(during_before, 6),
            "during_vs_after": round(during_after, 6),
            "before_vs_after": round(before_after, 6),
            "protected_regions": {
                name: round(value, 6) for name, value in protected_diffs.items()
            },
        },
    }
    return evidence, errors


def verify_audio(
    project_dir: Path,
    render_path: Path,
    profile: dict[str, Any],
    ffmpeg: str,
) -> tuple[dict[str, Any], list[str]]:
    errors: list[str] = []
    build_manifest = load_json(project_dir / "build_manifest_v4.json")
    audio_manifest_path = project_dir / build_manifest["audio_manifest"]
    audio_manifest = load_json(audio_manifest_path)
    settings = profile["audio"]
    target_i = float(settings["integrated_lufs"])
    target_tp = float(settings["true_peak_dbtp_max"])
    target_lra = float(settings["lra_max"])
    render_stats, render_raw = measure_loudness(
        render_path, ffmpeg, target_i, target_tp, target_lra
    )
    if audio_manifest.get("gate") != "PASS_AUDIO_LOUDNESS_NORMALIZATION":
        errors.append(f"AUDIO_MANIFEST_GATE_FAIL:{audio_manifest.get('gate')}")
    roles = {clip.get("role") for clip in audio_manifest.get("voice_clips", [])}
    if not {"TTS", "SOURCE_SPEECH"}.issubset(roles):
        errors.append(f"VOICE_ROLES_MISSING:{sorted(role for role in roles if role)}")
    for clip in audio_manifest.get("voice_clips", []):
        if clip.get("normalization") != "ffmpeg_loudnorm_2pass":
            errors.append(f"CLIP_NOT_2PASS:{clip.get('id')}")
        if clip.get("status") != "PASS":
            errors.append(f"CLIP_STATUS_FAIL:{clip.get('id')}:{clip.get('status')}")
        for required in ("input", "output", "applied_gain_db"):
            if required not in clip:
                errors.append(f"CLIP_METRIC_MISSING:{clip.get('id')}:{required}")
    mix = audio_manifest.get("mix", {})
    if mix.get("bgm_normalized_to_minus_14_lufs") is not False:
        errors.append("BGM_WAS_NORMALIZED_TO_VOICE_TARGET")
    if mix.get("sfx_normalized_to_minus_14_lufs") is not False:
        errors.append("SFX_WAS_NORMALIZED_TO_VOICE_TARGET")
    if mix.get("bgm_ducking_applied") is not True:
        errors.append("BGM_DUCKING_NOT_APPLIED")
    if abs(render_stats["integrated_lufs"] - target_i) > 0.7:
        errors.append(
            f"RENDER_LUFS_OUT_OF_RANGE:{render_stats['integrated_lufs']:.3f}"
        )
    if render_stats["true_peak_dbtp"] > target_tp:
        errors.append(
            f"RENDER_TRUE_PEAK_OUT_OF_RANGE:{render_stats['true_peak_dbtp']:.3f}"
        )
    if render_stats["lra_lu"] > target_lra + 0.1:
        errors.append(f"RENDER_LRA_OUT_OF_RANGE:{render_stats['lra_lu']:.3f}")
    table = [
        {
            "id": clip["id"],
            "role": clip["role"],
            "input_lufs": clip["input"]["integrated_lufs"],
            "output_lufs": clip["output"]["integrated_lufs"],
            "true_peak_dbtp": clip["output"]["true_peak_dbtp"],
            "lra_lu": clip["output"]["lra_lu"],
            "applied_gain_db": clip["applied_gain_db"],
        }
        for clip in audio_manifest.get("voice_clips", [])
    ]
    table.append(
        {
            "id": "FINAL_RENDER",
            "role": "MASTER",
            "input_lufs": None,
            "output_lufs": render_stats["integrated_lufs"],
            "true_peak_dbtp": render_stats["true_peak_dbtp"],
            "lra_lu": render_stats["lra_lu"],
            "applied_gain_db": audio_manifest["final_master"]["applied_gain_db"],
        }
    )
    return {
        "audio_manifest": str(audio_manifest_path.resolve()),
        "render_measurement": render_stats,
        "render_ffmpeg_measurement": render_raw,
        "measurement_table": table,
    }, errors


def validate(
    project_dir: Path,
    render_path: Path,
    output_dir: Path,
    profile_path: Path,
    ffmpeg: str,
    ffprobe: str,
) -> dict[str, Any]:
    if shutil.which(ffmpeg) is None or shutil.which(ffprobe) is None:
        raise EvidenceError("FFMPEG_OR_FFPROBE_NOT_FOUND")
    for path in (project_dir, render_path, profile_path):
        if not path.exists():
            raise EvidenceError(f"REQUIRED_PATH_MISSING:{path}")
    profile = load_json(profile_path)
    timeline = load_json(project_dir / "visual_timeline_v4.json")
    build_manifest = load_json(project_dir / "build_manifest_v4.json")
    if build_manifest.get("profile_sha256") != sha256_file(profile_path):
        raise EvidenceError("V4_PROFILE_SHA_MISMATCH")
    output_dir.mkdir(parents=True, exist_ok=True)
    frame_dir = output_dir / "frames"
    render_probe = probe_render(render_path, ffprobe)
    streams = render_probe.get("streams", [])
    video_streams = [stream for stream in streams if stream.get("codec_type") == "video"]
    audio_streams = [stream for stream in streams if stream.get("codec_type") == "audio"]
    if not video_streams or not audio_streams:
        raise EvidenceError("RENDER_VIDEO_OR_AUDIO_STREAM_MISSING")
    video = video_streams[0]
    if (int(video.get("width", 0)), int(video.get("height", 0))) != (1920, 1080):
        raise EvidenceError(f"RENDER_DIMENSIONS_INVALID:{video}")
    duration = float(render_probe["format"]["duration"])
    if duration < 21.4:
        raise EvidenceError(f"RENDER_DURATION_TOO_SHORT:{duration}")

    chapter_evidence, chapter_errors = verify_chapters(
        timeline, render_path, frame_dir, ffmpeg
    )
    semantic_evidence, semantic_errors = verify_semantic_sync(
        timeline, render_path, frame_dir, ffmpeg
    )
    focus_evidence, focus_errors = verify_focus_lines(
        timeline, render_path, project_dir, frame_dir, ffmpeg
    )
    audio_evidence, audio_errors = verify_audio(
        project_dir, render_path, profile, ffmpeg
    )
    gates = {
        "PASS_CHAPTER_ACTIVE_STATE": not chapter_errors,
        "PASS_SEMANTIC_VISUAL_SYNC": not semantic_errors,
        "PASS_SOURCE_VIDEO_FOCUS_LINES": not focus_errors,
        "PASS_AUDIO_LOUDNESS_NORMALIZATION": not audio_errors,
    }
    errors = {
        "PASS_CHAPTER_ACTIVE_STATE": chapter_errors,
        "PASS_SEMANTIC_VISUAL_SYNC": semantic_errors,
        "PASS_SOURCE_VIDEO_FOCUS_LINES": focus_errors,
        "PASS_AUDIO_LOUDNESS_NORMALIZATION": audio_errors,
    }
    manifest = {
        "schema_version": "politics_v4_dynamic_evidence_manifest_v1",
        "profile_id": profile["profile_id"],
        "render": {
            "path": str(render_path.resolve()),
            "sha256": sha256_file(render_path),
            "duration_s": duration,
            "probe": render_probe,
        },
        "gates": gates,
        "errors": errors,
        "chapter_evidence": chapter_evidence,
        "semantic_evidence": semantic_evidence,
        "focus_evidence": focus_evidence,
        "audio_evidence": audio_evidence,
        "result": "PASS" if all(gates.values()) else "FAIL",
    }
    manifest_path = output_dir / "v4_dynamic_evidence_manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    manifest["manifest_path"] = str(manifest_path.resolve())
    return manifest


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", type=Path, required=True)
    parser.add_argument("--render", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--profile", type=Path, default=DEFAULT_PROFILE)
    parser.add_argument("--ffmpeg", default="ffmpeg")
    parser.add_argument("--ffprobe", default="ffprobe")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        manifest = validate(
            args.project.resolve(),
            args.render.resolve(),
            args.output_dir.resolve(),
            args.profile.resolve(),
            args.ffmpeg,
            args.ffprobe,
        )
    except (
        EvidenceError,
        AudioBuildError,
        OSError,
        ValueError,
        KeyError,
        json.JSONDecodeError,
    ) as exc:
        print(f"V4_EVIDENCE_FAIL:{exc}", file=sys.stderr)
        return 2
    for gate, passed in manifest["gates"].items():
        print(gate if passed else f"FAIL:{gate}")
        for error in manifest["errors"][gate]:
            print(f"  {error}")
    print(manifest["manifest_path"])
    return 0 if manifest["result"] == "PASS" else 3


if __name__ == "__main__":
    raise SystemExit(main())

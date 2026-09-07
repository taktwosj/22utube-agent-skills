# -*- coding: utf-8 -*-
"""빌드가 끝난 V8 프로젝트를 CapCut 이 바로 열 수 있는 상태로 만든다.

빌더가 내놓은 그대로 열면 두 가지가 사람을 기다리게 한다.

1. 미디어마다 `C:/__CAPCUT_RELINK_REQUIRED__/...` 라는 없는 경로가 적혀 있다.
   사람이 CapCut 에서 한 번 이어 주라는 뜻인데, 카드가 백 개를 넘으면 CapCut 이
   없는 경로를 하나씩 찾다가 창이 멈춘다. 미디어 폴더는 빌드 시점에 이미
   확정돼 있으므로 여기서 실제 경로로 이어 둔다. `draft_meta_info.json` 까지
   함께 고쳐야 한다. 타임라인만 고치면 CapCut 의 미디어 목록이 여전히 없는
   파일을 찾는다.

2. 음량 노멀라이즈가 꺼진 채로 남는다. 빌더는 켜서 붙이지만 id 재발급 단계를
   지나면서 근본 템플릿의 꺼진 항목으로 대체된다. 여기서 소리 나는 세그먼트만
   골라 다시 켜고, CapCut 이 열면서 재는 값을 ffmpeg 로 미리 재서 적어 둔다.
   그래야 여는 순간 멈추지 않는다.

사용:
    python finalize_politics_media_and_loudness.py --project <프로젝트 폴더> \
        --media-dir <미디어 폴더> [--target-lufs -14.0] [--workers 8]

CapCut 이 열려 있으면 아무것도 하지 않는다.
"""
from __future__ import annotations

import argparse
import json
import os
import pathlib
import re
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor

CANONICAL = ("draft_content.json", "template-2.tmp")
META = "draft_meta_info.json"
SENTINEL = "C:/__CAPCUT_RELINK_REQUIRED__"
MEDIA_SUFFIX = (".mp4", ".wav", ".m4a", ".mp3", ".png", ".jpg", ".jpeg")
AUDIBLE_SUFFIX = (".mp4", ".wav", ".m4a", ".mp3")


def require_capcut_closed() -> None:
    if os.name != "nt":
        return
    probe = subprocess.run(["tasklist", "/FI", "IMAGENAME eq CapCut.exe"],
                           capture_output=True)
    if b"CapCut.exe" in probe.stdout:
        raise SystemExit("CAPCUT_MUST_BE_CLOSED")


def canonical_files(root: pathlib.Path) -> list[pathlib.Path]:
    out = [root / name for name in CANONICAL] + [root / META]
    for timeline in (root / "Timelines").glob("*"):
        if timeline.is_dir():
            out += [timeline / name for name in CANONICAL]
    return [p for p in out if p.is_file()]


def relink(node, media: pathlib.Path, missing: list[str]) -> None:
    """자리표시자 경로를 미디어 폴더의 실제 파일로 바꾼다."""
    if isinstance(node, dict):
        for key, value in node.items():
            if isinstance(value, str) and value.startswith(SENTINEL):
                name = value.rsplit("/", 1)[-1]
                target = media / name
                if target.is_file():
                    node[key] = str(target).replace("\\", "/")
                else:
                    missing.append(name)
            else:
                relink(value, media, missing)
    elif isinstance(node, list):
        for value in node:
            relink(value, media, missing)


def measure(path: str, target: float) -> tuple[float, float] | None:
    """ffmpeg loudnorm 분석. (통합 음량, 트루 피크)."""
    probe = subprocess.run(
        ["ffmpeg", "-nostdin", "-hide_banner", "-i", path,
         "-af", f"loudnorm=I={target}:TP=-1:LRA=11:print_format=json",
         "-f", "null", "-"],
        capture_output=True)
    blocks = re.findall(r"\{[^{}]*\"input_i\"[^{}]*\}",
                        probe.stderr.decode("utf-8", "replace"), re.S)
    if not blocks:
        return None
    try:
        parsed = json.loads(blocks[-1])
        return float(parsed["input_i"]), float(parsed["input_tp"])
    except (KeyError, ValueError, json.JSONDecodeError):
        return None


def audible_loudness(document: dict) -> dict[str, str]:
    """소리 나는 세그먼트가 물고 있는 loudness id -> 미디어 경로."""
    materials: dict[str, dict] = {}
    for group in ("videos", "audios"):
        for item in document["materials"].get(group, []):
            materials[str(item["id"])] = item
    known = {str(item["id"]) for item in document["materials"].get("loudnesses", [])}
    picked: dict[str, str] = {}
    for track in document["tracks"]:
        if track["type"] not in ("video", "audio"):
            continue
        for segment in track["segments"]:
            material = materials.get(str(segment.get("material_id")))
            if not material:
                continue
            path = str(material.get("path", ""))
            if not path.lower().endswith(AUDIBLE_SUFFIX):
                continue
            if float(segment.get("volume", 0)) <= 0:
                continue
            for ref in segment.get("extra_material_refs", []):
                if str(ref) in known:
                    picked[str(ref)] = path
                    break
    return picked


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", type=pathlib.Path, required=True)
    parser.add_argument("--media-dir", type=pathlib.Path, required=True)
    parser.add_argument("--target-lufs", type=float, default=-14.0)
    parser.add_argument("--workers", type=int, default=8)
    parser.add_argument("--report", type=pathlib.Path)
    args = parser.parse_args()

    require_capcut_closed()
    root = args.project
    media = args.media_dir.resolve()
    if not root.is_dir():
        raise SystemExit(f"PROJECT_NOT_FOUND: {root}")
    if not media.is_dir():
        raise SystemExit(f"MEDIA_DIR_NOT_FOUND: {media}")
    files = canonical_files(root)
    if not files:
        raise SystemExit(f"DRAFT_NOT_FOUND: {root}")

    # 1) 없는 경로를 실제 파일로 잇는다
    linked, missing_all = 0, []
    for path in files:
        document = json.loads(path.read_text(encoding="utf-8"))
        before = path.read_text(encoding="utf-8").count(SENTINEL)
        missing: list[str] = []
        relink(document, media, missing)
        path.write_text(json.dumps(document, ensure_ascii=False), encoding="utf-8")
        after = path.read_text(encoding="utf-8").count(SENTINEL)
        linked += before - after
        missing_all += missing
    if missing_all:
        raise SystemExit("MEDIA_FILE_MISSING: " + ", ".join(sorted(set(missing_all))[:5]))
    print(f"미디어 경로 {linked} 건 연결")

    # 2) 노멀라이즈를 켜고 그 값을 미리 재 둔다
    document = json.loads(files[0].read_text(encoding="utf-8"))
    picked = audible_loudness(document)
    if not picked:
        print("소리 나는 세그먼트가 없다. 음량 단계는 건너뛴다")
        return 0
    paths = sorted(set(picked.values()))
    print(f"소리 나는 세그먼트 {len(picked)}개, 파일 {len(paths)}개 측정")
    with ThreadPoolExecutor(max_workers=max(1, args.workers)) as pool:
        measured = dict(zip(paths, pool.map(lambda p: measure(p, args.target_lufs), paths)))
    good = {k: v for k, v in measured.items() if v}
    if len(good) != len(paths):
        raise SystemExit(f"LOUDNESS_MEASURE_FAILED: {len(paths) - len(good)} 개")

    values = {}
    for loudness_id, path in picked.items():
        avg, peak = good[path]
        values[loudness_id] = {"avg_loudness": avg, "peak_loudness": peak}

    enabled = 0
    for path in files:
        if path.name == META:
            continue
        document = json.loads(path.read_text(encoding="utf-8"))
        count = 0
        for item in document.get("materials", {}).get("loudnesses", []):
            if str(item["id"]) in values:
                item["enable"] = True
                item["target_loudness"] = args.target_lufs
                item["loudness_param"] = values[str(item["id"])]
                count += 1
        path.write_text(json.dumps(document, ensure_ascii=False), encoding="utf-8")
        enabled = max(enabled, count)
    print(f"음량 노멀라이즈 {enabled} 건 켜고 값 기록 (목표 {args.target_lufs} LUFS)")

    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps({
            "schema": "politics-longform-finalize.v1",
            "status": "PASS",
            "project": str(root),
            "media_dir": str(media),
            "relinked": linked,
            "normalized": enabled,
            "target_lufs": args.target_lufs,
        }, ensure_ascii=False, indent=1), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())

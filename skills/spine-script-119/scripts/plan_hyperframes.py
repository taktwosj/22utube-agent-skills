# -*- coding: utf-8 -*-
"""만들어야 할 하이퍼프레임 장면표를 뽑는다.

나레이션 카드는 전부 움직이는 영상이다. 카드는 평균 삼사 초라 한 장에 한 편씩
만들면 짧은 클립이 줄줄이 이어져 화면이 계속 끊긴다. 연속한 카드를 열 초 안팎으로
묶어 한 장면으로 만들고, 카드마다 그 장면의 다른 구간을 가져간다.

화면 문법은 `hyperframes-politics-119` 를 따른다. 장면마다 시각 문법을 다르게 배정하고,
나레이션 원고를 쓰기 전에 배정을 끝낸다. 민주 블루 인셋 카드 같은 정지 이미지 카드로
대체하지 않는다. 장면표에 적을 것: 시각 문법 번호, 비트 수, 대비축, 주장 라벨 필요 여부.

    python plan_hyperframes.py --root E:\\22utube\\<episode_id>
    python plan_hyperframes.py --root <root> --missing      아직 없는 것만
    python plan_hyperframes.py --root <root> --tsv          표로
"""
from __future__ import annotations

import io
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _common import hyperframe_files, narration_order, resolve_root, root_parser  # noqa: E402

if hasattr(sys.stdout, "buffer"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")


def timecode(us: int) -> str:
    s = us / 1_000_000
    return f"{int(s // 60):02d}:{s % 60:06.3f}"


def main() -> None:
    parser = root_parser("하이퍼프레임 장면표")
    parser.add_argument("--missing", action="store_true", help="영상이 없는 것만")
    parser.add_argument("--target", type=float, default=10.0, help="장면 목표 길이(초)")
    parser.add_argument("--tsv", action="store_true", help="탭 구분 표로")
    args = parser.parse_args()
    root = resolve_root(args)

    from _common import scene_plan  # 지연 import: 타임라인이 있어야 한다
    covered = hyperframe_files(root)
    only = None
    if args.missing:
        missing_ids = [c for c in narration_order(root) if c not in covered]
        only = set(missing_ids)
        if not missing_ids:
            print("빠진 장면 없음. 나레이션 카드 전부에 영상이 있다.")
            return
    plan = scene_plan(root, target_seconds=args.target, only=only)

    narration = root / "narration"

    def line(nl: str) -> str:
        f = narration / f"{nl}.txt"
        return " ".join(f.read_text(encoding="utf-8").split()) if f.is_file() else ""

    if args.tsv:
        print("\t".join(["파일명", "필요초", "구간", "카드", "대사"]))
        for sc in plan:
            for c in sc["cards"]:
                print("\t".join([sc["file"], f'{sc["need_seconds"]:.6f}',
                                 timecode(sc["start_us"]), c["nl"], line(c["nl"])]))
        return

    total = 0
    for i, sc in enumerate(plan, 1):
        total += sc["need_us"]
        end = sc["start_us"] + sc["need_us"]
        print(f"\n## {i}. {sc['file']}")
        print(f"   구간      {timecode(sc['start_us'])} ~ {timecode(end)}")
        print(f"   필요 길이  {sc['need_seconds']:.6f}초  (카드 {len(sc['cards'])}장)")
        offset = 0
        for c in sc["cards"]:
            a, b = offset / 1e6, (offset + c["dur_us"]) / 1e6
            print(f"     {c['nl']:6} {c['dur_us']/1e6:6.3f}s  {a:7.3f}~{b:7.3f}  {line(c['nl'])}")
            offset += c["dur_us"]
    print(f"\n장면 {len(plan)}개 · 합계 {total/1e6/60:.2f}분")
    print("1920x1080 · H.264 · 30fps · 오디오 스트림 없음 · 필요 길이 이상")
    print(f"넣는 곳: {root / 'hyperframes'}")


if __name__ == "__main__":
    main()

# -*- coding: utf-8 -*-
"""쇼츠 CapCut 프로젝트를 검사한다. 빌드 뒤에 돌린다.

CapCut 은 타임라인을 네 곳에 나눠 들고 있다. 한 곳이라도 어긋나면 열었을 때
근본 상태로 되돌아가거나, 구간을 옮기는 순간 영상이 사라진다.

    draft_content.json
    template-2.tmp
    Timelines/<타임라인 id>/draft_content.json
    Timelines/<타임라인 id>/template-2.tmp

CapCut 이 프로젝트를 한 번 열면 `.bak` 을 남기고 절대경로를
`##_draftpath_placeholder_<GUID>_##` 로 바꾼다. 그 GUID 는 전 프로젝트 공용 토큰이라
충돌이 아니다. 둘 다 검사에서 뺀다.
"""
from __future__ import annotations

import json
import os
import pathlib
import re

from _common import SHORTS_CAPCUT_ROOT, root_parser

CAPCUT = pathlib.Path(
    r"C:/Users/arajun/AppData/Local/CapCut/User Data/Projects/com.lveditor.draft")
UUID = re.compile(r"[0-9A-Fa-f]{8}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{12}")
PLACEHOLDER = re.compile(r"##_draftpath_placeholder_[^\"]*")


def real_ids(text: str) -> set:
    """CapCut 이 넣은 공용 경로 토큰의 GUID 는 뺀다."""
    return set(UUID.findall(text)) - set(UUID.findall(" ".join(PLACEHOLDER.findall(text))))


def main() -> None:
    args = root_parser("쇼츠 CapCut 프로젝트를 검사한다").parse_args()
    root = args.root
    if root is None:
        raise SystemExit("ROOT_REQUIRED: --root 또는 SPINE_EPISODE_ROOT")

    path = root / "work" / "shorts.json"
    if not path.is_file():
        raise SystemExit(f"SHORTS_JSON_MISSING: {path}")
    data = json.loads(path.read_text(encoding="utf-8"))

    capcut_root = CAPCUT / SHORTS_CAPCUT_ROOT
    if not capcut_root.is_dir():
        raise SystemExit(f"SHORT_CAPCUT_ROOT_MISSING: {capcut_root}")
    root_ids = real_ids((capcut_root / "draft_content.json").read_text(encoding="utf-8"))

    total = 0
    seen: dict = {}
    for row in data["shorts"]:
        project = CAPCUT / row["project_name"]
        if not project.is_dir():
            print(f"{row['project_name']:26s} 없음")
            total += 1
            continue

        text = (project / "draft_content.json").read_text(encoding="utf-8")
        doc = json.loads(text)
        timeline = project / "Timelines" / doc["id"]
        mirrors = all(f.is_file() and f.read_text(encoding="utf-8") == text
                      for f in (project / "template-2.tmp",
                                timeline / "draft_content.json",
                                timeline / "template-2.tmp"))
        layout = json.loads((project / "timeline_layout.json").read_text(encoding="utf-8"))
        layout_ok = layout["dockItems"][0]["timelineIds"] == [doc["id"]]

        ids = real_ids(text)
        clash = len(ids & root_ids) + sum(len(ids & other) for other in seen.values())
        seen[row["project_name"]] = ids

        index = {}
        for bucket, items in doc["materials"].items():
            if isinstance(items, list):
                for item in items:
                    if isinstance(item, dict) and "id" in item:
                        index[item["id"]] = (bucket, item)

        # 삽화 → 본편 → 삽화 한 트랙. 사용자가 본편을 더 나눴을 수 있어 3컷 이상이면 통과한다
        slot = [t for t in doc["tracks"] if t["type"] == "video" and len(t["segments"]) >= 3]
        narration = [t for t in doc["tracks"] if t["type"] == "audio"
                     and any(index[s["material_id"]][1].get("type") == "extract_music"
                             for s in t["segments"])]
        ghost = sum(1 for f in project.rglob("*") if f.is_file() and f.suffix in (".json", ".tmp")
                    and "Presets/Combination" in
                    f.read_text(encoding="utf-8", errors="ignore").replace("\\", "/"))
        broken = [item["path"] for bucket, items in doc["materials"].items()
                  if isinstance(items, list)
                  for item in items if isinstance(item, dict) and item.get("path")
                  and "##" not in item["path"] and not os.path.exists(item["path"])]

        problems = ((0 if mirrors else 1) + (0 if layout_ok else 1) + clash + ghost
                    + len(broken) + (0 if slot else 1) + (0 if narration else 1))
        total += problems
        print(f"{row['project_name']:26s} {doc['duration'] / 1e6:6.1f}초 "
              f"슬롯={'O' if slot else 'X'} 나레이션={'O' if narration else 'X'} "
              f"정본4벌={'O' if mirrors else 'X'} id충돌={clash} 유령={ghost} "
              f"깨짐={len(broken)}" + ("" if problems == 0 else f"   <<< 문제 {problems}"))

    print(f"총 이상 {total}건")
    if total:
        raise SystemExit("SHORT_VERIFY_FAILED")


if __name__ == "__main__":
    main()

# -*- coding: utf-8 -*-
"""쇼츠 삽화 프롬프트를 뽑는다. 롱폼 카드를 렌더할 때 같이 돌린다.

삽화는 쇼츠에서 나레이션 구간을 받치는 그림이다. 앞뒤 삽화 사이에 본편 발화가 들어간다.
롱폼 CSS 카드는 전부 같은 결이라 쇼츠에서 화면이 죽는다. 그래서 삽화를 따로 만든다.

    결        신문 삽화·목판화. 무겁고 시사 다큐 톤
    금지      실존 인물 얼굴, 화면 안 글자, 로고, 정당 상징
    허용      개념 그래픽 — 저울, 서류, 캐비닛, 해협, 갈라진 길
    크기      720p 로 충분하다. 쇼츠에서 작게 들어간다

산출물은 `<root>/work/short_art_prompts.md` 다. 이걸 그대로 투군에 던진다.
"""
from __future__ import annotations

import json

from _common import SHORTS_ART, root_parser

TONE = ("신문 삽화 · 목판화. 굵은 선각, 거친 해칭, 종이 질감. "
        "낮은 채도의 먹빛과 붉은 강조 하나. 무겁고 시사 다큐 톤.")
BAN = ("실존 인물의 얼굴을 그리지 않는다. 화면 안에 글자·숫자·로고·정당 상징을 넣지 않는다. "
       "사람이 필요하면 실루엣이나 뒷모습으로만 둔다.")


def main() -> None:
    parser = root_parser("쇼츠 삽화 프롬프트를 만든다")
    parser.add_argument("--size", default="1280x720", help="생성 크기 (기본 720p)")
    args = parser.parse_args()
    root = args.root
    if root is None:
        raise SystemExit("ROOT_REQUIRED: --root 또는 SPINE_EPISODE_ROOT")

    path = root / "work" / "shorts.json"
    if not path.is_file():
        raise SystemExit(f"SHORTS_JSON_MISSING: {path} — mark_shorts.py 를 먼저 돌린다")
    data = json.loads(path.read_text(encoding="utf-8"))

    lines = [f"# 쇼츠 삽화 요청 — {data['episode_id']}", "",
             f"공통 결: {TONE}", f"금지: {BAN}", f"크기: {args.size}",
             f"저장 위치: `{SHORTS_ART}`", ""]
    for row in data["shorts"]:
        lines += [
            f"## {row['art']}", "",
            f"- 쇼츠: `{row['project_name']}`",
            f"- 상대 주장: {row['claim']}",
            f"- 반박 카드: {row['counter']}",
            "- 그림: 반박 카드가 가리키는 사물 하나를 화면 가운데에 크게 둔다. "
            "인물이 아니라 사물이나 구조로 논지를 보여준다.",
            "",
        ]
    lines += ["---", "",
              "받은 파일은 위 저장 위치에 `art` 이름 그대로 넣는다. "
              "`build_short.py` 가 그 이름으로 찾는다."]

    out = root / "work" / "short_art_prompts.md"
    out.write_text("\n".join(lines), encoding="utf-8")
    print(f"삽화 {len(data['shorts'])}건 → {out}")
    for row in data["shorts"]:
        marker = "있음" if (SHORTS_ART / row["art"]).is_file() else "없음"
        print(f"  {row['art']:34s} {marker}")


if __name__ == "__main__":
    main()

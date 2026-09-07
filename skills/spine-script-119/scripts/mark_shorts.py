# -*- coding: utf-8 -*-
"""쇼츠 구간을 잠근다. 나레이션 원고를 쓰기 전에 돌린다.

쇼츠는 롱폼을 다 만든 뒤에 잘라내는 물건이 아니다. 나레이션과 삽화가 이미
만들어진 뒤에 고르면 쇼츠에 쓸 문장이 없다. 붙어 있는 나레이션을 끌어다 쓰게 되고,
그러면 앞뒤 문맥 없이는 말이 되지 않는다.

그래서 척추 자막을 확보한 직후 여기서 구간을 잠그고, 그 결과를 나레이션 원고가 받는다.

쇼츠 구조는 기승전결이 아니라 논쟁 카드다.

    claim    상대가 던지는 문장. 쇼츠 앞에 그대로 세운다
    counter  상대가 못 받아치는 사실 한 줄. 회차에서 가장 센 것
             예) "공소 취소를 가장 먼저 주장한 사람이 조국이다"
                 "노무현은 미국이 지정한 키르쿠크를 거절했다"

회차 정의는 `<root>/work/cards_def.py` 의 `SHORTS` 에만 둔다.
"""
from __future__ import annotations

import json
import re

from _common import SHORTS_ART, SHORTS_CAPCUT_ROOT, load_cards_def_raw, root_parser

MIN_SHORTS, MAX_SHORTS = 2, 3
MIN_LEN, MAX_LEN = 20.0, 90.0
T_LIMIT = 12
MENTION_LIMIT = 14
# 앞 문장을 받는 지시어로 시작하면 쇼츠에서 혼자 서지 못한다
DEICTIC = re.compile(r"^(그런데|그래서|그리고|그러니까|그게|그건|그 |이 |저 |여기|거기|이쪽|그쪽|반면)")
REQUIRED = ("slug", "project_name", "source", "start", "end", "claim", "counter",
            "t1", "t2", "mentions", "head_narration", "tail_narration", "art")


def fail(code: str, detail: str) -> None:
    raise SystemExit(f"{code}: {detail}")


def check(entry: dict, seen: set, sources: dict) -> dict:
    for key in REQUIRED:
        if key not in entry:
            fail("SHORT_FIELD_MISSING", f"{entry.get('slug', '?')} / {key}")

    slug = entry["slug"]
    if slug in seen:
        fail("SHORT_SLUG_DUPLICATE", slug)
    seen.add(slug)

    length = float(entry["end"]) - float(entry["start"])
    if not MIN_LEN <= length <= MAX_LEN:
        fail("SHORT_RANGE_OUT_OF_BOUNDS", f"{slug} {length:.1f}초 (허용 {MIN_LEN}~{MAX_LEN})")

    for key in ("claim", "counter"):
        text = entry[key].strip()
        if not text:
            fail("SHORT_CARD_EMPTY", f"{slug} / {key}")
        if DEICTIC.match(text):
            fail("SHORT_CARD_NOT_STANDALONE",
                 f"{slug} / {key} — 지시어로 시작해 혼자 서지 못한다: {text}")

    for key in ("t1", "t2"):
        if len(entry[key]) > T_LIMIT:
            fail("SHORT_TITLE_TOO_LONG", f"{slug} / {key} {len(entry[key])}자 (한도 {T_LIMIT})")

    mentions = entry["mentions"]
    if not 1 <= len(mentions) <= 3:
        fail("SHORT_MENTION_COUNT", f"{slug} {len(mentions)}개 (1~3)")
    for start, end, text, mood in mentions:
        if len(text) > MENTION_LIMIT:
            fail("SHORT_MENTION_TOO_LONG", f"{slug} / {text} {len(text)}자 (한도 {MENTION_LIMIT})")
        if mood not in ("normal", "anger"):
            fail("SHORT_MENTION_MOOD_INVALID", f"{slug} / {mood}")
        if not 0 <= start < end <= length:
            fail("SHORT_MENTION_RANGE_INVALID", f"{slug} / {start}~{end} (구간 {length:.1f}초)")

    for key in ("head_narration", "tail_narration"):
        if not entry[key]:
            fail("SHORT_NARRATION_MISSING",
                 f"{slug} / {key} — 나레이션 원고에 쇼츠용 줄을 심어야 한다")

    # 출처는 채널명만 쓴다. SOURCES 에 적어 둔 표기를 그대로 가져온다.
    credit = entry.get("credit")
    if not credit:
        row = sources.get(entry["source"])
        if not row:
            fail("SHORT_SOURCE_UNKNOWN", f"{slug} / {entry['source']}")
        credit = f"출처 : {row[2]}"

    return {
        "slug": slug,
        "project_name": entry["project_name"],
        "source": entry["source"],
        "start": round(float(entry["start"]), 3),
        "end": round(float(entry["end"]), 3),
        "duration": round(length, 3),
        "claim": entry["claim"].strip(),
        "counter": entry["counter"].strip(),
        "t1": entry["t1"],
        "t2": entry["t2"],
        "credit": entry.get("credit") or credit,
        "mentions": [[float(a), float(b), t, m] for a, b, t, m in mentions],
        "head_narration": list(entry["head_narration"]),
        "tail_narration": list(entry["tail_narration"]),
        "art": entry["art"],
        "art_path": str(SHORTS_ART / entry["art"]),
        "scale": entry.get("scale"),
    }


def main() -> None:
    args = root_parser("쇼츠 구간을 잠그고 work/shorts.json 을 쓴다").parse_args()
    root = args.root
    if root is None:
        fail("ROOT_REQUIRED", "--root 또는 SPINE_EPISODE_ROOT")

    mod = load_cards_def_raw(root)
    shorts = getattr(mod, "SHORTS", None)
    if not shorts:
        fail("SHORTS_MISSING", "cards_def.py 에 SHORTS 를 정의한다")
    if not MIN_SHORTS <= len(shorts) <= MAX_SHORTS:
        fail("SHORTS_COUNT_OUT_OF_BOUNDS", f"{len(shorts)}개 (허용 {MIN_SHORTS}~{MAX_SHORTS})")

    sources = dict(getattr(mod, "SOURCES", {}) or {})
    seen: set = set()
    rows = [check(dict(entry), seen, sources) for entry in shorts]

    payload = {
        "episode_id": getattr(mod, "EPISODE_ID", root.name),
        "capcut_root": SHORTS_CAPCUT_ROOT,
        "shorts": rows,
    }
    out = root / "work" / "shorts.json"
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"쇼츠 {len(rows)}건 잠금 → {out}")
    for row in rows:
        print(f"\n  {row['slug']}  {row['duration']:.1f}초  [{row['source']}]")
        print(f"    상대 주장   {row['claim']}")
        print(f"    반박 카드   {row['counter']}")
        print(f"    나레이션    앞 {' '.join(row['head_narration'])} / "
              f"뒤 {' '.join(row['tail_narration'])}")
    print("\n나레이션 원고에 위 줄을 심는다. 쇼츠에 쓸 줄은 앞뒤 문맥 없이 혼자 성립해야 한다.")


if __name__ == "__main__":
    main()

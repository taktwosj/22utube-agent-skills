# -*- coding: utf-8 -*-
"""cards_def.py 의 CARDS 를 컷표와 나레이션 줄로 새로 쓴다.

입력  <root>/work/final_cuts.py      MONTAGE · BODY · CHAPTERS  (틀: templates/final_cuts.template.py)
      <root>/work/narration_lines.json   tts_lines.py 가 만든 줄 목록 (name, block, duration)
출력  <root>/work/cards_def.py 의 `CARDS = [` 부터 끝까지를 덮어쓴다. 그 위 회차 정의는 그대로 둔다.

순서: 몽타주 → 첫 CTA → BODY 블록마다 [그 블록 나레이션 줄들 → 그 블록 뒤 컷들] → 마무리 CTA.
CTA 는 N_CTA 블록의 첫 줄 wav 를 앞뒤 두 번 쓴다.

컷 kind:  H 몽타주 / S 증언·척추 / B 사건 원본·살
N_SHORTS 블록(쇼츠 도입·마무리 줄)은 롱폼 카드로 만들지 않는다. 컷표에 있으면 SHORTS_BLOCK_IN_BODY 로 막는다.
"""
from __future__ import annotations

import ast
import importlib.util
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _common import resolve_root, root_parser  # noqa: E402

KIND_LABEL = {"S": "증언", "B": "원본"}
# 롱폼 카드가 되지 않는 나레이션 블록. 쇼츠 도입·마무리 줄은 롱폼 줄과 한 번에 합성하지만(NL 번호가 이어져야
# build_short 가 wav 를 집는다) 롱폼 타임라인에는 넣지 않는다. 컷표에 없어도 오류가 아니다.
SHORTS_ONLY_BLOCKS = {"N_SHORTS"}


def load_cuts(root: Path):
    path = root / "work" / "final_cuts.py"
    if not path.is_file():
        raise SystemExit(f"FINAL_CUTS_MISSING: {path} — templates/final_cuts.template.py 를 복사해 채운다")
    spec = importlib.util.spec_from_file_location("final_cuts", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    for name in ("MONTAGE", "BODY", "CHAPTERS"):
        if not hasattr(mod, name):
            raise SystemExit(f"FINAL_CUTS_FIELD_MISSING: {name}")
    return mod


def main() -> int:
    args = root_parser("컷표 + 나레이션 줄 → CARDS").parse_args()
    root = resolve_root(args)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    fc = load_cuts(root)
    rows = json.loads((root / "work" / "narration_lines.json").read_text(encoding="utf-8"))
    by: dict[str, list[str]] = {}
    for r in rows:
        by.setdefault(r["block"], []).append(r["name"])

    if not by.get("N_CTA"):
        raise SystemExit("NARRATION_CTA_MISSING: N_CTA 블록 줄이 없다")
    body_blocks = {x for x, _ in fc.BODY}
    leaked = [b for b in SHORTS_ONLY_BLOCKS if b in body_blocks]
    if leaked:
        raise SystemExit("SHORTS_BLOCK_IN_BODY: " + ", ".join(leaked) + " — 쇼츠 전용 줄은 롱폼 컷표에 넣지 않는다")
    missing = [b for b, _ in fc.BODY if b not in fc.CHAPTERS]
    if missing:
        raise SystemExit("CHAPTER_LABEL_MISSING: " + ", ".join(missing))
    unused = [b for b in by if b != "N_CTA" and b not in SHORTS_ONLY_BLOCKS and b not in body_blocks]
    if unused:
        raise SystemExit("NARRATION_BLOCK_NOT_IN_BODY: " + ", ".join(unused))
    for key, kind, *_ in fc.MONTAGE:
        if kind != "H":
            raise SystemExit(f"MONTAGE_KIND_NOT_H: {key}")

    cta_nl = by["N_CTA"][0]
    lines = ["CARDS = [", "    # ---- 오프닝 몽타주 (나레이션 없음, 세기 순) ----"]
    for i, (key, kind, v, a, b, memo) in enumerate(fc.MONTAGE, 1):
        lines.append(f'    ("C00_HOOK_{i:02d}", "SRC", "{v}", {a}, {b}, "오프닝", "오프닝", "{memo}", "몽타주 {i}"),')
    lines.append(f'    ("C00_CTA", "NAR") + cta("{cta_nl}"),')

    n = nar = src = 0
    for block, cuts in fc.BODY:
        short, title = fc.CHAPTERS[block]
        lines.append(f"    # ---- {block} · {title} ----")
        for nl in by.get(block, []):
            n += 1
            nar += 1
            lines.append(f'    ("C{n:03d}_{nl}", "NAR") + N("{nl}", "{short}", "{title}", "{title}", "{short}", '
                         f'"{title}", "화면 문구 위", "화면 문구 아래", "푸터", "{short}", "블록", "서브", "grid"),')
        for key, kind, v, a, b, memo in cuts:
            if kind not in KIND_LABEL:
                raise SystemExit(f"CUT_KIND_UNKNOWN: {key} {kind} — 본편 컷은 S 또는 B")
            n += 1
            src += 1
            lines.append(f'    ("C{n:03d}_{key}", "SRC", "{v}", {a}, {b}, "{short}", "{title}", "{memo}", '
                         f'"{KIND_LABEL[kind]}"),')
    lines.append(f'    ("C999_CTA", "NAR") + cta("{cta_nl}", "마무리"),')
    lines.append("]")

    path = root / "work" / "cards_def.py"
    text = path.read_text(encoding="utf-8")
    if "\nCARDS = [" not in text:
        raise SystemExit("CARDS_ANCHOR_MISSING: cards_def.py 에 줄 머리 `CARDS = [` 가 없다")
    out = text.split("\nCARDS = [")[0] + "\n" + "\n".join(lines) + "\n"
    ast.parse(out)
    path.write_text(out, encoding="utf-8")
    print(f"CARDS: 몽타주 {len(fc.MONTAGE)} / NAR {nar + 2} / SRC {src}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

# -*- coding: utf-8 -*-
"""TTS 전에 나레이션 원고를 검사한다.

narration/<block>.txt 를 NARRATION_ORDER 순서로 읽어 금지 표현·아라비아 숫자·인명 근사
변형(check_captions 와 같은 편집거리 1)을 잡고 줄 수·글자 수·예상 초를 찍는다. 근사 변형이
오탐이면 그 표기를 cards_def.GLOSSARY 에 넣는다. 걸리면 TTS 를 만들지 않는다. gen_script.py 는 같은
패턴으로 NL 줄을 다시 검사하는 안전망이다.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _common import load_cards_def_raw, resolve_root, root_parser  # noqa: E402
from gen_script import narration_style_hits  # noqa: E402
from check_captions import ALLOW_SUFFIX, BASE_GLOSSARY, lev1  # noqa: E402

DIGIT_RE = re.compile(r"[0-9０-９]")
CHARS_PER_SEC = 10.3  # Typecast 템포 1.2 실측. 공백 제외
# 보상앵커 작가모드의 동행 문장 표지. 시청자 옆에서 같이 보고 멈추고 묻는 말.
COVIEW_RE = re.compile(r"같이|함께|우리|보시죠|보겠습니다|들어 보|멈춰|짚어 보|따라가 보|궁금")


def writer_report(root: Path, blocks: dict[str, list[str]]) -> list[str]:
    """챕터별 동행 문장 수를 찍는다. 집필 가이드라 경고만 낸다 — 통과·실패를 가르지 않는다.

    챕터는 work/final_cuts.py 의 CHAPTERS(블록 → (짧은 이름, 제목))로 묶는다. 컷표가 아직 없으면
    블록 단위로만 찍고 경고는 내지 않는다.
    """
    chapters: dict[str, str] = {}
    fc_path = root / "work" / "final_cuts.py"
    if fc_path.is_file():
        import importlib.util
        spec = importlib.util.spec_from_file_location("final_cuts_for_check", fc_path)
        fc = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(fc)  # type: ignore[union-attr]
        chapters = {b: v[1] for b, v in getattr(fc, "CHAPTERS", {}).items()}
    counts: dict[str, list[int]] = {}
    for block, lines in blocks.items():
        if block in ("N_CTA", "N_SHORTS"):  # CTA 와 쇼츠 전용 줄은 챕터가 아니다
            continue
        c = counts.setdefault(chapters.get(block, block), [0, 0])
        c[0] += len(lines)
        c[1] += sum(1 for line in lines if COVIEW_RE.search(line))
    print("-- 동행 문장 (보상앵커 작가모드)")
    warnings = []
    for key, (n, hit) in counts.items():
        print(f"   {key:24s} {n:3d}줄 동행 {hit}")
        if chapters and hit == 0:
            warnings.append(f"WRITER_COVIEW_MISSING:{key}")
    return warnings


# 편집거리 1 비교를 건너뛰는 짧은 용어 길이. 두 글자 용어(대검·조국·검찰)는 흔한 낱말(대목·검증)과
# 한 글자 차이라 오탐만 낸다(2026-09-17 한동훈 회차: 오탐 39건, 실제 오류 0건). 정확 일치만 본다.
NEAR_MISS_MIN_TERM = 3


def known_spans(text: str, known: set[str]) -> list[tuple[int, int]]:
    """본문에서 표준 표기가 실제로 나오는 구간. 그 안의 조각은 다른 용어의 오탈자가 아니다(봉지욱 안의 '지욱')."""
    spans = []
    for k in known:
        start = text.find(k)
        while start != -1:
            spans.append((start, start + len(k)))
            start = text.find(k, start + 1)
    return spans


def near_misses(text: str, glossary: list[str]) -> list[tuple[str, str]]:
    """표준 표기와 편집거리 1인 조각. 조사 변형·목록의 다른 표기·공백 낀 조각·표준 표기 안의 조각은 통과."""
    known = set(glossary)
    spans = known_spans(text, known)
    hits: list[tuple[str, str]] = []
    for term in glossary:
        n = len(term)
        if n < NEAR_MISS_MIN_TERM:
            continue
        for i in range(len(text) - n + 1):
            w = text[i:i + n]
            if w == term or w in known or not re.search(r"[가-힣]", w):
                continue
            if re.search(r"\s", w):  # 공백을 낀 조각은 낱말이 아니다(" 검" ← 대검)
                continue
            if any(a <= i and i + n <= b for a, b in spans):
                continue
            if any(w == term[:-1] + sfx or w == term + sfx for sfx in ALLOW_SUFFIX):
                continue
            if lev1(w, term):
                hits.append((term, w))
                break
    return hits


def check_lines(block: str, lines: list[str], glossary: list[str] | None = None) -> list[str]:
    failures: list[str] = []
    for number, raw in enumerate(lines, 1):
        text = raw.strip()
        if not text:
            continue
        if DIGIT_RE.search(text):
            failures.append(f"NARRATION_DIGIT_FORBIDDEN:{block}:{number}:{text[:40]}")
        for code, found in narration_style_hits(text)[:1]:
            failures.append(f"NARRATION_STYLE_FORBIDDEN:{block}:{number}:{code}:{found}")
        for term, w in near_misses(text, glossary or []):
            failures.append(f"NARRATION_TERM_NEAR_MISS:{block}:{number}:{term}<-{w}")
    return failures


def main() -> int:
    args = root_parser("TTS 전 나레이션 원고 검사").parse_args()
    root = resolve_root(args)
    cd = load_cards_def_raw(root)
    order = list(dict.fromkeys(getattr(cd, "NARRATION_ORDER", None) or []))
    if not order:
        raise SystemExit("CARDS_DEF_FIELD_MISSING: NARRATION_ORDER")
    narr = root / "narration"
    glossary = list(dict.fromkeys(BASE_GLOSSARY + list(getattr(cd, "GLOSSARY", []))))
    failures: list[str] = []
    blocks: dict[str, list[str]] = {}
    total_lines = total_chars = 0
    for block in order:
        path = narr / f"{block}.txt"
        if not path.is_file():
            failures.append(f"NARRATION_BLOCK_MISSING:{block}:{path}")
            continue
        lines = path.read_text(encoding="utf-8").splitlines()
        failures += check_lines(block, lines, glossary)
        kept = [line.strip() for line in lines if line.strip()]
        blocks[block] = kept
        chars = sum(len(line.replace(" ", "")) for line in kept)
        total_lines += len(kept)
        total_chars += chars
        print(f"{block:8s} {len(kept):3d}줄 {chars:5d}자 ≈{chars / CHARS_PER_SEC:6.1f}s")
    for warning in writer_report(root, blocks):
        print(warning)
    if failures:
        for failure in failures:
            print(failure)
        return 2
    print(f"NARRATION_CHECK PASS: {total_lines}줄 {total_chars}자 ≈{total_chars / CHARS_PER_SEC:.1f}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

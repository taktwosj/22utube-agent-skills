# -*- coding: utf-8 -*-
"""자막 QA — (1) 길이·조각 (2) 타이밍 드리프트 (3) 정치 인명·용어 근사 변형.

119 의 validate_srt_text_fidelity 는 raw/display 가 같으면 통과한다. 양쪽에 같은 오인식이
있으면 못 잡는다. 이 검사가 그 구멍을 메운다. 화면에 뜨는 자막(lower SRT)만 본다.
"""
from __future__ import annotations

import json
import re
import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _common import load_cards_def, resolve_root, root_parser  # noqa: E402
import vtt_clean  # noqa: E402

# 회차를 가리지 않는 정치 인명·기관 표기. 회차 고유어는 cards_def.GLOSSARY 에 추가한다.
CORE_GLOSSARY = ["국민의힘", "더불어민주당", "조국혁신당", "이재명", "한동훈", "나경원", "정청래", "김민석",
                 "윤석열", "박근혜", "박정희", "조국", "유시민", "김어준", "최욱", "봉지욱", "황희두", "장인수",
                 "중앙정보부", "대법원", "법무부", "검찰", "국회", "전당대회", "여론조사", "언론중재위",
                 "뉴스공장", "매불쇼", "저널리스트", "겸손은힘들다", "레거시", "제작진", "평론가", "패널", "종편"]

# 확장 어휘 스냅샷. 없으면 CORE_GLOSSARY 만으로 동작한다(폴백). 오인식 매핑이 아니라 표준 표기 목록이다.
GLOSSARY_FILE = Path(__file__).parent.parent / "references" / "politics_glossary_v1.txt"


def load_base_glossary() -> list[str]:
    terms = list(CORE_GLOSSARY)
    if GLOSSARY_FILE.exists():
        for line in GLOSSARY_FILE.read_text(encoding="utf-8").splitlines():
            t = line.strip()
            if t and not t.startswith("#"):
                terms.append(t)
    return list(dict.fromkeys(terms))


BASE_GLOSSARY = load_base_glossary()
ALLOW_SUFFIX = ("가", "는", "은", "이", "을", "를", "의", "에", "로", "와", "과", "도", " ", ",", ".", "?")


def lev1(a: str, b: str) -> bool:
    """편집거리 1 (길이 같으면 치환 1, 다르면 삽입/삭제 1)."""
    if a == b:
        return False
    if len(a) == len(b):
        return sum(x != y for x, y in zip(a, b)) == 1
    if abs(len(a) - len(b)) != 1:
        return False
    s, l = (a, b) if len(a) < len(b) else (b, a)
    i = 0
    while i < len(s) and s[i] == l[i]:
        i += 1
    return s[i:] == l[i + 1:]


def parse_srt(path: Path):
    raw = path.read_text(encoding="utf-8").strip()
    out = []
    for m in re.finditer(r"(\d\d):(\d\d):(\d\d),(\d\d\d) --> (\d\d):(\d\d):(\d\d),(\d\d\d)\n(.*?)(?=\n\n|\Z)", raw, re.S):
        g = m.groups()
        s = int(g[0]) * 3600 + int(g[1]) * 60 + int(g[2]) + int(g[3]) / 1000
        e = int(g[4]) * 3600 + int(g[5]) * 60 + int(g[6]) + int(g[7]) / 1000
        out.append((s, e, g[8].strip()))
    return out


def main():
    args = root_parser("자막 QA").parse_args()
    root = resolve_root(args)
    cd = load_cards_def(root)
    vtt_clean.set_root(root)
    srt = root / "srt"
    tl = {r["card_id"]: r for r in json.loads((root / "work" / "timeline.json").read_text(encoding="utf-8"))["cards"]}
    glossary = list(dict.fromkeys(BASE_GLOSSARY + list(getattr(cd, "GLOSSARY", []))))
    vis = lambda t: len(re.sub(r"\s", "", t))
    fail = 0

    # (1) 길이·조각
    tot = short = long_ = multi = 0
    for p in list(srt.glob("C*.display.srt")) + list(srt.glob("C*.narration.srt")):
        for _, _, t in parse_srt(p):
            tot += 1; multi += "\n" in t; short += vis(t) <= 5; long_ += vis(t) > 15
    print(f"[1] cue {tot} | 5자 이하 {short} | 15자 초과 {long_} | 2줄 {multi}")
    fail += (long_ > 0) + (multi > 0)

    # (2) 타이밍 드리프트 — 출력 cue 첫 단어열을 원본 단어 시각과 대조
    drift = []
    for card in cd.CARDS:
        if card[1] != "SRC":
            continue
        cid, vid, t_in, t_out = card[0], card[2], card[3], card[4]
        p = srt / f"{cid}.display.srt"
        if not p.exists():
            continue
        tl_start = tl[cid]["target_start_us"] / 1e6
        seq = []
        for c in json.loads((srt / f"{vid}.cues.json").read_text(encoding="utf-8")):
            s, e = c["start"], c["end"]
            if e <= t_in or s >= t_out:
                continue
            s = max(s, t_in) - t_in + tl_start; e = min(e, t_out) - t_in + tl_start
            words = vtt_clean.correct(c["text"]).split()
            total = sum(len(w) for w in words) or 1; acc = 0
            for w in words:
                seq.append((w, s + (e - s) * acc / total)); acc += len(w)
        words = [w for w, _ in seq]; pos = 0
        for cs, _, text in parse_srt(p):
            pw = text.split()
            if not pw:
                continue
            hit = None
            for k in range(pos, len(words) - len(pw) + 1):
                if abs(seq[k][1] - cs) <= 8.0 and words[k:k + len(pw)] == pw:
                    hit = k; break
            if hit is None:
                for k in range(pos, len(words) - 1):
                    if abs(seq[k][1] - cs) <= 8.0 and words[k] == pw[0] and (len(pw) < 2 or words[k + 1] == pw[1]):
                        hit = k; break
            if hit is None:
                continue
            pos = hit + 1
            drift.append((abs(cs - seq[hit][1]), cid, round(cs, 2), text[:18]))
    if drift:
        drift.sort(reverse=True)
        vals = [d[0] for d in drift]; over = sum(v > 0.6 for v in vals)
        print(f"[2] 타이밍 cue {len(vals)} | 중앙값 {statistics.median(vals):.2f}s | 0.6s 초과 {over} ({over/len(vals)*100:.1f}%) | 최대 {vals[0]:.2f}s")
        for d in drift[:5]:
            print(f"      {d[0]:5.2f}s {d[1]:14s} @{d[2]} {d[3]}")
        fail += over / len(vals) > 0.05

    # (3) 인명·용어 근사 변형 — 화면 노출 자막만
    hits, seen = [], set()
    for card in cd.CARDS:
        if card[1] != "SRC" or card[2] in cd.BURNED_CAPTION:
            continue
        p = srt / f"{card[0]}.display.srt"
        if not p.exists():
            continue
        text = " ".join(t for _, _, t in parse_srt(p))
        for term in glossary:
            n = len(term)
            for i in range(len(text) - n + 1):
                w = text[i:i + n]
                if w == term or not re.search(r"[가-힣]", w) or (term, w) in seen:
                    continue
                # 조사만 붙은 정상 변형은 통과
                if any(w == term[:-1] + sfx or w == term + sfx for sfx in ALLOW_SUFFIX):
                    continue
                if lev1(w, term):
                    seen.add((term, w))
                    hits.append((card[0], term, w, text[max(0, i - 10):i + n + 10]))
    print(f"[3] 용어 근사 변형 {len(hits)}건 (편집거리 1, 조사 변형 제외) — 사람이 훑어 오탐 걸러낸다")
    for cid, term, w, ctx in hits[:40]:
        print(f"      {cid:14s} {term} <- {w}   …{ctx}…")

    print("\nRESULT:", "FAIL" if fail else "PASS", f"(하드 실패 {fail}건; [3]은 판단 항목)")
    sys.exit(1 if fail else 0)


if __name__ == "__main__":
    main()

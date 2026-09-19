# -*- coding: utf-8 -*-
r"""잠근 쇼츠 구간을 실제 mp4 와 SRT 로 잘라낸다. 롱폼 조립이 끝난 뒤에 돌린다.

`-c copy` 를 쓰지 않는다. 키프레임에 붙어 수 초 어긋난다. 재인코딩한다.

산출물은 `E:\22utube\_shorts\<episode_id>\<slug>\` 에 슬러그 이름으로 셋이 나온다.

    <slug>.mp4        본편 구간
    <slug>.srt        원본 자막을 구간으로 자른 것
    <slug>_8자.srt    여덟 자 안팎으로 잘게 쪼갠 것 — CapCut 이 쓰는 쪽

자동자막 오탈자는 `<root>/work/corrections.json` 으로 고친다.
"""
from __future__ import annotations

import json
import re
import subprocess

from _common import SHORT_SPEED, SHORTS_ROOT, load_cards_def_raw, root_parser
from check_captions import ALLOW_SUFFIX, lev1, load_base_glossary
import vtt_clean

MAX_CHARS = 8
MIN_DUR = 0.22


ENTITY_RE = re.compile(r"&(?:gt|lt|amp|quot|apos|nbsp|#\d+);")
SPEAKER_RE = re.compile(r">>+")


def hard_defects(text: str, fixes) -> list[str]:
    """확실한 결함만 본다. 오탐이 없어야 게이트가 산다.

    (1) html 엔티티 — 직접 파서를 쓰면 남는다. vtt_clean 을 건너뛴 증거다
    (2) 화자 전환 표시 `>>` — 자막에 그대로 박힌다
    (3) 교정표에 적어 둔 오인식이 출력에 그대로 남아 있는 경우 — 교정이 안 걸렸다
    """
    out = []
    for m in dict.fromkeys(ENTITY_RE.findall(text)):
        out.append(f"html 엔티티 {m}")
    if SPEAKER_RE.search(text):
        out.append("화자 전환 표시 >>")
    for wrong, right in fixes:
        # 좌우가 같은 쌍은 교정이 아니다. 영원히 걸리므로 무시한다
        # `=` 로 시작하는 줄 전체 일치 규칙은 vtt_clean 이 이미 적용했다
        if wrong.startswith("="):
            if text.strip() == wrong[1:] and wrong[1:] != right:
                out.append(f"교정 미적용 {wrong} -> {right}")
            continue
        if wrong and wrong != right and wrong in text:
            out.append(f"교정 미적용 {wrong} -> {right}")
    return out


def suspect_terms(text: str, glossary) -> list[tuple[str, str, str]]:
    """오인식 의심 — 용어집과 편집거리 1인 조각. 오탐이 많아 사람이 훑는 참고용이다.

    쇼츠 SRT 는 롱폼 check_captions 의 검사 대상이 아니라 여기서 같이 찍는다.
    실제 오인식이면 <root>/work/corrections.json 에 넣고 vtt_clean 부터 다시 돌린다.
    """
    known = set(glossary) | {right for _, right in vtt_clean.table()}
    hits, seen = [], set()
    for term in glossary:
        n = len(term)
        for i in range(len(text) - n + 1):
            w = text[i:i + n]
            if w == term or w in known or not re.search(r"[가-힣]", w) or (term, w) in seen:
                continue
            if any(w == term[:-1] + sfx or w == term + sfx for sfx in ALLOW_SUFFIX):
                continue
            if lev1(w, term):
                seen.add((term, w))
                hits.append((term, w, text[max(0, i - 12):i + n + 12]))
    return hits


def ts(sec: float) -> str:
    sec = max(sec, 0.0)
    return (f"{int(sec // 3600):02d}:{int(sec % 3600 // 60):02d}:"
            f"{sec % 60:06.3f}").replace(".", ",")


def load_cues(path):
    data = json.loads(path.read_text(encoding="utf-8"))
    rows = data["cues"] if isinstance(data, dict) else data
    out = []
    for cue in rows:
        start = cue.get("start", cue.get("s"))
        end = cue.get("end", cue.get("e"))
        text = (cue.get("text") or cue.get("t") or "").replace("\n", " ").strip()
        if start is None or end is None or not text:
            continue
        out.append((float(start), float(end), text))
    return out


def chunks(text: str, limit: int = MAX_CHARS):
    out, cur = [], ""
    for word in text.split():
        while len(word) > limit:
            if cur:
                out.append(cur)
                cur = ""
            out.append(word[:limit])
            word = word[limit:]
        cand = (cur + " " + word).strip()
        if len(cand) <= limit:
            cur = cand
        else:
            if cur:
                out.append(cur)
            cur = word
    if cur:
        out.append(cur)
    return out


def write_srt(rows, dest) -> int:
    lines = [f"{i}\n{ts(a)} --> {ts(max(b, a + 0.15))}\n{t}\n"
             for i, (a, b, t) in enumerate(rows, 1)]
    dest.write_text("\n".join(lines), encoding="utf-8")
    return len(rows)


def split8(rows):
    """원 큐를 [start, 다음 start) 로 재구성해 사이의 빈틈을 없앤 뒤 여덟 자로 쪼갠다."""
    spans = []
    for i, (a, b, t) in enumerate(rows):
        end = rows[i + 1][0] if i + 1 < len(rows) else b
        if end - a >= 0.05 and t.strip():
            spans.append((a, end, t.strip()))

    out = []
    for a, b, t in spans:
        parts = chunks(t)
        if not parts:
            continue
        weights = [max(len(p), 1) for p in parts]
        total = sum(weights)
        cursor, span = a, b - a
        for part, weight in zip(parts, weights):
            dur = max(span * weight / total, MIN_DUR)
            out.append((cursor, cursor + dur, part))
            cursor += dur

    out.sort(key=lambda r: r[0])
    clean = []
    for i, (a, b, t) in enumerate(out):
        nxt = out[i + 1][0] if i + 1 < len(out) else b
        clean.append((a, min(b, nxt) if nxt > a else a + MIN_DUR, t))
    return clean


def main() -> None:
    parser = root_parser("쇼츠 구간을 mp4 와 SRT 로 잘라낸다")
    parser.add_argument("--only", help="이 슬러그만 자른다")
    args = parser.parse_args()
    root = args.root
    if root is None:
        raise SystemExit("ROOT_REQUIRED: --root 또는 SPINE_EPISODE_ROOT")

    path = root / "work" / "shorts.json"
    if not path.is_file():
        raise SystemExit(f"SHORTS_JSON_MISSING: {path} — mark_shorts.py 를 먼저 돌린다")
    data = json.loads(path.read_text(encoding="utf-8"))
    episode = data["episode_id"]

    # corrections.json 은 [오인식, 정확표기] 쌍의 목록이다. 빈 쌍과 주석 줄은 버린다.
    fixes = []
    corrections = root / "work" / "corrections.json"
    if corrections.is_file():
        raw = json.loads(corrections.read_text(encoding="utf-8"))
        pairs = raw if isinstance(raw, list) else list(raw.get("replace", raw).items())
        fixes = [(a, b) for a, b in pairs if a and b]

    vtt_clean.set_root(root)
    cards = load_cards_def_raw(root)
    glossary = list(dict.fromkeys(load_base_glossary() + list(getattr(cards, "GLOSSARY", []))))

    done = failed = suspect = defects = 0
    for row in data["shorts"]:
        if args.only and row["slug"] != args.only:
            continue
        slug, start, end = row["slug"], row["start"], row["end"]
        src = root / "clips" / f"{row['source']}.mp4"
        if not src.is_file():
            raise SystemExit(f"SHORT_SOURCE_CLIP_MISSING: {src}")

        outdir = SHORTS_ROOT / episode / slug
        outdir.mkdir(parents=True, exist_ok=True)
        mp4 = outdir / f"{slug}.mp4"
        result = subprocess.run([
            "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
            "-ss", f"{start:.3f}", "-to", f"{end:.3f}", "-i", str(src),
            "-filter:v", f"setpts=PTS/{SHORT_SPEED}", "-filter:a", f"atempo={SHORT_SPEED}",
            "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-ac", "2",
            "-movflags", "+faststart", str(mp4),
        ], capture_output=True, text=True)
        if result.returncode != 0:
            print(f"실패 {slug} — {result.stderr.strip()[:200]}")
            failed += 1
            continue

        cues = load_cues(root / "srt" / f"{row['source']}.cues.json")
        window = []
        for a, b, t in cues:
            if b <= start or a >= end:
                continue
            t = vtt_clean.correct(t)
            window.append(((max(a, start) - start) / SHORT_SPEED,
                           (min(b, end) - start) / SHORT_SPEED, t))

        raw_n = write_srt(window, outdir / f"{slug}.srt")
        eight = split8(window)
        eight_n = write_srt(eight, outdir / f"{slug}_8자.srt")
        over = sum(1 for _, _, t in eight if len(t) > MAX_CHARS)
        size = mp4.stat().st_size / 1_000_000
        print(f"완료 {slug:24s} {(end - start) / SHORT_SPEED:5.1f}초 {size:6.1f}MB  "
              f"자막 {raw_n} → {eight_n}개  여덟자초과 {over}")

        text = " ".join(t for _, _, t in window)
        # 교정은 cue 하나 안에서만 걸린다. 이어붙인 문장으로 검사하면 cue 경계에
        # 걸친 다중 어절 교정쌍이 영원히 "교정 미적용" 으로 뜨고 고칠 방법이 없다.
        # 화면에는 cue 단위로 나가므로 검사도 cue 단위가 맞다.
        found = []
        for _, _, cue_text in window:
            for d in hard_defects(cue_text, fixes):
                if d not in found:
                    found.append(d)
        for d in found:
            print(f"     자막 결함  {d}")
            defects += 1
        for term, w, ctx in suspect_terms(text, glossary):
            print(f"     용어 의심  {term} <- {w}   …{ctx}…")
            suspect += 1
        done += 1

    print(f"\n완료 {done} / 실패 {failed} → {SHORTS_ROOT / episode}")
    if suspect:
        print(f"용어 의심 {suspect}건 — 참고용이다. 실제 오인식이면 "
              f"{root / 'work' / 'corrections.json'} 에 넣고 vtt_clean 부터 다시 돌린다.")
    if defects:
        print(f"FAIL_SHORT_CAPTION_DEFECT: 자막 결함 {defects}건. "
              f"vtt_clean.py 로 다시 만들고 corrections.json 을 채운 뒤 다시 자른다.")
        raise SystemExit(1)


if __name__ == "__main__":
    main()

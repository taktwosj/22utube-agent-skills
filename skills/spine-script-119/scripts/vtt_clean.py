# -*- coding: utf-8 -*-
"""YouTube 자동자막(VTT) -> 롤링 겹침 제거 -> 정치 용어 교정 -> cues.json.

롤링 자막은 각 cue가 앞 cue의 꼬리를 반복한다. 문자열 동일/시작 비교만으로는
겹침이 남는다. 단어 단위로 최대 겹침 길이를 찾아 제거한다.
겹침 제거를 교정보다 먼저 한다. 순서를 바꾸면 교정된 단어가 겹침 판정을 깬다.

교정표 = BASE(범용 정치 오인식) + <root>/work/corrections.json(회차별). 둘 다 raw/display 에 같이 적용된다.
"""
from __future__ import annotations

import html
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _common import resolve_root, root_parser  # noqa: E402

TS = re.compile(r"(\d{2}):(\d{2}):(\d{2})[.,](\d{3})\s*-->\s*(\d{2}):(\d{2}):(\d{2})[.,](\d{3})")
TAG = re.compile(r"<[^>]*>")
SPEAKER_MARK = re.compile(r"^\s*(?:>>+|-)\s*")  # DIALOGUE_MARKER_REMOVAL 로 허용됨

# 회차를 가리지 않고 반복되는 정치 오인식. 회차 고유 이름은 corrections.json 에 둔다.
BASE_CORRECTIONS = [
    ("보안수사권", "보완수사권"), ("보안 수사권", "보완수사권"), ("보안수사", "보완수사"),
    ("보안 수사", "보완수사"),
    ("국민의임", "국민의힘"), ("국민의 임", "국민의힘"), ("국민의 힘", "국민의힘"),
    ("소사청", "수사청"), ("공소 청", "공소청"),
    ("한동운", "한동훈"), ("한 동훈", "한동훈"), ("한둥훈", "한동훈"),
    ("윤성열", "윤석열"), ("조희데", "조희대"),
    ("조국 혁신당", "조국혁신당"), ("조국 조국 혁신당", "조국혁신당"),
    ("체포동이안", "체포동의안"), ("체포 동의안", "체포동의안"), ("체포동안", "체포동의안"),
    ("범무부", "법무부"), ("범부 장관", "법무부 장관"),
    ("재신 판결", "재심 판결"), ("재신판결", "재심 판결"),
    ("사형 선거", "사형 선고"), ("사형선거", "사형 선고"),
    ("새누당", "새누리당"), ("무과한", "무고한"),
    ("전널리스트", "저널리스트"), ("전널", "저널"),
    ("매블쇼", "매불쇼"), ("매부쇼", "매불쇼"), ("맵을 쏘", "매불쇼"), ("맵을쇼", "매불쇼"), ("매불 쇼", "매불쇼"),
    ("유심민", "유시민"), ("유신민", "유시민"),
    ("장르한 여의도", "장르만 여의도"), ("장르한여의도", "장르만 여의도"),
    ("겸불뉴스공장", "겸손은힘들다 뉴스공장"),
    ("쥐대", "쥐떼"), ("쥐때", "쥐떼"),
    ("1배들", "일베들"), ("1배죠", "일베죠"), ("1배 수준", "일베 수준"),
    ("재작진", "제작진"), ("문제식이", "문제의식이"), ("문제 식이", "문제의식이"),
    ("언론 중제위", "언론중재위"), ("언론중제위", "언론중재위"), ("재소 방침", "제소 방침"),
    ("연남뉴스", "연합뉴스"), ("개항 신문", "경향신문"), ("한결의", "한겨레"),
    ("제레 언론", "레거시 언론"), ("직권 여당", "집권 여당"),
    ("구태어", "구태여"), ("선어명", "서너 명"), ("제차", "재차"),
    ("일심", "1심"), ("이심", "2심"),
]


def load_corrections(root: Path | None):
    table = list(BASE_CORRECTIONS)
    if root is not None:
        p = root / "work" / "corrections.json"
        if p.is_file():
            extra = json.loads(p.read_text(encoding="utf-8"))
            # 회차 교정을 앞에 둔다. 더 구체적인 패턴이 먼저 맞아야 한다.
            table = [tuple(x) for x in extra] + table
    return table


_TABLE: list[tuple[str, str]] = list(BASE_CORRECTIONS)


def set_root(root: Path | None) -> None:
    global _TABLE
    _TABLE = load_corrections(root)


def correct(text: str) -> str:
    for a, b in _TABLE:
        text = text.replace(a, b)
    return text


def to_seconds(m, base):
    h, mi, s, ms = (int(m.group(base + i)) for i in range(4))
    return h * 3600 + mi * 60 + s + ms / 1000.0


def parse_vtt(path):
    cues = []
    lines = Path(path).read_text(encoding="utf-8", errors="replace").splitlines()
    i = 0
    while i < len(lines):
        m = TS.search(lines[i])
        if not m:
            i += 1
            continue
        start, end = to_seconds(m, 1), to_seconds(m, 5)
        i += 1
        buf = []
        while i < len(lines) and lines[i].strip() and not TS.search(lines[i]):
            buf.append(TAG.sub("", lines[i]))
            i += 1
        text = html.unescape(" ".join(buf))
        text = SPEAKER_MARK.sub("", text).replace(">>", " ")
        text = " ".join(text.split())
        if text:
            cues.append({"start": start, "end": end, "text": text})
    return cues


def strip_overlap(prev_words, words):
    """prev 꼬리와 words 머리의 최대 겹침을 제거한 나머지."""
    limit = min(len(prev_words), len(words))
    for n in range(limit, 0, -1):
        if prev_words[-n:] == words[:n]:
            return words[n:]
    return words


def dedup(cues):
    out, carried = [], []
    for c in cues:
        words = c["text"].split()
        if not words:
            continue
        fresh = strip_overlap(carried[-40:], words) if carried else words
        if not fresh:
            continue
        out.append({"start": c["start"], "end": c["end"], "text": " ".join(fresh)})
        carried.extend(fresh)
    return out


def main():
    p = root_parser("VTT -> cues.json (겹침 제거 + 용어 교정)")
    p.add_argument("--all", action="store_true", help="<root>/srt/*.ko-orig.vtt 전부 처리")
    p.add_argument("vtt", nargs="*", type=Path)
    args = p.parse_args()
    root = resolve_root(args)
    set_root(root)
    srt_dir = root / "srt"
    targets = list(args.vtt) + (sorted(srt_dir.glob("*.ko-orig.vtt")) if args.all else [])
    if not targets:
        raise SystemExit("VTT_REQUIRED: 파일을 주거나 --all")
    for src in targets:
        stem = src.name.split(".")[0]
        cues = dedup(parse_vtt(src))
        for c in cues:
            c["text"] = correct(c["text"])
        (srt_dir / f"{stem}.cues.json").write_text(json.dumps(cues, ensure_ascii=False, indent=1), encoding="utf-8")
        (srt_dir / f"{stem}.txt").write_text(
            "\n".join(f"[{int(c['start'])//60:02d}:{int(c['start'])%60:02d}] {c['text']}" for c in cues),
            encoding="utf-8")
        print(f"{stem}: cues={len(cues)} chars={sum(len(c['text']) for c in cues)}")


if __name__ == "__main__":
    main()

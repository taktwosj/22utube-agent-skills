# -*- coding: utf-8 -*-
"""컷 실측 → 타임라인 → SRT 생성.

- SRT는 타임라인 절대값이고 카드 구간 안으로 clamp한다.
- 하단 cue는 공백 제외 15자 이하 한 줄이다.
- 원본 cue를 병합해도 구성 원본(parts)을 보존해, 재분할 시각을 원본 발화 경계에 앵커한다.
  균등 분할만 하면 병합 창 안에서 자막이 최대 4초 밀린다. (2026-09-02 실측)
- raw/display 는 같은 텍스트다. 교정은 cue 단위로 먼저, 병합 뒤 한 번 더 건다.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _common import load_cards_def, resolve_root, root_parser  # noqa: E402
import vtt_clean  # noqa: E402

MAX_CHARS = 15    # 화면 한 줄 한도, 공백 제외
MERGE_CHARS = 60  # 병합 상한


def run(args):
    p = subprocess.run(args, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if p.returncode != 0:
        raise RuntimeError(f"{args[0]} failed: {(p.stderr or '')[-400:]}")
    return p.stdout


def probe(path):
    return float(run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                      "-of", "csv=p=0", str(path)]).strip())


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest().upper()


def srt_ts(ms):
    ms = int(ms)
    h, ms = divmod(ms, 3600000)
    m, ms = divmod(ms, 60000)
    s, ms = divmod(ms, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def visible_len(text):
    return len(text.replace(" ", ""))


def split_line(text):
    """공백 제외 15자 이하 조각으로 나눈다. 단어 경계를 지키고 5자 이하 조각을 없앤다."""
    words = text.split()
    if not words:
        return []
    groups = [[]]
    for w in words:
        if groups[-1] and visible_len(" ".join(groups[-1] + [w])) > MAX_CHARS:
            groups.append([w])
        else:
            groups[-1].append(w)
    for _ in range(len(groups) * 2):
        moved = False
        for i, g in enumerate(groups):
            if not g or visible_len(" ".join(g)) > 5:
                continue
            if i > 0 and len(groups[i - 1]) > 1:
                donor = groups[i - 1]
                if visible_len(" ".join([donor[-1]] + g)) <= MAX_CHARS:
                    g.insert(0, donor.pop()); moved = True; break
            if i + 1 < len(groups) and len(groups[i + 1]) > 1:
                donor = groups[i + 1]
                if visible_len(" ".join(g + [donor[0]])) <= MAX_CHARS:
                    g.append(donor.pop(0)); moved = True; break
        if not moved:
            break
    out = [" ".join(g) for g in groups if g]
    fixed = []
    for piece in out:
        while visible_len(piece) > MAX_CHARS:
            cut = MAX_CHARS
            while visible_len(piece[:cut]) > MAX_CHARS:
                cut -= 1
            fixed.append(piece[:cut]); piece = piece[cut:].lstrip()
        if piece:
            fixed.append(piece)
    changed = True
    while changed and len(fixed) > 1:
        changed = False
        for i, piece in enumerate(fixed):
            if visible_len(piece) > 5:
                continue
            options = []
            if i > 0:
                options.append((visible_len(fixed[i - 1]), i - 1, "L"))
            if i + 1 < len(fixed):
                options.append((visible_len(fixed[i + 1]), i + 1, "R"))
            options.sort()
            for _, j, side in options:
                joined = f"{fixed[j]} {piece}" if side == "L" else f"{piece} {fixed[j]}"
                if visible_len(joined) <= MAX_CHARS:
                    fixed[j] = joined; fixed.pop(i); changed = True; break
            if changed:
                break
    return fixed


def write_srt(path, cues, start_us, duration_us):
    """cue를 ms 정수로 옮기고 카드 창 안으로 clamp. 시작은 올림, 끝은 내림."""
    lo = -(-int(start_us) // 1000)
    hi = (int(start_us) + int(duration_us)) // 1000
    kept = []
    for a, b, t in cues:
        am = max(lo, int(round(a * 1000)))
        bm = min(hi, int(round(b * 1000)))
        if kept and am < kept[-1][1]:
            am = kept[-1][1]
        if bm - am < 120:
            continue
        kept.append((am, bm, t))
    lines = []
    for i, (a, b, t) in enumerate(kept, 1):
        lines += [str(i), f"{srt_ts(a)} --> {srt_ts(b)}", t, ""]
    path.write_text("\n".join(lines), encoding="utf-8")
    return len(kept)


def merge_cues(cues):
    """짧은 원본 cue를 병합하되 parts 를 보존한다."""
    merged = []
    for c in cues:
        item = dict(c)
        item["parts"] = [{"text": c["text"], "start": c["start"], "end": c["end"]}]
        if merged:
            prev = merged[-1]
            joined = f"{prev['text']} {c['text']}".strip()
            ends_sentence = prev["text"].rstrip().endswith((".", "?", "!"))
            if not ends_sentence and c["start"] - prev["end"] < 1.2 and visible_len(joined) <= MERGE_CHARS:
                prev["text"] = joined; prev["end"] = c["end"]; prev["parts"] += item["parts"]
                continue
        merged.append(item)
    changed = True
    while changed and len(merged) > 1:
        changed = False
        for i, c in enumerate(merged):
            if visible_len(c["text"]) > 5:
                continue
            targets = []
            if i > 0:
                targets.append((visible_len(merged[i - 1]["text"]), i - 1, "L"))
            if i + 1 < len(merged):
                targets.append((visible_len(merged[i + 1]["text"]), i + 1, "R"))
            targets.sort()
            for _, j, side in targets:
                other = merged[j]; left = side == "L"
                joined = f"{other['text']} {c['text']}" if left else f"{c['text']} {other['text']}"
                if visible_len(joined) > MERGE_CHARS:
                    continue
                other["text"] = joined
                other["parts"] = (other["parts"] + c["parts"]) if left else (c["parts"] + other["parts"])
                other["start"] = min(other["start"], c["start"]); other["end"] = max(other["end"], c["end"])
                merged.pop(i); changed = True; break
            if changed:
                break
    return merged


def _anchor_map(parts):
    """문자 오프셋 -> 시각. 원본 cue 경계를 knot 으로 쓴다."""
    knots, pos = [], 0
    for p in parts:
        n = len(p["text"])
        knots.append((pos, pos + n, p["start"], p["end"]))
        pos += n + 1
    total = max(pos - 1, 1)

    def at(ch):
        ch = max(0, min(ch, total))
        for lo, hi, ts, te in knots:
            if ch < lo:
                return ts
            if ch <= hi:
                return ts + (te - ts) * ((ch - lo) / max(1, hi - lo))
        return knots[-1][3]
    return at


def source_cues(srt_dir, vid, t_in, t_out, tl_start):
    cues = json.loads((srt_dir / f"{vid}.cues.json").read_text(encoding="utf-8"))
    window = t_out - t_in
    inside = []
    for c in cues:
        s, e = c["start"], c["end"]
        if e <= t_in or s >= t_out:
            continue
        s = max(s, t_in) - t_in; e = min(e, t_out) - t_in
        if e - s < 0.20:
            continue
        inside.append({"start": s, "end": e, "text": " ".join(vtt_clean.correct(c["text"]).split())})
    out = []
    for m in merge_cues(inside):
        parts = m["parts"]
        joined = " ".join(p["text"] for p in parts)
        fixed = " ".join(vtt_clean.correct(joined).split())
        pieces = split_line(fixed)
        if not pieces:
            continue
        if fixed == joined and len(parts) > 1:
            at = _anchor_map(parts); cur = 0
            for piece in pieces:
                idx = fixed.find(piece, cur)
                if idx < 0:
                    idx = cur
                a, b = at(idx), at(idx + len(piece)); cur = idx + len(piece)
                if b - a < 0.12:
                    b = a + 0.12
                out.append((tl_start + a, tl_start + min(b, window), piece))
        else:
            s, e = m["start"], m["end"]; step = (e - s) / len(pieces)
            for k, piece in enumerate(pieces):
                a = s + k * step; b = min(s + (k + 1) * step, window)
                if b - a >= 0.12:
                    out.append((tl_start + a, tl_start + b, piece))
    tidy = []
    for a, b, t in out:
        if tidy and a < tidy[-1][1]:
            a = tidy[-1][1]
        if b - a >= 0.12:
            tidy.append((a, b, t))
    return tidy


def narration_cues(narr_dir, name, duration, tl_start, numerals):
    text = (narr_dir / f"{name}.txt").read_text(encoding="utf-8").strip()
    pieces = []
    for line in text.splitlines():
        line = line.strip()
        for a, b in numerals:
            line = line.replace(a, b)
        if line:
            pieces += split_line(line)
    total = sum(max(1, visible_len(p)) for p in pieces)
    out, t = [], 0.0
    for p in pieces:
        share = duration * max(1, visible_len(p)) / total
        out.append((tl_start + t, tl_start + min(t + share, duration), p)); t += share
    return out


def main():
    args = root_parser("컷 실측 → timeline.json + SRT").parse_args()
    root = resolve_root(args)
    cd = load_cards_def(root)
    vtt_clean.set_root(root)
    clips, srt, narr, work = root / "clips", root / "srt", root / "narration", root / "work"
    srt.mkdir(exist_ok=True)
    numerals = getattr(cd, "DISPLAY_NUMERALS", [])
    timeline_us, records = 0, []
    for card in cd.CARDS:
        cid, kind = card[0], card[1]
        if kind == "SRC":
            vid, t_in, t_out = card[2], card[3], card[4]
            dst = clips / f"{cid}.mp4"
            if not dst.exists():
                # 프레임 정확도를 위해 재인코딩한다. -c copy 는 키프레임에 붙어 수 초 어긋난다.
                run(["ffmpeg", "-nostdin", "-y", "-loglevel", "error", "-ss", f"{t_in:.3f}",
                     "-i", str(clips / f"{vid}.mp4"), "-t", f"{t_out - t_in:.3f}",
                     "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
                     "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", str(dst)])
            dur = probe(dst); dur_us = int(round(dur * 1_000_000))
            cues = source_cues(srt, vid, t_in, t_in + dur, timeline_us / 1_000_000)
            raw_p, disp_p = srt / f"{cid}.raw.srt", srt / f"{cid}.display.srt"
            n = write_srt(raw_p, cues, timeline_us, dur_us); write_srt(disp_p, cues, timeline_us, dur_us)
            ch, date, disp = cd.SOURCES[vid]
            records.append({
                "card_id": cid, "kind": "SRC", "video_id": vid,
                "target_start_us": timeline_us, "target_duration_us": dur_us,
                "source_file": str(dst), "source_sha256": sha256(dst), "source_duration_us": dur_us,
                "source_channel": ch, "source_date": date, "source_display_label": disp,
                "source_in": t_in, "source_out": t_in + dur,
                "raw_transcript_path": str(raw_p), "raw_transcript_sha256": sha256(raw_p),
                "display_srt_path": str(disp_p), "display_srt_sha256": sha256(disp_p),
                "source_srt_file": str(disp_p), "source_srt_sha256": sha256(disp_p),
                "lower_mode": "NONE" if vid in cd.BURNED_CAPTION else "SRT", "cue_count": n,
            })
        else:
            nm = card[2]
            wav = narr / f"{nm}.wav"
            dur = probe(wav); dur_us = int(round(dur * 1_000_000))
            cues = narration_cues(narr, nm, dur, timeline_us / 1_000_000, numerals)
            nsrt = srt / f"{cid}.narration.srt"
            n = write_srt(nsrt, cues, timeline_us, dur_us)
            records.append({
                "card_id": cid, "kind": "NAR", "narration_name": nm,
                "target_start_us": timeline_us, "target_duration_us": dur_us,
                "narration_audio_file": str(wav), "narration_audio_sha256": sha256(wav),
                "audio_duration_us": dur_us,
                "narration_srt_file": str(nsrt), "narration_srt_sha256": sha256(nsrt),
                "image_file": str(root / "cards" / f"{cid}.png"), "cue_count": n,
            })
        timeline_us += dur_us
    total = timeline_us / 1_000_000
    (work / "timeline.json").write_text(json.dumps({"total_seconds": total, "cards": records},
                                                   ensure_ascii=False, indent=1), encoding="utf-8")
    src = sum(r["target_duration_us"] for r in records if r["kind"] == "SRC") / 1e6
    nar = sum(r["target_duration_us"] for r in records if r["kind"] == "NAR") / 1e6
    hook = sum(r["target_duration_us"] for r in records if r["card_id"].startswith("C00_HOOK")) / 1e6
    spine_vid = getattr(cd, "SPINE_VIDEO_ID", None)
    spine = sum(r["target_duration_us"] for r in records
                if r["kind"] == "SRC" and r.get("video_id") == spine_vid
                and not r["card_id"].startswith("C00_HOOK")) / 1e6 if spine_vid else 0.0
    print(f"cards={len(records)} total={total:.2f}s ({total/60:.2f}min)")
    print(f"source={src:.2f}s narration={nar:.2f}s ({nar/total*100:.1f}%) hook={hook:.2f}s")
    if spine_vid:
        print(f"spine={spine:.2f}s ({spine/60:.2f}min, {spine/total*100:.1f}%)  "
              f"{'OK' if spine/total >= 0.5 and spine >= 900 else 'BELOW_CONTRACT'}")


if __name__ == "__main__":
    main()

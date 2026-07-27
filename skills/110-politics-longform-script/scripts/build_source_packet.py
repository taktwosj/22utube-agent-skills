#!/usr/bin/env python3
"""수집 자막을 GPT 입력 패킷으로 묶는다.

GPT 는 이 파일 하나만 보고 초벌 대본을 쓴다. 원본 mp4 는 필요 없다.
매니페스트가 선언한 cue 수와 실제 SRT cue 수가 다르면 아무것도 쓰지 않고
멈춘다 -- 다른 회차 자막이 섞였다는 뜻이다.

    py -3.14 build_source_packet.py --episode <에피소드 경로>
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
from pathlib import Path

TC = re.compile(
    r"(\d{2}):(\d{2}):(\d{2})[,.](\d{3})\s*-->\s*"
    r"(\d{2}):(\d{2}):(\d{2})[,.](\d{3})")

# 수집보고서가 의혹으로 표시한 사안. 확정 서술과 같은 문장에 오면 검증에서
# 걸린다. 회차마다 다르므로 매니페스트에서 덮어쓸 수 있다.
DEFAULT_ALLEGATION_TERMS = ["신천지", "의혹", "개입", "가입"]

LEXICON = [
    "보완수사권", "공소청", "중수청", "형사소송법", "직접수사권",
    "국가수사본부", "고위공직자범죄수사처", "합동수사본부",
]


def to_sec(h, m, s, ms):
    return int(h) * 3600 + int(m) * 60 + int(s) + int(ms) / 1000


def parse_srt(text):
    """(cue_index, start_sec, end_sec, text) 목록. 번호는 1부터 다시 매긴다.

    원본 번호를 믿지 않는다. 수집기가 정리하면서 번호가 비거나 겹칠 수 있고,
    대본은 '몇 번째 cue' 로 참조하므로 순서가 곧 번호다.
    """
    cues = []
    block = []
    for line in text.replace("\r\n", "\n").replace("\r", "\n").split("\n"):
        if line.strip():
            block.append(line)
            continue
        if block:
            cues.append(block)
            block = []
    if block:
        cues.append(block)

    out = []
    dropped = []
    for b in cues:
        m = None
        body_from = 0
        for i, line in enumerate(b[:3]):
            m = TC.search(line)
            if m:
                body_from = i + 1
                break
        if not m:
            # 조용히 버리면 불완전한 자막이 정본이 된다. 대본은 이 자막을
            # 근거로 쓰는데 원문 일부가 없다는 사실을 아무도 모른다.
            dropped.append(b[0][:60] if b else "")
            continue
        body = " ".join(x.strip() for x in b[body_from:]).strip()
        if not body:
            dropped.append(b[0][:60] if b else "")
            continue
        out.append({
            "cue": len(out) + 1,
            "start": round(to_sec(*m.group(1, 2, 3, 4)), 3),
            "end": round(to_sec(*m.group(5, 6, 7, 8)), 3),
            "text": body,
        })
    return out, dropped


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--episode", default=os.environ.get("PL_EPISODE_DIR"),
                    help="에피소드 디렉터리 (환경변수 PL_EPISODE_DIR 도 가능)")
    args = ap.parse_args()

    if not args.episode:
        print("BLOCKED: --episode 또는 PL_EPISODE_DIR 가 필요하다",
              file=sys.stderr)
        return 2

    ep = Path(args.episode)
    mpath = ep / "00_source" / "source_manifest.json"
    if not mpath.is_file():
        print(f"BLOCKED_SOURCE_PACKET_NOT_BUILT: 매니페스트 없음 {mpath}",
              file=sys.stderr)
        return 2

    manifest = json.loads(mpath.read_text(encoding="utf-8"))
    tdir = ep / "10_analysis" / "transcripts"

    sources = []
    missing = []
    mismatch = []
    for s in manifest["sources"]:
        sid = s["source_id"]
        spath = tdir / f"{sid}.srt"
        if not spath.is_file():
            missing.append(str(spath))
            continue
        cues, dropped = parse_srt(spath.read_text(encoding="utf-8"))
        if dropped:
            mismatch.append(f"{sid}: 읽지 못한 cue 블록 {len(dropped)}개 "
                            f"(첫 줄 {dropped[0]!r})")
            continue
        want = s.get("transcript_cue_count")
        if want is None:
            # 개수 선언이 없으면 대조할 기준이 없다. 자막이 잘려도 모른다.
            mismatch.append(f"{sid}: 매니페스트에 transcript_cue_count 없음")
            continue
        if len(cues) != want:
            mismatch.append(f"{sid}: 실제 {len(cues)} != 매니페스트 {want}")
            continue
        sources.append({
            "source_id": sid,
            "video_id": s["video_id"],
            "title": s["title"],
            "channel": s["channel"],
            "upload_date": s["upload_date"],
            "url": s["url"],
            "duration_sec": s["duration_sec"],
            "cue_count": len(cues),
            "srt_sha256": sha256(spath),
            "cues": cues,
        })

    if missing:
        print("BLOCKED_TRANSCRIPT_MISSING", file=sys.stderr)
        for m in missing:
            print("  " + m, file=sys.stderr)
        return 1
    if mismatch:
        print("BLOCKED_TRANSCRIPT_MISMATCH: 다른 회차 자막이 섞였을 수 있다",
              file=sys.stderr)
        for m in mismatch:
            print("  " + m, file=sys.stderr)
        return 1

    constraints = manifest.get("editorial_constraints", {})
    packet = {
        "schema": "politics-longform-source-packet.v1",
        "episode_id": manifest["episode_id"],
        "source_manifest_sha256": sha256(mpath),
        "counts": {
            "sources": len(sources),
            "total_cues": sum(s["cue_count"] for s in sources),
        },
        "editorial_constraints": constraints,
        "allegation_terms": manifest.get("allegation_terms",
                                         DEFAULT_ALLEGATION_TERMS),
        "lexicon": LEXICON,
        "instructions_for_gpt":
            "references/draft-schema.md 의 양식과 유의사항을 따른다. "
            "DIRECT 인용은 아래 cues[].text 와 문자 단위로 같아야 한다.",
        "sources": sources,
    }

    outdir = ep / "20_script"
    outdir.mkdir(parents=True, exist_ok=True)
    out = outdir / "source_packet_v1.json"
    tmp = out.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(packet, ensure_ascii=False, indent=2),
                   encoding="utf-8")
    tmp.replace(out)

    print(f"OK  {out}")
    print(f"    소스 {len(sources)}건 / cue {packet['counts']['total_cues']}")
    print(f"    SHA-256 {sha256(out)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

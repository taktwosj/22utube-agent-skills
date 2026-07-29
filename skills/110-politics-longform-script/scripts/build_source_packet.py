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
from pathlib import Path, PurePosixPath

TC = re.compile(
    r"(\d{2}):(\d{2}):(\d{2})[,.](\d{3})\s*-->\s*"
    r"(\d{2}):(\d{2}):(\d{2})[,.](\d{3})")

# 수집보고서가 의혹으로 표시한 사안. 확정 서술과 같은 문장에 오면 검증에서
# 걸린다. 회차마다 다르므로 매니페스트에서 덮어쓸 수 있다.
DEFAULT_ALLEGATION_TERMS = ["신천지", "의혹", "개입", "가입"]

SOURCE_REVIEW_RELPATH = (
    Path("90_reports") / "source_srt_quality_report_v1.json")
TERM_PACK_RELPATH = Path("10_analysis") / "episode_term_pack_v1.json"
EPISODE_CANDIDATES_RELPATH = (
    Path("10_analysis") / "source_term_candidates_v1.json")
DEFAULT_REGISTRY = (
    Path(__file__).resolve().parent.parent
    / "references" / "politics_terms_v1.jsonl")
SOURCE_REVIEW_SCHEMA = "source_srt_quality_report_v1"


def load_source_review(ep, manifest, registry_path=DEFAULT_REGISTRY):
    """Fail closed unless the exact SRTs passed user audio comparison."""
    report_path = ep / SOURCE_REVIEW_RELPATH
    term_pack_path = ep / TERM_PACK_RELPATH
    candidates_path = ep / EPISODE_CANDIDATES_RELPATH
    if not report_path.is_file():
        raise ValueError("WAIT_SOURCE_ASR_REVIEW: source SRT quality report missing")
    if not term_pack_path.is_file():
        raise ValueError("WAIT_SOURCE_ASR_REVIEW: episode term pack missing")
    if not candidates_path.is_file():
        raise ValueError("WAIT_SOURCE_ASR_REVIEW: first-seen term scan missing")
    report = json.loads(report_path.read_text(encoding="utf-8"))
    term_pack = json.loads(term_pack_path.read_text(encoding="utf-8"))
    if report.get("schema_version") != SOURCE_REVIEW_SCHEMA:
        raise ValueError("WAIT_SOURCE_ASR_REVIEW: review schema invalid")
    if report.get("status") != "PASS_110_SOURCE_SRT_REVIEWED":
        raise ValueError("WAIT_SOURCE_ASR_REVIEW: review is not PASS")
    if report.get("episode_id") != manifest.get("episode_id"):
        raise ValueError("WAIT_SOURCE_ASR_REVIEW: episode_id mismatch")
    if term_pack.get("schema_version") != "politics_episode_term_pack_v1":
        raise ValueError("WAIT_SOURCE_ASR_REVIEW: term pack schema invalid")
    if report.get("term_pack_sha256") != sha256(term_pack_path):
        raise ValueError("WAIT_SOURCE_ASR_REVIEW: term pack changed after review")
    registry_sha = sha256(registry_path)
    if (report.get("registry_sha256") != registry_sha
            or term_pack.get("registry_sha256") != registry_sha):
        raise ValueError("WAIT_SOURCE_ASR_REVIEW: registry SHA mismatch")
    transcripts = report.get("transcripts")
    if not isinstance(transcripts, dict):
        raise ValueError("WAIT_SOURCE_ASR_REVIEW: transcript bindings missing")
    expected_sources = {
        source.get("source_id") for source in manifest.get("sources", [])}
    if set(transcripts) != expected_sources:
        raise ValueError("WAIT_SOURCE_ASR_REVIEW: transcript binding count mismatch")
    receipt = report.get("review_receipt") or {}
    if receipt.get("errors") != []:
        raise ValueError("WAIT_SOURCE_ASR_REVIEW: receipt errors remain")
    rel = receipt.get("path")
    if not isinstance(rel, str) or not rel:
        raise ValueError("WAIT_SOURCE_ASR_REVIEW: receipt path missing")
    normalized = rel.replace("\\", "/")
    pure = PurePosixPath(normalized)
    if (pure.is_absolute() or ".." in pure.parts
            or re.match(r"^[A-Za-z]:", normalized)):
        raise ValueError("WAIT_SOURCE_ASR_REVIEW: receipt path outside episode")
    receipt_path = (ep / Path(*pure.parts)).resolve()
    root = ep.resolve()
    if root != receipt_path and root not in receipt_path.parents:
        raise ValueError("WAIT_SOURCE_ASR_REVIEW: receipt path outside episode")
    if (not receipt_path.is_file()
            or sha256(receipt_path) != receipt.get("sha256")):
        raise ValueError("WAIT_SOURCE_ASR_REVIEW: receipt SHA mismatch")
    candidates_sha = sha256(candidates_path)
    if (report.get("episode_candidates_sha256") != candidates_sha
            or receipt.get("episode_candidates_sha256") != candidates_sha):
        raise ValueError("WAIT_SOURCE_ASR_REVIEW: first-seen term scan SHA mismatch")
    return report_path, report, transcripts, term_pack


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
    ap.add_argument("--registry", type=Path, default=DEFAULT_REGISTRY,
                    help="검수에 사용한 정치용어 JSONL 정본")
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

    try:
        review_path, review, review_transcripts, term_pack = load_source_review(
            ep, manifest, args.registry)
    except Exception as exc:
        print(str(exc), file=sys.stderr)
        return 1

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
        if review_transcripts.get(sid) != sha256(spath):
            mismatch.append(f"{sid}: source SRT changed after semantic review")
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
        "source_srt_review": {
            "path": review_path.relative_to(ep).as_posix(),
            "sha256": sha256(review_path),
            "status": review["status"],
            "registry_sha256": review.get("registry_sha256"),
            "term_pack_sha256": review.get("term_pack_sha256"),
            "review_receipt_sha256": (
                review.get("review_receipt") or {}).get("sha256"),
            "episode_candidates_sha256": review.get(
                "episode_candidates_sha256"),
            "transcripts": review_transcripts,
        },
        "counts": {
            "sources": len(sources),
            "total_cues": sum(s["cue_count"] for s in sources),
        },
        "editorial_constraints": constraints,
        "allegation_terms": manifest.get("allegation_terms",
                                         DEFAULT_ALLEGATION_TERMS),
        "lexicon": [item["canonical"]
                    for item in term_pack.get("terms", [])],
        "lexicon_policy": {
            "source": TERM_PACK_RELPATH.as_posix(),
            "observed_terms_are_not_correction_authority": True,
            "silent_autocorrection": False,
        },
        "instructions_for_gpt":
            "references/draft-schema.md 의 양식과 유의사항을 따른다. "
            "DIRECT 인용은 아래 cues[].text 와 문자 단위로 같아야 한다. "
            "lexicon은 검수 힌트이며 원문 자동 교정 권한이 아니다.",
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

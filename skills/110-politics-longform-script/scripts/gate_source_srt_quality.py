#!/usr/bin/env python3
"""Gate imported source SRT before 110 creates a source packet.

The registry narrows review and detects approved confusion pairs or close
phonetic matches.  It never silently edits text.  A PASS additionally requires
an audio-comparison receipt bound to the exact final SRT files.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

from politics_term_registry import (
    atomic_write_json,
    load_registry,
    normalize_key,
    phonetic_similarity,
    sha256_file,
)

HERE = Path(__file__).resolve().parent
DEFAULT_REGISTRY = HERE.parent / "references" / "politics_terms_v1.jsonl"
TIMECODE = re.compile(
    r"(\d{2}):(\d{2}):(\d{2})[,.](\d{3})\s*-->\s*"
    r"(\d{2}):(\d{2}):(\d{2})[,.](\d{3})"
)
WORD = re.compile(r"[가-힣A-Za-z0-9]{2,20}")
EPISODE_CANDIDATES_RELPATH = (
    Path("10_analysis") / "source_term_candidates_v1.json")


def to_sec(h: str, m: str, s: str, ms: str) -> float:
    return int(h) * 3600 + int(m) * 60 + int(s) + int(ms) / 1000


def issue_id(*parts: object) -> str:
    value = "\x1f".join(str(part) for part in parts)
    return "srt_" + hashlib.sha256(value.encode("utf-8")).hexdigest()[:16]


def parse_srt(path: Path) -> tuple[list[dict], list[str]]:
    blocks = re.split(r"\n\s*\n", path.read_text(encoding="utf-8").replace("\r\n", "\n"))
    cues: list[dict] = []
    invalid: list[str] = []
    for block in blocks:
        lines = [line.strip() for line in block.splitlines() if line.strip()]
        if not lines:
            continue
        time_index = next(
            (index for index, line in enumerate(lines[:3]) if TIMECODE.search(line)),
            None,
        )
        if time_index is None:
            invalid.append(lines[0][:80])
            continue
        body = " ".join(lines[time_index + 1 :]).strip()
        if not body:
            invalid.append(lines[0][:80])
            continue
        match = TIMECODE.search(lines[time_index])
        cues.append({
            "cue": len(cues) + 1,
            "start": round(to_sec(*match.group(1, 2, 3, 4)), 3),
            "end": round(to_sec(*match.group(5, 6, 7, 8)), 3),
            "text": body,
        })
    return cues, invalid


def candidate_windows(text: str) -> list[str]:
    words = WORD.findall(text)
    result: list[str] = []
    for start in range(len(words)):
        for width in (1, 2, 3):
            if start + width <= len(words):
                result.append(" ".join(words[start : start + width]))
    return result


def load_receipt(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def review_window(cue: dict) -> dict:
    return {
        "start_sec": cue["start"],
        "end_sec": cue["end"],
        "audio_review_start_sec": round(max(0, cue["start"] - 3), 3),
        "audio_review_end_sec": round(cue["end"] + 3, 3),
        "raw_asr": cue["text"],
    }


def relative_to_episode(path: Path, episode: Path) -> str:
    resolved = path.resolve()
    root = episode.resolve()
    if resolved == root or root in resolved.parents:
        return resolved.relative_to(root).as_posix()
    return f"external/{path.name}"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--episode",
        type=Path,
        default=Path(os.environ["PL_EPISODE_DIR"])
        if os.environ.get("PL_EPISODE_DIR")
        else None,
    )
    parser.add_argument("--registry", type=Path, default=DEFAULT_REGISTRY)
    parser.add_argument("--term-pack", type=Path)
    parser.add_argument("--review-receipt", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--near-threshold", type=float, default=0.86)
    args = parser.parse_args()
    if args.episode is None:
        parser.error("--episode 또는 PL_EPISODE_DIR가 필요하다")
    if not 0.75 <= args.near_threshold <= 1:
        parser.error("--near-threshold는 0.75~1이어야 한다")

    term_pack_path = (
        args.term_pack
        or args.episode / "10_analysis" / "episode_term_pack_v1.json"
    )
    receipt_path = (
        args.review_receipt
        or args.episode / "90_reports" / "source_srt_review_receipt_v1.json"
    )
    output = (
        args.output
        or args.episode / "90_reports" / "source_srt_quality_report_v1.json"
    )

    try:
        registry = load_registry(args.registry)
        term_pack = json.loads(term_pack_path.read_text(encoding="utf-8"))
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"WAIT_SOURCE_ASR_REVIEW: 입력 오류 {exc}", file=sys.stderr)
        return 2
    registry_sha = sha256_file(args.registry)
    term_pack_sha = sha256_file(term_pack_path)
    if term_pack.get("schema_version") != "politics_episode_term_pack_v1":
        print("WAIT_SOURCE_ASR_REVIEW: term pack schema 불일치", file=sys.stderr)
        return 2
    if term_pack.get("registry_sha256") != registry_sha:
        print("WAIT_SOURCE_ASR_REVIEW: term pack registry SHA 불일치", file=sys.stderr)
        return 2

    by_id = {record["term_id"]: record for record in registry}
    selected: list[dict] = []
    for packed in term_pack.get("terms", []):
        record = by_id.get(packed.get("term_id"))
        if not record or record["canonical"] != packed.get("canonical"):
            print("WAIT_SOURCE_ASR_REVIEW: term pack 항목 변조", file=sys.stderr)
            return 2
        selected.append(record)

    transcript_dir = args.episode / "10_analysis" / "transcripts"
    manifest_path = args.episode / "00_source" / "source_manifest.json"
    if not manifest_path.is_file():
        print("WAIT_SOURCE_ASR_REVIEW: source_manifest.json 없음", file=sys.stderr)
        return 2
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    source_ids = [source["source_id"] for source in manifest.get("sources", [])]
    if not source_ids:
        print("WAIT_SOURCE_ASR_REVIEW: source 목록 없음", file=sys.stderr)
        return 2

    transcripts: dict[str, str] = {}
    cue_sets: dict[str, list[dict]] = {}
    issues: list[dict] = []
    for source_id in source_ids:
        path = transcript_dir / f"{source_id}.srt"
        if not path.is_file():
            print(f"WAIT_SOURCE_ASR_REVIEW: 자막 없음 {path}", file=sys.stderr)
            return 2
        transcripts[source_id] = sha256_file(path)
        cues, invalid = parse_srt(path)
        cue_sets[source_id] = cues
        for first_line in invalid:
            issues.append(
                {
                    "issue_id": issue_id(source_id, "INVALID_SRT_BLOCK", first_line),
                    "severity": "block",
                    "kind": "INVALID_SRT_BLOCK",
                    "source_id": source_id,
                    "cue": None,
                    "start_sec": None,
                    "end_sec": None,
                    "audio_review_start_sec": None,
                    "audio_review_end_sec": None,
                    "raw_asr": first_line,
                    "observed": first_line,
                    "suggested": None,
                    "candidate_text": None,
                    "similarity": None,
                    "confidence": "BLOCK",
                    "reason": "INVALID_SRT_BLOCK",
                    "message": "시간축 또는 본문을 읽을 수 없는 SRT 블록",
                }
            )

    valid_norms = {record["normalized"] for record in registry}
    for record in selected:
        canonical = record["canonical"]
        canonical_norm = record["normalized"]
        for source_id, cues in cue_sets.items():
            source_norm = normalize_key(" ".join(cue["text"] for cue in cues))
            for confusion in record["asr_confusions"]:
                confusion_norm = normalize_key(confusion["surface"])
                for cue in cues:
                    if confusion_norm and confusion_norm in normalize_key(cue["text"]):
                        issue = {
                                "issue_id": issue_id(
                                    source_id,
                                    cue["cue"],
                                    "APPROVED_ASR_CONFUSION",
                                    confusion["surface"],
                                    canonical,
                                ),
                                "severity": "block",
                                "kind": "APPROVED_ASR_CONFUSION",
                                "source_id": source_id,
                                "cue": cue["cue"],
                                **review_window(cue),
                                "observed": confusion["surface"],
                                "suggested": canonical,
                                "candidate_text": cue["text"].replace(
                                    confusion["surface"], canonical),
                                "similarity": None,
                                "confidence": "APPROVED_CONFUSION",
                                "reason": confusion["evidence"],
                                "message": "승인된 정치용어 ASR 오인식 쌍과 일치",
                            }
                        issues.append(issue)
            if canonical_norm in source_norm:
                continue
            if len(canonical_norm) < 3:
                continue
            if (
                record["category"] not in {"named_entity", "news_noun_phrase"}
                and record["priority"] < 60
            ):
                continue
            best: tuple[float, int, str] | None = None
            for cue in cues:
                for observed in candidate_windows(cue["text"]):
                    observed_norm = normalize_key(observed)
                    if observed_norm in valid_norms or observed_norm == canonical_norm:
                        continue
                    if abs(len(observed_norm) - len(canonical_norm)) > 2:
                        continue
                    score = phonetic_similarity(observed_norm, canonical_norm)
                    if best is None or score > best[0]:
                        best = (score, cue["cue"], observed)
            threshold = max(
                args.near_threshold,
                0.92 if len(canonical_norm) <= 3 else args.near_threshold,
            )
            if best and best[0] >= threshold:
                cue = next(
                    item for item in cues if item["cue"] == best[1])
                issues.append({
                        "issue_id": issue_id(
                            source_id,
                            best[1],
                            "PHONETIC_NEAR_MATCH",
                            best[2],
                            canonical,
                        ),
                        "severity": "review",
                        "kind": "PHONETIC_NEAR_MATCH",
                        "source_id": source_id,
                        "cue": best[1],
                        **review_window(cue),
                        "observed": best[2],
                        "suggested": canonical,
                        "candidate_text": cue["text"].replace(
                            best[2], canonical),
                        "similarity": round(best[0], 4),
                        "confidence": round(best[0], 4),
                        "reason": "PHONETIC_NEAR_MATCH",
                        "message": "회차 정치용어와 발음이 가까우나 표기가 다름",
                    })

    episode_candidates_path = args.episode / EPISODE_CANDIDATES_RELPATH
    if not episode_candidates_path.is_file():
        print("WAIT_SOURCE_ASR_REVIEW: PROJECT_GPT first-seen term scan missing",
              file=sys.stderr)
        return 2
    try:
        candidate_payload = json.loads(
            episode_candidates_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"WAIT_SOURCE_ASR_REVIEW: candidate queue invalid {exc}",
              file=sys.stderr)
        return 2
    if (set(candidate_payload) != {
            "schema", "episode_id", "generated_by", "transcripts", "candidates"}
            or candidate_payload.get("schema")
            != "politics-longform-source-term-candidates.v1"
            or candidate_payload.get("episode_id") != manifest.get("episode_id")
            or candidate_payload.get("generated_by") != "PROJECT_GPT"
            or candidate_payload.get("transcripts") != transcripts
            or not isinstance(candidate_payload.get("candidates"), list)):
        print("WAIT_SOURCE_ASR_REVIEW: candidate queue schema/binding invalid",
              file=sys.stderr)
        return 2
    episode_candidates_sha = sha256_file(episode_candidates_path)
    for position, candidate in enumerate(candidate_payload["candidates"], 1):
        if not isinstance(candidate, dict):
            print(f"WAIT_SOURCE_ASR_REVIEW: candidate {position} invalid",
                  file=sys.stderr)
            return 2
        if (not {"source_id", "cue", "raw_term"} <= set(candidate)
                or not set(candidate) <= {
                    "source_id", "cue", "raw_term", "proposed_term",
                    "confidence", "reason"}):
            print(f"WAIT_SOURCE_ASR_REVIEW: candidate {position} fields invalid",
                  file=sys.stderr)
            return 2
        source_id = candidate.get("source_id")
        cue_no = candidate.get("cue")
        raw_term = candidate.get("raw_term")
        cue = next((item for item in cue_sets.get(source_id, [])
                    if item["cue"] == cue_no), None)
        if (cue is None or not isinstance(raw_term, str)
                or not raw_term or raw_term not in cue["text"]):
            print(f"WAIT_SOURCE_ASR_REVIEW: candidate {position} binding invalid",
                  file=sys.stderr)
            return 2
        proposed = candidate.get("proposed_term") or raw_term
        if not isinstance(proposed, str) or not proposed:
            print(f"WAIT_SOURCE_ASR_REVIEW: candidate {position} term invalid",
                  file=sys.stderr)
            return 2
        issues.append({
            "issue_id": issue_id(
                source_id, cue_no, "NEW_OR_UNKNOWN_TERM", raw_term,
                proposed),
            "severity": "review",
            "kind": "NEW_OR_UNKNOWN_TERM",
            "source_id": source_id,
            "cue": cue_no,
            **review_window(cue),
            "observed": raw_term,
            "suggested": proposed,
            "candidate_text": cue["text"].replace(raw_term, proposed),
            "similarity": None,
            "confidence": candidate.get("confidence", "UNASSESSED"),
            "reason": candidate.get("reason", "FIRST_SEEN_TERM"),
            "message": "처음 보거나 확신이 낮은 용어: 사용자 음성 확인 필요",
        })

    issues = list({item["issue_id"]: item for item in issues}.values())

    issues.sort(
        key=lambda item: (
            item["source_id"],
            item["cue"] if item["cue"] is not None else -1,
            item["kind"],
            item["issue_id"],
        )
    )
    receipt_errors: list[str] = []
    receipt_sha: str | None = None
    receipt: dict | None = None
    if not receipt_path.is_file():
        receipt_errors.append("audio comparison receipt missing")
    else:
        try:
            receipt = load_receipt(receipt_path)
            receipt_sha = sha256_file(receipt_path)
        except (OSError, json.JSONDecodeError) as exc:
            receipt_errors.append(f"invalid receipt: {exc}")
    if receipt is not None:
        if receipt.get("schema_version") != "source_srt_review_receipt_v1":
            receipt_errors.append("receipt schema mismatch")
        if receipt.get("audio_compared") is not True:
            receipt_errors.append("audio_compared must be true")
        if receipt.get("review_origin") != "USER_AUDIO_REVIEW":
            receipt_errors.append("review_origin must be USER_AUDIO_REVIEW")
        if receipt.get("recorded_by") != "PROJECT_GPT":
            receipt_errors.append("recorded_by must be PROJECT_GPT")
        if not str(receipt.get("reviewed_by", "")).strip():
            receipt_errors.append("reviewed_by missing")
        if receipt.get("registry_sha256") != registry_sha:
            receipt_errors.append("receipt registry SHA mismatch")
        if receipt.get("term_pack_sha256") != term_pack_sha:
            receipt_errors.append("receipt term pack SHA mismatch")
        if receipt.get("episode_candidates_sha256") != episode_candidates_sha:
            receipt_errors.append("receipt first-seen term scan SHA mismatch")
        if receipt.get("transcripts") != transcripts:
            receipt_errors.append("receipt transcript SHA mismatch")
        decision_items = receipt.get("decisions")
        if not isinstance(decision_items, list):
            receipt_errors.append("decisions must be a list")
            decision_items = []
        decisions = {}
        for item in decision_items:
            if (not isinstance(item, dict)
                    or set(item) != {"issue_id", "action", "rationale"}
                    or item.get("action") not in {
                        "corrected", "accepted", "false_positive"}
                    or not str(item.get("rationale", "")).strip()):
                receipt_errors.append("invalid issue decision")
                continue
            decision_id = item.get("issue_id")
            if decision_id in decisions:
                receipt_errors.append(f"duplicate issue decision: {decision_id}")
                continue
            decisions[decision_id] = item
        for issue in issues:
            if issue["severity"] == "block":
                receipt_errors.append(
                    f"blocking issue must be corrected in SRT: {issue['issue_id']}"
                )
                continue
            decision = decisions.get(issue["issue_id"])
            if decision is None:
                receipt_errors.append(f"issue decision missing: {issue['issue_id']}")
                continue
            if decision.get("action") == "corrected":
                receipt_errors.append(
                    f"corrected issue still present; fix SRT and rerun: {issue['issue_id']}"
                )
            if len(str(decision.get("rationale", "")).strip()) < 5:
                receipt_errors.append(f"issue rationale too short: {issue['issue_id']}")

    status = (
        "PASS_110_SOURCE_SRT_REVIEWED"
        if not receipt_errors
        else "WAIT_SOURCE_ASR_REVIEW"
    )
    report = {
        "schema_version": "source_srt_quality_report_v1",
        "episode_id": manifest.get("episode_id"),
        "status": status,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "registry_sha256": registry_sha,
        "term_pack_sha256": term_pack_sha,
        "transcripts": transcripts,
        "lexical_scan": {
            "selected_term_count": len(selected),
            "issue_count": len(issues),
            "near_threshold": args.near_threshold,
            "silent_autocorrection": False,
            "audio_fidelity_proven_by_lexicon": False,
        },
        "issues": issues,
        "episode_candidates_sha256": episode_candidates_sha,
        "notification_contract": {
            "required_fields": [
                "source_id", "cue", "start_sec", "end_sec", "raw_asr",
                "candidate_text", "audio_review_start_sec",
                "audio_review_end_sec", "reason", "confidence"],
            "auto_correction_allowed": False,
            "required_user_action": "LISTEN_AND_CONFIRM",
        },
        "review_receipt": {
            "path": relative_to_episode(receipt_path, args.episode),
            "sha256": receipt_sha,
            "episode_candidates_sha256": (
                receipt or {}).get("episode_candidates_sha256"),
            "errors": receipt_errors,
        },
    }
    atomic_write_json(output, report)
    print(
        f"{status} issues={len(issues)} receipt_errors={len(receipt_errors)} "
        f"output={output}"
    )
    return 0 if status == "PASS_110_SOURCE_SRT_REVIEWED" else 1


if __name__ == "__main__":
    raise SystemExit(main())

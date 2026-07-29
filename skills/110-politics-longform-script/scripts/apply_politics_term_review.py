#!/usr/bin/env python3
"""Apply explicit human review decisions to a politics term registry."""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

from politics_term_registry import (
    load_registry,
    normalize_display,
    normalize_key,
    sha256_file,
)


def write_jsonl(path: Path, records: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        "".join(json.dumps(record, ensure_ascii=False) + "\n" for record in records),
        encoding="utf-8",
    )
    temporary.replace(path)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--registry", type=Path, required=True)
    parser.add_argument("--review", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--sources-metadata", type=Path)
    parser.add_argument("--metadata-output", type=Path)
    args = parser.parse_args()
    if args.registry.resolve() == args.output.resolve():
        parser.error("원본 덮어쓰기는 금지한다. 검수 출력 경로를 따로 지정한다")
    if args.sources_metadata and args.metadata_output is None:
        parser.error("--sources-metadata 사용 시 --metadata-output도 필요하다")

    try:
        records = load_registry(args.registry)
        review = json.loads(args.review.read_text(encoding="utf-8"))
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"FAIL_POLITICS_TERM_REVIEW: {exc}", file=sys.stderr)
        return 2
    if review.get("schema_version") != "politics_term_review_v1":
        print("FAIL_POLITICS_TERM_REVIEW: schema 불일치", file=sys.stderr)
        return 2
    reviewed_by = str(review.get("reviewed_by", "")).strip()
    reviewed_at = str(review.get("reviewed_at", "")).strip()
    decisions = review.get("decisions")
    if not reviewed_by or not reviewed_at or not isinstance(decisions, list):
        print("FAIL_POLITICS_TERM_REVIEW: 검수자·시각·결정 누락", file=sys.stderr)
        return 2

    by_id = {record["term_id"]: record for record in records}
    seen_decisions: set[str] = set()
    confusion_owners: dict[str, str] = {}
    for record in records:
        for item in record["asr_confusions"]:
            confusion_owners[normalize_key(item["surface"])] = record["term_id"]

    for decision in decisions:
        term_id = decision.get("term_id")
        if term_id in seen_decisions:
            print(f"FAIL_POLITICS_TERM_REVIEW: 중복 결정 {term_id}", file=sys.stderr)
            return 2
        seen_decisions.add(term_id)
        record = by_id.get(term_id)
        if record is None:
            print(f"FAIL_POLITICS_TERM_REVIEW: 알 수 없는 term_id {term_id}", file=sys.stderr)
            return 2
        if decision.get("canonical") != record["canonical"]:
            print(
                f"FAIL_POLITICS_TERM_REVIEW: canonical 불일치 {term_id}",
                file=sys.stderr,
            )
            return 2
        action = decision.get("action")
        evidence = str(decision.get("evidence", "")).strip()
        if not evidence:
            print(f"FAIL_POLITICS_TERM_REVIEW: 근거 없음 {term_id}", file=sys.stderr)
            return 2
        status = {
            "approve": "approved",
            "keep_observed": "observed",
            "deprecate": "deprecated",
            "block": "blocked",
        }.get(action)
        if status is None:
            print(f"FAIL_POLITICS_TERM_REVIEW: action 오류 {term_id}", file=sys.stderr)
            return 2
        record["status"] = status
        record["approval"] = (
            {
                "approved_by": reviewed_by,
                "approved_at": reviewed_at,
                "evidence": evidence,
            }
            if status == "approved"
            else None
        )
        if status != "approved":
            record["asr_confusions"] = []
        additions = decision.get("asr_confusions", [])
        if additions and status != "approved":
            print(
                f"FAIL_POLITICS_TERM_REVIEW: 승인되지 않은 용어의 confusion {term_id}",
                file=sys.stderr,
            )
            return 2
        for item in additions:
            surface = normalize_display(str(item.get("surface", "")))
            item_evidence = str(item.get("evidence", "")).strip()
            if len(surface) < 2 or not item_evidence:
                print(f"FAIL_POLITICS_TERM_REVIEW: confusion 근거 오류 {term_id}", file=sys.stderr)
                return 2
            normalized = normalize_key(surface)
            if normalized in {
                record["normalized"],
                *(normalize_key(alias) for alias in record["aliases"]),
            }:
                print(
                    f"FAIL_POLITICS_TERM_REVIEW: 정식 표기를 confusion으로 등록 {term_id}",
                    file=sys.stderr,
                )
                return 2
            owner = confusion_owners.get(normalized)
            if owner and owner != term_id:
                print(
                    f"FAIL_POLITICS_TERM_REVIEW: confusion 충돌 {surface!r}",
                    file=sys.stderr,
                )
                return 2
            confusion_owners[normalized] = term_id
            if any(
                normalize_key(existing["surface"]) == normalized
                for existing in record["asr_confusions"]
            ):
                continue
            record["asr_confusions"].append(
                {
                    "surface": surface,
                    "evidence": item_evidence,
                    "approved_by": reviewed_by,
                    "approved_at": reviewed_at,
                }
            )

    write_jsonl(args.output, records)
    try:
        load_registry(args.output)
    except ValueError as exc:
        print(f"FAIL_POLITICS_TERM_REVIEW_OUTPUT: {exc}", file=sys.stderr)
        return 2

    if args.sources_metadata:
        metadata_output = args.metadata_output
        metadata = json.loads(args.sources_metadata.read_text(encoding="utf-8"))
        metadata["registry_file"] = args.output.name
        metadata["registry_sha256"] = sha256_file(args.output)
        metadata["record_count"] = len(records)
        metadata["status_counts"] = dict(
            Counter(record["status"] for record in records)
        )
        metadata_output.parent.mkdir(parents=True, exist_ok=True)
        temporary = metadata_output.with_suffix(metadata_output.suffix + ".tmp")
        temporary.write_text(
            json.dumps(metadata, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        temporary.replace(metadata_output)
    print(
        f"PASS_POLITICS_TERM_REVIEW decisions={len(decisions)} "
        f"output={args.output} sha256={sha256_file(args.output)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

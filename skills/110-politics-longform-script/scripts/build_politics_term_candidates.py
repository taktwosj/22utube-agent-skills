#!/usr/bin/env python3
"""Extract review-only politics term candidates from article CSV files.

This command never promotes terms to ``approved`` and never creates ASR
confusion pairs.  Its JSONL output must be reviewed before replacing the master
registry.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import re
import sys
import unicodedata
from collections import defaultdict
from pathlib import Path

TOKEN = re.compile(r"[가-힣A-Za-z][가-힣A-Za-z0-9·ㆍ]{1,23}")
STOP = {
    "가운데",
    "관련",
    "경우",
    "기자",
    "뉴스",
    "대한",
    "대해",
    "때문",
    "무단",
    "사진",
    "오전",
    "오후",
    "위해",
    "이날",
    "이번",
    "전재",
    "제공",
    "지난",
    "최근",
    "통해",
    "현재",
    "copyright",
}
PARTICLES = (
    "으로부터",
    "에게서",
    "에서는",
    "으로는",
    "까지는",
    "으로",
    "에서",
    "에게",
    "부터",
    "까지",
    "께서",
    "처럼",
    "보다",
    "마다",
    "조차",
    "마저",
    "은",
    "는",
    "이",
    "가",
    "을",
    "를",
    "에",
    "와",
    "과",
    "도",
    "만",
    "로",
)


def clean_term(value: str) -> str | None:
    value = unicodedata.normalize("NFC", value).strip()
    lowered = value.casefold()
    if lowered in STOP or re.fullmatch(r"[a-z ]+", lowered):
        return None
    for suffix in PARTICLES:
        if value.endswith(suffix) and len(value) - len(suffix) >= 2:
            value = value[: -len(suffix)]
            break
    if len(value.replace(" ", "")) < 2 or not re.search(r"[가-힣A-Z]", value):
        return None
    return value


def words(value: str) -> list[str]:
    output = []
    for token in TOKEN.findall(value):
        cleaned = clean_term(token)
        if cleaned:
            output.append(cleaned)
    return output


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, action="append", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--source-id", required=True)
    parser.add_argument("--title-column", default="title")
    parser.add_argument("--content-column", default="content")
    parser.add_argument("--limit", type=int, default=5000)
    parser.add_argument("--min-document-frequency", type=int, default=3)
    args = parser.parse_args()

    counts: dict[str, dict] = defaultdict(
        lambda: {"total": 0, "documents": 0, "titles": 0, "last_doc": -1}
    )
    document = 0
    for input_path in args.input:
        try:
            handle = input_path.open(encoding="utf-8-sig", newline="")
        except OSError as exc:
            print(f"FAIL_TERM_CANDIDATE_INPUT: {exc}", file=sys.stderr)
            return 2
        with handle:
            reader = csv.DictReader(handle)
            if (
                args.title_column not in (reader.fieldnames or [])
                or args.content_column not in (reader.fieldnames or [])
            ):
                print(
                    f"FAIL_TERM_CANDIDATE_COLUMNS: {input_path}",
                    file=sys.stderr,
                )
                return 2
            for row in reader:
                title = row.get(args.title_column, "") or ""
                content = row.get(args.content_column, "") or ""
                if not title and not content:
                    continue
                document += 1
                title_words = words(title)
                body_words = words(content)
                for sequence, is_title in (
                    (title_words, True),
                    (body_words, False),
                ):
                    candidates = list(sequence)
                    candidates.extend(
                        f"{sequence[index]} {sequence[index + 1]}"
                        for index in range(len(sequence) - 1)
                        if len(sequence[index]) <= 15
                        and len(sequence[index + 1]) <= 15
                    )
                    for term in candidates:
                        entry = counts[term]
                        entry["total"] += 1
                        if is_title:
                            entry["titles"] += 1
                        if entry["last_doc"] != document:
                            entry["documents"] += 1
                            entry["last_doc"] = document

    ranked = []
    for canonical, count in counts.items():
        if count["documents"] < args.min_document_frequency:
            continue
        score = (
            count["total"]
            + count["documents"] * 2
            + count["titles"] * 6
            + math.log2(1 + count["documents"]) * 3
        )
        ranked.append((score, canonical, count))
    ranked.sort(key=lambda item: (-item[0], item[1]))

    rows = []
    normalized_seen: set[str] = set()
    for score, canonical, count in ranked:
        normalized = "".join(ch for ch in canonical.casefold() if ch.isalnum())
        if normalized in normalized_seen:
            continue
        normalized_seen.add(normalized)
        rows.append(
            {
                "schema_version": "politics_term_record_v1",
                "term_id": "pt_"
                + hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:16],
                "canonical": canonical,
                "normalized": normalized,
                "aliases": [],
                "asr_confusions": [],
                "category": (
                    "news_noun_phrase" if " " in canonical else "news_noun"
                ),
                "status": "observed",
                "approval": None,
                "rank": len(rows) + 1,
                "priority": 1,
                "evidence": {
                    "source_id": args.source_id,
                    "document_frequency": count["documents"],
                    "total_mentions": count["total"],
                    "title_mentions": count["titles"],
                    "corpus_score": round(score, 3),
                },
            }
        )
        if len(rows) >= args.limit:
            break
    for index, row in enumerate(rows):
        row["priority"] = max(
            1, round(100 - index * 99 / max(1, len(rows) - 1))
        )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    temporary = args.output.with_suffix(args.output.suffix + ".tmp")
    temporary.write_text(
        "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows),
        encoding="utf-8",
    )
    temporary.replace(args.output)
    print(
        f"PASS_POLITICS_TERM_CANDIDATES records={len(rows)} "
        f"documents={document} output={args.output}"
    )
    print("status=observed approved=0 silent_autocorrection=false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

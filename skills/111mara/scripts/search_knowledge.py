#!/usr/bin/env python3
"""Search the bundled 111mara knowledge cards without external dependencies."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any, Iterable


TOKEN_RE = re.compile(r"[0-9A-Za-z가-힣]+")
AUTHORITY_ORDER = {"MARA_CANONICAL": 5, "A": 4, "MIXED": 3, "EXPERIENCE": 2, "PEER": 1}


def normalize_text(value: Any) -> str:
    if isinstance(value, list):
        value = " ".join(normalize_text(item) for item in value)
    elif isinstance(value, dict):
        value = " ".join(normalize_text(item) for item in value.values())
    elif value is None:
        value = ""
    return " ".join(TOKEN_RE.findall(str(value).lower()))


def tokenize(value: str) -> list[str]:
    return [token for token in TOKEN_RE.findall(value.lower()) if len(token) >= 2]


def load_cards(cards_path: Path | str) -> tuple[list[dict[str, Any]], int]:
    path = Path(cards_path)
    cards: list[dict[str, Any]] = []
    skipped = 0
    with path.open("r", encoding="utf-8-sig") as handle:
        for line in handle:
            if not line.strip():
                continue
            try:
                card = json.loads(line)
            except json.JSONDecodeError:
                skipped += 1
                continue
            if isinstance(card, dict):
                cards.append(card)
            else:
                skipped += 1
    return cards, skipped


def _score_card(card: dict[str, Any], query: str, tokens: Iterable[str]) -> int:
    question = normalize_text(card.get("question_variants", []))
    topic = normalize_text(card.get("topic_path", []))
    answer = normalize_text(card.get("canonical_answer", ""))
    supporting = normalize_text(
        [card.get("conditions", []), card.get("exceptions", []), card.get("answer_scope", "")]
    )
    score = 0
    if query in question:
        score += 100
    if query in topic:
        score += 45
    if query in answer:
        score += 25
    for token in tokens:
        score += question.count(token) * 8
        score += topic.count(token) * 6
        score += answer.count(token) * 3
        score += supporting.count(token) * 2
    return score


def _result_view(card: dict[str, Any], score: int) -> dict[str, Any]:
    return {
        "card_id": card.get("card_id"),
        "score": score,
        "topic_path": card.get("topic_path", []),
        "question_variants": card.get("question_variants", []),
        "canonical_answer": card.get("canonical_answer", ""),
        "conditions": card.get("conditions", []),
        "exceptions": card.get("exceptions", []),
        "authority_tier": card.get("authority_tier", ""),
        "evidence": card.get("evidence", []),
        "conflict_ids": card.get("conflict_ids", []),
        "temporal_status": card.get("temporal_status", ""),
        "confidence": card.get("confidence", ""),
    }


def _rank_cards(
    query: str,
    cards: Iterable[dict[str, Any]],
    limit: int,
    category: str | None,
) -> list[dict[str, Any]]:
    normalized_query = normalize_text(query)
    if not normalized_query:
        raise ValueError("query must not be empty")
    if limit < 1:
        raise ValueError("limit must be at least 1")

    category_text = normalize_text(category) if category else ""
    query_tokens = tokenize(normalized_query)
    ranked: list[tuple[int, int, str, dict[str, Any]]] = []

    for card in cards:
        topic = normalize_text(card.get("topic_path", []))
        if category_text and category_text not in topic:
            continue
        score = _score_card(card, normalized_query, query_tokens)
        if score <= 0:
            continue
        authority = AUTHORITY_ORDER.get(str(card.get("authority_tier", "")).upper(), 0)
        ranked.append((score, authority, str(card.get("card_id", "")), card))

    ranked.sort(key=lambda item: (-item[0], -item[1], item[2]))
    return [_result_view(card, score) for score, _, _, card in ranked[:limit]]


def search_cards(
    query: str,
    cards_path: Path | str,
    limit: int = 5,
    category: str | None = None,
) -> dict[str, Any]:
    cards, skipped = load_cards(cards_path)
    results = _rank_cards(query, cards, limit, category)
    return {
        "query": query.strip(),
        "category": category,
        "count": len(results),
        "skipped_malformed": skipped,
        "results": results,
    }


def search_card_files(
    query: str,
    cards_paths: Iterable[Path | str],
    limit: int = 5,
    category: str | None = None,
) -> dict[str, Any]:
    paths = list(cards_paths)
    if not paths:
        raise ValueError("at least one cards path is required")
    cards: list[dict[str, Any]] = []
    skipped = 0
    for path in paths:
        loaded, malformed = load_cards(path)
        cards.extend(loaded)
        skipped += malformed
    results = _rank_cards(query, cards, limit, category)
    return {
        "query": query.strip(),
        "category": category,
        "count": len(results),
        "skipped_malformed": skipped,
        "corpora_searched": len(paths),
        "results": results,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Search 111mara knowledge cards")
    parser.add_argument("--query", required=True, help="Korean or English search question")
    parser.add_argument("--limit", type=int, default=5, help="Maximum results (default: 5)")
    parser.add_argument("--category", help="Optional topic-path filter")
    parser.add_argument(
        "--cards",
        type=Path,
        nargs="+",
        help="One or more knowledge-card JSONL paths; defaults to bundled chat and lecture corpora",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        references = Path(__file__).parents[1] / "references"
        cards_paths = args.cards or [
            references / "knowledge_cards.jsonl",
            references / "lecture_cards.jsonl",
        ]
        existing_paths = [path for path in cards_paths if path.exists()]
        payload = search_card_files(args.query, existing_paths, args.limit, args.category)
    except (FileNotFoundError, OSError, ValueError) as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=False))
        return 2
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

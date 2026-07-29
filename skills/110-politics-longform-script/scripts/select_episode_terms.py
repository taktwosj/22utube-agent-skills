#!/usr/bin/env python3
"""Select a small episode-specific lexicon from the master politics registry."""
from __future__ import annotations

import argparse
import json
import math
import os
import re
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

from politics_term_registry import (
    atomic_write_json,
    flatten_strings,
    load_registry,
    normalize_key,
    sha256_file,
)

HERE = Path(__file__).resolve().parent
DEFAULT_REGISTRY = HERE.parent / "references" / "politics_terms_v1.jsonl"
GENERIC_SINGLE_NOUNS = {
    "가운데",
    "관련",
    "경우",
    "결과",
    "과정",
    "관계",
    "기사",
    "내용",
    "대상",
    "동안",
    "문제",
    "방안",
    "사람",
    "사실",
    "상황",
    "일부",
    "입장",
    "지금",
    "직접",
    "최근",
    "한편",
    "해당",
    "현재",
}


def read_path(path: Path) -> str:
    if path.suffix.lower() == ".json":
        return "\n".join(flatten_strings(json.loads(path.read_text(encoding="utf-8"))))
    return path.read_text(encoding="utf-8", errors="replace")


def context_files(episode: Path, explicit: list[Path]) -> list[Path]:
    files = list(explicit)
    manifest = episode / "00_source" / "source_manifest.json"
    if manifest.is_file():
        files.append(manifest)
    research = episode / "10_analysis" / "research"
    if research.is_dir():
        files.extend(
            path
            for path in sorted(research.rglob("*"))
            if path.is_file() and path.suffix.lower() in {".json", ".md", ".txt"}
        )
    unique: list[Path] = []
    seen: set[Path] = set()
    for path in files:
        resolved = path.resolve()
        if resolved not in seen:
            seen.add(resolved)
            unique.append(path)
    return unique


def portable_path(path: Path, episode: Path, registry: Path) -> str:
    resolved = path.resolve()
    for root, prefix in (
        (episode.resolve(), ""),
        (registry.resolve().parent.parent, "skill/"),
    ):
        if resolved == root or root in resolved.parents:
            relative = resolved.relative_to(root).as_posix()
            return prefix + relative
    return f"external/{path.name}"


def load_index(path: Path, registry_sha256: str) -> list[dict]:
    with sqlite3.connect(path) as connection:
        meta = dict(connection.execute("SELECT key, value FROM meta"))
        if meta.get("registry_sha256") != registry_sha256:
            raise ValueError("SQLite index registry SHA mismatch")
        aliases: dict[str, list[str]] = {}
        for alias, term_id in connection.execute(
            "SELECT alias, term_id FROM aliases"
        ):
            aliases.setdefault(term_id, []).append(alias)
        confusions: dict[str, list[dict]] = {}
        for row in connection.execute(
            """
            SELECT surface, term_id, evidence, approved_by, approved_at
            FROM asr_confusions
            """
        ):
            surface, term_id, evidence, approved_by, approved_at = row
            confusions.setdefault(term_id, []).append(
                {
                    "surface": surface,
                    "evidence": evidence,
                    "approved_by": approved_by,
                    "approved_at": approved_at,
                }
            )
        records = []
        for row in connection.execute(
            """
            SELECT term_id, canonical, normalized, category, status, rank,
                   priority, source_id, document_frequency, total_mentions,
                   title_mentions
            FROM terms
            ORDER BY rank
            """
        ):
            (
                term_id,
                canonical,
                normalized,
                category,
                status,
                rank,
                priority,
                source_id,
                document_frequency,
                total_mentions,
                title_mentions,
            ) = row
            records.append(
                {
                    "term_id": term_id,
                    "canonical": canonical,
                    "normalized": normalized,
                    "category": category,
                    "status": status,
                    "rank": rank,
                    "priority": priority,
                    "aliases": aliases.get(term_id, []),
                    "asr_confusions": confusions.get(term_id, []),
                    "evidence": {
                        "source_id": source_id,
                        "document_frequency": document_frequency,
                        "total_mentions": total_mentions,
                        "title_mentions": title_mentions,
                    },
                }
            )
    return records


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
    parser.add_argument("--index", type=Path)
    parser.add_argument("--context", type=Path, action="append", default=[])
    parser.add_argument("--limit", type=int, default=150)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.episode is None:
        parser.error("--episode 또는 PL_EPISODE_DIR가 필요하다")
    if not 1 <= args.limit <= 500:
        parser.error("--limit는 1~500이어야 한다")

    default_index = args.episode / "10_analysis" / "politics_terms_v1.sqlite"
    index_path = args.index or (default_index if default_index.is_file() else None)
    try:
        registry_sha = sha256_file(args.registry)
        records = (
            load_index(index_path, registry_sha)
            if index_path is not None
            else load_registry(args.registry)
        )
    except (OSError, ValueError) as exc:
        print(f"FAIL_POLITICS_TERM_REGISTRY: {exc}", file=sys.stderr)
        return 2
    files = context_files(args.episode, args.context)
    if not files:
        print(
            "WAIT_EPISODE_TERM_CONTEXT: source manifest 또는 승인 기사 문맥이 필요하다",
            file=sys.stderr,
        )
        return 1

    chunks: list[str] = []
    hashes: dict[str, str] = {}
    for path in files:
        if not path.is_file():
            print(f"WAIT_EPISODE_TERM_CONTEXT: 파일 없음 {path}", file=sys.stderr)
            return 1
        chunks.append(read_path(path))
        hashes[portable_path(path, args.episode, args.registry)] = sha256_file(path)
    context = "\n".join(chunks)
    compact_context = normalize_key(context)

    selected: list[dict] = []
    for record in records:
        if record["status"] in {"deprecated", "blocked"}:
            continue
        canonical = record["canonical"]
        if (
            record["category"] == "news_noun"
            and canonical in GENERIC_SINGLE_NOUNS
        ):
            continue
        canonical_hits = compact_context.count(record["normalized"])
        alias_hits = 0
        matched_aliases: list[str] = []
        if record["status"] == "approved":
            for alias in record["aliases"]:
                hits = compact_context.count(normalize_key(alias))
                if hits:
                    alias_hits += hits
                    matched_aliases.append(alias)
        hits = canonical_hits + alias_hits
        if not hits:
            continue
        evidence = record["evidence"]
        category_bonus = {
            "named_entity": 12,
            "news_noun_phrase": 10,
            "institution": 12,
            "office": 10,
            "legal_term": 12,
            "policy": 10,
            "election": 10,
            "diplomacy_security": 10,
        }.get(record["category"], 0)
        score = (
            hits * 12
            + category_bonus
            + record["priority"] / 4
            + math.log2(1 + evidence["title_mentions"]) * 2
            + (20 if record["status"] == "approved" else 0)
        )
        selected.append(
            {
                "term_id": record["term_id"],
                "canonical": canonical,
                "normalized": record["normalized"],
                "category": record["category"],
                "status": record["status"],
                "priority": record["priority"],
                "score": round(score, 3),
                "matches": {
                    "canonical": canonical_hits,
                    "approved_alias": alias_hits,
                    "aliases": matched_aliases,
                },
                "asr_confusions": (
                    record["asr_confusions"]
                    if record["status"] == "approved"
                    else []
                ),
            }
        )
    selected.sort(key=lambda item: (-item["score"], -item["priority"], item["canonical"]))
    selected = selected[: args.limit]
    if not selected:
        print("WAIT_EPISODE_TERMS_EMPTY: 회차 문맥과 일치하는 용어가 없다", file=sys.stderr)
        return 1

    output = args.output or args.episode / "10_analysis" / "episode_term_pack_v1.json"
    payload = {
        "schema_version": "politics_episode_term_pack_v1",
        "status": "PASS_110_EPISODE_TERMS_SELECTED",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "registry_path": portable_path(
            args.registry, args.episode, args.registry),
        "registry_sha256": registry_sha,
        "term_source": {
            "kind": "sqlite_index" if index_path is not None else "jsonl_registry",
            "path": portable_path(
                index_path or args.registry, args.episode, args.registry),
            "sha256": sha256_file(index_path or args.registry),
        },
        "context_sha256": hashes,
        "selection_policy": {
            "limit": args.limit,
            "source_srt_alone_is_not_context": True,
            "observed_terms_are_not_correction_authority": True,
            "approved_aliases_only": True,
            "silent_autocorrection": False,
        },
        "selected_count": len(selected),
        "terms": selected,
    }
    atomic_write_json(output, payload)
    print(f"PASS_110_EPISODE_TERMS_SELECTED count={len(selected)} output={output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

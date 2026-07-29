#!/usr/bin/env python3
"""Build a disposable SQLite index from politics_terms_v1.jsonl."""
from __future__ import annotations

import argparse
import os
import sqlite3
import sys
from pathlib import Path

from politics_term_registry import load_registry, sha256_file

HERE = Path(__file__).resolve().parent
DEFAULT_REGISTRY = HERE.parent / "references" / "politics_terms_v1.jsonl"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--registry", type=Path, default=DEFAULT_REGISTRY)
    parser.add_argument("--episode", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    output = args.output
    if output is None:
        episode = args.episode or (
            Path(os.environ["PL_EPISODE_DIR"]) if os.environ.get("PL_EPISODE_DIR") else None
        )
        if episode is None:
            parser.error("--output 또는 --episode/PL_EPISODE_DIR가 필요하다")
        output = episode / "10_analysis" / "politics_terms_v1.sqlite"

    try:
        records = load_registry(args.registry)
    except (OSError, ValueError) as exc:
        print(f"FAIL_POLITICS_TERM_REGISTRY: {exc}", file=sys.stderr)
        return 2

    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_suffix(output.suffix + ".tmp")
    if temporary.exists():
        temporary.unlink()
    connection = sqlite3.connect(temporary)
    try:
        connection.executescript(
            """
            PRAGMA journal_mode=OFF;
            PRAGMA synchronous=FULL;
            CREATE TABLE meta (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            );
            CREATE TABLE terms (
                term_id TEXT PRIMARY KEY,
                canonical TEXT NOT NULL UNIQUE,
                normalized TEXT NOT NULL UNIQUE,
                category TEXT NOT NULL,
                status TEXT NOT NULL,
                rank INTEGER NOT NULL,
                priority INTEGER NOT NULL,
                source_id TEXT NOT NULL,
                document_frequency INTEGER NOT NULL,
                total_mentions INTEGER NOT NULL,
                title_mentions INTEGER NOT NULL
            );
            CREATE TABLE aliases (
                alias TEXT NOT NULL,
                normalized TEXT NOT NULL,
                term_id TEXT NOT NULL REFERENCES terms(term_id),
                UNIQUE(normalized, term_id)
            );
            CREATE TABLE asr_confusions (
                surface TEXT NOT NULL,
                normalized TEXT NOT NULL,
                term_id TEXT NOT NULL REFERENCES terms(term_id),
                evidence TEXT NOT NULL,
                approved_by TEXT NOT NULL,
                approved_at TEXT NOT NULL,
                UNIQUE(normalized, term_id)
            );
            CREATE INDEX terms_status_priority
                ON terms(status, priority DESC, rank ASC);
            CREATE INDEX aliases_normalized ON aliases(normalized);
            CREATE INDEX asr_confusions_normalized ON asr_confusions(normalized);
            """
        )
        connection.executemany(
            "INSERT INTO meta(key, value) VALUES(?, ?)",
            [
                ("schema_version", "politics_term_sqlite_v1"),
                ("registry_sha256", sha256_file(args.registry)),
                ("record_count", str(len(records))),
            ],
        )
        for record in records:
            evidence = record["evidence"]
            connection.execute(
                """
                INSERT INTO terms VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record["term_id"],
                    record["canonical"],
                    record["normalized"],
                    record["category"],
                    record["status"],
                    record["rank"],
                    record["priority"],
                    evidence["source_id"],
                    evidence["document_frequency"],
                    evidence["total_mentions"],
                    evidence["title_mentions"],
                ),
            )
            connection.executemany(
                "INSERT INTO aliases(alias, normalized, term_id) VALUES(?, ?, ?)",
                [
                    (
                        alias,
                        "".join(ch for ch in alias.casefold() if ch.isalnum()),
                        record["term_id"],
                    )
                    for alias in record["aliases"]
                ],
            )
            connection.executemany(
                """
                INSERT INTO asr_confusions(
                    surface, normalized, term_id, evidence, approved_by, approved_at
                ) VALUES(?, ?, ?, ?, ?, ?)
                """,
                [
                    (
                        item["surface"],
                        "".join(
                            ch for ch in item["surface"].casefold() if ch.isalnum()
                        ),
                        record["term_id"],
                        item["evidence"],
                        item["approved_by"],
                        item["approved_at"],
                    )
                    for item in record["asr_confusions"]
                ],
            )
        connection.commit()
        check = connection.execute("SELECT COUNT(*) FROM terms").fetchone()[0]
        if check != len(records):
            raise RuntimeError(f"row count mismatch: {check} != {len(records)}")
    finally:
        connection.close()
    temporary.replace(output)
    print(f"PASS_POLITICS_TERM_INDEX records={len(records)} output={output}")
    print(f"registry_sha256={sha256_file(args.registry)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

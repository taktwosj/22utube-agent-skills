#!/usr/bin/env python3
"""Shared helpers for the politics term registry.

The JSONL file is the reviewable source of truth.  SQLite files are disposable
runtime indexes and must always be rebuilt from this registry.
"""
from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from pathlib import Path
from typing import Iterable

SCHEMA_VERSION = "politics_term_record_v1"
ALLOWED_STATUS = {"observed", "approved", "deprecated", "blocked"}
ALLOWED_CATEGORY = {
    "named_entity",
    "news_noun",
    "news_noun_phrase",
    "legal_term",
    "institution",
    "office",
    "policy",
    "election",
    "diplomacy_security",
}
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
TERM_ID_RE = re.compile(r"^pt_[0-9a-f]{16}$")


class RegistryError(ValueError):
    """Raised when the registry is not safe to consume."""


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def normalize_display(value: str) -> str:
    return re.sub(r"\s+", " ", unicodedata.normalize("NFC", value)).strip()


def normalize_key(value: str) -> str:
    value = normalize_display(value).casefold()
    return "".join(ch for ch in value if ch.isalnum())


def validate_record(record: dict, line_number: int | None = None) -> None:
    where = f"line {line_number}: " if line_number else ""
    required = {
        "schema_version",
        "term_id",
        "canonical",
        "normalized",
        "aliases",
        "asr_confusions",
        "category",
        "status",
        "approval",
        "rank",
        "priority",
        "evidence",
    }
    missing = sorted(required - record.keys())
    if missing:
        raise RegistryError(f"{where}missing fields: {', '.join(missing)}")
    extra = sorted(record.keys() - required)
    if extra:
        raise RegistryError(f"{where}unexpected fields: {', '.join(extra)}")
    if record["schema_version"] != SCHEMA_VERSION:
        raise RegistryError(f"{where}unsupported schema_version")
    if not TERM_ID_RE.fullmatch(str(record["term_id"])):
        raise RegistryError(f"{where}invalid term_id")
    canonical = normalize_display(str(record["canonical"]))
    if len(canonical) < 2 or canonical != record["canonical"]:
        raise RegistryError(f"{where}canonical is not normalized")
    if normalize_key(canonical) != record["normalized"]:
        raise RegistryError(f"{where}normalized does not match canonical")
    if record["status"] not in ALLOWED_STATUS:
        raise RegistryError(f"{where}invalid status")
    approval = record["approval"]
    if record["status"] == "approved":
        if not isinstance(approval, dict):
            raise RegistryError(f"{where}approved term lacks approval evidence")
        if not all(
            str(approval.get(key, "")).strip()
            for key in ("approved_by", "approved_at", "evidence")
        ):
            raise RegistryError(f"{where}incomplete approval evidence")
    elif approval is not None:
        raise RegistryError(f"{where}non-approved term cannot carry approval")
    if record["category"] not in ALLOWED_CATEGORY:
        raise RegistryError(f"{where}invalid category")
    if not isinstance(record["rank"], int) or record["rank"] < 1:
        raise RegistryError(f"{where}invalid rank")
    if not isinstance(record["priority"], int) or not 1 <= record["priority"] <= 100:
        raise RegistryError(f"{where}invalid priority")
    if (not isinstance(record["aliases"], list)
            or not all(isinstance(alias, str) and len(alias) >= 2
                       for alias in record["aliases"])):
        raise RegistryError(f"{where}aliases must be an array")
    alias_norms = [normalize_key(alias) for alias in record["aliases"]]
    if len(alias_norms) != len(set(alias_norms)):
        raise RegistryError(f"{where}duplicate aliases")
    if not isinstance(record["asr_confusions"], list):
        raise RegistryError(f"{where}asr_confusions must be an array")
    if record["asr_confusions"] and record["status"] != "approved":
        raise RegistryError(
            f"{where}only approved terms may carry ASR confusion authority"
        )
    confusion_norms: set[str] = set()
    for confusion in record["asr_confusions"]:
        if not isinstance(confusion, dict):
            raise RegistryError(f"{where}invalid ASR confusion")
        needed = {"surface", "evidence", "approved_by", "approved_at"}
        if set(confusion) != needed:
            raise RegistryError(f"{where}ASR confusion lacks approval evidence")
        if not all(str(confusion[key]).strip() for key in needed):
            raise RegistryError(f"{where}ASR confusion has empty evidence")
        normalized_confusion = normalize_key(confusion["surface"])
        if normalized_confusion in confusion_norms:
            raise RegistryError(f"{where}duplicate ASR confusion")
        if normalized_confusion in {record["normalized"], *alias_norms}:
            raise RegistryError(f"{where}canonical/alias cannot be confusion")
        confusion_norms.add(normalized_confusion)
    evidence = record["evidence"]
    if not isinstance(evidence, dict) or not evidence.get("source_id"):
        raise RegistryError(f"{where}missing evidence source")
    if set(evidence) != {
            "source_id", "document_frequency", "total_mentions",
            "title_mentions", "corpus_score"}:
        raise RegistryError(f"{where}unexpected evidence fields")
    for key in ("document_frequency", "total_mentions"):
        if not isinstance(evidence.get(key), int) or evidence[key] < 1:
            raise RegistryError(f"{where}invalid evidence.{key}")
    if (not isinstance(evidence.get("title_mentions"), int)
            or evidence["title_mentions"] < 0):
        raise RegistryError(f"{where}invalid evidence.title_mentions")
    if (not isinstance(evidence.get("corpus_score"), (int, float))
            or isinstance(evidence.get("corpus_score"), bool)
            or evidence["corpus_score"] < 0):
        raise RegistryError(f"{where}invalid evidence.corpus_score")


def load_registry(path: Path) -> list[dict]:
    records: list[dict] = []
    ids: set[str] = set()
    canonicals: set[str] = set()
    normalized: set[str] = set()
    with path.open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            if not line.strip():
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError as exc:
                raise RegistryError(f"line {line_number}: invalid JSON: {exc}") from exc
            validate_record(record, line_number)
            checks = (
                ("term_id", record["term_id"], ids),
                ("canonical", record["canonical"], canonicals),
                ("normalized", record["normalized"], normalized),
            )
            for name, value, seen in checks:
                if value in seen:
                    raise RegistryError(f"line {line_number}: duplicate {name} {value!r}")
                seen.add(value)
            records.append(record)
    if not records:
        raise RegistryError("empty registry")
    return records


def atomic_write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def flatten_strings(value: object) -> Iterable[str]:
    if isinstance(value, str):
        yield value
    elif isinstance(value, list):
        for item in value:
            yield from flatten_strings(item)
    elif isinstance(value, dict):
        for item in value.values():
            yield from flatten_strings(item)


CHOSEONG = "ㄱㄲㄴㄷㄸㄹㅁㅂㅃㅅㅆㅇㅈㅉㅊㅋㅌㅍㅎ"
JUNGSEONG = "ㅏㅐㅑㅒㅓㅔㅕㅖㅗㅘㅙㅚㅛㅜㅝㅞㅟㅠㅡㅢㅣ"
JONGSEONG = "\0ㄱㄲㄳㄴㄵㄶㄷㄹㄺㄻㄼㄽㄾㄿㅀㅁㅂㅄㅅㅆㅇㅈㅊㅋㅌㅍㅎ"


def to_jamo(value: str) -> str:
    out: list[str] = []
    for char in normalize_key(value):
        code = ord(char)
        if 0xAC00 <= code <= 0xD7A3:
            offset = code - 0xAC00
            out.append(CHOSEONG[offset // 588])
            out.append(JUNGSEONG[(offset % 588) // 28])
            tail = JONGSEONG[offset % 28]
            if tail != "\0":
                out.append(tail)
        else:
            out.append(char)
    return "".join(out)


def levenshtein(left: str, right: str) -> int:
    if len(left) < len(right):
        left, right = right, left
    previous = list(range(len(right) + 1))
    for row, char_left in enumerate(left, 1):
        current = [row]
        for column, char_right in enumerate(right, 1):
            current.append(
                min(
                    current[-1] + 1,
                    previous[column] + 1,
                    previous[column - 1] + (char_left != char_right),
                )
            )
        previous = current
    return previous[-1]


def phonetic_similarity(left: str, right: str) -> float:
    left_jamo = to_jamo(left)
    right_jamo = to_jamo(right)
    longest = max(len(left_jamo), len(right_jamo))
    if not longest:
        return 1.0
    return 1.0 - levenshtein(left_jamo, right_jamo) / longest

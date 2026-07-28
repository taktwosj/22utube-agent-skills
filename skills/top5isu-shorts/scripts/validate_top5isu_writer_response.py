#!/usr/bin/env python3
"""Parse and deterministically validate top5isu ChatGPT writer responses."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any, Dict, Iterable, List, Set


BEGIN_SENTINEL = "TOP5ISU_WRITER_JSON_BEGIN"
END_SENTINEL = "TOP5ISU_WRITER_JSON_END"
FORBIDDEN_VISIBLE_MARKS = set('()"“”‘’')
FORBIDDEN_KEYS = {"tab_id", "target_id", "conversation_id", "session_id", "cookies", "url"}


class GateFail(Exception):
    pass


def _require(condition: bool, code: str, detail: str) -> None:
    if not condition:
        raise GateFail(f"{code}: {detail}")


def extract_writer_json(raw: str) -> Dict[str, Any]:
    begin = raw.find(BEGIN_SENTINEL)
    end = raw.find(END_SENTINEL, begin + len(BEGIN_SENTINEL))
    _require(begin >= 0 and end > begin, "FAIL_WRITER_ENVELOPE", "sentinels missing or out of order")
    payload = raw[begin + len(BEGIN_SENTINEL) : end].strip()
    if payload.startswith("```json"):
        payload = payload[7:]
    elif payload.startswith("```"):
        payload = payload[3:]
    if payload.endswith("```"):
        payload = payload[:-3]
    try:
        result = json.loads(payload.strip())
    except json.JSONDecodeError as exc:
        raise GateFail(f"FAIL_WRITER_JSON: {exc}")
    _require(isinstance(result, dict), "FAIL_WRITER_JSON", "response must be an object")
    return result


def _walk_keys(value: Any) -> Iterable[str]:
    if isinstance(value, dict):
        for key, child in value.items():
            yield str(key).lower()
            yield from _walk_keys(child)
    elif isinstance(value, list):
        for child in value:
            yield from _walk_keys(child)


def _walk_strings(value: Any) -> Iterable[str]:
    if isinstance(value, dict):
        for child in value.values():
            yield from _walk_strings(child)
    elif isinstance(value, list):
        for child in value:
            yield from _walk_strings(child)
    elif isinstance(value, str):
        yield value


def _contains_browser_identifier(value: str) -> bool:
    patterns = (
        r"https://chatgpt\.com/c/",
        r"\b[0-9A-Fa-f]{24,}\b",
        r"(?i)\b(tab_id|target_id|conversation_id|session_id|cookies?)\b\s*[=:]",
        r"(?i)\b(token|cookie|session)\b\s*[=:]\s*\S+",
    )
    return any(re.search(pattern, value) for pattern in patterns)


def _numbers(text: str) -> Set[str]:
    return {token.replace(",", "") for token in re.findall(r"\d+(?:,\d{3})*(?:\.\d+)?", text)}


def _visible_text(response: Dict[str, Any]) -> str:
    chunks: List[str] = [str(response.get("greeting", ""))]
    chunks.extend(str(value) for value in (response.get("topic_intro") or []))
    for item in response.get("ranks") or []:
        if isinstance(item, dict):
            chunks.append(str(item.get("narration", "")))
    for item in response.get("sections") or []:
        if isinstance(item, dict):
            chunks.append(str(item.get("narration", "")))
    chunks.append(str(response.get("close", "")))
    return "\n".join(chunks)


def validate_writer_response(packet: Dict[str, Any], response: Dict[str, Any]) -> Dict[str, Any]:
    _require(response.get("schema_version") == "top5isu_writer_response_v1", "FAIL_WRITER_RESPONSE", "wrong schema version")
    _require(response.get("style_profile") == packet.get("style_profile"), "FAIL_WRITER_RESPONSE", "profile mismatch")
    keys = set(_walk_keys(response))
    _require(not (keys & FORBIDDEN_KEYS), "FAIL_WRITER_BROWSER_ID", "browser identifiers are forbidden")
    _require(not any(_contains_browser_identifier(value) for value in _walk_strings(response)), "FAIL_WRITER_BROWSER_ID", "browser identifier values are forbidden")
    profile = packet.get("style_profile")
    facts = {str(item["fact_id"]): item for item in packet.get("evidence", [])}
    visible = _visible_text(response)
    for phrase in packet.get("forbidden_phrases", []):
        _require(str(phrase) not in visible, "FAIL_WRITER_PHRASE", f"forbidden phrase: {phrase}")
    _require(not any(mark in visible for mark in FORBIDDEN_VISIBLE_MARKS), "FAIL_WRITER_VISIBLE_MARK", "parentheses or quotation marks found")
    if profile == "top5":
        _require(response.get("greeting") == packet.get("fixed_greeting"), "FAIL_WRITER_GREETING", "fixed greeting changed")
        intro_raw = response.get("topic_intro")
        requirements = packet.get("topic_intro_requirements") or {}
        if not isinstance(intro_raw, list):
            raise GateFail("FAIL_WRITER_INTRO: topic_intro must be a list")
        intro: List[Any] = intro_raw
        _require(requirements.get("min_sentences", 1) <= len(intro) <= requirements.get("max_sentences", 2), "FAIL_WRITER_INTRO", "topic intro count out of range")
        ranks_raw = response.get("ranks")
        if not isinstance(ranks_raw, list):
            raise GateFail("FAIL_WRITER_RANKS: ranks must be a list")
        ranks: List[Any] = ranks_raw
        rank_order = [item.get("rank") if isinstance(item, dict) else None for item in ranks]
        _require(rank_order == [5, 4, 3, 2, 1], "FAIL_WRITER_RANKS", "rank order must be 5..1")
        for item in ranks:
            rank = item["rank"]
            narration = str(item.get("narration", "")).strip()
            fact_ids_raw = item.get("fact_ids")
            _require(bool(narration), "FAIL_WRITER_RESPONSE", f"rank {rank} narration missing")
            if not isinstance(fact_ids_raw, list) or not fact_ids_raw:
                raise GateFail(f"FAIL_WRITER_FACT_ID: rank {rank} fact_ids missing")
            fact_ids: List[Any] = fact_ids_raw
            referenced = []
            for fact_id in fact_ids:
                _require(str(fact_id) in facts, "FAIL_WRITER_FACT_ID", f"unknown fact_id {fact_id}")
                fact = facts[str(fact_id)]
                _require(fact.get("rank") == rank, "FAIL_WRITER_FACT_ID", f"fact {fact_id} belongs to another rank")
                referenced.append(fact)
            allowed = {str(rank)}
            for fact in referenced:
                allowed.update(str(token).replace(",", "") for token in fact.get("allowed_numeric_tokens", []))
            invented = sorted(_numbers(narration) - allowed)
            _require(not invented, "FAIL_WRITER_NUMBER", f"rank {rank} invented numbers: {invented}")
        _require(bool(str(response.get("close", "")).strip()), "FAIL_WRITER_RESPONSE", "close is required")
        return {"status": "PASS", "style_profile": profile, "rank_order": rank_order, "fact_ids": sorted(facts)}
    sections_raw = response.get("sections")
    if not isinstance(sections_raw, list):
        raise GateFail("FAIL_WRITER_STORY: gunlimbo sections must be a list")
    sections: List[Any] = sections_raw
    story_order = [item.get("role") if isinstance(item, dict) else None for item in sections]
    _require(story_order == ["setup", "complication", "emotional_turn"], "FAIL_WRITER_STORY", "gunlimbo story order is wrong")
    opening_hook = str(packet.get("opening_hook", "")).strip()
    setup_narration = str(sections[0].get("narration", "")) if sections and isinstance(sections[0], dict) else ""
    _require(bool(opening_hook) and setup_narration.startswith(opening_hook), "FAIL_WRITER_HOOK", "gunlimbo opening_hook must be preserved exactly")
    for item in sections:
        role = str(item.get("role", ""))
        narration = str(item.get("narration", "")).strip()
        fact_ids_raw = item.get("fact_ids")
        _require(bool(narration), "FAIL_WRITER_RESPONSE", f"{role} narration missing")
        if not isinstance(fact_ids_raw, list) or not fact_ids_raw:
            raise GateFail(f"FAIL_WRITER_FACT_ID: {role} fact_ids missing")
        allowed: Set[str] = set()
        for fact_id in fact_ids_raw:
            _require(str(fact_id) in facts, "FAIL_WRITER_FACT_ID", f"unknown fact_id {fact_id}")
            fact = facts[str(fact_id)]
            _require(fact.get("story_role") == role, "FAIL_WRITER_FACT_ID", f"fact {fact_id} belongs to another story role")
            allowed.update(str(token).replace(",", "") for token in fact.get("allowed_numeric_tokens", []))
        invented = sorted(_numbers(narration) - allowed)
        _require(not invented, "FAIL_WRITER_NUMBER", f"{role} invented numbers: {invented}")
    _require(bool(str(response.get("close", "")).strip()), "FAIL_WRITER_RESPONSE", "gunlimbo close is required")
    return {"status": "PASS", "style_profile": profile, "story_order": story_order, "opening_hook_preserved": True, "fact_ids": sorted(facts)}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("packet")
    parser.add_argument("response")
    parser.add_argument("--qa-out", default="")
    args = parser.parse_args()
    try:
        packet = json.loads(Path(args.packet).read_text(encoding="utf-8"))
        raw = Path(args.response).read_text(encoding="utf-8")
        response = extract_writer_json(raw)
        qa = validate_writer_response(packet, response)
        if args.qa_out:
            Path(args.qa_out).write_text(json.dumps(qa, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(qa, ensure_ascii=False))
        return 0
    except (OSError, json.JSONDecodeError, GateFail) as exc:
        print(str(exc))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

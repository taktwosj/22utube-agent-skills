#!/usr/bin/env python3
"""Fail-closed Humanize KR fidelity gate for the 110 political longform skill.

Humanize KR may edit only narration wording. This gate emits a SHA-bound receipt
that proves the source-bound facts, direct quotes, numeric literals, protected
proper names, and direct-voice style contract survived the edit.
"""
from __future__ import annotations

import argparse
import difflib
import hashlib
import json
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any

import draft_md

SCHEMA = "politics-longform-humanize-korean-gate.v1"
SKILL_ROOT = Path(__file__).resolve().parent.parent
PIN_PATH = SKILL_ROOT / "references" / "humanize-korean-v2.3.2" / "UPSTREAM.json"
ADAPTER_PATH = SKILL_ROOT / "references" / "humanize-korean-v2.3.2.md"

UPSTREAM_PIN = {
    "repository": "https://github.com/epoko77-ai/im-not-ai",
    "tag": "v2.3.2",
    "commit": "bad4ef0d1e15c7b4e09be0cb213c456d8b9a4258",
    "license": "MIT",
}
UPSTREAM_ARTIFACTS = {
    "codex/skills/humanize-korean/SKILL.md": (
        "7a60c8240218ac7a3cb15f26f0824a682958cdc0475ba2d828c8375edc870569"
    ),
    "skills/humanize-korean/references/quick-rules.md": (
        "258bd9f755fc04a5894f42e5e0a0dcf3c66ee7cf20854d91b4fbac0becf2c08e"
    ),
}
REQUIRED_CHECKS = ("UPSTREAM", "FACT", "QUOTE", "NUMBER", "NAME", "DIRECT_VOICE")

# The user rejected defensive / checklist-style narration. Scan narration only:
# source quotes must stay verbatim even when one of these strings occurs there.
DIRECT_VOICE_RULES = {
    "CHECKLIST_FRAME": re.compile(
        r"(?:첫째|둘째|셋째|세\s*가지\s*(?:기준|질문)|오늘\s*우리가\s*남길\s*질문은\s*하나)"
    ),
    "DEFENSIVE_DISCLAIMER": re.compile(
        r"(?:단정하지\s*않|말할\s*일은\s*아니|보기\s*이르|"
        r"이건\s*사실이\s*아니라\s*해석|확대할\s*필요(?:는)?\s*없)"
    ),
    "AI_TELL": re.compile(
        r"(?:결론적으로|요약하면|정리하자면|시사하는\s*바가\s*크|"
        r"주목할\s*만하|크게\s*세\s*가지(?:로)?\s*나눌\s*수)"
    ),
}
NUMBER_RE = re.compile(
    r"(?<![0-9A-Za-z가-힣])[-+]?\d[\d,]*(?:\.\d+)?(?:\s*(?:%|퍼센트|명|건|개|년|월|일|시|분|초|회|억|만|천|시간))?"
)
ROLE_NAME_RE = re.compile(
    r"(?<![가-힣])([가-힣]{2,4})(?=\s*(?:대통령|총리|장관|수석|대표|의원|후보자|원내대표|대변인|비서실장))"
)
NOT_A_PERSON_NAME = {
    "청와대", "대통령실", "민주당", "국민의힘", "조국혁신당", "후보자",
    "지지율", "인사", "연대", "메시지", "여론", "정치", "정부", "국회",
}


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def json_digest(value: Any) -> str:
    data = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(data.encode("utf-8")).hexdigest()


def _counter_delta(before: Counter, after: Counter) -> dict[str, list[str]]:
    removed = list((before - after).elements())
    added = list((after - before).elements())
    return {"removed": sorted(removed), "added": sorted(added)}


def _check(violations: list[str], **extra: Any) -> dict[str, Any]:
    return {
        "status": "PASS" if not violations else "FAIL",
        "count": len(violations),
        "violations": violations,
        **extra,
    }


def narration_text(draft: dict[str, Any]) -> str:
    return "\n".join(
        segment.get("text", "")
        for chapter in draft["chapters"]
        for segment in chapter["segments"]
        if segment["type"] == "NARRATION"
    )


def _structural_signature(draft: dict[str, Any]) -> dict[str, Any]:
    chapters = []
    for chapter in draft["chapters"]:
        segments = []
        for segment in chapter["segments"]:
            item = {
                "type": segment["type"],
                "segment_id": segment["segment_id"],
                "source_id": segment.get("source_id"),
                "time_in": segment.get("time_in"),
                "time_out": segment.get("time_out"),
                "cue_from": segment.get("cue_from"),
                "cue_to": segment.get("cue_to"),
                "cues_skipped": segment.get("cues_skipped", []),
                "skip_class": segment.get("skip_class"),
                "quote_mode": segment.get("quote_mode"),
                "grounding": segment.get("grounding", []),
            }
            segments.append(item)
        chapters.append({
            "chapter_number": chapter["chapter_number"],
            "chapter_title": chapter["chapter_title"],
            "segments": segments,
        })
    return {
        "episode_id": draft.get("episode_id"),
        "source_packet_sha256": draft.get("source_packet_sha256"),
        "declared_counts": draft.get("declared_counts"),
        "chapters": chapters,
    }


def _source_quotes(draft: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "segment_id": segment["segment_id"],
            "source_id": segment.get("source_id"),
            "cue_from": segment.get("cue_from"),
            "cue_to": segment.get("cue_to"),
            "text": segment.get("text", ""),
        }
        for chapter in draft["chapters"]
        for segment in chapter["segments"]
        if segment["type"] == "SOURCE_VIDEO"
    ]


def _packet_terms(packet: dict[str, Any]) -> set[str]:
    values: set[str] = set()

    def add(value: Any) -> None:
        if isinstance(value, str):
            value = value.strip()
            if 2 <= len(value) <= 80 and "\n" not in value:
                values.add(value)
        elif isinstance(value, dict):
            for key in ("term", "canonical", "name", "label"):
                add(value.get(key))

    for key in ("lexicon", "terms", "term_pack"):
        raw = packet.get(key, [])
        if isinstance(raw, list):
            for item in raw:
                add(item)
    return values


def _fact_anchor_counts(text: str, packet: dict[str, Any]) -> Counter:
    anchors = [term for term in _packet_terms(packet) if term in text]
    return Counter({term: text.count(term) for term in anchors})


def _name_anchor_counts(text: str, packet: dict[str, Any]) -> Counter:
    names = {
        match.group(1)
        for match in ROLE_NAME_RE.finditer(text)
    }
    for term in _packet_terms(packet):
        if term in NOT_A_PERSON_NAME:
            continue
        if re.fullmatch(r"[가-힣]{2,4}", term) and term in text:
            names.add(term)
    return Counter({name: text.count(name) for name in names})


def _edit_rate(before: str, after: str) -> float:
    # New lines are deliberate delivery rhythm; do not count them as semantic edits.
    normalized_before = re.sub(r"\s+", "", before)
    normalized_after = re.sub(r"\s+", "", after)
    if not normalized_before and not normalized_after:
        return 0.0
    ratio = difflib.SequenceMatcher(None, normalized_before, normalized_after).ratio()
    return round((1.0 - ratio) * 100, 2)


def verify_upstream_snapshot() -> list[str]:
    violations: list[str] = []
    try:
        raw = json.loads(PIN_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return [f"upstream pin을 읽을 수 없다: {exc}"]

    if raw.get("schema") != "110-humanize-korean-upstream-pin.v1":
        violations.append("upstream pin schema가 다르다")
    if raw.get("upstream") != UPSTREAM_PIN:
        violations.append("upstream repository/tag/commit/license pin이 다르다")
    actual = {
        item.get("path"): item.get("sha256")
        for item in raw.get("upstream_artifacts", [])
        if isinstance(item, dict)
    }
    if actual != UPSTREAM_ARTIFACTS:
        violations.append("upstream artifact SHA pin이 다르다")
    try:
        adapter = ADAPTER_PATH.read_text(encoding="utf-8")
    except OSError as exc:
        violations.append(f"110 Humanize KR adapter가 없다: {exc}")
    else:
        for required in (UPSTREAM_PIN["repository"], UPSTREAM_PIN["tag"], "DIRECT VOICE"):
            if required not in adapter:
                violations.append(f"adapter에 필수 upstream/direct-voice 선언이 없다: {required}")
    return violations


def _parse(path: Path) -> tuple[dict[str, Any] | None, list[str]]:
    try:
        return draft_md.parse_draft_md(path.read_text(encoding="utf-8")), []
    except (OSError, draft_md.DraftFormatError, UnicodeDecodeError) as exc:
        return None, [f"대본 형식 또는 읽기 실패: {exc}"]


def _read_packet(path: Path) -> tuple[dict[str, Any] | None, list[str]]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, UnicodeDecodeError) as exc:
        return None, [f"source packet 읽기 실패: {exc}"]
    if not isinstance(data, dict):
        return None, ["source packet root가 object가 아니다"]
    return data, []


def _relative(path: Path, root: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return path.name


def build_report(
    *,
    before_path: Path,
    after_path: Path,
    source_packet_path: Path,
    episode_id: str,
    episode_root: Path | None = None,
) -> dict[str, Any]:
    before_path = before_path.resolve()
    after_path = after_path.resolve()
    source_packet_path = source_packet_path.resolve()
    path_root = (episode_root or before_path.parent).resolve()
    before, before_errors = _parse(before_path)
    after, after_errors = _parse(after_path)
    packet, packet_errors = _read_packet(source_packet_path)

    upstream_errors = verify_upstream_snapshot()
    fact_errors = before_errors + after_errors + packet_errors
    quote_errors: list[str] = []
    number_errors: list[str] = []
    name_errors: list[str] = []
    style_errors: list[str] = []
    edit_rate = 100.0
    fact_anchors: dict[str, list[str]] = {"removed": [], "added": []}
    name_anchors: dict[str, list[str]] = {"removed": [], "added": []}
    numeric_literals: dict[str, list[str]] = {"removed": [], "added": []}

    if before is not None and after is not None and packet is not None:
        before_structure = _structural_signature(before)
        after_structure = _structural_signature(after)
        if before_structure != after_structure:
            fact_errors.append(
                "frontmatter·chapter·source binding·grounding 구조가 바뀌었다 "
                f"({json_digest(before_structure)[:12]} != {json_digest(after_structure)[:12]})"
            )

        before_quotes = _source_quotes(before)
        after_quotes = _source_quotes(after)
        if before_quotes != after_quotes:
            quote_errors.append("[원본] 직접 인용 또는 해당 source/cue binding이 바뀌었다")

        before_text = narration_text(before)
        after_text = narration_text(after)
        fact_anchors = _counter_delta(
            _fact_anchor_counts(before_text, packet),
            _fact_anchor_counts(after_text, packet),
        )
        if fact_anchors["removed"] or fact_anchors["added"]:
            fact_errors.append(f"source packet fact anchor 변경: {fact_anchors}")

        numeric_literals = _counter_delta(
            Counter(NUMBER_RE.findall(before_text)),
            Counter(NUMBER_RE.findall(after_text)),
        )
        if numeric_literals["removed"] or numeric_literals["added"]:
            number_errors.append(f"나레이션 수치·단위 변경: {numeric_literals}")

        name_anchors = _counter_delta(
            _name_anchor_counts(before_text, packet),
            _name_anchor_counts(after_text, packet),
        )
        if name_anchors["removed"] or name_anchors["added"]:
            name_errors.append(f"보호 인물·고유명사 변경: {name_anchors}")

        for label, pattern in DIRECT_VOICE_RULES.items():
            hits = sorted(set(match.group(0) for match in pattern.finditer(after_text)))
            if hits:
                style_errors.append(f"{label}: {', '.join(hits)}")
        edit_rate = _edit_rate(before_text, after_text)

    checks = {
        "UPSTREAM": _check(upstream_errors),
        "FACT": _check(fact_errors, anchors=fact_anchors),
        "QUOTE": _check(quote_errors),
        "NUMBER": _check(number_errors, literals=numeric_literals),
        "NAME": _check(name_errors, anchors=name_anchors),
        "DIRECT_VOICE": _check(style_errors),
    }
    total_violations = sum(item["count"] for item in checks.values())
    warnings: list[str] = []
    if 30.0 < edit_rate < 50.0:
        warnings.append(f"편집률 {edit_rate}%: upstream 30% 경고 범위. 문장별 롤백 검토 필요")
    if edit_rate >= 50.0:
        warnings.append(f"편집률 {edit_rate}%: upstream 50% 강제 중단 범위")

    if checks["UPSTREAM"]["count"]:
        status = "WAIT_HUMANIZE_UPSTREAM"
    elif any(checks[name]["count"] for name in ("FACT", "QUOTE", "NUMBER", "NAME")):
        status = "WAIT_HUMANIZE_FIDELITY"
    elif checks["DIRECT_VOICE"]["count"]:
        status = "WAIT_HUMANIZE_STYLE"
    elif edit_rate >= 50.0:
        status = "WAIT_HUMANIZE_OVEREDIT"
    else:
        status = "PASS"

    def file_info(path: Path) -> dict[str, str]:
        return {"path": _relative(path, path_root), "sha256": sha256_file(path)}

    return {
        "schema": SCHEMA,
        "status": status,
        "episode_id": episode_id,
        "before": file_info(before_path),
        "after": file_info(after_path),
        "source_packet": file_info(source_packet_path),
        "upstream": UPSTREAM_PIN,
        "edit_rate_percent": edit_rate,
        "warnings": warnings,
        "checks": checks,
        "total_violations": total_violations,
    }


def _episode_path(episode: Path, raw: str, *, prefix: str) -> Path:
    candidate = Path(raw)
    if candidate.is_absolute() or ".." in candidate.parts:
        raise ValueError(f"{prefix}: episode 밖 경로는 허용하지 않는다: {raw}")
    resolved = (episode / candidate).resolve()
    try:
        resolved.relative_to(episode.resolve())
    except ValueError as exc:
        raise ValueError(f"{prefix}: episode 밖 경로는 허용하지 않는다: {raw}") from exc
    return resolved


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--episode", required=True, type=Path)
    parser.add_argument("--before", default="20_script/script_draft_pre_humanize_v1.md")
    parser.add_argument("--after", default="20_script/script_draft_v1.md")
    parser.add_argument("--source-packet", default="20_script/source_packet_v1.json")
    parser.add_argument("--out", default="90_reports/humanize_korean_gate_v1.json")
    parser.add_argument("--write", action="store_true", help="receipt를 --out에 저장")
    args = parser.parse_args(argv)

    episode = args.episode.resolve()
    try:
        before = _episode_path(episode, args.before, prefix="before")
        after = _episode_path(episode, args.after, prefix="after")
        packet = _episode_path(episode, args.source_packet, prefix="source packet")
        out = _episode_path(episode, args.out, prefix="out")
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 2

    report = build_report(
        before_path=before,
        after_path=after,
        source_packet_path=packet,
        episode_id=episode.name,
        episode_root=episode,
    )
    rendered = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.write:
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0 if report["status"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())

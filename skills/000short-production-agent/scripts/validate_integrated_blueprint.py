#!/usr/bin/env python3
"""Fail-closed validator for the single human-facing Shorts blueprint."""

from __future__ import annotations

import argparse
import re
from pathlib import Path
from typing import Any


class BlueprintGateFail(Exception):
    pass


DESIGN_SECTIONS = (
    "기본 정보",
    "제작 판단",
    "상단 고정 문구",
    "조립 역할 순서",
    "트랙별 타임라인",
    "TTS 복사용 문구",
    "승인 전 점검",
)
ASSEMBLY_SECTIONS = (
    "프로젝트 실체",
    "설계도 반영 결과",
    "실제 CapCut 트랙 구성",
    "TTS 실제 길이 대조",
    "검증 결과",
    "남은 사람 작업",
)
UPLOAD_FIELDS = (
    "제목",
    "상세설명",
    "출처",
    "해시태그",
    "추천 업로드채널",
)


def _sections(text: str) -> list[tuple[str, int]]:
    return [(m.group(1).strip(), m.start()) for m in re.finditer(r"(?m)^##\s+(.+?)\s*$", text)]


def _section_body(text: str, section: str) -> str:
    marker = f"## {section}"
    start = text.find(marker)
    if start < 0:
        return ""
    next_start = text.find("\n## ", start + len(marker))
    return text[start + len(marker): next_start if next_start >= 0 else len(text)]


def _require_sections(text: str, required: tuple[str, ...], token: str) -> None:
    names = {name for name, _ in _sections(text)}
    missing = [name for name in required if name not in names]
    if missing:
        raise BlueprintGateFail(f"{token}: missing sections: {', '.join(missing)}")


def _require_table(text: str, section: str, token: str) -> None:
    body = _section_body(text, section)
    rows = [
        line.strip()
        for line in body.splitlines()
        if line.strip().startswith("|") and line.strip().endswith("|")
    ]
    if len(rows) < 3:
        raise BlueprintGateFail(f"{token}: {section} must contain a markdown table")
    separator_cells = [cell.strip() for cell in rows[1].strip("|").split("|")]
    if not separator_cells or not all(re.fullmatch(r":?-{3,}:?", cell) for cell in separator_cells):
        raise BlueprintGateFail(f"{token}: {section} must contain a markdown table separator")
    if not any(row != rows[0] and row != rows[1] for row in rows[2:]):
        raise BlueprintGateFail(f"{token}: {section} must contain a markdown table")


def _require_nonempty_body(text: str, section: str, token: str) -> None:
    body = re.sub(r"(?m)^\s*[-#|`\s]+$", "", _section_body(text, section)).strip()
    if not body:
        raise BlueprintGateFail(f"{token}: {section} is empty")


def _require_upload_fields(text: str) -> None:
    body = _section_body(text, "업로드 패키지")
    values: dict[str, str] = {}
    for field in UPLOAD_FIELDS:
        match = re.search(rf"(?m)^\s*{re.escape(field)}\s*:\s*(\S.*)$", body)
        if not match or not match.group(1).strip():
            raise BlueprintGateFail(f"FAIL_UPLOAD_PACKAGE: {field} is empty")
        value = match.group(1).strip()
        if value.lower() in {"없음", "none", "todo", "tbd", "n/a", "미정"}:
            raise BlueprintGateFail(f"FAIL_UPLOAD_PACKAGE: {field} is a placeholder")
        values[field] = value
    if not re.search(r"https?://\S+", values["출처"]):
        raise BlueprintGateFail("FAIL_UPLOAD_PACKAGE: 출처 must include a URL")
    if not re.search(r"#[^\s#]+", values["해시태그"]):
        raise BlueprintGateFail("FAIL_UPLOAD_PACKAGE: 해시태그 must include # tags")


def validate_integrated_blueprint(path: Path, *, phase: str = "production") -> dict[str, Any]:
    if not path.is_file():
        raise BlueprintGateFail(f"FAIL_DESIGN_BLUEPRINT_MISSING: {path}")
    text = path.read_text(encoding="utf-8-sig")
    if not text.lstrip().startswith("# 설계도"):
        raise BlueprintGateFail("FAIL_DESIGN_BLUEPRINT_HEADING: first heading must be # 설계도")
    _require_sections(text, DESIGN_SECTIONS, "FAIL_DESIGN_BLUEPRINT")
    _require_table(text, "조립 역할 순서", "FAIL_DESIGN_BLUEPRINT")
    _require_table(text, "트랙별 타임라인", "FAIL_DESIGN_BLUEPRINT")
    _require_nonempty_body(text, "TTS 복사용 문구", "FAIL_DESIGN_BLUEPRINT")
    if phase == "design":
        return {"status": "PASS", "phase": "design", "path": str(path)}
    _require_sections(text, ("조립도", *ASSEMBLY_SECTIONS), "FAIL_ASSEMBLY_BLUEPRINT")
    _require_sections(text, ("업로드 패키지",), "FAIL_UPLOAD_PACKAGE")
    _require_table(text, "설계도 반영 결과", "FAIL_ASSEMBLY_BLUEPRINT")
    _require_table(text, "실제 CapCut 트랙 구성", "FAIL_ASSEMBLY_BLUEPRINT")
    _require_table(text, "TTS 실제 길이 대조", "FAIL_ASSEMBLY_BLUEPRINT")
    _require_nonempty_body(text, "검증 결과", "FAIL_ASSEMBLY_BLUEPRINT")
    headings = _sections(text)
    if headings[-1][0] != "업로드 패키지":
        raise BlueprintGateFail("FAIL_UPLOAD_PACKAGE: 업로드 패키지 must be the final H2 section")
    _require_upload_fields(text)
    return {"status": "PASS", "phase": "production", "path": str(path), "last_section": headings[-1][0]}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("blueprint")
    parser.add_argument("--phase", choices=("design", "production"), default="production")
    args = parser.parse_args()
    try:
        print(validate_integrated_blueprint(Path(args.blueprint), phase=args.phase))
    except BlueprintGateFail as exc:
        print(str(exc))
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

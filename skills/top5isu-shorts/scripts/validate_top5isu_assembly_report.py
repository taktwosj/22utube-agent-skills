#!/usr/bin/env python3
"""Validate the final top5isu assembly report and CapCut project name."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


class GateFail(Exception):
    pass


REQUIRED_TOKENS = (
    "# 조립도 보고서",
    "## 프로젝트 실체",
    "CapCut 프로젝트 파일 이름:",
    "## 설계 반영 및 검증",
    "## 사용자 수동 편집",
    "manual_edit_policy=MANUAL_EDIT_EXPECTED",
    "manual_edit_difference_is_failure=false",
    "current_draft_reread_required=true",
    "## 캣컵복사하기",
)


def _field(text: str, label: str) -> str:
    match = re.search(rf"^{re.escape(label)}\s*:\s*(.+?)\s*$", text, re.MULTILINE)
    return match.group(1).strip() if match else ""


def validate_assembly_report_text(text: str, expected_project_name: str) -> dict:
    expected_project_name = expected_project_name.strip()
    if not expected_project_name or "\n" in expected_project_name or "\r" in expected_project_name:
        raise GateFail("FAIL_CAPCUT_PROJECT_NAME: expected project name is empty or invalid")
    missing = [token for token in REQUIRED_TOKENS if token not in text]
    if missing:
        raise GateFail(f"FAIL_ASSEMBLY_REPORT: missing required tokens: {missing}")
    reported_name = _field(text, "CapCut 프로젝트명")
    folder_name = _field(text, "CapCut 프로젝트 폴더명")
    file_name = _field(text, "CapCut 프로젝트 파일 이름")
    project_path = _field(text, "CapCut 프로젝트 경로")
    if (
        reported_name != expected_project_name
        or folder_name != expected_project_name
        or file_name != expected_project_name
    ):
        raise GateFail(
            "FAIL_CAPCUT_PROJECT_NAME: report project/folder/file name must exactly match "
            f"{expected_project_name!r}"
        )
    project_dir = Path(project_path).expanduser()
    if not project_path or project_dir.name != expected_project_name:
        raise GateFail("FAIL_CAPCUT_PROJECT_NAME: project path basename must match project name")
    if not project_dir.is_dir() or not (project_dir / "draft_content.json").is_file():
        raise GateFail(
            "FAIL_CAPCUT_PROJECT_PATH: actual CapCut project folder and draft_content.json are required"
        )
    last_line = next((line.strip() for line in reversed(text.splitlines()) if line.strip()), "")
    if last_line != expected_project_name:
        raise GateFail("FAIL_CAPCUT_PROJECT_NAME: assembly report must end with exact project name")
    return {
        "assembly_report_status": "PASS",
        "capcut_project_name": expected_project_name,
        "capcut_project_path": project_path,
        "manual_edit_expected": True,
        "manual_edit_difference_is_failure": False,
        "current_draft_reread_required": True,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("report")
    parser.add_argument("--project-name", required=True)
    args = parser.parse_args()
    try:
        result = validate_assembly_report_text(
            Path(args.report).read_text(encoding="utf-8-sig"),
            args.project_name,
        )
    except (GateFail, OSError) as exc:
        print(str(exc))
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

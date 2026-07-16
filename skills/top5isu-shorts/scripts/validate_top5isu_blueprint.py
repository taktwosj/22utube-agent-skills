#!/usr/bin/env python3
"""Validate the standalone top5isu design blueprint."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


class GateFail(Exception):
    pass


REQUIRED_HEADINGS = (
    "# 설계도",
    "## 기본 정보",
    "## 제작 판단",
    "## 대본",
    "## 트랙별 타임라인",
    "## 오디오 계획",
    "## 이미지 계획",
    "## CapCut 프로젝트",
    "## 검증 및 보고",
)


def validate_blueprint_text(text: str, style_profile: str) -> dict:
    if style_profile not in {"top5", "gunlimbo"}:
        raise GateFail("WAIT_USER_PROFILE: style_profile must be top5 or gunlimbo")
    missing = [heading for heading in REQUIRED_HEADINGS if heading not in text]
    if missing:
        raise GateFail(f"FAIL_TOP5ISU_BLUEPRINT: missing headings: {missing}")
    if f"style_profile: {style_profile}" not in text:
        raise GateFail("FAIL_TOP5ISU_BLUEPRINT: selected style_profile is not locked")
    if "standalone_factory: true" not in text:
        raise GateFail("FAIL_TOP5ISU_BLUEPRINT: standalone factory lock missing")
    if "|" not in text:
        raise GateFail("FAIL_TOP5ISU_BLUEPRINT: timeline table missing")
    return {
        "top5isu_blueprint_status": "PASS",
        "style_profile": style_profile,
        "standalone_factory": True,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("blueprint")
    parser.add_argument("--profile", required=True, choices=("top5", "gunlimbo"))
    args = parser.parse_args()
    try:
        text = Path(args.blueprint).read_text(encoding="utf-8-sig")
        result = validate_blueprint_text(text, args.profile)
    except (GateFail, OSError) as exc:
        print(str(exc))
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

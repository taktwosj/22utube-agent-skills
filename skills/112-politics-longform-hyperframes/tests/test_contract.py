#!/usr/bin/env python3
"""112 스킬 문서 경계 계약 회귀 테스트."""

from __future__ import annotations

import re
import unittest
from pathlib import Path


SKILL = Path(__file__).resolve().parent.parent
BOUNDARY_DOCS = (
    SKILL / "SKILL.md",
    SKILL / "references" / "template-contract.md",
)

CAPCUT_RE = re.compile(r"CapCut|캡컷", re.I)
RULE_SECTIONS = ("Core Boundary", "분리 경계", "Common Mistakes")
RULE_PHRASES = (
    "OUT_OF_SCOPE",
    "FORBIDDEN",
    "KEEP_UNCHANGED",
    "금지",
    "않는다",
    "수정하지",
    "돌려보낸다",
)

EXPECTED_KEEP_UNCHANGED = (
    r"%USERPROFILE%\agent-skills\skills\119-politics-longform-capcut",
    r"%USERPROFILE%\worktrees\agent-skills-000-politics-new\skills\000-politics-longform",
)
EXPECTED_TEMPLATE_DEFAULT = r"${PL_HYPERFRAMES_REPO}\template"

REQUIRED_ANCHORS = {
    "SKILL.md": (
        r"(?m)^CapCut lane\(119\)=OUT_OF_SCOPE\s*$",
        r"(?m)^HYPERFRAMES_FAILURE_AUTO_RUN_119=FORBIDDEN\s*$",
        r"(?m)^MODIFY_119_OR_ITS_WORKTREE=FORBIDDEN\s*$",
        r"(?m)^MODIFY_000_OR_ITS_WORKTREE=FORBIDDEN\s*$",
        rf"(?m)^KEEP_UNCHANGED={re.escape(EXPECTED_KEEP_UNCHANGED[0])}\s*$",
        rf"(?m)^KEEP_UNCHANGED={re.escape(EXPECTED_KEEP_UNCHANGED[1])}\s*$",
        rf"(?m)^template_default={re.escape(EXPECTED_TEMPLATE_DEFAULT)}\s*$",
    ),
    # 이 문서에는 CapCut 언급이 0건이라 CapCut 검사만으로는 아무것도 지켜지지
    # 않는다. 유일한 경계 선언인 아래 한 줄이 지워져도 조용히 통과한다.
    "template-contract.md": (
        r"(?m)^EXISTING_LANES_MODIFICATION=FORBIDDEN\s*$",
    ),
}


def iter_blocks(text: str):
    """문서 문자열에서 (시작 줄, 문단, 상위 섹션)을 낸다."""
    section = ""
    buffer: list[str] = []
    start = 1
    for line_no, line in enumerate(text.splitlines(), 1):
        if line.startswith("#"):
            if buffer:
                yield start, "\n".join(buffer), section
                buffer = []
            section = line.lstrip("# ").strip()
            continue
        if not line.strip():
            if buffer:
                yield start, "\n".join(buffer), section
                buffer = []
            continue
        if not buffer:
            start = line_no
        buffer.append(line)
    if buffer:
        yield start, "\n".join(buffer), section


def in_rule_context(block: str, section: str) -> bool:
    return (any(name in section for name in RULE_SECTIONS)
            or any(phrase in block for phrase in RULE_PHRASES))


def check_capcut_boundary(text: str, doc_name: str) -> list[str]:
    return [
        f"{doc_name}:{line_no} [{section}] 경계 밖 CapCut 언급"
        for line_no, block, section in iter_blocks(text)
        if CAPCUT_RE.search(block) and not in_rule_context(block, section)
    ]


def check_required_anchors(text: str, doc_name: str) -> list[str]:
    """경계 선언 자체가 삭제되거나 약화된 경우를 찾는다."""
    return [
        f"{doc_name}: 앵커 소실 {pattern}"
        for pattern in REQUIRED_ANCHORS[doc_name]
        if not re.search(pattern, text)
    ]


def check_keep_unchanged_paths(text: str, doc_name: str) -> list[str]:
    if doc_name != "SKILL.md":
        return []
    values = re.findall(r"(?m)^KEEP_UNCHANGED\s*=\s*(\S+)\s*$", text)
    violations = []
    for expected in EXPECTED_KEEP_UNCHANGED:
        if expected not in values:
            violations.append(f"{doc_name}: KEEP_UNCHANGED 경로 소실 {expected}")
    for value in values:
        if not re.match(r"^(?:[A-Za-z]:|%USERPROFILE%)[\\/]", value):
            violations.append(f"{doc_name}: KEEP_UNCHANGED 루트 미고정 경로 {value}")
    return violations


def check_template_default(text: str, doc_name: str) -> list[str]:
    if doc_name != "SKILL.md":
        return []
    values = re.findall(r"(?m)^template_default\s*=\s*(\S+)\s*$", text)
    if not values:
        return [f"{doc_name}: template_default 선언 없음"]
    violations = []
    if values != [EXPECTED_TEMPLATE_DEFAULT]:
        violations.append(
            f"{doc_name}: template_default repo 정본 아님 {values!r}")
    for value in values:
        if re.search(r"OneDrive|22factory_", value, re.I):
            violations.append(
                f"{doc_name}: template_default 금지 factory 경로 {value}")
    return violations


BOUNDARY_CHECKS = (
    check_capcut_boundary,
    check_required_anchors,
    check_keep_unchanged_paths,
    check_template_default,
)


DOC_REGRESSIONS = (
    (
        "REG-1 CapCut lane 경계 삭제",
        "SKILL.md",
        "CapCut lane(119)=OUT_OF_SCOPE",
        "CapCut lane(119)=IN_SCOPE",
    ),
    (
        "REG-2 119 자동 우회 금지코드 바꿔치기",
        "SKILL.md",
        "HYPERFRAMES_FAILURE_AUTO_RUN_119=FORBIDDEN",
        "HYPERFRAMES_FAILURE_AUTO_RUN_119=ALLOWED",
    ),
    (
        "REG-3 119 수정 금지코드 바꿔치기",
        "SKILL.md",
        "MODIFY_119_OR_ITS_WORKTREE=FORBIDDEN",
        "MODIFY_119_OR_ITS_WORKTREE=ALLOWED",
    ),
    (
        "REG-4 000 수정 금지코드 바꿔치기",
        "SKILL.md",
        "MODIFY_000_OR_ITS_WORKTREE=FORBIDDEN",
        "MODIFY_000_OR_ITS_WORKTREE=ALLOWED",
    ),
    (
        "REG-5 119 절대경로를 상대경로로 격하",
        "SKILL.md",
        "KEEP_UNCHANGED=" + EXPECTED_KEEP_UNCHANGED[0],
        r"KEEP_UNCHANGED=skills\119-politics-longform-capcut",
    ),
    (
        "REG-6 000 절대경로를 상대경로로 격하",
        "SKILL.md",
        "KEEP_UNCHANGED=" + EXPECTED_KEEP_UNCHANGED[1],
        r"KEEP_UNCHANGED=skills\000-politics-longform",
    ),
    (
        "REG-7 template_default를 OneDrive 사본으로 변경",
        "SKILL.md",
        "template_default=" + EXPECTED_TEMPLATE_DEFAULT,
        r"template_default=%USERPROFILE%\OneDrive\22utube\22factory_20260628\template",
    ),
    (
        "REG-9 기존 lane 수정 금지 선언 소멸",
        "template-contract.md",
        "EXISTING_LANES_MODIFICATION=FORBIDDEN",
        "",
    ),
    (
        "REG-8 경계 밖 CapCut 지시 삽입",
        "template-contract.md",
        "각 요소에 composition prefix를 포함한 고유 `id`, 고유 `data-hf-id`,",
        "각 요소에 composition prefix를 포함한 고유 `id`, 고유 `data-hf-id`,\n"
        "CapCut 편집 단계에 전달한다.",
    ),
)


class TestBoundaryContract(unittest.TestCase):
    def test_real_documents_have_no_contract_violations(self):
        for path in BOUNDARY_DOCS:
            text = path.read_text(encoding="utf-8")
            found = []
            for check in BOUNDARY_CHECKS:
                found += check(text, path.name)
            with self.subTest(document=path.name):
                self.assertEqual(found, [])


class TestBoundaryRegressionFixtures(unittest.TestCase):
    def test_every_real_document_regression_is_caught(self):
        """실문서를 메모리에서 훼손하면 검사 중 하나는 반드시 잡아야 한다."""
        for label, doc_name, old, new in DOC_REGRESSIONS:
            with self.subTest(regression=label):
                path = next(path for path in BOUNDARY_DOCS
                            if path.name == doc_name)
                text = path.read_text(encoding="utf-8")
                self.assertIn(old, text, f"{label}: 픽스처가 실문서와 어긋난다")
                damaged = text.replace(old, new)
                found = []
                for check in BOUNDARY_CHECKS:
                    found += check(damaged, doc_name)
                self.assertNotEqual(found, [], f"{label}: 아무 검사도 못 잡음")


if __name__ == "__main__":
    unittest.main(verbosity=2)

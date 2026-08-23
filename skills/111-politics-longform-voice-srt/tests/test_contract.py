#!/usr/bin/env python3
"""111 스킬 계약 회귀 테스트.

표준 라이브러리만 사용한다. 실행:
    py -3.14 -m unittest discover -s skills/111-politics-longform-voice-srt/tests

검사 단위는 줄이 아니라 **문단**이다. 한글 문서는 한 문장이 여러 줄로 접히기
때문에 줄 단위로 보면 "CapCut ...을 / 쓰지 않는다"가 두 줄로 갈려 오탐이 난다.
"""
import os
import re
import subprocess
import sys
import unittest
from pathlib import Path

SKILL = Path(__file__).resolve().parent.parent
DOCS = [SKILL / "SKILL.md"] + sorted((SKILL / "references").glob("*.md"))
SCRIPTS = sorted((SKILL / "scripts").glob("*.py"))
BOUNDARY_DOCS = [SKILL / "SKILL.md", SKILL / "references" / "lane-contract.md"]

CAPCUT_RE = re.compile(r"CapCut|캡컷", re.I)

# 구현 종속 문자열 — 폐기 선언 안에서만 등장할 수 있다.
FORBIDDEN_LITERALS = [
    "editability",
    "material_id",
    "draft_content",
    "draft_meta",
    "공백 제외 최대 20자",
    "공백 제외 20자",
    "max lines: 1",
    "font size: 8.0",
    "role: tts",
]

# 금지 대상을 이름으로 부를 수 있는 섹션. 이 밖에서 나오면 누출이다.
RULE_SECTIONS = (
    "Lane 경계", "Lane 계약", "상속 / 폐기", "용어 계약", "용어 충돌",
    "금지 산출물", "필수 테스트", "실패 상태", "Core Boundary",
)

# 문단 자체가 금지를 말하고 있음을 보여주는 표현.
RULE_PHRASES = (
    "FORBIDDEN", "KEEP_UNCHANGED", "NOT_USED", "FAIL_CAPCUT", "dependency",
    "금지", "않는다", "폐기", "레거시", "alias", "충돌", "0건", "제외",
    "돌려보낸다", "한정", "근거",
)


def iter_blocks(paths):
    """(path, 시작 줄번호, 문단 텍스트, 상위 섹션 제목)을 낸다."""
    for p in paths:
        section = ""
        buf, start = [], 1
        for i, line in enumerate(p.read_text(encoding="utf-8").splitlines(), 1):
            if line.startswith("#"):
                if buf:
                    yield p, start, "\n".join(buf), section
                    buf = []
                section = line.lstrip("# ").strip()
                continue
            if not line.strip():
                if buf:
                    yield p, start, "\n".join(buf), section
                    buf = []
                continue
            if not buf:
                start = i
            buf.append(line)
        if buf:
            yield p, start, "\n".join(buf), section


def in_rule_context(block, section):
    return (any(s in section for s in RULE_SECTIONS)
            or any(ph in block for ph in RULE_PHRASES))


def check_keep_unchanged_has_path(text):
    """KEEP_UNCHANGED 경로 선언 위반 목록을 돌려준다."""
    violations = []
    declarations = 0
    for line_no, line in enumerate(text.splitlines(), 1):
        line = line.strip().strip("`")
        match = re.fullmatch(r"KEEP_UNCHANGED(?:\s*=\s*(.*))?", line)
        if not match:
            continue
        declarations += 1
        value = match.group(1) or ""
        tokens = [token.strip("`'\".,;()[]{}") for token in value.split()]
        if not any(len(token) >= 2 and re.search(r"[\\/]", token)
                   for token in tokens):
            violations.append(f"line {line_no}: KEEP_UNCHANGED 경로 없음")
    if declarations == 0 and re.search(
            r"(?m)^\s*MODIFY_000_OR_ITS_WORKTREE\s*=\s*FORBIDDEN\s*$", text):
        violations.append("KEEP_UNCHANGED 경로 선언 없음")
    return violations


REQUIRED_FAILURE_CODE = "FAIL_CAPCUT_DEPENDENCY_DETECTED"


def check_forbidden_outputs_have_failure_code(text):
    """금지 산출물과 실패 코드의 문단 결합 위반 목록을 돌려준다."""
    violations = []
    lines = text.splitlines()
    for index, line in enumerate(lines):
        if not re.fullmatch(r"##\s+금지 산출물\s*", line.strip()):
            continue
        paragraph = []
        for body_line in lines[index + 1:]:
            if re.match(r"^#{1,2}\s+", body_line):
                break
            if not body_line.strip():
                if paragraph:
                    break
                continue
            paragraph.append(body_line)
        block = "\n".join(paragraph)
        # 아무 FAIL_* 나 허용하면 코드를 바꿔치기해도 통과한다.
        # 금지와 결합돼야 하는 코드는 하나뿐이다.
        if REQUIRED_FAILURE_CODE not in block:
            violations.append(
                f"line {index + 1}: 금지 산출물 문단에 "
                f"{REQUIRED_FAILURE_CODE} 없음")
    return violations


def check_forbidden_target_is_specific(text):
    """일반명사만 쓴 금지 대상 위반 목록을 돌려준다."""
    # 접미사를 고정하면 legacy_editor_fallback 같은 파생 이름이 빠져나간다.
    # 실제로 지난 회차 개명은 _dependency 와 _fallback 둘 다였다.
    generic_target = re.compile(
        r"\blegacy[ _-]?editor\w*|기존\s*편집기|구\s*편집기|외부\s*도구",
        re.I,
    )
    # 아무 대문자 토큰이나 인정하면 `# NO_AUTO_RUN` 주석만 붙여도 통과한다.
    # 경로 구분자 하나만 인정해도 마찬가지다. 금지 대상을 실제로 지목하는
    # 고유명사 · 스킬 식별자 · 루트 고정 절대경로만 인정한다.
    specific_target = re.compile(
        r"CapCut|캡컷|Supertone|HyperFrames|"
        r"\b(?:000|110|111|112|119)-[a-z-]+|"
        r"(?:[A-Za-z]:|%USERPROFILE%)[\\/]",
    )
    violations = []
    for line_no, line in enumerate(text.splitlines(), 1):
        stripped = line.strip()
        if stripped.startswith("#"):
            continue
        if not re.search(r"FORBIDDEN|금지", stripped, re.I):
            continue
        if not generic_target.search(stripped):
            continue
        remainder = re.sub(r"FORBIDDEN", "", stripped, flags=re.I)
        remainder = generic_target.sub("", remainder)
        if not specific_target.search(remainder):
            violations.append(f"line {line_no}: 금지 대상이 일반명사뿐임")
    return violations


# 위 세 검사는 "남아 있는 선언이 잘 쓰였나"만 본다. 선언 자체가 사라지거나
# 절대경로가 상대경로로 격하되면 검사할 대상이 없어져 전부 통과한다.
# 방어의 존재 자체를 못박는다.
REQUIRED_ANCHORS = {
    "SKILL.md": [
        # 상대경로는 어느 루트 기준인지 말하지 않는다. 112 는 둘 다 절대경로다.
        r"KEEP_UNCHANGED\s*=\s*(?:[A-Za-z]:|%USERPROFILE%)[\\/]\S*119-politics-longform-capcut",
        r"KEEP_UNCHANGED\s*=\s*(?:[A-Za-z]:|%USERPROFILE%)[\\/]\S*000-politics-longform",
        r"HYPERFRAMES_FAILURE_AUTO_RUN_119\s*=\s*FORBIDDEN",
    ],
    "lane-contract.md": [
        r"(?m)^##\s+금지 산출물\s*$",
        r"capcut_dependency\s*=\s*0",
        r"capcut_fallback\s*=\s*FORBIDDEN",
    ],
}


def check_required_anchors(text, doc_name):
    """방어 선언이 실재하는지 확인한다. 없어진 것은 잘 쓰였는지 볼 수 없다."""
    return [f"{doc_name}: 앵커 소실 {pat}"
            for pat in REQUIRED_ANCHORS[doc_name] if not re.search(pat, text)]


class TestBoundaryDeclarationStrength(unittest.TestCase):
    @staticmethod
    def _real_contract_texts():
        return [(p, p.read_text(encoding="utf-8")) for p in BOUNDARY_DOCS]

    def test_keep_unchanged_accepts_paths(self):
        text = (
            "KEEP_UNCHANGED=%USERPROFILE%\\agent-skills\\skills\\119-politics-longform-capcut\n"
            "KEEP_UNCHANGED = skills\\119-politics-longform-capcut"
        )
        self.assertEqual(check_keep_unchanged_has_path(text), [])

    def test_keep_unchanged_rejects_missing_or_named_only_path(self):
        for text in (
                "KEEP_UNCHANGED",
                "KEEP_UNCHANGED=기존 lane",
                "MODIFY_000_OR_ITS_WORKTREE=FORBIDDEN"):
            with self.subTest(text=text):
                self.assertNotEqual(check_keep_unchanged_has_path(text), [])

    def test_keep_unchanged_real_documents(self):
        for path, text in self._real_contract_texts():
            with self.subTest(path=path.name):
                self.assertEqual(check_keep_unchanged_has_path(text), [])

    def test_forbidden_outputs_accepts_failure_code_same_paragraph(self):
        text = (
            "## 금지 산출물\n\n"
            "CapCut draft / project / timeline.\n"
            "하나라도 생성되면 `FAIL_CAPCUT_DEPENDENCY_DETECTED`."
        )
        self.assertEqual(check_forbidden_outputs_have_failure_code(text), [])

    def test_forbidden_outputs_rejects_forward_reference(self):
        text = (
            "## 금지 산출물\n\n"
            "CapCut draft / project / timeline.\n"
            "하나라도 생성되면 아래 실패 상태를 사용한다.\n\n"
            "## 실패 상태\n\n"
            "FAIL_CAPCUT_DEPENDENCY_DETECTED"
        )
        self.assertNotEqual(check_forbidden_outputs_have_failure_code(text), [])

    def test_forbidden_outputs_real_documents(self):
        for path, text in self._real_contract_texts():
            with self.subTest(path=path.name):
                self.assertEqual(
                    check_forbidden_outputs_have_failure_code(text), [])

    def test_forbidden_target_accepts_specific_names(self):
        text = (
            "capcut_dependency = FORBIDDEN\n"
            "CapCut fallback 사용 금지\n"
            "Supertone TTS API 외부 도구 사용 금지"
        )
        self.assertEqual(check_forbidden_target_is_specific(text), [])

    def test_forbidden_target_rejects_generic_names(self):
        for text in (
                "legacy_editor_dependency = FORBIDDEN",
                "legacy editor 사용 금지",
                "기존 편집기 사용 금지",
                "구 편집기 사용 금지",
                "외부 도구 사용 금지"):
            with self.subTest(text=text):
                self.assertNotEqual(check_forbidden_target_is_specific(text), [])

    def test_forbidden_target_real_documents(self):
        for path, text in self._real_contract_texts():
            with self.subTest(path=path.name):
                self.assertEqual(check_forbidden_target_is_specific(text), [])

    def test_anchors_reject_removal(self):
        """실문서에서 앵커를 하나씩 지우면 반드시 걸려야 한다."""
        for path, text in self._real_contract_texts():
            for pat in REQUIRED_ANCHORS[path.name]:
                with self.subTest(doc=path.name, pat=pat):
                    damaged = re.sub(pat, "", text)
                    self.assertNotEqual(damaged, text, "앵커가 원래 없다")
                    self.assertNotEqual(
                        check_required_anchors(damaged, path.name), [])

    def test_anchors_real_documents(self):
        for path, text in self._real_contract_texts():
            with self.subTest(path=path.name):
                self.assertEqual(check_required_anchors(text, path.name), [])


# 합성 문자열 픽스처는 검사식이 스스로 만든 세계 안에서만 성립한다.
# 방어가 실제로 무너지는지는 실문서를 훼손해봐야 안다.
# 앞 4건은 지난 회차에 실제로 일어난 훼손, 뒤 3건은 검사식 우회 시도다.
DOC_REGRESSIONS = [
    ("REG-1a  KEEP_UNCHANGED 를 이름 선언으로 대체", "SKILL.md",
     r"KEEP_UNCHANGED = %USERPROFILE%\agent-skills\skills"
     r"\119-politics-longform-capcut",
     "MODIFY_119_OR_ITS_WORKTREE = FORBIDDEN"),
    ("REG-1c  절대경로를 상대경로로 격하", "SKILL.md",
     r"KEEP_UNCHANGED = %USERPROFILE%\agent-skills\skills"
     r"\119-politics-longform-capcut",
     r"KEEP_UNCHANGED = skills\119-politics-longform-capcut"),
    ("REG-2   capcut_dependency 개명", "lane-contract.md",
     "capcut_dependency = 0", "legacy_editor_dependency = 0"),
    ("REG-3   실패코드를 전방참조로 대체", "lane-contract.md",
     "하나라도 생성되면 `FAIL_CAPCUT_DEPENDENCY_DETECTED`.",
     "하나라도 생성되면 아래 실패 상태를 사용한다."),
    ("REG-2b  개명 + 무관한 대문자 토큰으로 위장", "lane-contract.md",
     "capcut_fallback   = FORBIDDEN",
     "legacy_editor_fallback = FORBIDDEN  # NO_AUTO_RUN"),
    ("REG-3b  실패코드 바꿔치기", "lane-contract.md",
     "하나라도 생성되면 `FAIL_CAPCUT_DEPENDENCY_DETECTED`.",
     "하나라도 생성되면 `FAIL_OTHER_CODE`."),
    ("REG-4   금지 산출물 섹션 소멸", "lane-contract.md",
     "## 금지 산출물", "## 산출물 메모"),
]

BOUNDARY_CHECKS = (
    lambda text, name: check_keep_unchanged_has_path(text),
    lambda text, name: check_forbidden_outputs_have_failure_code(text),
    lambda text, name: check_forbidden_target_is_specific(text),
    check_required_anchors,
)


class TestBoundaryRegressionFixtures(unittest.TestCase):
    def test_every_regression_is_caught(self):
        """실문서를 훼손하면 검사 중 하나는 반드시 걸려야 한다."""
        for label, doc_name, old, new in DOC_REGRESSIONS:
            with self.subTest(regression=label):
                path = next(p for p in BOUNDARY_DOCS if p.name == doc_name)
                text = path.read_text(encoding="utf-8")
                self.assertIn(old, text, f"{label}: 픽스처가 실문서와 어긋난다")
                damaged = text.replace(old, new)
                found = []
                for check in BOUNDARY_CHECKS:
                    found += check(damaged, doc_name)
                self.assertNotEqual(found, [], f"{label}: 아무 검사도 못 잡음")


class TestCapCutLeakage(unittest.TestCase):
    def test_capcut_mentions_are_boundary_declarations_only(self):
        bad = [f"{p.name}:{i} [{section}]"
               for p, i, block, section in iter_blocks(DOCS)
               if CAPCUT_RE.search(block) and not in_rule_context(block, section)]
        self.assertEqual(bad, [], "경계 선언이 아닌 CapCut 언급:\n" + "\n".join(bad))

    def test_no_capcut_in_scripts(self):
        bad = [f"{p.name}:{i}" for p, i, block, _ in iter_blocks(SCRIPTS)
               if CAPCUT_RE.search(block)]
        self.assertEqual(bad, [], f"스크립트에 CapCut 언급: {bad}")

    def test_forbidden_implementation_literals(self):
        bad = []
        for p, i, block, section in iter_blocks(DOCS + SCRIPTS):
            if "FORBIDDEN_LITERALS" in block:
                continue
            for lit in FORBIDDEN_LITERALS:
                if lit in block and not in_rule_context(block, section):
                    bad.append(f"{p.name}:{i}: {lit} [{section}]")
        self.assertEqual(bad, [], "CapCut 구현 종속 문자열:\n" + "\n".join(bad))

    def test_no_capcut_lane_execution_instruction(self):
        """119(CapCut) 실행 지시가 금지 선언 밖에 있으면 안 된다.

        번호 개편 전에는 이 검사가 '111' 을 봤다. 지금 111 은 이 스킬
        자신이라, 그대로 두면 자기 실행을 막고 정작 CapCut 우회는 못 잡는다.
        """
        bad = []
        for p, i, block, section in iter_blocks(DOCS):
            if "119" not in block:
                continue
            if re.search(r"119[^\n]{0,40}(실행하|호출하)", block) \
                    and not in_rule_context(block, section):
                bad.append(f"{p.name}:{i} [{section}]")
        self.assertEqual(bad, [], "119 실행 지시:\n" + "\n".join(bad))


class TestTerminology(unittest.TestCase):
    def test_no_bare_tts_role_name(self):
        allowed = ("Supertone TTS API", "SUPERTONE_TTS_GUIDE", "Supertone TTS",
                   "TTS_PARAMS_LOCKED", "WAIT_TTS_PARAMS_LOCK",
                   "TTS_PARAMS_INTEGRITY_FAIL")
        bad = []
        for p, i, block, section in iter_blocks(DOCS):
            if "TTS" not in block:
                continue
            stripped = block
            for a in allowed:
                stripped = stripped.replace(a, "")
            if "TTS" in stripped and not in_rule_context(block, section):
                bad.append(f"{p.name}:{i} [{section}]")
        self.assertEqual(bad, [], "TTS 단독 사용:\n" + "\n".join(bad))

    def test_required_names_present(self):
        text = "\n".join(p.read_text(encoding="utf-8") for p in DOCS)
        for name in ("PROJECT_GPT_CORRECTED_SRT_LOCK",
                     "SOURCE_SPEECH_CAPTION_FIDELITY",
                     "narration_audio", "narration_caption",
                     "source_speech_caption", "production_input_v1.json"):
            with self.subTest(name=name):
                self.assertIn(name, text)

    def test_legacy_lock_name_is_alias_only(self):
        bad = []
        for p, i, block, _ in iter_blocks(DOCS):
            if "USER_CORRECTED_SRT_LOCK" not in block:
                continue
            if "alias" not in block and "레거시" not in block:
                bad.append(f"{p.name}:{i}")
        self.assertEqual(bad, [], f"레거시 명칭이 alias 선언 밖에서 사용됨: {bad}")


class TestScriptGuards(unittest.TestCase):
    REQUIRED_ENV = ("PL_EPISODE_DIR",)

    def _env_without_contract_vars(self):
        drop = {"PL_EPISODE_DIR", "PL_VIDEO_DIR", "PL_SCRIPT_SHA256"}
        env = {k: v for k, v in os.environ.items() if k not in drop}
        # 한글 오류 메시지가 cp949로 디코드되면 출력이 통째로 사라진다
        env["PYTHONIOENCODING"] = "utf-8"
        return env

    def test_scripts_exit_without_env(self):
        env = self._env_without_contract_vars()
        for script in SCRIPTS:
            with self.subTest(script=script.name):
                r = subprocess.run([sys.executable, str(script)],
                                   capture_output=True, text=True,
                                   encoding="utf-8", errors="replace",
                                   env=env, timeout=120)
                self.assertNotEqual(
                    r.returncode, 0,
                    f"{script.name}: 환경변수 없이 성공하면 안 된다")
                out = (r.stdout or "") + (r.stderr or "")
                self.assertTrue(
                    any(v in out for v in self.REQUIRED_ENV),
                    f"{script.name}: 누락 환경변수를 이름으로 보고해야 한다\n{out[:400]}")

    def test_scripts_compile(self):
        for script in SCRIPTS:
            with self.subTest(script=script.name):
                r = subprocess.run(
                    [sys.executable, "-m", "py_compile", str(script)],
                    capture_output=True, text=True, timeout=120)
                self.assertEqual(r.returncode, 0, r.stderr)


class TestNoAutomaticGit(unittest.TestCase):
    def test_skill_forbids_automatic_git_actions(self):
        text = (SKILL / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn(
            "Git clone/worktree/commit/push/PR 생성은 111 기본 흐름이 아니며 자동 실행하지 않는다.",
            text,
        )
        self.assertIn("Git commit/push/PR은 실행하지 않는다.", text)
        self.assertNotIn("일반 push", text)

    def test_scripts_have_no_repo_checkout_dependency(self):
        for script in SCRIPTS:
            with self.subTest(script=script.name):
                text = script.read_text(encoding="utf-8")
                self.assertNotIn("PL_REPO_EPISODE", text)
                self.assertNotIn("REPO_EPISODE", text)


class TestAlignmentContract(unittest.TestCase):
    def test_no_char_proportional_distribution(self):
        bad = [f"{p.name}:{i}" for p, i, block, _ in iter_blocks(SCRIPTS)
               if re.search(r"weights\s*=|proportional", block)]
        self.assertEqual(bad, [], f"문자 수 비례 배분 흔적: {bad}")


if __name__ == "__main__":
    unittest.main(verbosity=2)

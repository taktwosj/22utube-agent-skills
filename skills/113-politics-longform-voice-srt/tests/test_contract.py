#!/usr/bin/env python3
"""113 스킬 계약 회귀 테스트.

표준 라이브러리만 사용한다. 실행:
    py -3.14 -m unittest discover -s skills/113-politics-longform-voice-srt/tests

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

    def test_no_111_execution_instruction(self):
        bad = []
        for p, i, block, section in iter_blocks(DOCS):
            if "111" not in block:
                continue
            if re.search(r"111[^\n]{0,40}(실행하|호출하)", block) \
                    and not in_rule_context(block, section):
                bad.append(f"{p.name}:{i} [{section}]")
        self.assertEqual(bad, [], "111 실행 지시:\n" + "\n".join(bad))


class TestTerminology(unittest.TestCase):
    def test_no_bare_tts_role_name(self):
        allowed = ("Supertone TTS API", "SUPERTONE_TTS_GUIDE", "Supertone TTS")
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
    REQUIRED_ENV = ("PL_EPISODE_DIR", "PL_REPO_EPISODE")

    def _env_without_contract_vars(self):
        drop = {"PL_EPISODE_DIR", "PL_REPO_EPISODE",
                "PL_VIDEO_DIR", "PL_SCRIPT_SHA256"}
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


class TestAlignmentContract(unittest.TestCase):
    def test_no_char_proportional_distribution(self):
        bad = [f"{p.name}:{i}" for p, i, block, _ in iter_blocks(SCRIPTS)
               if re.search(r"weights\s*=|proportional", block)]
        self.assertEqual(bad, [], f"문자 수 비례 배분 흔적: {bad}")


if __name__ == "__main__":
    unittest.main(verbosity=2)

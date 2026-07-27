#!/usr/bin/env python3
"""정치롱폼 lane 라우팅 계약.

목표 상태를 적는다. 지금은 실패하는 게 정상이다 (RED).

    110 대본  ->  111 음성·SRT  ->  112 HyperFrames
    119 CapCut 은 명시 요청에만. 탐색 후보로도 잡히면 안 된다

개별 스킬이 아니라 저장소 공통에 둔다. 스킬 안에 두면 그 스킬을 지울 때
라우팅 계약도 같이 사라진다.
"""
from __future__ import annotations

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKILLS = ROOT / "skills"

LANE = {
    "script": "110-politics-longform-script",
    "voice": "111-politics-longform-voice-srt",
    "screen": "112-politics-longform-hyperframes",
    "capcut": "119-politics-longform-capcut",
}

# 일반 정치롱폼 요청에 쓰이는 말. 이 어휘로는 대본 스킬만 걸려야 한다.
GENERIC_TRIGGERS = ("정치롱폼", "정치 롱폼", "정치미드폼", "민주진영 유튜브",
                    "매불쇼 롱폼", "유시민 롱폼")
CAPCUT_TRIGGERS = ("CapCut", "캡컷", "119")

RETIRED = "113-politics-longform-voice-srt"


def description_of(skill_dir):
    # 없는 스킬은 예외가 아니라 빈 description 이다. FileNotFoundError 로
    # 터지면 ERROR 가 되어 "기능 부재" 인지 "테스트 버그" 인지 구분이 안 된다.
    path = SKILLS / skill_dir / "SKILL.md"
    if not path.is_file():
        return ""
    text = path.read_text(encoding="utf-8")
    m = re.search(r"(?ms)^---\s*\n(.*?)^---\s*$", text)
    if not m:
        return ""
    d = re.search(r"(?ms)^description:\s*(.+?)(?=^\w+:|\Z)", m.group(1))
    return " ".join(d.group(1).split()) if d else ""


def trigger_items(desc):
    """description 에서 트리거 항목을 낱개로 뽑는다.

    부분 문자열로 보면 '하이퍼프레임 정치롱폼' 이 '정치롱폼' 으로 잡혀
    한정된 트리거까지 위반이 된다. 문제는 일반어를 '단독 항목' 으로
    선언하는 것이므로 항목 단위로 정확히 비교한다.
    """
    body = re.sub(r"(?i)^use\s+(only\s+)?when\s+"
                  r"(the\s+user\s+)?(explicitly\s+)?"
                  r"(says|requests?|a\s+political[\w\s-]*?contains)\s*",
                  "", desc).strip()
    body = re.split(r"(?i)\bor\s+asks?\s+to\b", body)[0]
    items = re.split(r",|\bor\b", body)
    return [i.strip(" .`\"'") for i in items if i.strip(" .`\"'")]


def existing_skill_dirs():
    return sorted(p.name for p in SKILLS.iterdir()
                  if p.is_dir() and (p / "SKILL.md").is_file())


class TestLaneMembership(unittest.TestCase):
    def test_all_four_lane_skills_exist(self):
        for role, name in LANE.items():
            with self.subTest(role=role):
                self.assertTrue((SKILLS / name / "SKILL.md").is_file(),
                                f"{name} 없음")

    def test_retired_number_is_gone(self):
        """옛 113 은 새 111 로 옮겨졌다. 남아 있으면 두 스킬이 같은 일을 한다."""
        self.assertFalse((SKILLS / RETIRED).exists(),
                         f"{RETIRED} 가 아직 있다")

    def test_number_order_matches_execution_order(self):
        order = [LANE["script"], LANE["voice"], LANE["screen"]]
        nums = [int(n.split("-")[0]) for n in order]
        self.assertEqual(nums, sorted(nums),
                         f"번호가 실행 순서와 어긋난다: {nums}")


class TestGenericRequestRoutesToScript(unittest.TestCase):
    def test_only_script_skill_claims_generic_triggers(self):
        """'정치롱폼' 만 말했을 때 걸리는 스킬은 110 하나여야 한다.

        한정된 '하이퍼프레임 정치롱폼' 은 위반이 아니다. 일반어를 단독
        항목으로 선언하는 것만 문제다.
        """
        for name in existing_skill_dirs():
            if name == LANE["script"]:
                continue
            items = trigger_items(description_of(name))
            hits = [i for i in items if i in GENERIC_TRIGGERS]
            with self.subTest(skill=name):
                self.assertEqual(hits, [],
                                 f"{name} 이 일반 트리거를 단독으로 문다: {hits}")

    def test_script_skill_claims_the_generic_request(self):
        items = trigger_items(description_of(LANE["script"]))
        self.assertTrue(any(i in GENERIC_TRIGGERS for i in items),
                        f"110 이 일반 정치롱폼 요청을 받지 않는다: {items}")


class TestCapCutIsExplicitOnly(unittest.TestCase):
    def test_capcut_description_has_only_explicit_triggers(self):
        desc = description_of(LANE["capcut"])
        self.assertTrue(any(t in desc for t in CAPCUT_TRIGGERS),
                        "119 가 CapCut 명시 트리거를 갖고 있지 않다")

    def test_capcut_description_carries_no_generic_vocabulary(self):
        """부정문이라도 description 에 들어가면 탐색 후보로 잡힌다.

        '일반 정치롱폼 금지' 같은 문구는 본문과 라우터에 두고
        description 에는 명시 트리거만 남긴다.
        """
        items = trigger_items(description_of(LANE["capcut"]))
        hits = [i for i in items if i in GENERIC_TRIGGERS]
        self.assertEqual(hits, [], f"119 가 일반 어휘를 단독 트리거로 문다: {hits}")


class TestTriggerExtraction(unittest.TestCase):
    """추출기 자체 시험. 이게 틀리면 위 검사 전체가 헛돈다."""

    def test_bare_generic_is_extracted_as_item(self):
        items = trigger_items(
            "Use when the user says 111정치롱폼, 정치롱폼, 정치미드폼, "
            "or asks to design a video.")
        self.assertIn("정치롱폼", items)
        self.assertNotIn("design a video", items)

    def test_qualified_trigger_is_not_a_bare_generic(self):
        items = trigger_items(
            "Use when the user explicitly requests 112정치롱폼, "
            "하이퍼프레임 정치롱폼, HyperFrames 정치롱폼.")
        self.assertNotIn("정치롱폼", items)
        self.assertIn("하이퍼프레임 정치롱폼", items)


class TestNoStaleReferences(unittest.TestCase):
    SCAN_SUFFIX = (".md", ".py", ".json", ".ps1", ".sh")
    # docs/superpowers 는 과거 설계·기획 문서다. 그 시점에 111 이 CapCut
    # lane 이었다는 것이 사실이므로 고치면 기록이 거짓이 된다. 살아 있는
    # 표면만 검사한다.
    SKIP_DIRS = {"__pycache__", ".git", "node_modules", "superpowers"}

    SELF = Path(__file__).resolve()

    def _files(self):
        # 이 파일은 금지 문자열을 상수로 갖고 있다. 자기 자신을 스캔하면
        # 영원히 실패한다.
        for p in ROOT.rglob("*"):
            if not p.is_file() or p.suffix not in self.SCAN_SUFFIX:
                continue
            if any(d in p.parts for d in self.SKIP_DIRS):
                continue
            if p.resolve() == self.SELF:
                continue
            yield p

    def test_no_reference_to_retired_113(self):
        bad = [str(p.relative_to(ROOT)) for p in self._files()
               if RETIRED in p.read_text(encoding="utf-8", errors="replace")]
        self.assertEqual(bad, [], f"옛 113 참조 잔존: {bad}")

    def test_no_reference_to_old_capcut_directory(self):
        """옛 111-politics-longform 경로가 남으면 가리키는 곳이 없다."""
        pat = re.compile(r"111-politics-longform(?!-voice-srt)")
        bad = [str(p.relative_to(ROOT)) for p in self._files()
               if pat.search(p.read_text(encoding="utf-8", errors="replace"))]
        self.assertEqual(bad, [], f"옛 CapCut 경로 참조 잔존: {bad}")

    def test_no_garbage_from_mechanical_substitution(self):
        """치환 순서를 틀리면 나오는 쓰레기 문자열."""
        garbage = ("119-politics-longform-capcut-voice-srt",
                   "111-politics-longform-capcut",
                   "119-politics-longform-voice-srt")
        bad = []
        for p in self._files():
            text = p.read_text(encoding="utf-8", errors="replace")
            for g in garbage:
                if g in text:
                    bad.append(f"{p.relative_to(ROOT)}: {g}")
        self.assertEqual(bad, [], f"치환 쓰레기: {bad}")


if __name__ == "__main__":
    unittest.main(verbosity=2)

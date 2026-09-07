import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILL_DIR = ROOT / "skills" / "spine-script-119"
SKILL = SKILL_DIR / "SKILL.md"
SCRIPTS = SKILL_DIR / "scripts"
MANIFEST = ROOT / "manifests" / "skill-set.json"

SHORTS_SCRIPTS = (
    "mark_shorts.py",
    "gen_short_art.py",
    "cut_shorts.py",
    "build_short.py",
    "verify_shorts.py",
)


class SpineScript119ShortsContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = SKILL.read_text(encoding="utf-8")

    def test_skill_is_registered_in_manifest(self):
        manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
        entry = next((s for s in manifest["skills"] if s["name"] == "spine-script-119"), None)
        self.assertIsNotNone(entry, "spine-script-119 is not registered")
        self.assertTrue(entry["enabled"])
        self.assertEqual(sorted(entry["targets"]), ["claude", "codex", "hermes"])

    def test_shorts_scripts_exist(self):
        for name in SHORTS_SCRIPTS:
            self.assertTrue((SCRIPTS / name).is_file(), f"missing script: {name}")

    def test_shorts_stage_runs_before_narration(self):
        """쇼츠 구간은 나레이션 원고보다 먼저 잠근다. 순서가 뒤집히면 쇼츠에 쓸 문장이 없다."""
        order = self.text.split("## 실행 순서", 1)[1]
        mark = order.index("mark_shorts.py")
        narration = order.index("(나레이션 원고)")
        art = order.index("gen_short_art.py")
        self.assertLess(mark, narration)
        self.assertLess(narration, art)
        for name in ("cut_shorts.py", "build_short.py", "verify_shorts.py"):
            self.assertGreater(order.index(name), art)

    def test_shorts_contract_is_documented(self):
        section = self.text.split("## 쇼츠", 1)[1].split("\n## ", 1)[0]
        for required in (
            "claim",
            "counter",
            "롱폼 wav 를 그대로 쓴다",
            "실존 인물의 얼굴을 그리지 않는다",
            "P0_ROOT_shrt_119short_v1",
            "template-2.tmp",
        ):
            self.assertIn(required, section)

    def test_cards_def_template_carries_shorts_block(self):
        template = (SKILL_DIR / "templates" / "cards_def.template.py").read_text(encoding="utf-8")
        self.assertIn("SHORTS = [", template)
        for field in ("claim", "counter", "head_narration", "tail_narration", "art"):
            self.assertIn(field, template)

    def test_mark_shorts_rejects_context_dependent_cards(self):
        """반박 카드가 지시어로 시작하면 쇼츠에서 혼자 서지 못한다."""
        source = (SCRIPTS / "mark_shorts.py").read_text(encoding="utf-8")
        self.assertIn("SHORT_CARD_NOT_STANDALONE", source)
        self.assertIn("SHORT_NARRATION_MISSING", source)

    def test_verify_ignores_capcut_generated_artifacts(self):
        """CapCut 이 남기는 .bak 과 공용 경로 토큰은 결함이 아니다."""
        source = (SCRIPTS / "verify_shorts.py").read_text(encoding="utf-8")
        self.assertIn("draftpath_placeholder", source)
        self.assertIn("len(t[\"segments\"]) >= 3", source)


if __name__ == "__main__":
    unittest.main()

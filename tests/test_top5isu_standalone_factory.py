from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from _support import load_source_module_no_bytecode


ROOT = Path(__file__).resolve().parents[1]
SKILL_ROOT = ROOT / "skills" / "top5isu-shorts"
FACTORY = SKILL_ROOT / "scripts" / "create_top5isu_episode.py"
BLUEPRINT_VALIDATOR = SKILL_ROOT / "scripts" / "validate_top5isu_blueprint.py"


class Top5IsuStandaloneFactoryTests(unittest.TestCase):
    def test_profile_router_requires_explicit_top5_or_gunlimbo(self):
        module = load_source_module_no_bytecode("top5isu_factory_router", FACTORY)

        self.assertEqual(module.route_profile("TOP5 순위 쇼츠 끝까지"), "top5")
        self.assertEqual(module.route_profile("군림보 감동 쇼츠 끝까지"), "gunlimbo")
        with self.assertRaisesRegex(module.GateFail, "WAIT_USER_PROFILE"):
            module.route_profile("쇼츠 하나 만들어")
        with self.assertRaisesRegex(module.GateFail, "WAIT_USER_PROFILE"):
            module.route_profile("TOP5와 군림보 둘 다")

    def test_episode_scaffold_creates_fixed_factory_directories(self):
        module = load_source_module_no_bytecode("top5isu_factory_scaffold", FACTORY)
        with tempfile.TemporaryDirectory() as td:
            episode = module.create_episode(Path(td), "EP_001", "gunlimbo")
            expected = {
                "00_source",
                "10_analysis",
                "20_script",
                "30_audio",
                "40_assets",
                "50_capcut_project",
                "90_reports",
            }
            self.assertEqual(expected, {p.name for p in episode.iterdir() if p.is_dir()})
            state = json.loads((episode / "top5isu_episode_state.json").read_text(encoding="utf-8"))
            self.assertEqual(state["skill"], "top5isu-shorts")
            self.assertEqual(state["style_profile"], "gunlimbo")
            self.assertEqual(state["stage"], "INTAKE")
            self.assertTrue(state["standalone_factory"])
            self.assertEqual(state["external_skill_handoff"], "forbidden")

    def test_blueprint_validator_accepts_full_internal_stage_contract(self):
        module = load_source_module_no_bytecode("top5isu_blueprint", BLUEPRINT_VALIDATOR)
        blueprint = """# 설계도
## 기본 정보
style_profile: top5
## 제작 판단
standalone_factory: true
## 대본
안녕하세요. 오늘의 탑파이브 주제인데요.
## 트랙별 타임라인
| track | content |
| T1 | hook |
## 오디오 계획
TTS
## 이미지 계획
7 images
## CapCut 프로젝트
50_capcut_project
## 검증 및 보고
FINAL_REPORT
"""
        result = module.validate_blueprint_text(blueprint, "top5")
        self.assertEqual(result["top5isu_blueprint_status"], "PASS")

        with self.assertRaisesRegex(module.GateFail, "FAIL_TOP5ISU_BLUEPRINT"):
            module.validate_blueprint_text(blueprint.replace("## CapCut 프로젝트", "## 누락"), "top5")


if __name__ == "__main__":
    unittest.main()

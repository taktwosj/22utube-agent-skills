"""지시서에 실린 예시가 실제 PRE-119 validator 를 통과하는지 검사한다.

문서만 고치고 계약이 바뀌면 예시가 조용히 썩는다. 그걸 막는다.
"""
import importlib.util
import json
import re
import sys
import tempfile
import unittest
from pathlib import Path

# 설치본 스킬 안에 __pycache__ 를 만들면 다음 release activate 가
# unlisted release files 로 죽는다. import 전에 끈다.
sys.dont_write_bytecode = True


ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills" / "119-politics-longform-capcut"
BRIEF = SKILL / "references" / "pre119-togun-authoring-brief.md"
VALIDATOR = SKILL / "scripts" / "validate_pre119_handoff.py"

CARD_KEYS = [
    "order", "card_id", "card_type", "chapter_label", "chapter_title", "chapter_hook",
    "source_id", "source_range_policy", "source_in_candidate", "source_out_candidate",
    "visual_asset_ref", "visual_role", "style_profile", "narration_asset_ref",
    "narration_text", "source_audio", "narration_audio", "lower_mode",
    "lower_line1", "lower_line2", "cta_like_subscribe", "why_this_segment", "next_card",
]


def load_validator():
    spec = importlib.util.spec_from_file_location("pre119_validator", VALIDATOR)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class Pre119TogunBriefContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = BRIEF.read_text(encoding="utf-8")
        cls.validator = load_validator()

    def seed_block(self):
        blocks = re.findall(r"```\n(.*?)```", self.text, re.S)
        return next(b for b in blocks if b.lstrip().startswith("[ASSEMBLY_ONLY_SEED]")).strip()

    def test_example_seed_parses_with_the_real_validator(self):
        seed = self.seed_block()
        path = Path(tempfile.mkdtemp()) / "119_final_script.md"
        path.write_text("# 대본\n\n산문은 블록 밖에 있다.\n\n" + seed + "\n", encoding="utf-8")
        parsed = self.validator.parse_assembly_only_seed(path)
        self.assertEqual(parsed["policy"].get("execution_mode"), "ASSEMBLY_ONLY")
        self.assertTrue(parsed["cards"])

    def test_example_card_carries_every_template_key_in_order(self):
        seed = self.seed_block()
        card = seed[seed.index("[CARD]"):seed.index("[/CARD]")]
        keys = [line.split(":", 1)[0].strip() for line in card.splitlines()
                if ":" in line and not line.strip().startswith("[")]
        self.assertEqual(keys, CARD_KEYS)

    def test_example_handoff_passes_the_identity_and_field_gates(self):
        raw = re.search(r"```json\n(.*?)```", self.text, re.S).group(1)
        handoff = json.loads(raw)
        self.assertEqual(handoff["schema"], "togun-pre119-handoff-v3")
        self.assertEqual(handoff["route"], "TOGUN_PRE119_TO_119_DIRECT")
        self.assertEqual(handoff["editorial_owner"], "TOGUN_PRE119")
        self.assertEqual(handoff["source_state"], "PRE119_SOURCE_CANDIDATE")
        for key in ("episode_id", "project_name", "central_question", "selected_thesis",
                    "chapter_order", "between_image", "between_narration", "lower_mode",
                    "execution_mode", "cta_like_subscribe"):
            self.assertIn(key, handoff)
        self.assertIn(handoff["lower_mode"], {"SRT", "COMMENTARY_2LINE", "NONE", "MIXED"})
        self.assertEqual(handoff["execution_mode"], "ASSEMBLY_ONLY")
        self.assertIn(str(handoff["cta_like_subscribe"]).upper(), {"ON", "OFF"})

    def test_required_package_paths_match_the_validator(self):
        code = VALIDATOR.read_text(encoding="utf-8")
        for path in ("00_README.md", "00_source/source_packet.md",
                     "10_analysis/pre119_editorial_packet.md",
                     "20_script/119_final_script.md", "20_script/pre119_handoff.json",
                     "90_reports/source_gap_and_status.md"):
            self.assertIn(path, code, f"validator 에 없는 경로를 지시서가 요구한다: {path}")
            self.assertIn(path, self.text, f"지시서가 필수 경로를 빠뜨렸다: {path}")

    def test_author_capability_boundary_is_stated(self):
        self.assertIn("텍스트와 웹 검색만 쓴다", self.text)
        self.assertIn("영상·음성은 열지 않는다", self.text)
        self.assertIn("압축을 푼 텍스트로 받아야 한다", self.text)

    def test_hash_is_left_to_the_assembler(self):
        self.assertIn("current_final_script_sha256", self.text)
        self.assertIn("너는 파일 해시를", self.text)

    def test_terminal_card_rule_is_stated(self):
        self.assertIn("마지막 카드의 `next_card` 는 `END` 다", self.text)

    def test_montage_contract_is_carried_into_the_brief(self):
        self.assertIn("C00_HOOK_CTA", self.text)
        self.assertIn("자기 진영 인사가 자기 진영을 비판한 발언", self.text)
        self.assertIn("BODY_REUSE=", self.text)


if __name__ == "__main__":
    unittest.main()

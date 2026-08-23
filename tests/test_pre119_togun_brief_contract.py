"""지시서에 실린 예시와 검증 스크립트가 실제 계약과 맞는지 검사한다.

문서만 고치고 계약이 바뀌면 예시가 조용히 썩는다. 그걸 막는다.
"""
import hashlib
import importlib.util
import json
import re
import subprocess
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
REQUIRED_PATHS = [
    "00_README.md",
    "00_source/source_packet.md",
    "10_analysis/pre119_editorial_packet.md",
    "20_script/119_final_script.md",
    "20_script/pre119_handoff.json",
    "90_reports/source_gap_and_status.md",
]
NEWLINE = chr(10)


def load_validator():
    spec = importlib.util.spec_from_file_location("pre119_validator", VALIDATOR)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def fenced_blocks(text, fence="```"):
    """펜스로 감싼 블록의 본문만 뽑는다. 정규식 이스케이프를 피한다."""
    parts = text.split(fence)
    return [part.split(NEWLINE, 1)[1] for part in parts[1::2] if NEWLINE in part]


class Pre119TogunBriefContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = BRIEF.read_text(encoding="utf-8")
        cls.validator = load_validator()

    def seed_block(self):
        blocks = fenced_blocks(self.text)
        return next(b for b in blocks if b.lstrip().startswith("[ASSEMBLY_ONLY_SEED]")).strip()

    def handoff_block(self):
        blocks = fenced_blocks(self.text)
        return next(b for b in blocks
                    if b.lstrip().startswith("{") and "togun-pre119-handoff-v3" in b)

    def self_check_script(self):
        blocks = fenced_blocks(self.text, fence="````")
        return next(b for b in blocks if "SELF_CHECK PASS" in b)

    def build_package(self):
        """지시서의 예시만으로 유효한 package-root 를 만든다."""
        seed = self.seed_block()
        card = seed[seed.index("[CARD]"):seed.index("[/CARD]") + len("[/CARD]")]
        second = (card.replace("C00_HOOK_01", "C00_HOOK_02")
                      .replace("next_card: C00_HOOK_02", "next_card: END")
                      .replace("order: 1", "order: 2"))
        seed = seed.replace("[/ASSEMBLY_ONLY_SEED]",
                            second + NEWLINE + "[/ASSEMBLY_ONLY_SEED]")

        root = Path(tempfile.mkdtemp())
        for folder in ("20_script", "00_source", "10_analysis", "90_reports"):
            (root / folder).mkdir()
        script = root / "20_script/119_final_script.md"
        script.write_text("# 대본" + NEWLINE * 2 + "산문은 블록 밖에" + NEWLINE * 2
                          + seed + NEWLINE, encoding="utf-8")

        handoff = json.loads(self.handoff_block())
        for key in ("episode_id", "project_name", "central_question", "selected_thesis",
                    "between_image", "between_narration"):
            handoff[key] = "채움"
        handoff["chapter_order"] = ["오프닝", "본편"]
        handoff["script_lock"]["current_final_script_sha256"] = hashlib.sha256(
            script.read_bytes()).hexdigest()
        (root / "20_script/pre119_handoff.json").write_text(
            json.dumps(handoff, ensure_ascii=False, indent=2), encoding="utf-8")
        for stub in REQUIRED_PATHS:
            path = root / stub
            if not path.exists():
                path.write_text("stub" + NEWLINE, encoding="utf-8")
        return root, script

    def test_example_seed_parses_with_the_real_validator(self):
        root, script = self.build_package()
        parsed = self.validator.parse_assembly_only_seed(script)
        self.assertEqual(parsed["policy"].get("execution_mode"), "ASSEMBLY_ONLY")
        self.assertEqual(parsed["card_order"], ["C00_HOOK_01", "C00_HOOK_02"])

    def test_example_card_carries_every_template_key_in_order(self):
        seed = self.seed_block()
        card = seed[seed.index("[CARD]"):seed.index("[/CARD]")]
        keys = [line.split(":", 1)[0].strip() for line in card.splitlines()
                if ":" in line and not line.strip().startswith("[")]
        self.assertEqual(keys, CARD_KEYS)

    def test_example_handoff_passes_the_identity_and_field_gates(self):
        handoff = json.loads(self.handoff_block())
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
        for path in REQUIRED_PATHS:
            self.assertIn(path, code, f"validator 에 없는 경로를 지시서가 요구한다: {path}")
            self.assertIn(path, self.text, f"지시서가 필수 경로를 빠뜨렸다: {path}")

    def test_author_capability_boundary_is_stated(self):
        self.assertIn("텍스트, 웹 검색, 코드 실행을 쓴다", self.text)
        self.assertIn("영상과 음성은 열지 못한다", self.text)
        self.assertNotIn("너는 zip 을 열 수 없다", self.text)

    def test_author_computes_the_script_hash_itself(self):
        self.assertIn("current_final_script_sha256", self.text)
        self.assertIn("네가 직접 계산해서 채운다", self.text)
        self.assertIn("한 바이트도 고치지 마라", self.text)

    def test_delivery_is_a_drive_zip_shaped_like_the_package_root(self):
        self.assertIn("## 전달 — Google Drive", self.text)
        self.assertIn("zip 을 풀면 곧바로", self.text)
        self.assertIn("최상위에 폴더를 한 겹 더 감싸지 마라", self.text)
        self.assertIn("shorts_candidates.md", self.text)
        self.assertNotIn("텍스트로만 전달한다. ZIP 금지", self.text)

    def test_self_check_script_is_fenced_so_inner_backticks_survive(self):
        # 스크립트 본문에 ``` 가 들어 있어서 3중 펜스로 감싸면 블록이 중간에 끊긴다.
        self.assertIn("````python", self.text)
        self.assertIn("SELF_CHECK PASS", self.self_check_script())

    def test_self_check_script_passes_a_good_package(self):
        root, _ = self.build_package()
        (root / "_check.py").write_text(self.self_check_script(), encoding="utf-8")
        done = subprocess.run([sys.executable, "-B", "_check.py"], cwd=root,
                              capture_output=True, text=True, encoding="utf-8")
        self.assertEqual(done.returncode, 0, done.stderr[-500:])
        self.assertIn("SELF_CHECK PASS", done.stdout)

    def test_self_check_script_catches_the_defects_it_exists_for(self):
        root, script = self.build_package()
        (root / "_check.py").write_text(self.self_check_script(), encoding="utf-8")
        good = script.read_text(encoding="utf-8")
        cases = {
            "정책줄 삭제": good.replace("execution_mode: ASSEMBLY_ONLY" + NEWLINE, "", 1),
            "시드에 산문": good.replace("lower_mode: SRT",
                                   "lower_mode: SRT" + NEWLINE + "설명 문장", 1),
            "끊긴 next_card": good.replace("next_card: END", "next_card: C99_NOPE"),
            "SHA 불일치": good + NEWLINE + "대본 수정" + NEWLINE,
        }
        for label, broken in cases.items():
            with self.subTest(label=label):
                script.write_text(broken, encoding="utf-8")
                done = subprocess.run([sys.executable, "-B", "_check.py"], cwd=root,
                                      capture_output=True, text=True, encoding="utf-8")
                self.assertEqual(done.returncode, 1, f"{label} 을 잡지 못했다")
        script.write_text(good, encoding="utf-8")

    def test_terminal_card_rule_is_stated(self):
        self.assertIn("마지막 카드의 `next_card` 는 `END` 다", self.text)

    def test_montage_contract_is_carried_into_the_brief(self):
        self.assertIn("C00_HOOK_CTA", self.text)
        self.assertIn("자기 진영 인사가 자기 진영을 비판한 발언", self.text)
        self.assertIn("BODY_REUSE=", self.text)

    def test_subtitle_gap_analysis_is_delegated_to_the_author(self):
        self.assertIn("무자막 구간", self.text)
        self.assertIn("2초 이상", self.text)
        self.assertIn("90% 미만", self.text)


if __name__ == "__main__":
    unittest.main()

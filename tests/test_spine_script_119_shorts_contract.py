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


def test_short_builder_normalizes_audio_and_opens_with_sfx():
    """쇼츠 빌더가 소리 나는 세그먼트마다 음량 노멀라이즈를 켜고,
    자막 애니메이션을 0.1초로 맞추고, 시작 순간에 효과음을 깐다."""
    src = (SCRIPTS / "build_short.py").read_text(encoding="utf-8")
    assert "def attach_loudness" in src
    assert '"target_loudness": target' in src
    assert '"enable": True' in src
    assert "self.attach_loudness(seg, mat, dur)" in src
    assert "def set_text_anim" in src
    assert "duration=100_000" in src
    assert "for a in [0.0] + list(starts):" in src


def test_build_assets_keeps_captions_on_sentence_boundaries():
    """컷 끝에서 말이 문장 중간에 끊겨 보이지 않게 한다.

    창 밖으로 반쯤 걸친 cue 는 버리고, 마지막 조각에 다음 문장의 첫 마디가
    매달려 있으면 잘라 낸다. 회차 정의의 구간이 바뀌면 예전 컷을 다시 자른다.
    """
    src = (SCRIPTS / "build_assets.py").read_text(encoding="utf-8")
    assert "CUE_EDGE" in src
    assert "if s < t_in - CUE_EDGE or e > t_out + CUE_EDGE:" in src
    assert "SENT_END" in src
    assert "cut.json" in src
    assert "if dst.exists() and have != want:" in src


def test_short_body_runs_faster_than_source():
    """쇼츠 본편은 1.2배로 돌린다. 나레이션은 건드리지 않는다."""
    common = (SCRIPTS / "_common.py").read_text(encoding="utf-8")
    assert "SHORT_SPEED = 1.2" in common
    cut = (SCRIPTS / "cut_shorts.py").read_text(encoding="utf-8")
    assert "setpts=PTS/{SHORT_SPEED}" in cut
    assert "atempo={SHORT_SPEED}" in cut
    # 자막 시간도 같이 당겨야 말과 어긋나지 않는다
    assert "/ SHORT_SPEED" in cut
    build = (SCRIPTS / "build_short.py").read_text(encoding="utf-8")
    assert "a / SHORT_SPEED" in build


def test_short_project_carries_no_dead_media_path():
    """근본에서 물려받은 죽은 미디어 경로를 미디어 목록에서 걷어 낸다."""
    build = (SCRIPTS / "build_short.py").read_text(encoding="utf-8")
    assert "def clean_meta" in build
    assert "draft_meta_info.json" in build
    assert "./Resources/media/" in build


def test_plate_track_found_by_name_not_only_path():
    """근본을 CapCut 에서 한 번 열면 배경판 경로가 캐시 해시로 바뀐다."""
    build = (SCRIPTS / "build_short.py").read_text(encoding="utf-8")
    assert 'material_name' in build
    assert '"jungch.png" in tag' in build


def test_shorts_contract_documents_intro_and_outro():
    """쇼츠는 롱폼 유입이 목적이라 도입 한 줄과 마무리 두 줄을 뺀다."""
    doc = SKILL.read_text(encoding="utf-8")
    assert "SHORT_SPEED" in doc
    assert "더 자세한 내용은 아래 영상에서 보실 수 있습니다" in doc
    assert "구독과 좋아요 부탁드립니다" in doc
    assert "1080×1415" in doc

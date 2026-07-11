import json
from pathlib import Path
import tempfile
import unittest

from _support import load_source_module_no_bytecode


ROOT = Path(__file__).resolve().parents[1]
TIKITAKA = ROOT / "skills" / "00-tikitaka" / "SKILL.md"
PRODUCTION = ROOT / "skills" / "000short-production-agent" / "SKILL.md"
LAYOUT_CONTRACT = ROOT / "skills" / "000short-production-agent" / "03_CAPCUT_LAYOUT_CONTRACT.md"
CAPTION_SCHEMA = ROOT / "skills" / "000short-production-agent" / "schemas" / "caption_beat_map.schema.json"
CAPTION_VALIDATOR = ROOT / "skills" / "000short-production-agent" / "scripts" / "validate_caption_beat_map.py"
BUILDER = (
    ROOT.parent
    / "OneDrive"
    / "22utube"
    / "22factory_20260628"
    / "00_asset_tools"
    / "tools"
    / "build_capcut_from_tikitaka_v3.py"
)
TIKITAKA_HARNESS = ROOT / "skills" / "00-tikitaka" / "scripts" / "tikitaka_harness_runner.py"


def test_tikitaka_handoff_declares_caption_beat_map_authority():
    text = TIKITAKA.read_text(encoding="utf-8")
    for token in (
        "caption_beat_map",
        "CAPTION_BEAT_MAP_HANDOFF",
        "caption_role",
        "audio_basis",
        "caption_profiles_v2",
        "fixed_lower_safe_zone_v1",
    ):
        assert token in text
    harness = TIKITAKA_HARNESS.read_text(encoding="utf-8")
    assert '"caption_beat_map": "caption_beat_map.json"' in harness
    assert "CAPTION_BEAT_MAP_REQUIRED" in harness
    assert 'data.get("profile_version") != "caption_profiles_v2"' in harness
    assert 'data.get("face_avoidance") != "fixed_lower_safe_zone_v1"' in harness


def test_production_contract_declares_fixed_caption_profiles():
    text = (PRODUCTION.read_text(encoding="utf-8") + LAYOUT_CONTRACT.read_text(encoding="utf-8"))
    for token in (
        "CAPTION_BEAT_MAP_REQUIRED",
        "TTS (T3): y=-900",
        "화자발언 (T4/T5): y=-500",
        "( ) 상황설명 (T6): y=700",
        "원본 영상 V1: video_scale=1.20",
        "caption_profiles_v2",
        "max_chars_per_line=10",
        "max_lines=1",
        "fixed_lower_safe_zone_v1",
    ):
        assert token in text


def test_caption_beat_map_schema_requires_timing_and_layout_contract():
    schema = json.loads(CAPTION_SCHEMA.read_text(encoding="utf-8"))
    assert schema["properties"]["profile_version"]["const"] == "caption_profiles_v2"
    assert schema["properties"]["face_avoidance"]["const"] == "fixed_lower_safe_zone_v1"
    beat_required = schema["properties"]["beats"]["items"]["required"]
    assert set(
        (
            "beat_id",
            "edit_id",
            "text",
            "start_sec",
            "end_sec",
            "caption_role",
            "audio_basis",
            "max_chars_per_line",
            "max_lines",
            "y",
            "timing_source",
        )
    ).issubset(set(beat_required))
    beat_properties = schema["properties"]["beats"]["items"]["properties"]
    assert beat_properties["max_chars_per_line"]["const"] == 10
    assert beat_properties["max_lines"]["const"] == 1


def test_builder_uses_caption_beat_map_and_new_profiles():
    text = BUILDER.read_text(encoding="utf-8")
    for token in (
        "caption_beat_map",
        "max_chars_per_line",
        "max_lines",
        "CAPTION_BEAT_MAP_REQUIRED",
        "CAPTION_LAYOUT_PROFILES",
        "VIDEO_SCALE = 1.20",
        "apply_caption_layout",
        "apply_video_scale",
    ):
        assert token in text
    for token in ("implemented_segments", "protected_fields_preserved", "source_timeline_design_path"):
        assert token in text


def test_builder_profile_values_are_machine_readable():
    module = load_source_module_no_bytecode("caption_builder", BUILDER)

    assert module.caption_layout_profile("tts_narration") == {
        "y": -900,
        "max_chars_per_line": 10,
        "max_lines": 1,
    }
    assert module.caption_layout_profile("speaker_quote")["y"] == -500
    assert module.caption_layout_profile("situation_caption")["y"] == 700
    assert module.VIDEO_SCALE == 1.20


def test_builder_splits_tts_into_one_line_sequential_beats():
    module = load_source_module_no_bytecode("caption_builder_split", BUILDER)
    chunks = module.split_caption_window("가" * 31, 0.0, 3.0, max_chars=10, max_lines=1)
    assert len(chunks) == 4
    assert all("\n" not in chunk[0] for chunk in chunks)
    assert all(len(chunk[0]) <= 10 for chunk in chunks)
    assert all(previous[2] == current[1] for previous, current in zip(chunks, chunks[1:]))


def test_builder_applies_video_scale_and_caption_y():
    module = load_source_module_no_bytecode("caption_builder_layout", BUILDER)
    video = {"clip": {"scale": {"x": 1.0, "y": 1.0}}}
    module.apply_video_scale(video)
    assert video["clip"]["scale"] == {"x": 1.2, "y": 1.2}
    text = {"clip": {"transform": {"x": 0, "y": 0}}}
    module.apply_caption_layout(text, module.caption_layout_profile("speaker_quote"))
    assert text["clip"]["transform"]["y"] == -500


def test_caption_validator_rejects_wrong_profile_position():
    import json

    module = load_source_module_no_bytecode("caption_validator", CAPTION_VALIDATOR)
    payload = {
        "status": "PASS",
        "profile_version": "caption_profiles_v2",
        "video_scale": 1.2,
        "face_avoidance": "fixed_lower_safe_zone_v1",
        "beats": [
            {
                "beat_id": "E1_B01",
                "edit_id": "E1",
                "text": "테스트",
                "start_sec": 0.0,
                "end_sec": 1.0,
                "caption_role": "speaker_quote",
                "audio_basis": "source_speech",
                "max_chars_per_line": 10,
                "max_lines": 1,
                "y": -900,
                "timing_source": "source_word_timestamp",
            }
        ],
    }
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "caption_beat_map.json"
        path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
        try:
            module.validate(path)
        except module.GateFail as exc:
            assert "FAIL_CAPTION_Y_POSITION" in str(exc)
        else:
            raise AssertionError("validator accepted wrong speaker y position")


class CaptionAssemblyContractTests(unittest.TestCase):
    def test_tikitaka_handoff_declares_caption_beat_map_authority(self):
        test_tikitaka_handoff_declares_caption_beat_map_authority()

    def test_production_contract_declares_fixed_caption_profiles(self):
        test_production_contract_declares_fixed_caption_profiles()

    def test_caption_beat_map_schema_requires_timing_and_layout_contract(self):
        test_caption_beat_map_schema_requires_timing_and_layout_contract()

    def test_builder_uses_caption_beat_map_and_new_profiles(self):
        test_builder_uses_caption_beat_map_and_new_profiles()

    def test_builder_profile_values_are_machine_readable(self):
        test_builder_profile_values_are_machine_readable()

    def test_builder_splits_tts_into_one_line_sequential_beats(self):
        test_builder_splits_tts_into_one_line_sequential_beats()

    def test_builder_applies_video_scale_and_caption_y(self):
        test_builder_applies_video_scale_and_caption_y()

    def test_caption_validator_rejects_wrong_profile_position(self):
        test_caption_validator_rejects_wrong_profile_position()

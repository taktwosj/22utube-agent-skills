from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
import zipfile
from pathlib import Path

from _support import load_source_module_no_bytecode


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "skills" / "top5isu-shorts" / "scripts"
CONTRACT_VALIDATOR = SCRIPTS / "validate_top5isu_contract.py"
PACKAGE_VALIDATOR = SCRIPTS / "validate_top5isu_package.py"
DRAFT_VALIDATOR = SCRIPTS / "validate_top5isu_capcut_draft.py"


def valid_contract() -> dict:
    return {
        "contract_version": "top5isu_build_contract_v1",
        "template_profile": "top5isu_v1",
        "style_profile": "top5",
        "fallback_allowed": False,
        "clone_required": True,
        "root_template_mutation": False,
        "fresh_project_id_required": True,
        "fresh_timeline_id_required": True,
        "archive_file": "top5isu_CAPCUT.zip",
        "archive_sha256": "a" * 64,
        "manifest_sha256": "b" * 64,
        "packaged_file_count": 3,
        "required_tracks": ["IMAGE_EFFECT_PRESETS", "TTS", "T2", "T1", "LOGO"],
        "image_effect_count_required": 7,
        "image_ui_y": -600,
        "image_json_transform_y": -0.15625,
        "logo_full_duration": True,
        "sample_media_policy": "replace_all",
        "audio_policy": {
            "speaker_segments_preserved": False,
            "speaker_mute_forbidden": False,
        },
        "audio_normalization": {
            "method": "ffmpeg_loudnorm",
            "target_integrated_lufs": -14,
            "preimport_measurement_required": True,
            "final_export_remeasure_required": True,
        },
        "portable_manifest_paths": True,
        "bak_allowed_in_portable_package": False,
    }


def minimal_content(sample_name: str = "episode_01.png", image_y: float = -0.15625) -> dict:
    duration = 20_250_000
    videos = []
    image_segments = []
    for index in range(7):
        material_id = f"image-{index}"
        videos.append(
            {
                "id": material_id,
                "type": "photo",
                "path": f"##_draftpath_placeholder_TEST_##/Resources/media/{sample_name if index == 0 else f'episode_{index + 1:02d}.png'}",
            }
        )
        image_segments.append(
            {
                "material_id": material_id,
                "clip": {"transform": {"x": 0.0, "y": image_y}},
                "target_timerange": {"start": index * 2_000_000, "duration": 2_000_000},
                "extra_material_refs": [f"animation-{index}"],
            }
        )
    videos.append(
        {
            "id": "logo-video",
            "type": "photo",
            "path": "##_draftpath_placeholder_TEST_##/Resources/media/jungboitsu.png",
        }
    )
    return {
        "name": "episode",
        "duration": duration,
        "canvas_config": {"ratio": "9:16", "width": 1080, "height": 1920},
        "materials": {"videos": videos, "audios": [], "loudnesses": []},
        "tracks": [
            {"name": "IMAGE_EFFECT_PRESETS", "type": "video", "segments": image_segments},
            {"name": "TTS", "type": "text", "segments": [{}]},
            {"name": "T2", "type": "text", "segments": [{}]},
            {"name": "T1", "type": "text", "segments": [{}]},
            {
                "name": "LOGO",
                "type": "video",
                "segments": [
                    {
                        "material_id": "logo-video",
                        "target_timerange": {"start": 0, "duration": duration},
                    }
                ],
            },
        ],
    }


def write_package(
    template_dir: Path,
    include_bak: bool = False,
    include_effect_build_path: bool = False,
) -> Path:
    archive = template_dir / "top5isu_CAPCUT.zip"
    content = minimal_content(sample_name="template_sample.png")
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("top5isu/draft_content.json", json.dumps(content))
        zf.writestr("top5isu/draft_meta_info.json", json.dumps({"draft_name": "top5isu"}))
        zf.writestr("top5isu/Resources/media/jungboitsu.png", b"png")
        if include_bak:
            zf.writestr("top5isu/draft_content.json.bak", b"backup")
        if include_effect_build_path:
            zf.writestr(
                "top5isu/Resources/effects/example/AmazingFeature/lua-meta.json",
                json.dumps({"build_source": "/Users/effect-developer/sdk/source.lua"}),
            )
    sha = hashlib.sha256(archive.read_bytes()).hexdigest()
    manifest = {
        "status": "PASS_TOP5ISU_PORTABLE_ROOT_TEMPLATE",
        "template_profile": "top5isu",
        "reference_project_name": "top5isu",
        "archive_file": archive.name,
        "tracks": ["IMAGE_EFFECT_PRESETS", "TTS", "T2", "T1", "LOGO"],
        "image_effect_segments": 7,
        "packaged_file_count": 3 + int(include_bak) + int(include_effect_build_path),
        "bak_remaining_in_package": 0,
        "absolute_user_path_refs_remaining": 0,
        "archive_sha256": sha,
    }
    (template_dir / "template_manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    return archive


class Top5IsuValidatorTests(unittest.TestCase):
    def test_valid_contract_passes(self):
        module = load_source_module_no_bytecode("top5isu_contract_valid", CONTRACT_VALIDATOR)
        result = module.validate_top5isu_contract(valid_contract())
        self.assertEqual(result["top5isu_contract_status"], "PASS")

    def test_contract_rejects_fallback_and_wrong_coordinate(self):
        module = load_source_module_no_bytecode("top5isu_contract_invalid", CONTRACT_VALIDATOR)
        contract = valid_contract()
        contract["fallback_allowed"] = True
        with self.assertRaisesRegex(module.GateFail, "FAIL_SHRT_WHITE_FALLBACK_FORBIDDEN"):
            module.validate_top5isu_contract(contract)

        contract = valid_contract()
        contract["image_json_transform_y"] = -600
        with self.assertRaisesRegex(module.GateFail, "FAIL_TOP5ISU_COORDINATE_LOCK"):
            module.validate_top5isu_contract(contract)

    def test_gunlimbo_contract_requires_preserved_speaker_audio(self):
        module = load_source_module_no_bytecode("top5isu_contract_gunlimbo", CONTRACT_VALIDATOR)
        contract = valid_contract()
        contract["style_profile"] = "gunlimbo"
        with self.assertRaisesRegex(module.GateFail, "FAIL_SPEAKER_AUDIO_POLICY"):
            module.validate_top5isu_contract(contract)

    def test_package_integrity_passes_and_tampering_fails(self):
        module = load_source_module_no_bytecode("top5isu_package", PACKAGE_VALIDATOR)
        with tempfile.TemporaryDirectory() as td:
            template_dir = Path(td)
            archive = write_package(template_dir)
            result = module.validate_top5isu_package(template_dir)
            self.assertEqual(result["top5isu_package_status"], "PASS")

            archive.write_bytes(archive.read_bytes() + b"tampered")
            with self.assertRaisesRegex(module.GateFail, "FAIL_TOP5ISU_ARCHIVE_INTEGRITY"):
                module.validate_top5isu_package(template_dir)

    def test_package_rejects_bak_even_when_manifest_claims_zero(self):
        module = load_source_module_no_bytecode("top5isu_package_bak", PACKAGE_VALIDATOR)
        with tempfile.TemporaryDirectory() as td:
            template_dir = Path(td)
            write_package(template_dir, include_bak=True)
            with self.assertRaisesRegex(module.GateFail, "FAIL_TOP5ISU_PORTABLE_PACKAGE"):
                module.validate_top5isu_package(template_dir)

    def test_package_ignores_vendor_effect_build_paths(self):
        module = load_source_module_no_bytecode("top5isu_package_effect_meta", PACKAGE_VALIDATOR)
        with tempfile.TemporaryDirectory() as td:
            template_dir = Path(td)
            write_package(template_dir, include_effect_build_path=True)
            result = module.validate_top5isu_package(template_dir)
            self.assertEqual(result["top5isu_package_status"], "PASS")

    def test_draft_passes_and_rejects_sample_residue_or_wrong_y(self):
        module = load_source_module_no_bytecode("top5isu_draft", DRAFT_VALIDATOR)
        with tempfile.TemporaryDirectory() as td:
            draft = Path(td)
            (draft / "draft_content.json").write_text(
                json.dumps(minimal_content()), encoding="utf-8"
            )
            result = module.validate_top5isu_capcut_draft(draft, "top5", None)
            self.assertEqual(result["top5isu_capcut_draft_status"], "PASS")

            (draft / "draft_content.json").write_text(
                json.dumps(minimal_content(sample_name="leehaneul_01.png")), encoding="utf-8"
            )
            with self.assertRaisesRegex(module.GateFail, "FAIL_TOP5ISU_SAMPLE_MEDIA_REMAINS"):
                module.validate_top5isu_capcut_draft(draft, "top5", None)

            (draft / "draft_content.json").write_text(
                json.dumps(minimal_content(image_y=-600)), encoding="utf-8"
            )
            with self.assertRaisesRegex(module.GateFail, "FAIL_TOP5ISU_COORDINATE_LOCK"):
                module.validate_top5isu_capcut_draft(draft, "top5", None)

    def test_gunlimbo_draft_requires_unmuted_speaker_manifest(self):
        module = load_source_module_no_bytecode("top5isu_draft_gunlimbo", DRAFT_VALIDATOR)
        with tempfile.TemporaryDirectory() as td:
            draft = Path(td)
            (draft / "draft_content.json").write_text(
                json.dumps(minimal_content()), encoding="utf-8"
            )
            with self.assertRaisesRegex(module.GateFail, "FAIL_SPEAKER_SEGMENT_MUTED"):
                module.validate_top5isu_capcut_draft(
                    draft,
                    "gunlimbo",
                    {"speaker_segments": [{"start_us": 0, "duration_us": 1_000_000, "muted": True}]},
                )


if __name__ == "__main__":
    unittest.main()

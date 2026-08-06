import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace


SKILL_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = SKILL_ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

from validate_capcut_project import validate_root_layout_contract


ARCHIVE_SHA256 = "4af774a3ff8b539d1ce3121998f444cf9063a0d5d6f1ddb9a2a75acbcf84bd4f"
WHITE_NAME = "transparent_center_white_1080x1920.png"


def _model(tracks, materials=None):
    return SimpleNamespace(tracks=tracks, materials=materials or {})


def _track(track_id, track_type, segments, name="misleading-name"):
    return {"id": track_id, "type": track_type, "name": name, "segments": segments}


def _contract(tracks, text_styles=None, tolerances=None):
    return {
        "archive_sha256": ARCHIVE_SHA256,
        "tracks": tracks,
        "text_styles": text_styles or {},
        "tolerances": tolerances
        or {"position_px": None, "size_px": None, "duration_us": None, "font_size": None},
    }


class RootLayoutContractValidatorTest(unittest.TestCase):
    def test_required_track_identity_uses_track_id_and_type_not_name(self):
        contract = _contract(
            [
                {
                    "track_id": "required-video",
                    "type": "video",
                    "role": "VIDEO",
                    "requirement": "REQUIRED",
                    "segment_rule": "근본은 세그먼트 1개.",
                },
                {
                    "track_id": "optional-text",
                    "type": "text",
                    "role": "STATE",
                    "requirement": "UNDETERMINED",
                    "segment_rule": "근본은 세그먼트 1개.",
                },
            ]
        )
        model = _model([_track("required-video", "video", [{"id": "v1"}], name="")])

        self.assertEqual(validate_root_layout_contract(model, contract, ARCHIVE_SHA256), [])

        wrong_id = _model([_track("wrong-id", "video", [{"id": "v1"}], name="VIDEO")])
        self.assertEqual(
            [error["code"] for error in validate_root_layout_contract(wrong_id, contract, ARCHIVE_SHA256)],
            ["ROOT_REQUIRED_TRACK_MISSING"],
        )

    def test_required_track_segment_count_comes_from_segment_rule(self):
        contract = _contract(
            [
                {
                    "track_id": "required-video",
                    "type": "video",
                    "role": "VIDEO",
                    "requirement": "REQUIRED",
                    "segment_rule": "근본은 세그먼트 1개(target_timerange start=0 duration=550000).",
                }
            ]
        )
        model = _model(
            [_track("required-video", "video", [{"id": "v1"}, {"id": "v2"}])]
        )

        errors = validate_root_layout_contract(model, contract, ARCHIVE_SHA256)

        self.assertEqual([error["code"] for error in errors], ["ROOT_REQUIRED_TRACK_SEGMENT_COUNT_MISMATCH"])
        self.assertEqual(errors[0]["expected"], 1)
        self.assertEqual(errors[0]["actual"], 2)

    def test_screen_white_requires_an_actual_material_reference(self):
        contract = _contract(
            [
                {
                    "track_id": "screen-white",
                    "type": "video",
                    "role": "SCREEN_WHITE",
                    "requirement": "REQUIRED",
                    "segment_rule": "근본은 세그먼트 1개.",
                    "referenced_assets": [WHITE_NAME],
                }
            ]
        )
        segment = {"id": "white", "material_id": "white-material"}
        wrong_material = {
            "videos": [
                {
                    "id": "white-material",
                    "type": "video",
                    "path": "##_draftpath_placeholder_x_##/Resources/media/not-white.png",
                }
            ]
        }
        model = _model([_track("screen-white", "video", [segment])], wrong_material)

        self.assertEqual(
            [error["code"] for error in validate_root_layout_contract(model, contract, ARCHIVE_SHA256)],
            ["ROOT_SCREEN_WHITE_REFERENCE_MISSING"],
        )

        same_name_wrong_folder = {
            "videos": [
                {
                    "id": "white-material",
                    "type": "video",
                    "path": f"##_draftpath_placeholder_x_##/other/{WHITE_NAME}",
                }
            ]
        }
        model = _model([_track("screen-white", "video", [segment])], same_name_wrong_folder)
        self.assertEqual(
            [error["code"] for error in validate_root_layout_contract(model, contract, ARCHIVE_SHA256)],
            ["ROOT_SCREEN_WHITE_REFERENCE_MISSING"],
        )

        right_material = {
            "videos": [
                {
                    "id": "white-material",
                    "type": "video",
                    "path": f"##_draftpath_placeholder_x_##/Resources/media/{WHITE_NAME}",
                }
            ]
        }
        model = _model([_track("screen-white", "video", [segment])], right_material)
        self.assertEqual(validate_root_layout_contract(model, contract, ARCHIVE_SHA256), [])

    def test_text_style_uses_exact_values_when_tolerance_is_null(self):
        contract = _contract(
            [
                {
                    "track_id": "title",
                    "type": "text",
                    "role": "T1",
                    "requirement": "UNDETERMINED",
                    "segment_rule": "근본은 세그먼트 1개.",
                }
            ],
            text_styles={
                "T1": {
                    "track_index": 7,
                    "font_size": 18.0,
                    "text_color_hex": "#ec1d1d",
                    "alignment": 1,
                    "letter_spacing": 0.0,
                    "line_spacing": 0.02,
                    "fixed_width": -1.0,
                    "fixed_height": -1.0,
                    "line_max_width": 0.82,
                    "clip_transform_raw": {"x": 0.0, "y": 0.6145124716553287},
                }
            },
        )
        material = {
            "id": "title-material",
            "type": "text",
            "font_size": 18.01,
            "text_color": "#ec1d1d",
            "alignment": 1,
            "letter_spacing": 0.0,
            "line_spacing": 0.02,
            "fixed_width": -1.0,
            "fixed_height": -1.0,
            "line_max_width": 0.82,
        }
        segment = {
            "id": "title-segment",
            "material_id": "title-material",
            "clip": {"transform": {"x": 0.0, "y": 0.6145124716553287}},
        }
        model = _model([_track("title", "text", [segment])], {"texts": [material]})

        errors = validate_root_layout_contract(model, contract, ARCHIVE_SHA256)

        self.assertEqual([error["code"] for error in errors], ["ROOT_TEXT_STYLE_MISMATCH"])
        self.assertEqual(errors[0]["field"], "font_size")

    def test_text_style_honors_font_tolerance_and_empty_policy(self):
        contract = _contract(
            [
                {
                    "track_id": "title",
                    "type": "text",
                    "role": "T1",
                    "requirement": "OPTIONAL_INTENTIONALLY_EMPTY",
                    "segment_rule": "근본은 세그먼트 1개.",
                }
            ],
            text_styles={
                "T1": {
                    "track_index": 7,
                    "font_size": 18.0,
                    "clip_transform_raw": {"x": 0.0, "y": 0.6},
                }
            },
            tolerances={"position_px": 0.02, "size_px": None, "duration_us": None, "font_size": 0.02},
        )
        self.assertEqual(validate_root_layout_contract(_model([]), contract, ARCHIVE_SHA256), [])

        material = {"id": "title-material", "type": "text", "font_size": 18.01}
        segment = {
            "id": "title-segment",
            "material_id": "title-material",
            "clip": {"transform": {"x": 0.0, "y": 0.6}},
        }
        model = _model([_track("title", "text", [segment])], {"texts": [material]})
        self.assertEqual(validate_root_layout_contract(model, contract, ARCHIVE_SHA256), [])

    def test_archive_sha256_is_part_of_track_identity(self):
        contract = _contract(
            [
                {
                    "track_id": "required-video",
                    "type": "video",
                    "role": "VIDEO",
                    "requirement": "REQUIRED",
                    "segment_rule": "근본은 세그먼트 1개.",
                }
            ]
        )
        model = _model([_track("required-video", "video", [{"id": "v1"}])])

        errors = validate_root_layout_contract(model, contract, "0" * 64)

        self.assertEqual(errors[0]["code"], "ROOT_ARCHIVE_SHA_MISMATCH")


if __name__ == "__main__":
    unittest.main()

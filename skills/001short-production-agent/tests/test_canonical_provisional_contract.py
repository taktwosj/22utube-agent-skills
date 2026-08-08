import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch


SKILL = Path(__file__).resolve().parents[1]
SCRIPTS = SKILL / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import build_episode_capcut as builder
import validate_design_lock
import validate_prebuild
import validate_capcut_project
from track_contract import CANONICAL_TRACKS, LOGICAL_ROLE_BY_TRACK, TRACK_LAYOUT


class CanonicalProvisionalContractTest(unittest.TestCase):
    def test_track_contract_has_exact_protocol_tools_builder_validator_parity(self):
        protocol = json.loads((SKILL / "protocol.json").read_text(encoding="utf-8"))
        tools = json.loads((SKILL / "tools.json").read_text(encoding="utf-8"))
        mapping = tools["capcut_preflight"]["track_mapping"]
        self.assertEqual(protocol["track_layout"], TRACK_LAYOUT)
        self.assertEqual(protocol["canonical_tracks"], list(CANONICAL_TRACKS))
        self.assertEqual(mapping["profile"], TRACK_LAYOUT)
        self.assertEqual(mapping["required"], list(CANONICAL_TRACKS))
        self.assertEqual([row["id"] for row in tools["production_tools"]], list(CANONICAL_TRACKS))
        self.assertEqual(tuple(builder.ROLE_BY_TRACK), CANONICAL_TRACKS)
        self.assertEqual(len(LOGICAL_ROLE_BY_TRACK), len(CANONICAL_TRACKS))

    def test_root_contract_must_be_workspace_relative_and_v2(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            with self.assertRaisesRegex(ValueError, "ROOT_CONTRACT_PATH_MUST_BE_WORKSPACE_RELATIVE"):
                builder._bind_portable_root_contract({
                    "root_contract_path": str(root / "root_contract.json"),
                    "workspace_root": str(root), "root_profile": "home_windows",
                })
            with patch.object(builder.resolve_shorts_capcut_root, "resolve_root_contract", return_value={
                "profile": "home_windows", "template_profile": "shrt_white_base_v1",
                "archive_sha256": "0" * 64, "archive": str(root / "root.zip"),
            }):
                with self.assertRaisesRegex(ValueError, "ROOT_CONTRACT_V2_PROFILE_REQUIRED"):
                    builder._bind_portable_root_contract({
                        "root_contract_path": "root_contract.json",
                        "workspace_root": str(root), "root_profile": "home_windows",
                    })

    def test_only_root_and_direct_timeline_drafts_are_primary(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            root_content = root / "draft_content.json"
            direct = root / "Timelines" / "main" / "draft_content.json"
            nested = root / "Timelines" / "main" / "subdraft" / "draft_content.json"
            for path, count in ((root_content, 15), (direct, 15), (nested, 1)):
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(json.dumps({"tracks": [{} for _ in range(count)]}), encoding="utf-8")
            documents = list(builder._documents(root))
            self.assertEqual([path for path, _ in documents], [root_content, direct])

    def test_protocol_has_one_v2_stage07_and_a12_empty_contract(self):
        protocol = json.loads((SKILL / "protocol.json").read_text(encoding="utf-8"))
        stage07 = next(row for row in protocol["stages"] if row["id"] == "07")
        self.assertEqual(protocol["track_layout"], "shrt_white_base_v2_15")
        self.assertEqual(stage07["produces"], [
            "30_audio_srt/audio_lock.json",
            "30_audio_srt/caption_lock.json",
            "30_audio_srt/final.srt",
        ])
        self.assertEqual(protocol["anchors"]["A12"], "reserved empty")

    def test_source_provisional_resolver_uses_source_identity_not_clean_video(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source = root / "source.mp4"; source.write_bytes(b"source")
            identity = root / "source_identity.json"
            import hashlib
            identity.write_text(json.dumps({
                "episode_id": "EP", "media_path": "source.mp4",
                "media_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
            }), encoding="utf-8")
            resolved = builder.resolve_visual_input({
                "visual_asset_mode": "SOURCE_VIDEO_PROVISIONAL",
                "source_identity_path": str(identity),
            })
            self.assertEqual(resolved["video_input_path"], source.resolve())
            self.assertEqual(resolved["video_asset_key"], "source_video")
            self.assertFalse(resolved["upload_ready"])
            self.assertNotIn("clean_video", resolved["resource_name"])
            source.write_bytes(b"changed")
            with self.assertRaisesRegex(RuntimeError, "SOURCE_PROVISIONAL_SHA_MISMATCH"):
                builder.resolve_visual_input({
                    "visual_asset_mode": "SOURCE_VIDEO_PROVISIONAL",
                    "source_identity_path": str(identity),
                })

    def test_source_provisional_prebuild_does_not_require_vmake(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source = root / "source.mp4"; template = root / "root.zip"
            source.write_bytes(b"source"); template.write_bytes(b"template")
            import hashlib
            source_sha = hashlib.sha256(source.read_bytes()).hexdigest()
            manifest = root / "build_manifest.json"
            manifest.write_text(json.dumps({
                "schema_version": "001short-build-manifest-v1", "episode_id": "EP",
                "visual_asset_mode": "SOURCE_VIDEO_PROVISIONAL",
                "source": {"path": str(source), "sha256": source_sha, "duration_us": 2_000_000},
                "template": {"root_name": "shrt white", "root_zip_path": str(template),
                             "root_zip_sha256": hashlib.sha256(template.read_bytes()).hexdigest()},
                "urakkai": {"production_type": "URAKKAI", "target_duration_us": 2_000_000,
                             "reorder_required": True, "locked_permutation": ["C2", "C1"],
                             "video_clips": [
                                 {"clip_id": "C2", "source_sha256": source_sha,
                                  "source_range_us": [1_000_000, 2_000_000], "target_range_us": [0, 1_000_000]},
                                 {"clip_id": "C1", "source_sha256": source_sha,
                                  "source_range_us": [0, 1_000_000], "target_range_us": [1_000_000, 2_000_000]},
                             ]},
                "source_audio": [
                    {"clip_id": "C2", "mode": "mute"},
                    {"clip_id": "C1", "mode": "mute"},
                ],
            }), encoding="utf-8")
            self.assertEqual(validate_prebuild.validate_prebuild(manifest)["status"], "PASS")

    def test_no_state_episode_is_legal(self):
        config = {
            "duration_us": 1_000_000, "state_cues": [], "T1": "첫 줄", "T2": "둘째 줄",
        }
        timeline = {"segments": [
            {"role": "T1", "text": "첫 줄", "content_type": "TITLE"},
            {"role": "T2", "text": "둘째 줄", "content_type": "TITLE"},
        ]}
        self.assertEqual(validate_design_lock.validate_role_contract(timeline), [])
        builder.validate_state_cues(config, timeline)

    def test_a12_nonempty_is_rejected(self):
        with self.assertRaisesRegex(RuntimeError, "A12_RESERVED_EMPTY"):
            builder.assert_a12_empty([{"role": "A12", "id": "bgm"}])

    def test_clean_prebuild_requires_vmake_binding(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source = root / "source.mp4"; template = root / "root.zip"
            source.write_bytes(b"source"); template.write_bytes(b"template")
            import hashlib
            source_sha = hashlib.sha256(source.read_bytes()).hexdigest()
            manifest = root / "build_manifest.json"
            manifest.write_text(json.dumps({
                "schema_version": "001short-build-manifest-v1", "episode_id": "EP",
                "visual_asset_mode": "CLEAN_VISUAL_READY",
                "source": {"path": str(source), "sha256": source_sha, "duration_us": 2_000_000},
                "template": {"root_name": "shrt white", "root_zip_path": str(template),
                             "root_zip_sha256": hashlib.sha256(template.read_bytes()).hexdigest()},
                "urakkai": {"production_type": "URAKKAI", "target_duration_us": 2_000_000,
                             "reorder_required": True, "locked_permutation": ["C2", "C1"],
                             "video_clips": [
                                 {"clip_id": "C2", "source_sha256": source_sha, "source_range_us": [1_000_000, 2_000_000], "target_range_us": [0, 1_000_000]},
                                 {"clip_id": "C1", "source_sha256": source_sha, "source_range_us": [0, 1_000_000], "target_range_us": [1_000_000, 2_000_000]},
                             ]},
                "source_audio": [{"clip_id": "C2", "mode": "mute"}, {"clip_id": "C1", "mode": "mute"}],
            }), encoding="utf-8")
            result = validate_prebuild.validate_prebuild(manifest)
            self.assertEqual(result["status"], "FAIL")
            self.assertIn("E_MANIFEST_INVALID", {row["code"] for row in result["errors"]})

    def test_readback_enforces_v2_role_tracks_titles_and_empty_a12(self):
        rich = lambda text: json.dumps({"text": text, "styles": [{"range": [0, len(text)]}]})
        tracks = [{"id": f"track-{index}", "segments": []} for index in range(15)]
        materials = {"items": [
            {"id": "m-t2", "type": "text", "content": rich("sub")},
            {"id": "m-t1", "type": "text", "content": rich("title")},
            {"id": "m-speaker", "type": "text", "content": rich("hello")},
        ]}
        tracks[9]["segments"] = [{"id": "T2", "role": "T2", "material_id": "m-t2"}]
        tracks[10]["segments"] = [{"id": "T1", "role": "T1", "material_id": "m-t1"}]
        tracks[6]["segments"] = [{"id": "SP1", "role": "A10_TEXT", "material_id": "m-speaker", "target_timerange": {"start": 0, "duration": 10}}]
        model = SimpleNamespace(tracks=tracks, materials=materials)
        contract = {
            "approved_role_text": {"T1": "title", "T2": "sub"},
            "approved_segment_text": {
                "SP1": {"role": "A10_TEXT", "start": 0, "duration": 10, "text": "hello", "color_role": "WHITE"},
            },
        }
        self.assertEqual(validate_capcut_project.validate_v2_role_routing(model, contract), [])
        tracks[6]["segments"][0]["role"] = "STATE"
        self.assertIn("V2_ROLE_TRACK_MISMATCH", {row["code"] for row in validate_capcut_project.validate_v2_role_routing(model, contract)})
        tracks[6]["segments"][0]["role"] = "A10_TEXT"
        tracks[14]["segments"] = [{"id": "bgm", "role": "A12"}]
        self.assertIn("V2_ROLE_TRACK_MISMATCH", {row["code"] for row in validate_capcut_project.validate_v2_role_routing(model, contract)})

    def test_duplicate_a9_cue_id_is_rejected(self):
        base = [
            {"role": "T1", "text": "title", "content_type": "TITLE"},
            {"role": "T2", "text": "sub", "content_type": "TITLE"},
        ]
        sound = {"role": "A9", "cue_id": "Q1", "content_type": "TTS", "start": 0, "duration": 10, "text": "same"}
        caption = {"role": "A9_TEXT", "cue_id": "Q1", "content_type": "TTS", "caption_role": "A9_TEXT", "start": 0, "duration": 10, "text": "same"}
        errors = validate_design_lock.validate_role_contract({"segments": base + [sound, dict(sound), caption]})
        self.assertIn("A9_TEXT_CUE_DUPLICATE", {row["code"] for row in errors})

    def test_a9_without_matching_a9_text_is_rejected(self):
        timeline = {"segments": [
            {"role": "T1", "text": "title", "content_type": "TITLE"},
            {"role": "T2", "text": "sub", "content_type": "TITLE"},
            {"role": "A9", "cue_id": "Q1", "content_type": "TTS", "start": 0,
             "duration": 10, "text": "narration"},
        ]}
        errors = validate_design_lock.validate_role_contract(timeline)
        self.assertIn("A9_TEXT_PAIRING_MISMATCH", {row["code"] for row in errors})

    def test_stage05_rejects_any_a12_placement(self):
        timeline = {"segments": [
            {"role": "T1", "text": "title", "content_type": "TITLE"},
            {"role": "T2", "text": "sub", "content_type": "TITLE"},
            {"segment_id": "bgm", "role": "A12"},
        ]}
        self.assertIn("A12_RESERVED_EMPTY", {row["code"] for row in validate_design_lock.validate_role_contract(timeline)})

    def test_builder_tts_cue_text_must_equal_approved_a9_text(self):
        timeline = {"segments": [
            {"role": "A9", "cue_id": "Q1", "start": 0, "duration": 10, "text": "approved"},
            {"role": "A9_TEXT", "cue_id": "Q1", "start": 0, "duration": 10, "text": "approved"},
        ]}
        with self.assertRaisesRegex(ValueError, "TTS_CUE_PLAN_AUTHORITY_MISMATCH"):
            builder.validate_tts_cues({"tts_cues": [{"cue_id": "Q1", "text": "swapped", "target_range_us": [0, 10]}]}, timeline)

    def test_readback_rejects_text_swap_even_when_role_and_range_stay_legal(self):
        rich = lambda text: json.dumps({"text": text, "styles": [{"range": [0, len(text)]}]})
        tracks = [{"id": f"track-{index}", "segments": []} for index in range(15)]
        materials = {"items": [
            {"id": "m-t2", "type": "text", "content": rich("sub")},
            {"id": "m-t1", "type": "text", "content": rich("title")},
            {"id": "m-speaker", "type": "text", "content": rich("state text")},
            {"id": "m-state", "type": "text", "content": rich("speaker text")},
        ]}
        timerange = {"start": 0, "duration": 10}
        tracks[9]["segments"] = [{"id": "T2", "role": "T2", "material_id": "m-t2", "target_timerange": timerange}]
        tracks[10]["segments"] = [{"id": "T1", "role": "T1", "material_id": "m-t1", "target_timerange": timerange}]
        tracks[6]["segments"] = [{"id": "SP", "role": "A10_TEXT", "material_id": "m-speaker", "target_timerange": timerange}]
        tracks[3]["segments"] = [{"id": "ST", "role": "STATE", "material_id": "m-state", "target_timerange": timerange}]
        model = SimpleNamespace(tracks=tracks, materials=materials)
        contract = {
            "approved_role_text": {"T1": "title", "T2": "sub"},
            "approved_segment_text": {
                "SP": {"role": "A10_TEXT", "start": 0, "duration": 10, "text": "speaker text", "color_role": "WHITE"},
                "ST": {"role": "STATE", "start": 0, "duration": 10, "text": "state text", "state_effect": "FLICKER_RAVE"},
            },
        }
        self.assertIn("CAPTION_SEGMENT_AUTHORITY_MISMATCH", {row["code"] for row in validate_capcut_project.validate_v2_role_routing(model, contract)})


if __name__ == "__main__":
    unittest.main()

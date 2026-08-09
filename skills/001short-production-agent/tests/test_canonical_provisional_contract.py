import copy
import json
import subprocess
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
from track_contract import (
    CANONICAL_TRACKS,
    LOGICAL_ROLE_BY_TRACK,
    STATE_TRACK_BY_EFFECT,
    TRACK_INDEX,
    TRACK_LAYOUT,
)


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

    def test_user_approved_nonmatching_clean_source_is_a_distinct_video_mode(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source = root / "source.mp4"
            clean = root / "clean.mp4"
            template = root / "root.zip"
            source.write_bytes(b"source")
            clean.write_bytes(b"different-duration-and-resolution")
            template.write_bytes(b"template")
            import hashlib

            def sha(path):
                return hashlib.sha256(path.read_bytes()).hexdigest()

            override = root / "user_clean_override.json"
            override.write_text(json.dumps({
                "schema_version": "001short-user-clean-override-v1",
                "episode_id": "EP",
                "status": "USER_APPROVED_NONMATCHING_CLEAN_SOURCE",
                "user_authority": {"evidence": "conversation", "exact_text": "이걸로 하라고"},
                "episode_clean_source_path": "clean.mp4",
                "clean_source_sha256": sha(clean),
                "clean_source_duration_us": 1_900_000,
                "clean_source_resolution": "360x640",
                "source_duration_us": 2_000_000,
                "source_resolution": "1080x1920",
                "clean_visual_ready_claim": False,
            }), encoding="utf-8")

            resolved = builder.resolve_visual_input({
                "episode_id": "EP",
                "visual_asset_mode": "USER_APPROVED_NONMATCHING_CLEAN_SOURCE",
                "clean_video": str(clean),
                "user_clean_override_path": str(override),
            })
            self.assertEqual(resolved["video_asset_key"], "user_approved_clean_video")
            self.assertEqual(resolved["video_input_path"], clean.resolve())
            self.assertFalse(resolved["upload_ready"])

            manifest = root / "build_manifest.json"
            manifest.write_text(json.dumps({
                "schema_version": "001short-build-manifest-v1", "episode_id": "EP",
                "visual_asset_mode": "USER_APPROVED_NONMATCHING_CLEAN_SOURCE",
                "source": {"path": str(source), "sha256": sha(source), "duration_us": 2_000_000},
                "template": {"root_name": "shrt white", "root_zip_path": str(template),
                             "root_zip_sha256": sha(template)},
                "clean_source": {
                    "origin": "USER_APPROVED_NONMATCHING_CLEAN_SOURCE",
                    "output_path": str(clean), "output_sha256": sha(clean),
                    "user_clean_override_path": str(override),
                    "user_clean_override_sha256": sha(override),
                },
                "urakkai": {"production_type": "URAKKAI", "target_duration_us": 2_000_000,
                             "reorder_required": True, "locked_permutation": ["C2", "C1"],
                             "video_clips": [
                                 {"clip_id": "C2", "source_sha256": sha(source),
                                  "source_range_us": [1_000_000, 2_000_000], "target_range_us": [0, 1_000_000]},
                                 {"clip_id": "C1", "source_sha256": sha(source),
                                  "source_range_us": [0, 1_000_000], "target_range_us": [1_000_000, 2_000_000]},
                             ]},
                "source_audio": [{"clip_id": "C2", "mode": "mute"}, {"clip_id": "C1", "mode": "mute"}],
            }), encoding="utf-8")
            self.assertEqual(validate_prebuild.validate_prebuild(manifest)["status"], "PASS")

            payload = json.loads(override.read_text(encoding="utf-8"))
            payload["user_authority"]["exact_text"] = ""
            override.write_text(json.dumps(payload), encoding="utf-8")
            with self.assertRaisesRegex(RuntimeError, "USER_CLEAN_OVERRIDE_AUTHORITY_INVALID"):
                builder.resolve_visual_input({
                    "episode_id": "EP",
                    "visual_asset_mode": "USER_APPROVED_NONMATCHING_CLEAN_SOURCE",
                    "clean_video": str(clean),
                    "user_clean_override_path": str(override),
                })

    def test_15_tracks_remain_but_only_laser_state_effect_is_routable(self):
        self.assertEqual(len(CANONICAL_TRACKS), 15)
        self.assertEqual(STATE_TRACK_BY_EFFECT, {"LASER_CUT": TRACK_INDEX["STATE_LASER"]})
        timeline = {"segments": [{
            "segment_id": "ST", "role": "STATE", "start": 0, "duration": 1_000_000,
            "text": "현재 상황", "content_type": "STATE", "caption_role": "STATE",
            "state_effect": "FLICKER_RAVE",
        }]}
        codes = {row["code"] for row in validate_design_lock.validate_role_contract(timeline)}
        self.assertIn("STATE_EFFECT_LASER_ONLY", codes)
        timeline["segments"][0]["state_effect"] = "LASER_CUT"
        codes = {row["code"] for row in validate_design_lock.validate_role_contract(timeline)}
        self.assertNotIn("STATE_EFFECT_LASER_ONLY", codes)
        for schema_name in ("approved_timeline.schema.json", "build_contract.schema.json"):
            schema_text = (SKILL / "schemas" / schema_name).read_text(encoding="utf-8")
            self.assertIn('"enum": ["LASER_CUT"]', schema_text)
            self.assertNotIn('"FLICKER_RAVE"', schema_text)
            self.assertNotIn('"GLITCH_SHAKE"', schema_text)

    def test_no_state_episode_is_legal(self):
        config = {
            "duration_us": 1_000_000, "state_cues": [], "T1": "첫 줄", "T2": "둘째 줄",
        }
        timeline = {"segments": [
            {"role": "VIDEO", "start": 0, "duration": 1_000_000},
            {"role": "T1", "start": 0, "duration": 1_000_000, "text": "첫 줄", "content_type": "TITLE"},
            {"role": "T2", "start": 0, "duration": 1_000_000, "text": "둘째 줄", "content_type": "TITLE"},
            {"role": "SCREEN_EFFECT", "start": 0, "duration": 1_000_000},
            {"role": "SCREEN_WHITE", "start": 0, "duration": 1_000_000},
        ]}
        self.assertEqual(validate_design_lock.validate_role_contract(timeline), [])
        builder.validate_state_cues(config, timeline)

    def test_full_span_anchor_rows_are_required(self):
        valid = [
            {"segment_id": "V", "role": "VIDEO", "start": 0, "duration": 1_000_000},
            {"segment_id": "T1", "role": "T1", "start": 0, "duration": 1_000_000,
             "text": "title", "content_type": "TITLE"},
            {"segment_id": "T2", "role": "T2", "start": 0, "duration": 1_000_000,
             "text": "subtitle", "content_type": "TITLE"},
            {"segment_id": "FX", "role": "SCREEN_EFFECT", "start": 0, "duration": 1_000_000},
            {"segment_id": "WHITE", "role": "SCREEN_WHITE", "start": 0, "duration": 1_000_000},
        ]
        self.assertEqual(validate_design_lock.validate_role_contract({"segments": valid}), [])
        cases = {
            "missing": [row for row in valid if row["role"] != "SCREEN_EFFECT"],
            "partial": [dict(row, duration=500_000) if row["role"] == "T1" else row for row in valid],
            "duplicate": valid + [dict(valid[-1], segment_id="WHITE2")],
        }
        for name, rows in cases.items():
            with self.subTest(name=name):
                errors = validate_design_lock.validate_role_contract({"segments": rows})
                self.assertIn("FULL_SPAN_ANCHOR_INVALID", {row["code"] for row in errors})

    def test_caption_line_too_long_is_rejected(self):
        timeline = {"segments": [
            {"segment_id": "V", "role": "VIDEO", "start": 0, "duration": 1_000_000},
            {"segment_id": "T1", "role": "T1", "start": 0, "duration": 1_000_000,
             "text": "12345678901", "content_type": "TITLE"},
            {"segment_id": "T2", "role": "T2", "start": 0, "duration": 1_000_000,
             "text": "subtitle", "content_type": "TITLE"},
            {"segment_id": "FX", "role": "SCREEN_EFFECT", "start": 0, "duration": 1_000_000},
            {"segment_id": "WHITE", "role": "SCREEN_WHITE", "start": 0, "duration": 1_000_000},
        ]}
        errors = validate_design_lock.validate_role_contract(timeline)
        self.assertIn("CAPTION_LINE_TOO_LONG", {row["code"] for row in errors})

    def test_design_lock_cli_relock_overwrites_only_when_flagged(self):
        import hashlib
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            media = root / "source.mp4"; media.write_bytes(b"source")
            identity = root / "source_identity.json"
            identity.write_text(json.dumps({
                "schema_version": "source-identity-v1", "episode_id": "EP",
                "source_id": "SRC", "source_fingerprint": "fp",
                "media_path": media.name,
                "media_sha256": hashlib.sha256(media.read_bytes()).hexdigest(),
            }), encoding="utf-8")
            segments = [
                {"segment_id": "V", "timeline_order": 0, "role": "VIDEO", "start": 0,
                 "duration": 1_000_000, "source_ref": "SRC"},
                {"segment_id": "T1", "timeline_order": 1, "role": "T1", "start": 0,
                 "duration": 1_000_000, "source_ref": "SRC", "text": "title", "content_type": "TITLE"},
                {"segment_id": "T2", "timeline_order": 2, "role": "T2", "start": 0,
                 "duration": 1_000_000, "source_ref": "SRC", "text": "subtitle", "content_type": "TITLE"},
                {"segment_id": "FX", "timeline_order": 3, "role": "SCREEN_EFFECT", "start": 0,
                 "duration": 1_000_000, "source_ref": "SRC"},
                {"segment_id": "WHITE", "timeline_order": 4, "role": "SCREEN_WHITE", "start": 0,
                 "duration": 1_000_000, "source_ref": "SRC"},
            ]
            timeline = root / "approved_timeline.json"
            timeline.write_text(json.dumps({
                "schema_version": "approved-timeline-v1", "episode_id": "EP",
                "source_fingerprint": "fp", "segments": segments,
            }), encoding="utf-8")
            digest = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
            handoff = root / "design_handoff.json"
            handoff.write_text(json.dumps({
                "schema_version": "tikitaka-design-handoff-v1", "episode_id": "EP", "status": "PASS",
                "source_identity_path": identity.name, "source_identity_sha256": digest(identity),
                "timeline_path": timeline.name, "timeline_sha256": digest(timeline),
                "source_fingerprint": "fp",
                "approved_timeline_order": [row["segment_id"] for row in segments],
            }), encoding="utf-8")
            evidence = root / "design_evidence.json"; evidence.write_text("{}", encoding="utf-8")
            command = [sys.executable, str(SCRIPTS / "validate_design_lock.py"),
                       "--handoff", str(handoff), "--source-identity", str(identity),
                       "--timeline", str(timeline), "--evidence", str(evidence)]
            blocked = subprocess.run(command, capture_output=True, text=True, check=False)
            self.assertEqual(blocked.returncode, 1)
            self.assertIn("DESIGN_LOCK_EVIDENCE_EXISTS", blocked.stdout)
            relocked = subprocess.run([*command, "--relock"], capture_output=True, text=True, check=False)
            self.assertEqual(relocked.returncode, 0, relocked.stdout + relocked.stderr)
            self.assertEqual(json.loads(evidence.read_text(encoding="utf-8"))["status"], "PASS")

    def test_state_meaningful_limit_is_per_line_in_design_and_builder(self):
        timeline = {"segments": [
            {"segment_id": "V1", "role": "VIDEO", "start": 0, "duration": 1_000_000},
            {"segment_id": "T1", "role": "T1", "start": 0, "duration": 1_000_000,
             "text": "title", "content_type": "TITLE"},
            {"segment_id": "T2", "role": "T2", "start": 0, "duration": 1_000_000,
             "text": "subtitle", "content_type": "TITLE"},
            {"segment_id": "FX", "role": "SCREEN_EFFECT", "start": 0, "duration": 1_000_000},
            {"segment_id": "WHITE", "role": "SCREEN_WHITE", "start": 0, "duration": 1_000_000},
            {"segment_id": "ST1", "role": "STATE", "start": 0, "duration": 500_000,
             "text": "12345678\nABCDEFGH", "content_type": "STATE", "caption_role": "STATE",
             "state_effect": "LASER_CUT"},
        ]}
        self.assertEqual(validate_design_lock.validate_role_contract(timeline), [])
        builder.validate_state_cues({
            "duration_us": 1_000_000,
            "state_cues": [{"segment_id": "ST1", "cue_id": "1", "start_us": 0,
                            "end_us": 500_000, "text": "12345678\nABCDEFGH"}],
        }, timeline)

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
            {"id": "m-video", "type": "video"},
            {"id": "m-fx", "type": "video_effect"},
            {"id": "m-white", "type": "photo"},
            {"id": "m-t2", "type": "text", "content": rich("sub")},
            {"id": "m-t1", "type": "text", "content": rich("title")},
            {"id": "m-speaker", "type": "text", "content": rich("hello")},
        ]}
        timerange = {"start": 0, "duration": 10}
        tracks[0]["segments"] = [{"id": "V", "role": "VIDEO", "material_id": "m-video", "target_timerange": timerange}]
        tracks[1]["segments"] = [{"id": "FX", "role": "SCREEN_EFFECT", "material_id": "m-fx", "target_timerange": timerange}]
        tracks[2]["segments"] = [{"id": "WHITE", "role": "SCREEN_WHITE", "material_id": "m-white", "target_timerange": timerange}]
        tracks[9]["segments"] = [{"id": "T2", "role": "T2", "material_id": "m-t2", "target_timerange": timerange}]
        tracks[10]["segments"] = [{"id": "T1", "role": "T1", "material_id": "m-t1", "target_timerange": timerange}]
        tracks[6]["segments"] = [{"id": "SP1", "role": "A10_TEXT", "material_id": "m-speaker", "target_timerange": {"start": 0, "duration": 10}}]
        model = SimpleNamespace(tracks=tracks, materials=materials)
        contract = {
            "track_layout_version": TRACK_LAYOUT,
            "approved_role_text": {"T1": "title", "T2": "sub"},
            "approved_segment_text": {
                "SP1": {"role": "A10_TEXT", "start": 0, "duration": 10, "text": "hello", "color_role": "WHITE"},
            },
            "timeline": [
                {"segment_id": "V", "role": "VIDEO", "start": 0, "duration": 10, "end": 10},
                {"segment_id": "FX", "role": "SCREEN_EFFECT", "start": 0, "duration": 10, "end": 10},
                {"segment_id": "WHITE", "role": "SCREEN_WHITE", "start": 0, "duration": 10, "end": 10},
                {"segment_id": "T2", "role": "T2", "start": 0, "duration": 10, "end": 10},
                {"segment_id": "T1", "role": "T1", "start": 0, "duration": 10, "end": 10},
                {"segment_id": "SP1", "role": "A10_TEXT", "start": 0, "duration": 10, "end": 10},
            ],
        }
        self.assertEqual(validate_capcut_project.validate_v2_role_routing(model, contract), [])
        tracks[6]["segments"][0]["role"] = "STATE"
        self.assertIn("V2_ROLE_TRACK_MISMATCH", {row["code"] for row in validate_capcut_project.validate_v2_role_routing(model, contract)})
        tracks[6]["segments"][0]["role"] = "A10_TEXT"
        tracks[14]["segments"] = [{"id": "bgm", "role": "A12"}]
        self.assertIn("V2_ROLE_TRACK_MISMATCH", {row["code"] for row in validate_capcut_project.validate_v2_role_routing(model, contract)})

    def test_readback_rejects_partial_full_span_anchor(self):
        rich = lambda text: json.dumps({"text": text, "styles": [{"range": [0, len(text)]}]})
        tracks = [{"id": f"track-{index}", "segments": []} for index in range(15)]
        materials = {"items": [
            {"id": "m-video", "type": "video"},
            {"id": "m-fx", "type": "video_effect"},
            {"id": "m-white", "type": "photo"},
            {"id": "m-t2", "type": "text", "content": rich("sub")},
            {"id": "m-t1", "type": "text", "content": rich("title")},
        ]}
        rows = [
            (0, "V", "VIDEO", "m-video", 1_000_000),
            (1, "FX", "SCREEN_EFFECT", "m-fx", 500_000),
            (2, "WHITE", "SCREEN_WHITE", "m-white", 1_000_000),
            (9, "T2", "T2", "m-t2", 1_000_000),
            (10, "T1", "T1", "m-t1", 1_000_000),
        ]
        for index, segment_id, role, material_id, duration in rows:
            tracks[index]["segments"] = [{
                "id": segment_id, "role": role, "material_id": material_id,
                "target_timerange": {"start": 0, "duration": duration},
            }]
        model = SimpleNamespace(tracks=tracks, materials=materials)
        contract = {
            "track_layout_version": TRACK_LAYOUT,
            "approved_role_text": {"T1": "title", "T2": "sub"},
            "approved_segment_text": {},
            "timeline": [
                {"segment_id": "V", "role": "VIDEO", "start": 0, "duration": 1_000_000, "end": 1_000_000},
                {"segment_id": "FX", "role": "SCREEN_EFFECT", "start": 0, "duration": 1_000_000, "end": 1_000_000},
                {"segment_id": "WHITE", "role": "SCREEN_WHITE", "start": 0, "duration": 1_000_000, "end": 1_000_000},
                {"segment_id": "T2", "role": "T2", "start": 0, "duration": 1_000_000, "end": 1_000_000},
                {"segment_id": "T1", "role": "T1", "start": 0, "duration": 1_000_000, "end": 1_000_000},
            ],
        }
        errors = validate_capcut_project.validate_v2_role_routing(model, contract)
        self.assertIn("FULL_SPAN_ANCHOR_MISMATCH", {row["code"] for row in errors})

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

    def test_mixed_policy_missing_a9_uses_policy_neutral_diagnostic(self):
        timeline = {
            "audio_policy": "A9_TTS_PLUS_A10_RETAINED",
            "segments": [
                {"role": "T1", "text": "title", "content_type": "TITLE"},
                {"role": "T2", "text": "sub", "content_type": "TITLE"},
            ],
        }
        errors = validate_design_lock.validate_role_contract(timeline)
        self.assertIn("A9_REQUIRED_FOR_TTS_POLICY", {row["code"] for row in errors})

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
            "track_layout_version": TRACK_LAYOUT,
            "approved_role_text": {"T1": "title", "T2": "sub"},
            "approved_segment_text": {
                "SP": {"role": "A10_TEXT", "start": 0, "duration": 10, "text": "speaker text", "color_role": "WHITE"},
                "ST": {"role": "STATE", "start": 0, "duration": 10, "text": "state text", "state_effect": "LASER_CUT"},
            },
        }
        self.assertIn("CAPTION_SEGMENT_AUTHORITY_MISMATCH", {row["code"] for row in validate_capcut_project.validate_v2_role_routing(model, contract)})

    def test_readback_rejects_caption_cue_layer_for_different_role(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            caption = root / "caption_lock.json"
            caption.write_text(json.dumps({
                "cues": [{"cue_id": "C1", "start_us": 0, "end_us": 10,
                          "text": "same", "layer": "STATE"}],
            }), encoding="utf-8")
            rich = json.dumps({"text": "same", "styles": [{"range": [0, 4]}]})
            model = SimpleNamespace(
                tracks=[{"segments": [{
                    "id": "SP", "role": "A10_TEXT", "material_id": "M",
                    "target_timerange": {"start": 0, "duration": 10},
                }]}],
                materials={"items": [{"id": "M", "type": "text", "content": rich}]},
            )
            contract = {
                "caption_lock_path": str(caption), "subtitle_roles": ["A10_TEXT"],
                "caption_bindings": [{"segment_id": "SP", "cue_id": "C1", "role": "A10_TEXT"}],
            }
            errors = validate_capcut_project.validate_subtitle_binding(model, contract)
            self.assertIn("SUBTITLE_BINDING_LAYER_MISMATCH", {row["code"] for row in errors})


if __name__ == "__main__":
    unittest.main()

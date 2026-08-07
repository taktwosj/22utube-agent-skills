import json
import hashlib
import copy
import os
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = SKILL_ROOT / "scripts"


def _run(script: str, *args: object) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPTS / script), *(str(arg) for arg in args)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )


def _approved_timeline() -> dict:
    return {
        "schema_version": "approved-timeline-v2",
        "episode_id": "SH_V2_TEST",
        "source_fingerprint": "source-sha",
        "project_name": "SH_V2_TEST_capcut",
        "production_mode": "URAKKAI",
        "root_profile": "shrt_white_base_v2",
        "total_duration_us": 10_000_000,
        "primary_speaker_id": "speaker-primary",
        "lane_policies": {
            "VIDEO": {"allow_gaps": False, "allow_overlaps": False},
            "A9": {"allow_gaps": True, "allow_overlaps": False},
            "A10": {"allow_gaps": True, "allow_overlaps": False},
        },
        "segments": [
            {
                "segment_id": "VIDEO_01",
                "timeline_order": 1,
                "role": "VIDEO",
                "start": 0,
                "duration": 10_000_000,
                "source_ref": "source-id",
                "source_range_us": [0, 10_000_000],
                "asset_key": "clean_video",
            },
            {
                "segment_id": "T1_FIXED",
                "timeline_order": 2,
                "role": "T1",
                "start": 0,
                "duration": 10_000_000,
                "source_ref": "source-id",
                "text": "title one",
            },
            {
                "segment_id": "T2_FIXED",
                "timeline_order": 3,
                "role": "T2",
                "start": 0,
                "duration": 10_000_000,
                "source_ref": "source-id",
                "text": "title two",
            },
            {
                "segment_id": "SPEAKER_PRIMARY",
                "timeline_order": 4,
                "role": "SPEAKER",
                "start": 1_000_000,
                "duration": 1_000_000,
                "source_ref": "source-id",
                "speaker_id": "speaker-primary",
                "text": "primary line",
            },
            {
                "segment_id": "SPEAKER_OTHER",
                "timeline_order": 5,
                "role": "SPEAKER",
                "start": 2_000_000,
                "duration": 1_000_000,
                "source_ref": "source-id",
                "speaker_id": "speaker-other",
                "text": "other line",
            },
            {
                "segment_id": "SPEAKER_UNKNOWN",
                "timeline_order": 6,
                "role": "SPEAKER",
                "start": 3_000_000,
                "duration": 1_000_000,
                "source_ref": "source-id",
                "speaker_id": "UNASSIGNED",
                "text": "unknown line",
            },
            {
                "segment_id": "STATE_1",
                "timeline_order": 7,
                "role": "STATE",
                "start": 4_000_000,
                "duration": 1_000_000,
                "source_ref": "source-id",
                "text": "state one",
                "state_effect": "FLICKER_RAVE",
            },
            {
                "segment_id": "STATE_2",
                "timeline_order": 8,
                "role": "STATE",
                "start": 5_000_000,
                "duration": 1_000_000,
                "source_ref": "source-id",
                "text": "state two",
                "state_effect": "GLITCH_SHAKE",
            },
            {
                "segment_id": "STATE_3",
                "timeline_order": 9,
                "role": "STATE",
                "start": 6_000_000,
                "duration": 1_000_000,
                "source_ref": "source-id",
                "text": "state three",
                "state_effect": "LASER_CUT",
            },
            {
                "segment_id": "SFX_WOW",
                "timeline_order": 10,
                "role": "A11_SFX",
                "start": 7_000_000,
                "duration": 500_000,
                "source_ref": "source-id",
                "sfx_kind": "WOW",
            },
            {
                "segment_id": "A12_FULL",
                "timeline_order": 11,
                "role": "A12",
                "start": 0,
                "duration": 10_000_000,
                "source_ref": "source-id",
                "asset_key": "bgm",
                "source_range_us": [0, 10_000_000],
            },
        ],
    }


TRACKS = [
    ("track-video", "video", "VIDEO", 1),
    ("track-screen-effect", "effect", "SCREEN_EFFECT", 1),
    ("track-screen-white", "video", "SCREEN_WHITE", 1),
    ("track-state-3", "text", "STATE_EFFECT_3", 1),
    ("track-state-2", "text", "STATE_EFFECT_2", 1),
    ("track-state-1", "text", "STATE_EFFECT_1", 1),
    ("track-white", "text", "A10_TEXT_WHITE", 1),
    ("track-yellow", "text", "A10_TEXT_YELLOW", 1),
    ("track-a9-text", "text", "A9_TEXT", 1),
    ("track-t2", "text", "T2", 1),
    ("track-t1", "text", "T1", 1),
    ("track-a9", "audio", "A9", 1),
    ("track-a10", "audio", "A10", 1),
    ("track-a11", "audio", "A11_SFX", 3),
    ("track-a12", "audio", "A12", 1),
]


def _write_v2_fixture(root: Path) -> tuple[Path, Path, Path]:
    project = root / "template" / "shrt_white_base_v2"
    timeline_id = "timeline-seed"
    mirror = project / "Timelines" / timeline_id
    mirror.mkdir(parents=True)
    (project / "Resources" / "media").mkdir(parents=True)
    (project / "Resources" / "media" / "transparent_center_white_1080x1920.png").write_bytes(b"png")
    materials = {"videos": [], "texts": [], "audios": [], "effects": []}
    tracks = []
    layout_tracks = []
    text_styles = {}
    for track_id, track_type, role, segment_count in TRACKS:
        segments = []
        material_ids = []
        for index in range(segment_count):
            material_id = f"material-{role.lower()}-{index + 1}"
            segment_id = f"seed-{role.lower()}-{index + 1}"
            material_ids.append(material_id)
            segment = {
                "id": segment_id,
                "material_id": material_id,
                "target_timerange": {"start": index * 500_000, "duration": 500_000},
                "source_timerange": {"start": 0, "duration": 500_000},
                "volume": 0 if role in {"VIDEO", "A9", "A10"} else 1,
            }
            if role in {"A10_TEXT_WHITE", "A10_TEXT_YELLOW"}:
                segment["extra_material_refs"] = [f"fuzzy-blur-{role.lower()}"]
            segments.append(segment)
            if track_type == "text":
                content = json.dumps({"text": role, "styles": [{"range": [0, len(role)]}]})
                materials["texts"].append(
                    {
                        "id": material_id,
                        "type": "text",
                        "content": content,
                        "text": role,
                        "metadata_marker": {"preserve": True, "role_seed": role},
                    }
                )
            elif track_type == "video":
                materials["videos"].append(
                    {
                        "id": material_id,
                        "type": "video",
                        "path": "##_draftpath_placeholder_fixture_##/Resources/media/seed.mp4",
                    }
                )
            elif track_type == "effect":
                materials["effects"].append({"id": material_id, "type": "effect"})
            else:
                materials["audios"].append({"id": material_id, "type": "music", "path": "seed.aac"})
        tracks.append({"id": track_id, "type": track_type, "segments": segments})
        layout_tracks.append(
            {
                "track_id": track_id,
                "type": track_type,
                "role": role,
                "requirement": "REQUIRED" if role in {"VIDEO", "SCREEN_EFFECT", "SCREEN_WHITE", "T1", "T2"} else "UNDETERMINED",
                "segment_ids": [segment["id"] for segment in segments],
                "material_ids": material_ids,
            }
        )
        if track_type == "text":
            text_styles[role] = {
                "track_id": track_id,
                "segment_id": segments[0]["id"],
                "material_id": material_ids[0],
                "animations": (
                    [
                        {
                            "group_id": f"fuzzy-blur-{role.lower()}",
                            "effect_id": "7596971792351153424",
                            "name": "퍼지 블러",
                        }
                    ]
                    if role in {"A10_TEXT_WHITE", "A10_TEXT_YELLOW"}
                    else []
                ),
            }
    content = {
        "id": timeline_id,
        "draft_id": "draft-seed",
        "main_timeline_id": timeline_id,
        "duration": 10_000_000,
        "tracks": tracks,
        "materials": materials,
    }
    for path in (project / "draft_content.json", mirror / "draft_content.json"):
        path.write_text(json.dumps(content), encoding="utf-8")
    (project / "draft_meta_info.json").write_text(
        json.dumps({"draft_id": "draft-seed", "draft_name": "seed", "tm_duration": 10_000_000}),
        encoding="utf-8",
    )
    (project / "Timelines" / "project.json").write_text(
        json.dumps({"id": "project-seed", "project_id": "project-seed", "draft_id": "draft-seed", "main_timeline_id": timeline_id}),
        encoding="utf-8",
    )
    archive = root / "shrt_white_base_v2.zip"
    with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as bundle:
        for path in sorted(project.rglob("*")):
            if path.is_file():
                bundle.write(path, path.relative_to(project.parent))
    archive_sha = hashlib.sha256(archive.read_bytes()).hexdigest()
    layout = root / "shrt_white_base_v2_layout_contract_v1.json"
    layout.write_text(
        json.dumps(
            {
                "contract_version": "1.0.0",
                "template_profile": "shrt_white_base_v2",
                "archive_sha256": archive_sha,
                "tracks": layout_tracks,
                "text_styles": text_styles,
                "speaker_policy": {
                    "primary_speaker_id": "A10_TEXT_WHITE",
                    "all_other_resolved_speaker_ids": "A10_TEXT_YELLOW",
                    "unknown_speaker_id": "UNASSIGNED_NO_GUESS",
                },
            }
        ),
        encoding="utf-8",
    )
    contract = root / "shorts_capcut_root_contract_v2.json"
    contract.write_text(
        json.dumps(
            {
                "schema_version": "shorts-capcut-root-contract-v1",
                "contract_id": "shorts_capcut_root_v2",
                "workspace_relative": True,
                "assembly_mode": "clean_staging_copy",
                "profiles": {
                    "fixture_v2": {
                        "template_profile": "shrt_white_base_v2",
                        "archive_relative_path": archive.name,
                        "archive_sha256": archive_sha,
                        "layout_contract_relative_path": layout.name,
                    }
                },
            }
        ),
        encoding="utf-8",
    )
    assets = root / "assets.json"
    video = root / "clean_video.mp4"
    bgm = root / "bgm.aac"
    tts = root / "tts.wav"
    speech = root / "speech.wav"
    video.write_bytes(b"video")
    bgm.write_bytes(b"bgm")
    tts.write_bytes(b"tts")
    speech.write_bytes(b"speech")
    assets.write_text(
        json.dumps(
            {
                "assets": {
                    "clean_video": {"path": str(video)},
                    "bgm": {"path": str(bgm)},
                    "tts": {"path": str(tts)},
                    "speech": {"path": str(speech)},
                }
            }
        ),
        encoding="utf-8",
    )
    return contract, layout, assets


class V2ProductionContractTests(unittest.TestCase):
    def test_tools_keep_root_contract_path_and_readiness_in_one_object(self):
        raw = (SKILL_ROOT / "tools.json").read_text(encoding="utf-8")
        self.assertEqual(raw.count('"root_contract"'), 1)
        tools = json.loads(raw)
        root_contract = tools["capcut_preflight"]["root_contract"]
        self.assertEqual(
            root_contract["path"],
            "00_asset_tools/templates/capcut/shrt_white_base_v2/shorts_capcut_root_contract_v2.json",
        )
        self.assertIn("draft_content.json", root_contract["required_files"])
        self.assertEqual(root_contract["missing"], "WAIT_CAPCUT_ROOT_CONTRACT")
        mapping = tools["capcut_preflight"]["track_mapping"]
        self.assertEqual(mapping["profile"], "shrt_white_base_v2")
        self.assertEqual(
            mapping["required"],
            [role for _, _, role, _ in TRACKS],
        )
        self.assertEqual(mapping["speaker_routes"], ["A10_TEXT_WHITE", "A10_TEXT_YELLOW"])
        self.assertEqual(mapping["A12"], "FULL_DURATION_BGM_VOLUME_1")
        self.assertEqual(tools["source_vocal_separation"]["A12"]["shrt_white_base_v2"], "FULL_DURATION_BGM_VOLUME_1")

    def test_compiler_rejects_invalid_input_schema_and_lane_discontinuity(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            output = root / "production_plan.json"
            invalid_inputs = []
            missing_source_fingerprint = _approved_timeline()
            missing_source_fingerprint.pop("source_fingerprint")
            invalid_inputs.append(("source_fingerprint", missing_source_fingerprint))
            for field in ("timeline_order", "source_ref"):
                timeline = _approved_timeline()
                timeline["segments"][0].pop(field)
                invalid_inputs.append((field, timeline))
            for field, timeline in invalid_inputs:
                source = root / f"missing-{field}.json"
                source.write_text(json.dumps(timeline), encoding="utf-8")
                completed = _run(
                    "compile_production_plan.py", "--approved-timeline", source, "--output", output
                )
                self.assertNotEqual(completed.returncode, 0)
                self.assertIn("APPROVED_TIMELINE_SCHEMA", completed.stdout)
                self.assertFalse(output.exists())

            timeline = _approved_timeline()
            timeline["segments"][0]["duration"] = 9_000_000
            source = root / "video-gap.json"
            source.write_text(json.dumps(timeline), encoding="utf-8")
            rejected_gap = _run(
                "compile_production_plan.py", "--approved-timeline", source, "--output", output
            )
            self.assertNotEqual(rejected_gap.returncode, 0)
            self.assertIn("APPROVED_TIMELINE_LANE_GAP:VIDEO", rejected_gap.stdout)

            timeline["lane_policies"]["VIDEO"]["allow_gaps"] = True
            source.write_text(json.dumps(timeline), encoding="utf-8")
            accepted_gap = _run(
                "compile_production_plan.py", "--approved-timeline", source, "--output", output
            )
            self.assertEqual(accepted_gap.returncode, 0, accepted_gap.stdout + accepted_gap.stderr)

            overlap_timeline = _approved_timeline()
            overlap_timeline["segments"].append(
                {
                    "segment_id": "VIDEO_OVERLAP",
                    "timeline_order": 12,
                    "role": "VIDEO",
                    "start": 9_000_000,
                    "duration": 1_000_000,
                    "source_ref": "overlap-source",
                    "source_range_us": [0, 1_000_000],
                    "asset_key": "clean_video",
                }
            )
            source.write_text(json.dumps(overlap_timeline), encoding="utf-8")
            rejected_overlap = _run(
                "compile_production_plan.py", "--approved-timeline", source, "--output", output
            )
            self.assertNotEqual(rejected_overlap.returncode, 0)
            self.assertIn("APPROVED_TIMELINE_LANE_OVERLAP:VIDEO", rejected_overlap.stdout)
            overlap_timeline["lane_policies"]["VIDEO"]["allow_overlaps"] = True
            source.write_text(json.dumps(overlap_timeline), encoding="utf-8")
            accepted_overlap = _run(
                "compile_production_plan.py", "--approved-timeline", source, "--output", output
            )
            self.assertEqual(
                accepted_overlap.returncode, 0, accepted_overlap.stdout + accepted_overlap.stderr
            )

    def test_schema_rejects_malformed_referenced_placement_and_range(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            timeline = root / "approved.json"
            plan = root / "plan.json"
            timeline.write_text(json.dumps(_approved_timeline()), encoding="utf-8")
            compiled = _run(
                "compile_production_plan.py", "--approved-timeline", timeline, "--output", plan
            )
            self.assertEqual(compiled.returncode, 0, compiled.stdout + compiled.stderr)
            payload = json.loads(plan.read_text(encoding="utf-8"))
            payload["timeline"][0]["placements"][0]["target_range_us"] = [5, "bad"]
            plan.write_text(json.dumps(payload), encoding="utf-8")
            rejected_type = _run("validate_executable_protocol.py", "--plan", plan)
            self.assertNotEqual(rejected_type.returncode, 0)
            self.assertIn("PRODUCTION_PLAN_SCHEMA", rejected_type.stdout)

            payload["timeline"][0]["placements"][0]["target_range_us"] = [5, 4]
            plan.write_text(json.dumps(payload), encoding="utf-8")
            rejected_order = _run("validate_executable_protocol.py", "--plan", plan)
            self.assertNotEqual(rejected_order.returncode, 0)
            self.assertIn("V2_TARGET_RANGE_INVALID", rejected_order.stdout)

    def test_schema_operations_match_public_builder_capabilities(self):
        schema = json.loads(
            (SKILL_ROOT / "schemas" / "executable_production_plan.schema.json").read_text(
                encoding="utf-8"
            )
        )
        declared = schema["$defs"]["placement"]["properties"]["operation"]["enum"]

        completed = _run("build_v2_contract_project.py", "--capabilities")

        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        capabilities = json.loads(completed.stdout)
        self.assertEqual(sorted(declared), capabilities["operations"])

    def test_stage05_cli_compiles_v2_routes_without_guessing(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            timeline = root / "approved_timeline.json"
            output = root / "production_plan.json"
            timeline.write_text(json.dumps(_approved_timeline()), encoding="utf-8")

            completed = _run(
                "compile_production_plan.py",
                "--approved-timeline",
                timeline,
                "--output",
                output,
            )

            self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
            receipt = json.loads(completed.stdout)
            self.assertEqual(receipt["status"], "PASS")
            plan = json.loads(output.read_text(encoding="utf-8"))
            placements = [
                placement
                for row in plan["timeline"]
                for placement in row["placements"]
            ]
            by_id = {placement["placement_id"]: placement for placement in placements}
            for placement_id in ("T1_FIXED", "T2_FIXED", "SCREEN_WHITE_FIXED", "SCREEN_EFFECT_FIXED"):
                self.assertEqual(by_id[placement_id]["target_range_us"], [0, 10_000_000])
            self.assertEqual(by_id["VIDEO_01"]["volume"], 0)
            self.assertEqual(by_id["SPEAKER_PRIMARY"]["anchor"], "A10_TEXT_WHITE")
            self.assertEqual(by_id["SPEAKER_OTHER"]["anchor"], "A10_TEXT_YELLOW")
            self.assertEqual(by_id["SPEAKER_UNKNOWN"]["anchor"], "A10_TEXT_UNASSIGNED")
            self.assertEqual(by_id["SPEAKER_UNKNOWN"]["operation"], "omit")
            self.assertEqual(by_id["STATE_1"]["anchor"], "STATE_EFFECT_1")
            self.assertEqual(by_id["STATE_2"]["anchor"], "STATE_EFFECT_2")
            self.assertEqual(by_id["STATE_3"]["anchor"], "STATE_EFFECT_3")
            self.assertEqual(by_id["SFX_WOW"]["sfx_seed"], 3)
            self.assertEqual(by_id["A9_SEED"]["operation"], "preserve_muted_seed")
            self.assertEqual(by_id["A10_SEED"]["operation"], "preserve_muted_seed")
            self.assertEqual(by_id["A12_FULL"]["volume"], 1)

            validated = _run("validate_executable_protocol.py", "--plan", output)
            self.assertEqual(validated.returncode, 0, validated.stdout + validated.stderr)

            by_id["SPEAKER_PRIMARY"]["speaker_route"] = "YELLOW"
            output.write_text(json.dumps(plan), encoding="utf-8")
            rejected = _run("validate_executable_protocol.py", "--plan", output)
            self.assertNotEqual(rejected.returncode, 0)
            self.assertIn("V2_PRIMARY_SPEAKER_ROUTE_INVALID", rejected.stdout)

    def test_v2_rejects_audible_non_seed_audio_operations(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            contract, _layout, assets = _write_v2_fixture(root)
            timeline = root / "approved_timeline.json"
            output = root / "production_plan.json"
            timeline.write_text(json.dumps(_approved_timeline()), encoding="utf-8")
            compiled = _run(
                "compile_production_plan.py",
                "--approved-timeline",
                timeline,
                "--output",
                output,
            )
            self.assertEqual(compiled.returncode, 0, compiled.stdout + compiled.stderr)
            valid_plan = json.loads(output.read_text(encoding="utf-8"))

            for anchor in ("A9", "A10"):
                with self.subTest(anchor=anchor):
                    plan = copy.deepcopy(valid_plan)
                    placement = next(
                        item
                        for row in plan["timeline"]
                        for item in row["placements"]
                        if item["anchor"] == anchor
                    )
                    placement["operation"] = "clone_template_segment"
                    placement["volume"] = 1
                    output.write_text(json.dumps(plan), encoding="utf-8")

                    rejected = _run("validate_executable_protocol.py", "--plan", output)

                    self.assertNotEqual(rejected.returncode, 0)
                    self.assertIn(f"V2_MUTED_SEED_OPERATION_INVALID:{anchor}", rejected.stdout)

                    blocked_build = _run(
                        "build_v2_contract_project.py",
                        "--production-plan",
                        output,
                        "--root-contract",
                        contract,
                        "--workspace-root",
                        root,
                        "--asset-manifest",
                        assets,
                        "--output-project",
                        root / f"output-{anchor}",
                        "--receipt",
                        root / f"receipt-{anchor}.json",
                    )
                    self.assertNotEqual(blocked_build.returncode, 0)
                    self.assertIn("V2_PRODUCTION_PLAN_SCHEMA_INVALID", blocked_build.stdout)

    def test_duplicate_segment_ids_and_wrong_sfx_mapping_are_rejected(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            approved = _approved_timeline()
            duplicate = dict(approved["segments"][3])
            duplicate["timeline_order"] = 12
            approved["segments"].append(duplicate)
            source = root / "duplicate.json"
            plan = root / "plan.json"
            source.write_text(json.dumps(approved), encoding="utf-8")
            rejected_duplicate = _run(
                "compile_production_plan.py", "--approved-timeline", source, "--output", plan
            )
            self.assertNotEqual(rejected_duplicate.returncode, 0)
            self.assertIn("APPROVED_TIMELINE_DUPLICATE_SEGMENT_ID:SPEAKER_PRIMARY", rejected_duplicate.stdout)

            source.write_text(json.dumps(_approved_timeline()), encoding="utf-8")
            compiled = _run(
                "compile_production_plan.py", "--approved-timeline", source, "--output", plan
            )
            self.assertEqual(compiled.returncode, 0, compiled.stdout + compiled.stderr)
            payload = json.loads(plan.read_text(encoding="utf-8"))
            wow = next(
                item
                for row in payload["timeline"]
                for item in row["placements"]
                if item["placement_id"] == "SFX_WOW"
            )
            wow["sfx_seed"] = 2
            plan.write_text(json.dumps(payload), encoding="utf-8")
            rejected_mapping = _run("validate_executable_protocol.py", "--plan", plan)
            self.assertNotEqual(rejected_mapping.returncode, 0)
            self.assertIn("V2_A11_SFX_MAPPING_INVALID:SFX_WOW", rejected_mapping.stdout)
            contract, _, assets = _write_v2_fixture(root)
            rejected_mapping_build = _run(
                "build_v2_contract_project.py", "--production-plan", plan,
                "--root-contract", contract, "--workspace-root", root,
                "--asset-manifest", assets, "--output-project", root / "wrong-sfx-output",
                "--receipt", root / "wrong-sfx-receipt.json",
            )
            self.assertNotEqual(rejected_mapping_build.returncode, 0)
            self.assertIn("V2_A11_SFX_MAPPING_INVALID:SFX_WOW", rejected_mapping_build.stdout)

            compiled = _run(
                "compile_production_plan.py", "--approved-timeline", source, "--output", plan
            )
            self.assertEqual(compiled.returncode, 0, compiled.stdout + compiled.stderr)
            payload = json.loads(plan.read_text(encoding="utf-8"))
            duplicate_row = json.loads(json.dumps(payload["timeline"][3]))
            duplicate_row["segment_key"] = "DUPLICATE_ROW"
            payload["timeline"].append(duplicate_row)
            plan.write_text(json.dumps(payload), encoding="utf-8")
            rejected_builder = _run(
                "build_v2_contract_project.py", "--production-plan", plan,
                "--root-contract", contract, "--workspace-root", root,
                "--asset-manifest", assets, "--output-project", root / "duplicate-output",
                "--receipt", root / "duplicate-receipt.json",
            )
            self.assertNotEqual(rejected_builder.returncode, 0)
            self.assertIn("V2_DUPLICATE_PLACEMENT_ID", rejected_builder.stdout)

    def test_v2_builder_stages_validates_and_promotes_project(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            contract, layout, assets = _write_v2_fixture(root)
            timeline = root / "approved_timeline.json"
            plan = root / "production_plan.json"
            output = root / "final" / "SH_V2_TEST_capcut"
            receipt = root / "build_receipt.json"
            timeline.write_text(json.dumps(_approved_timeline()), encoding="utf-8")
            compiled = _run(
                "compile_production_plan.py",
                "--approved-timeline",
                timeline,
                "--output",
                plan,
            )
            self.assertEqual(compiled.returncode, 0, compiled.stdout + compiled.stderr)
            compiled_plan = json.loads(plan.read_text(encoding="utf-8"))
            placements = {
                placement["placement_id"]: placement
                for row in compiled_plan["timeline"]
                for placement in row["placements"]
            }
            placements["T1_FIXED"]["operation"] = "replace_template_text"
            placements["SPEAKER_UNKNOWN"]["operation"] = "clear"
            plan.write_text(json.dumps(compiled_plan), encoding="utf-8")
            archive = root / "shrt_white_base_v2.zip"
            source_sha_before = hashlib.sha256(archive.read_bytes()).hexdigest()

            built = _run(
                "build_v2_contract_project.py",
                "--production-plan",
                plan,
                "--root-contract",
                contract,
                "--workspace-root",
                root,
                "--asset-manifest",
                assets,
                "--output-project",
                output,
                "--receipt",
                receipt,
            )

            self.assertEqual(built.returncode, 0, built.stdout + built.stderr)
            self.assertTrue(output.is_dir())
            self.assertEqual(source_sha_before, hashlib.sha256(archive.read_bytes()).hexdigest())
            build_receipt = json.loads(receipt.read_text(encoding="utf-8"))
            self.assertEqual(build_receipt["status"], "PASS")
            self.assertEqual(build_receipt["track_count"], 15)
            self.assertEqual(build_receipt["root_timeline_parity"], "PASS")
            self.assertEqual(build_receipt["id_mirror"], "PASS")

            validated = _run(
                "validate_v2_contract_project.py",
                "--project",
                output,
                "--production-plan",
                plan,
                "--layout-contract",
                layout,
            )
            self.assertEqual(validated.returncode, 0, validated.stdout + validated.stderr)
            readback = json.loads(validated.stdout)
            self.assertEqual(readback["status"], "PASS")
            self.assertEqual(readback["readback"]["A10_TEXT_UNASSIGNED"], [])
            content = json.loads((output / "draft_content.json").read_text(encoding="utf-8"))
            video_track = next(track for track in content["tracks"] if track["id"] == "track-video")
            video_material_id = video_track["segments"][0]["material_id"]
            video_material = next(
                item for item in content["materials"]["videos"] if item["id"] == video_material_id
            )
            self.assertEqual(
                video_material["path"],
                "##_draftpath_placeholder_fixture_##/Resources/media/clean_video.mp4",
            )

            content_path = output / "draft_content.json"
            content = json.loads(content_path.read_text(encoding="utf-8"))
            a11 = next(track for track in content["tracks"] if track["id"] == "track-a11")
            a11["segments"][0]["volume"] = 0
            content_path.write_text(json.dumps(content), encoding="utf-8")
            rejected = _run(
                "validate_v2_contract_project.py",
                "--project",
                output,
                "--production-plan",
                plan,
                "--layout-contract",
                layout,
            )
            self.assertNotEqual(rejected.returncode, 0)
            self.assertIn("V2_A11_SFX_VOLUME_INVALID", rejected.stdout)

    def test_static_validator_rejects_fuzzy_blur_and_portable_path_damage(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            contract, layout, assets = _write_v2_fixture(root)
            approved = root / "approved.json"
            plan = root / "plan.json"
            output = root / "output"
            receipt = root / "receipt.json"
            approved.write_text(json.dumps(_approved_timeline()), encoding="utf-8")
            compiled = _run("compile_production_plan.py", "--approved-timeline", approved, "--output", plan)
            self.assertEqual(compiled.returncode, 0, compiled.stdout + compiled.stderr)
            built = _run(
                "build_v2_contract_project.py",
                "--production-plan", plan,
                "--root-contract", contract,
                "--workspace-root", root,
                "--asset-manifest", assets,
                "--output-project", output,
                "--receipt", receipt,
            )
            self.assertEqual(built.returncode, 0, built.stdout + built.stderr)
            content_path = output / "draft_content.json"
            content = json.loads(content_path.read_text(encoding="utf-8"))
            white = next(track for track in content["tracks"] if track["id"] == "track-white")
            white["segments"][0]["extra_material_refs"] = []
            content_path.write_text(json.dumps(content), encoding="utf-8")
            rejected_style = _run(
                "validate_v2_contract_project.py", "--project", output,
                "--production-plan", plan, "--layout-contract", layout,
            )
            self.assertNotEqual(rejected_style.returncode, 0)
            self.assertIn("V2_FUZZY_BLUR_STYLE_INVALID:A10_TEXT_WHITE", rejected_style.stdout)

            content = json.loads((output / "Timelines" / content["main_timeline_id"] / "draft_content.json").read_text(encoding="utf-8"))
            video = next(track for track in content["tracks"] if track["id"] == "track-video")
            video_material_id = video["segments"][0]["material_id"]
            video_material = next(item for item in content["materials"]["videos"] if item["id"] == video_material_id)
            video_material["path"] = "C:\\machine-local\\source.mp4"
            for path in (content_path, output / "Timelines" / content["main_timeline_id"] / "draft_content.json"):
                path.write_text(json.dumps(content), encoding="utf-8")
            rejected_path = _run(
                "validate_v2_contract_project.py", "--project", output,
                "--production-plan", plan, "--layout-contract", layout,
            )
            self.assertNotEqual(rejected_path.returncode, 0)
            self.assertIn("V2_MEDIA_PATH_NOT_PORTABLE:VIDEO_01", rejected_path.stdout)

    def test_builder_preserves_existing_output_and_rejects_invalid_plan_before_extract(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            contract, _, assets = _write_v2_fixture(root)
            approved = root / "approved.json"
            plan = root / "plan.json"
            approved.write_text(json.dumps(_approved_timeline()), encoding="utf-8")
            compiled = _run(
                "compile_production_plan.py", "--approved-timeline", approved, "--output", plan
            )
            self.assertEqual(compiled.returncode, 0, compiled.stdout + compiled.stderr)
            output = root / "final" / "existing"
            output.mkdir(parents=True)
            sentinel = output / "keep.txt"
            sentinel.write_text("user-data", encoding="utf-8")
            receipt = root / "receipt.json"

            rejected_existing = _run(
                "build_v2_contract_project.py",
                "--production-plan", plan,
                "--root-contract", contract,
                "--workspace-root", root,
                "--asset-manifest", assets,
                "--output-project", output,
                "--receipt", receipt,
            )
            self.assertNotEqual(rejected_existing.returncode, 0)
            self.assertEqual(sentinel.read_text(encoding="utf-8"), "user-data")

            invalid_output = root / "final" / "invalid-plan"
            payload = json.loads(plan.read_text(encoding="utf-8"))
            payload["timeline"][0]["placements"][0]["target_range_us"] = [9, 1]
            plan.write_text(json.dumps(payload), encoding="utf-8")
            rejected_plan = _run(
                "build_v2_contract_project.py",
                "--production-plan", plan,
                "--root-contract", contract,
                "--workspace-root", root,
                "--asset-manifest", assets,
                "--output-project", invalid_output,
                "--receipt", receipt,
            )
            self.assertNotEqual(rejected_plan.returncode, 0)
            self.assertIn("V2_PRODUCTION_PLAN_SCHEMA_INVALID", rejected_plan.stdout)
            self.assertFalse(invalid_output.exists())

    def test_receipt_failure_rolls_back_only_new_output_and_retry_succeeds(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            contract, _, assets = _write_v2_fixture(root)
            approved = root / "approved.json"
            plan = root / "plan.json"
            output = root / "final" / "retry-safe"
            bad_receipt = root / "receipt-as-directory"
            bad_receipt.mkdir()
            approved.write_text(json.dumps(_approved_timeline()), encoding="utf-8")
            compiled = _run("compile_production_plan.py", "--approved-timeline", approved, "--output", plan)
            self.assertEqual(compiled.returncode, 0, compiled.stdout + compiled.stderr)

            failed = _run(
                "build_v2_contract_project.py", "--production-plan", plan,
                "--root-contract", contract, "--workspace-root", root,
                "--asset-manifest", assets, "--output-project", output,
                "--receipt", bad_receipt,
            )
            self.assertNotEqual(failed.returncode, 0)
            self.assertFalse(output.exists())
            self.assertTrue(bad_receipt.is_dir())

            good_receipt = root / "receipt.json"
            retried = _run(
                "build_v2_contract_project.py", "--production-plan", plan,
                "--root-contract", contract, "--workspace-root", root,
                "--asset-manifest", assets, "--output-project", output,
                "--receipt", good_receipt,
            )
            self.assertEqual(retried.returncode, 0, retried.stdout + retried.stderr)
            self.assertTrue(output.is_dir())
            self.assertEqual(json.loads(good_receipt.read_text(encoding="utf-8"))["status"], "PASS")

    def test_different_assets_cannot_share_one_portable_destination_name(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            contract, _, assets_path = _write_v2_fixture(root)
            approved = root / "approved.json"
            plan = root / "plan.json"
            output = root / "output"
            receipt = root / "receipt.json"
            approved.write_text(json.dumps(_approved_timeline()), encoding="utf-8")
            compiled = _run("compile_production_plan.py", "--approved-timeline", approved, "--output", plan)
            self.assertEqual(compiled.returncode, 0, compiled.stdout + compiled.stderr)
            assets = json.loads(assets_path.read_text(encoding="utf-8"))
            assets["assets"]["clean_video"]["relative_name"] = "collision.bin"
            assets["assets"]["bgm"]["relative_name"] = "collision.bin"
            assets_path.write_text(json.dumps(assets), encoding="utf-8")

            rejected = _run(
                "build_v2_contract_project.py", "--production-plan", plan,
                "--root-contract", contract, "--workspace-root", root,
                "--asset-manifest", assets_path, "--output-project", output,
                "--receipt", receipt,
            )
            self.assertNotEqual(rejected.returncode, 0)
            self.assertIn("V2_ASSET_DESTINATION_COLLISION:collision.bin", rejected.stdout)
            self.assertFalse(output.exists())

    def test_episode_asset_cannot_overwrite_different_immutable_root_fixed_asset(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            contract, _, assets_path = _write_v2_fixture(root)
            approved = root / "approved.json"
            plan = root / "plan.json"
            output = root / "output"
            receipt = root / "receipt.json"
            approved.write_text(json.dumps(_approved_timeline()), encoding="utf-8")
            compiled = _run("compile_production_plan.py", "--approved-timeline", approved, "--output", plan)
            self.assertEqual(compiled.returncode, 0, compiled.stdout + compiled.stderr)
            fixed_asset = (
                root
                / "template"
                / "shrt_white_base_v2"
                / "Resources"
                / "media"
                / "transparent_center_white_1080x1920.png"
            )
            archive = root / "shrt_white_base_v2.zip"
            fixed_sha_before = hashlib.sha256(fixed_asset.read_bytes()).hexdigest()
            archive_sha_before = hashlib.sha256(archive.read_bytes()).hexdigest()
            assets = json.loads(assets_path.read_text(encoding="utf-8"))
            assets["assets"]["clean_video"]["relative_name"] = fixed_asset.name.upper()
            assets_path.write_text(json.dumps(assets), encoding="utf-8")

            rejected = _run(
                "build_v2_contract_project.py", "--production-plan", plan,
                "--root-contract", contract, "--workspace-root", root,
                "--asset-manifest", assets_path, "--output-project", output,
                "--receipt", receipt,
            )
            self.assertNotEqual(rejected.returncode, 0)
            self.assertIn(
                "V2_ROOT_ASSET_DESTINATION_COLLISION:TRANSPARENT_CENTER_WHITE_1080X1920.PNG",
                rejected.stdout,
            )
            self.assertFalse(output.exists())
            self.assertEqual(fixed_sha_before, hashlib.sha256(fixed_asset.read_bytes()).hexdigest())
            self.assertEqual(archive_sha_before, hashlib.sha256(archive.read_bytes()).hexdigest())

    def test_text_replacement_preserves_all_non_allowlisted_material_metadata(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            contract, _, assets = _write_v2_fixture(root)
            approved = root / "approved.json"
            plan = root / "plan.json"
            output = root / "output"
            receipt = root / "receipt.json"
            approved.write_text(json.dumps(_approved_timeline()), encoding="utf-8")
            compiled = _run("compile_production_plan.py", "--approved-timeline", approved, "--output", plan)
            self.assertEqual(compiled.returncode, 0, compiled.stdout + compiled.stderr)
            seed = json.loads(
                (root / "template" / "shrt_white_base_v2" / "draft_content.json").read_text(
                    encoding="utf-8"
                )
            )
            seed_track = next(track for track in seed["tracks"] if track["id"] == "track-white")
            seed_material = next(
                item
                for item in seed["materials"]["texts"]
                if item["id"] == seed_track["segments"][0]["material_id"]
            )
            built = _run(
                "build_v2_contract_project.py", "--production-plan", plan,
                "--root-contract", contract, "--workspace-root", root,
                "--asset-manifest", assets, "--output-project", output,
                "--receipt", receipt,
            )
            self.assertEqual(built.returncode, 0, built.stdout + built.stderr)
            result = json.loads((output / "draft_content.json").read_text(encoding="utf-8"))
            result_track = next(track for track in result["tracks"] if track["id"] == "track-white")
            result_material = next(
                item
                for item in result["materials"]["texts"]
                if item["id"] == result_track["segments"][0]["material_id"]
            )

            seed_normalized = copy.deepcopy(seed_material)
            result_normalized = copy.deepcopy(result_material)
            seed_normalized.pop("id")
            result_normalized.pop("id")
            for material in (seed_normalized, result_normalized):
                rich = json.loads(material["content"])
                rich["text"] = "<allowed-text>"
                for style in rich["styles"]:
                    style["range"] = [0, 0]
                material["content"] = rich
                material["text"] = "<allowed-text>"
            self.assertEqual(result_normalized, seed_normalized)
            self.assertNotIn("role", result_material)
            self.assertNotIn("desc", result_material)

    def test_a9_a10_timeline_rows_compile_as_muted_seeds(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            contract, layout, assets = _write_v2_fixture(root)
            approved_payload = _approved_timeline()
            approved_payload["segments"].extend(
                [
                    {
                        "segment_id": "A9_LIVE",
                        "timeline_order": 12,
                        "role": "A9",
                        "start": 1_000_000,
                        "duration": 1_000_000,
                        "source_ref": "tts-source",
                        "source_range_us": [0, 1_000_000],
                        "asset_key": "tts",
                    },
                    {
                        "segment_id": "A10_LIVE",
                        "timeline_order": 13,
                        "role": "A10",
                        "start": 2_000_000,
                        "duration": 1_000_000,
                        "source_ref": "speech-source",
                        "source_range_us": [0, 1_000_000],
                        "asset_key": "speech",
                    },
                ]
            )
            approved = root / "approved.json"
            plan = root / "plan.json"
            output = root / "output"
            receipt = root / "receipt.json"
            approved.write_text(json.dumps(approved_payload), encoding="utf-8")
            compiled = _run(
                "compile_production_plan.py", "--approved-timeline", approved, "--output", plan
            )
            self.assertEqual(compiled.returncode, 0, compiled.stdout + compiled.stderr)
            payload = json.loads(plan.read_text(encoding="utf-8"))
            placements = {
                item["placement_id"]: item
                for row in payload["timeline"]
                for item in row["placements"]
            }
            self.assertEqual(placements["A9_LIVE"]["operation"], "preserve_muted_seed")
            self.assertEqual(placements["A10_LIVE"]["operation"], "preserve_muted_seed")
            self.assertEqual(placements["A9_LIVE"]["volume"], 0)
            self.assertEqual(placements["A10_LIVE"]["volume"], 0)
            self.assertNotIn("A9_SEED", placements)
            self.assertNotIn("A10_SEED", placements)

            built = _run(
                "build_v2_contract_project.py",
                "--production-plan", plan,
                "--root-contract", contract,
                "--workspace-root", root,
                "--asset-manifest", assets,
                "--output-project", output,
                "--receipt", receipt,
            )
            self.assertEqual(built.returncode, 0, built.stdout + built.stderr)
            checked = _run(
                "validate_v2_contract_project.py",
                "--project", output,
                "--production-plan", plan,
                "--layout-contract", layout,
            )
            self.assertEqual(checked.returncode, 0, checked.stdout + checked.stderr)
            content = json.loads((output / "draft_content.json").read_text(encoding="utf-8"))
            tracks = {track["id"]: track for track in content["tracks"]}
            self.assertEqual(tracks["track-a9"]["segments"][0]["volume"], 0)
            self.assertEqual(tracks["track-a10"]["segments"][0]["volume"], 0)

            tracks["track-a9"]["segments"][0]["volume"] = 1
            for content_path in (
                output / "draft_content.json",
                output / "Timelines" / content["main_timeline_id"] / "draft_content.json",
            ):
                content_path.write_text(json.dumps(content), encoding="utf-8")
            rejected_readback = _run(
                "validate_v2_contract_project.py",
                "--project",
                output,
                "--production-plan",
                plan,
                "--layout-contract",
                layout,
            )
            self.assertNotEqual(rejected_readback.returncode, 0)
            self.assertIn("V2_MUTED_SEED_READBACK_INVALID:A9", rejected_readback.stdout)

    @unittest.skipUnless(os.environ.get("SHORTS_V2_AUTHORITY_DIR"), "external v2 authority not configured")
    def test_actual_immutable_v2_root_roundtrip(self):
        authority = Path(os.environ["SHORTS_V2_AUTHORITY_DIR"]).resolve()
        workspace_root = authority.parents[3]
        contract = authority / "shorts_capcut_root_contract_v2.json"
        layout = authority / "shrt_white_base_v2_layout_contract_v1.json"
        archive = authority / "shrt_white_base_v2_CAPCUT_20260807.zip"
        self.assertTrue(contract.is_file())
        self.assertTrue(layout.is_file())
        source_sha_before = hashlib.sha256(archive.read_bytes()).hexdigest()
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            approved = root / "approved_timeline.json"
            plan = root / "production_plan.json"
            output = root / "output" / "actual-v2-roundtrip"
            receipt = root / "receipt.json"
            video = root / "clean_video.mp4"
            bgm = root / "bgm.aac"
            assets = root / "assets.json"
            video.write_bytes(b"fixture-video")
            bgm.write_bytes(b"fixture-bgm")
            assets.write_text(
                json.dumps({"assets": {"clean_video": {"path": str(video)}, "bgm": {"path": str(bgm)}}}),
                encoding="utf-8",
            )
            approved.write_text(json.dumps(_approved_timeline()), encoding="utf-8")
            compiled = _run("compile_production_plan.py", "--approved-timeline", approved, "--output", plan)
            self.assertEqual(compiled.returncode, 0, compiled.stdout + compiled.stderr)
            built = _run(
                "build_v2_contract_project.py",
                "--production-plan",
                plan,
                "--root-contract",
                contract,
                "--workspace-root",
                workspace_root,
                "--asset-manifest",
                assets,
                "--output-project",
                output,
                "--receipt",
                receipt,
            )
            self.assertEqual(built.returncode, 0, built.stdout + built.stderr)
            checked = _run(
                "validate_v2_contract_project.py",
                "--project",
                output,
                "--production-plan",
                plan,
                "--layout-contract",
                layout,
            )
            self.assertEqual(checked.returncode, 0, checked.stdout + checked.stderr)
            self.assertEqual(source_sha_before, hashlib.sha256(archive.read_bytes()).hexdigest())


if __name__ == "__main__":
    unittest.main()

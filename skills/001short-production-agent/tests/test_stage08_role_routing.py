import json
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch


SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import build_episode_capcut as builder
import validate_build_inputs as build_inputs
import validate_capcut_project as readback
import validate_design_lock
from track_contract import TRACK_LAYOUT


def approved_timeline():
    rows = [
        ("video", "VIDEO", 0, 1_000, {}),
        ("screen-effect", "SCREEN_EFFECT", 0, 1_000, {}),
        ("screen-white", "SCREEN_WHITE", 0, 1_000, {}),
        ("t1", "T1", 0, 1_000, {"text": "Seoul day", "content_type": "TITLE"}),
        ("t2", "T2", 0, 1_000, {"text": "Stream view", "content_type": "TITLE"}),
        ("speaker-primary", "A10_TEXT", 0, 400, {
            "text": "Amazing", "content_type": "SPEAKER", "caption_role": "A10_TEXT",
            "speaker_id": "SPK_01", "color_role": "WHITE",
        }),
        ("speaker-other", "A10_TEXT", 400, 400, {
            "text": "So nice", "content_type": "SPEAKER", "caption_role": "A10_TEXT",
            "speaker_id": "SPK_02", "color_role": "YELLOW",
        }),
        ("state", "STATE", 800, 200, {
            "text": "Firstsee", "content_type": "SITUATION", "caption_role": "STATE",
            "state_effect": "LASER_CUT",
        }),
    ]
    return {
        "schema_version": "approved-timeline-v1", "episode_id": "EP",
        "source_fingerprint": "fixture", "primary_speaker_id": "SPK_01",
        "segments": [
            {"segment_id": segment_id, "timeline_order": index, "role": role,
             "start": start, "duration": duration, "source_ref": "source", **extra}
            for index, (segment_id, role, start, duration, extra) in enumerate(
                sorted(rows, key=lambda row: (row[2], row[0])), 1
            )
        ],
    }


def project_payload():
    roles = [
        "VIDEO", "SCREEN_EFFECT", "SCREEN_WHITE", "SOURCE_CREDIT", "STATE_GLITCH",
        "STATE_LASER", "A10_TEXT_WHITE", "A10_TEXT_YELLOW", "A9_TEXT", "T2", "T1",
        "A9", "A10", "A11", "A12_RESERVED_EMPTY",
    ]
    materials, tracks = [], []
    for index, role in enumerate(roles):
        material_id = f"m-{role}"
        material = {
            "id": material_id, "type": "text", "role": role,
            "content": json.dumps({
                "text": "출처 : 채널명" if role == "SOURCE_CREDIT" else "seed",
                "styles": [{"range": [0, 8 if role == "SOURCE_CREDIT" else 4]}],
            }),
        }
        if role in {"VIDEO", "A9", "A10", "A11", "A12_RESERVED_EMPTY"}:
            material = {
                "id": material_id, "type": "video" if role == "VIDEO" else "audio",
                "role": role,
                "path": f"##_draftpath_placeholder_fixture_##/Resources/media/{role.lower()}.bin",
            }
        materials.append(material)
        tracks.append({"id": f"track-{index}", "segments": [{
            "id": f"seed-{role}", "material_id": material_id,
            "target_timerange": {"start": 0, "duration": 1},
            "source_timerange": {"start": 0, "duration": 1},
        }]})
    return {"tracks": tracks, "materials": {"items": materials}}


class Stage08RoleRoutingTest(unittest.TestCase):
    def _normalize_source_credit_fixture(self, source_credit=None):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            project = root / "project"
            media = project / "Resources" / "media"
            media.mkdir(parents=True)
            (media / "transparent_center_white_1080x1920.png").write_bytes(b"white")
            video = root / "source.mp4"; video.write_bytes(b"video")
            audio = root / "vocals.wav"; audio.write_bytes(b"audio")
            timeline_path = root / "timeline.json"
            timeline_path.write_text(json.dumps(approved_timeline()), encoding="utf-8")
            document = project / "draft_content.json"
            document.write_text(json.dumps(project_payload()), encoding="utf-8")
            (project / "draft_meta_info.json").write_text(
                json.dumps({"draft_id": "fixture"}), encoding="utf-8"
            )
            config = {
                "episode_id": "EP", "duration_us": 1_000,
                "approved_timeline_path": str(timeline_path),
                "T1": "Seoul day", "T2": "Stream view",
                "state_cues": [{"text": "Firstsee", "start_us": 800, "end_us": 1_000}],
                "audio_role": "A10",
                "_visual_input": {"video_input_path": str(video), "resource_name": "source.mp4"},
                "_resolved_root_contract": {"template_profile": "shrt_white_base_v3"},
            }
            if source_credit is not None:
                config["SOURCE_CREDIT"] = source_credit
            manifest = {
                "urakkai": {"video_clips": [{
                    "clip_id": "video", "source_range_us": [0, 1_000],
                    "target_range_us": [0, 1_000],
                }]},
                "source_audio": [],
            }
            with patch.object(builder, "_video_dimensions", return_value=(1080, 1920)):
                builder._normalize_source(project, config, audio, manifest)
            return json.loads(document.read_text(encoding="utf-8"))

    def test_source_credit_is_rebuilt_full_span_only_when_declared(self):
        declared = self._normalize_source_credit_fixture("출처 : 실제 채널")
        segments = declared["tracks"][3]["segments"]
        self.assertEqual(len(segments), 1)
        self.assertEqual(segments[0]["role"], "SOURCE_CREDIT")
        self.assertEqual(segments[0]["target_timerange"], {"start": 0, "duration": 1_000})
        material = next(
            row for row in declared["materials"]["items"]
            if row["id"] == segments[0]["material_id"]
        )
        self.assertEqual(json.loads(material["content"])["text"], "출처 : 실제 채널")

        undeclared = self._normalize_source_credit_fixture()
        self.assertEqual(undeclared["tracks"][3]["segments"], [])

    def test_v3_source_credit_readback_is_layout_range_and_text_bound(self):
        built = self._normalize_source_credit_fixture("출처 : 실제 채널")
        model = SimpleNamespace(tracks=built["tracks"], materials=built["materials"])
        timeline = approved_timeline()
        contract = {
            "track_layout_version": "shrt_white_base_v3_15",
            "timeline": [
                {**row, "end": row["start"] + row["duration"]}
                for row in timeline["segments"]
            ],
            "approved_role_text": {
                "T1": "Seoul day", "T2": "Stream view",
                "SOURCE_CREDIT": "출처 : 실제 채널",
            },
            "approved_segment_text": {
                row["segment_id"]: {
                    "role": row["role"], "start": row["start"],
                    "duration": row["duration"], "text": row["text"],
                    **({"color_role": row["color_role"]} if row["role"] == "A10_TEXT" else {}),
                    **({"state_effect": row["state_effect"]} if row["role"] == "STATE" else {}),
                }
                for row in timeline["segments"]
                if row["role"] in {"A10_TEXT", "STATE"}
            },
        }
        self.assertEqual(readback.validate_v2_role_routing(model, contract), [])

        model.tracks[3]["segments"][0]["target_timerange"]["duration"] = 999
        self.assertIn("FULL_SPAN_ANCHOR_MISMATCH", {
            item["code"] for item in readback.validate_v2_role_routing(model, contract)
        })
        model.tracks[3]["segments"][0]["target_timerange"]["duration"] = 1_000
        source_material = next(
            row for row in model.materials["items"]
            if row["id"] == model.tracks[3]["segments"][0]["material_id"]
        )
        source_material["content"] = json.dumps({
            "text": "출처 : 다른 채널", "styles": [{"range": [0, 10]}]
        })
        self.assertIn("TITLE_TEXT_AUTHORITY_MISMATCH", {
            item["code"] for item in readback.validate_v2_role_routing(model, contract)
        })

    def test_v2_layout_remains_valid_with_track_three_empty(self):
        built = self._normalize_source_credit_fixture()
        model = SimpleNamespace(tracks=built["tracks"], materials=built["materials"])
        timeline = approved_timeline()
        contract = {
            "track_layout_version": "shrt_white_base_v2_15",
            "root_template_profile": "shrt_white_base_v2",
            "timeline": [
                {**row, "end": row["start"] + row["duration"]}
                for row in timeline["segments"]
            ],
            "approved_role_text": {"T1": "Seoul day", "T2": "Stream view"},
            "approved_segment_text": {
                row["segment_id"]: {
                    "role": row["role"], "start": row["start"],
                    "duration": row["duration"], "text": row["text"],
                    **({"color_role": row["color_role"]} if row["role"] == "A10_TEXT" else {}),
                    **({"state_effect": row["state_effect"]} if row["role"] == "STATE" else {}),
                }
                for row in timeline["segments"]
                if row["role"] in {"A10_TEXT", "STATE"}
            },
        }
        self.assertEqual(readback.validate_v2_role_routing(model, contract), [])

    def test_build_contract_schema_keeps_source_credit_optional_and_nonempty(self):
        schema = json.loads(readback.BUILD_SCHEMA.read_text(encoding="utf-8"))
        role_schema = schema["properties"]["approved_role_text"]
        self.assertEqual(
            readback.validate_schema({"T1": "title", "T2": "subtitle"}, role_schema),
            [],
        )
        self.assertEqual(
            readback.validate_schema({
                "T1": "title", "T2": "subtitle", "SOURCE_CREDIT": "출처 : 채널",
            }, role_schema),
            [],
        )
        self.assertTrue(readback.validate_schema({
            "T1": "title", "T2": "subtitle", "SOURCE_CREDIT": "",
        }, role_schema))
        self.assertEqual(
            schema["properties"]["track_layout_version"]["enum"],
            ["shrt_white_base_v2_15", "shrt_white_base_v3_15"],
        )
        self.assertEqual(
            schema["properties"]["root_template_profile"]["enum"],
            ["shrt_white_base_v2", "shrt_white_base_v3"],
        )

    def test_builder_binds_v2_and_v3_profiles_to_their_layout_ids(self):
        expected = {
            "shrt_white_base_v2": "shrt_white_base_v2_15",
            "shrt_white_base_v3": "shrt_white_base_v3_15",
        }
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            contract_path = root / "contract.json"
            contract_path.write_text("{}", encoding="utf-8")
            archive = root / "template.zip"
            archive.write_bytes(b"zip")
            for profile, layout in expected.items():
                config = {
                    "workspace_root": str(root), "root_profile": "fixture",
                    "root_contract_path": "contract.json",
                }
                resolved = {
                    "profile": "fixture", "template_profile": profile,
                    "archive_sha256": "a" * 64, "archive": str(archive),
                }
                with patch.object(
                    builder.resolve_shorts_capcut_root,
                    "resolve_root_contract",
                    return_value=resolved,
                ):
                    builder._bind_portable_root_contract(config)
                self.assertEqual(
                    config["_resolved_root_contract"]["track_layout_version"], layout
                )

    def test_v3_template_requires_source_credit_seed_but_v2_remains_valid(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)

            def archive_for(name, payload):
                archive = root / name
                with zipfile.ZipFile(archive, "w") as bundle:
                    raw = json.dumps(payload)
                    bundle.writestr("root/draft_content.json", raw)
                    bundle.writestr("root/Timelines/main/draft_content.json", raw)
                return archive

            populated = archive_for("populated.zip", project_payload())
            builder._validate_template_track_layout(populated, "shrt_white_base_v3")

            missing_payload = project_payload()
            missing_payload["tracks"][3]["segments"] = []
            missing = archive_for("missing.zip", missing_payload)
            with self.assertRaisesRegex(
                RuntimeError, "PINNED_TEMPLATE_ANCHOR_MISSING:SOURCE_CREDIT"
            ):
                builder._validate_template_track_layout(missing, "shrt_white_base_v3")
            builder._validate_template_track_layout(missing, "shrt_white_base_v2")

    def test_design_role_contract_accepts_canonical_rows(self):
        self.assertEqual(validate_design_lock.validate_role_contract(approved_timeline()), [])

    def test_design_role_contract_rejects_title_and_cross_routing_errors(self):
        def row(timeline, segment_id):
            return next(item for item in timeline["segments"] if item["segment_id"] == segment_id)

        cases = []
        blank_t2 = approved_timeline(); row(blank_t2, "t2")["text"] = ""
        cases.append((blank_t2, "TITLE_TEXT_REQUIRED"))
        speaker_on_state = approved_timeline(); row(speaker_on_state, "speaker-primary")["role"] = "STATE"
        cases.append((speaker_on_state, "SPEAKER_ROLE_MISMATCH"))
        state_on_speaker = approved_timeline(); row(state_on_speaker, "state")["role"] = "A10_TEXT"
        cases.append((state_on_speaker, "STATE_ROLE_MISMATCH"))
        unassigned = approved_timeline(); row(unassigned, "speaker-primary")["speaker_id"] = "UNASSIGNED"
        cases.append((unassigned, "SPEAKER_ID_UNASSIGNED"))
        wrong_color = approved_timeline(); row(wrong_color, "speaker-other")["color_role"] = "WHITE"
        cases.append((wrong_color, "SPEAKER_COLOR_ROLE_MISMATCH"))
        long_state = approved_timeline(); row(long_state, "state")["text"] = "This state line is too long"
        cases.append((long_state, "STATE_TEXT_TOO_LONG"))
        for timeline, code in cases:
            with self.subTest(code=code):
                self.assertIn(code, {
                    item["code"] for item in validate_design_lock.validate_role_contract(timeline)
                })

    def test_plan_to_builder_to_readback_routes_titles_speaker_and_state(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            project = root / "project"
            media = project / "Resources" / "media"
            media.mkdir(parents=True)
            (media / "transparent_center_white_1080x1920.png").write_bytes(b"white")
            video = root / "source.mp4"; video.write_bytes(b"video")
            audio = root / "vocals.wav"; audio.write_bytes(b"audio")
            timeline_path = root / "timeline.json"
            timeline = approved_timeline()
            timeline_path.write_text(json.dumps(timeline), encoding="utf-8")
            document = project / "draft_content.json"
            payload = project_payload()
            document.write_text(json.dumps(payload), encoding="utf-8")
            (project / "draft_meta_info.json").write_text(
                json.dumps({"draft_id": "fixture"}), encoding="utf-8"
            )
            config = {
                "episode_id": "EP", "duration_us": 1_000,
                "approved_timeline_path": str(timeline_path),
                "T1": "Seoul day", "T2": "Stream view",
                "state_cues": [{"text": "Firstsee", "start_us": 800, "end_us": 1_000}],
                "audio_role": "A10",
                "_visual_input": {"video_input_path": str(video), "resource_name": "source.mp4"},
            }
            manifest = {
                "urakkai": {"video_clips": [{
                    "clip_id": "video", "source_range_us": [0, 1_000],
                    "target_range_us": [0, 1_000],
                }]},
                "source_audio": [],
            }
            with patch.object(builder, "_video_dimensions", return_value=(1080, 1920)):
                builder._normalize_source(project, config, audio, manifest)
            built = json.loads(document.read_text(encoding="utf-8"))
            model = SimpleNamespace(tracks=built["tracks"], materials=built["materials"])
            contract_rows = [
                {**row, "end": row["start"] + row["duration"]}
                for row in timeline["segments"]
            ]
            self.assertEqual(readback.validate_v2_role_routing(model, {
                "track_layout_version": TRACK_LAYOUT,
                "timeline": contract_rows,
                "approved_role_text": {"T1": "Seoul day", "T2": "Stream view"},
                "approved_segment_text": {
                    row["segment_id"]: {
                        "role": row["role"], "start": row["start"],
                        "duration": row["duration"], "text": row["text"],
                        **({"color_role": row["color_role"]} if row["role"] == "A10_TEXT" else {}),
                        **({"state_effect": row["state_effect"]} if row["role"] == "STATE" else {}),
                    }
                    for row in timeline["segments"]
                    if row["role"] in {"A10_TEXT", "STATE"}
                },
                "primary_speaker_id": "SPK_01",
            }), [])

    def test_builder_readback_rejects_title_mismatch(self):
        payload = project_payload()
        for index, segment_id, role, text in (
            (9, "t2", "T2", "Different title"),
            (10, "t1", "T1", "Seoul day"),
        ):
            segment = payload["tracks"][index]["segments"][0]
            segment.update({"id": segment_id, "role": role})
            material = next(
                row for row in payload["materials"]["items"]
                if row["id"] == segment["material_id"]
            )
            material["content"] = json.dumps({
                "text": text, "styles": [{"range": [0, len(text)]}]
            })
        model = SimpleNamespace(tracks=payload["tracks"], materials=payload["materials"])
        contract = {
            "track_layout_version": TRACK_LAYOUT,
            "timeline": approved_timeline()["segments"],
            "approved_role_text": {"T1": "Seoul day", "T2": "Stream view"},
        }
        self.assertIn("TITLE_TEXT_AUTHORITY_MISMATCH", {
            item["code"] for item in readback.validate_v2_role_routing(model, contract)
        })

    def test_readback_rejects_cross_track_placement(self):
        payload = project_payload()
        model = SimpleNamespace(tracks=payload["tracks"], materials=payload["materials"])
        model.tracks[3]["segments"] = [{
            "id": "speaker-primary", "role": "A10_TEXT", "color_role": "WHITE"
        }]
        contract = {
            "track_layout_version": TRACK_LAYOUT,
            "timeline": approved_timeline()["segments"],
            "approved_role_text": {"T1": "Seoul day", "T2": "Stream view"},
        }
        self.assertIn("V2_ROLE_TRACK_MISMATCH", {
            item["code"] for item in readback.validate_v2_role_routing(model, contract)
        })


class SourceCreditContractOnlyRoleTest(unittest.TestCase):
    """The credit row lives in the contract but never in the approved timeline.

    Its authority is v_plan, so the builder injects it after the timeline was
    approved.  Both timeline-vs-contract gates have to skip it or the episode is
    unbuildable either way: declared in the approved timeline it is counted twice
    against the draft, omitted it reads as contract-only drift.
    """

    @staticmethod
    def _rows():
        return [
            {"segment_id": "V01", "role": "VIDEO", "start": 0, "duration": 8_000_000},
            {"segment_id": "T1_FULL", "role": "T1", "start": 0, "duration": 8_000_000},
        ]

    def _contract(self, rows, *, with_credit):
        timeline = list(rows)
        if with_credit:
            timeline.append({
                "segment_id": "SOURCE_CREDIT", "role": "SOURCE_CREDIT",
                "start": 0, "duration": 8_000_000,
            })
        return {
            "timeline": timeline,
            "approved_actual_order": [row["segment_id"] for row in timeline],
        }

    def test_credit_row_is_excluded_from_the_timeline_authority_comparison(self):
        rows = self._rows()
        contract = self._contract(rows, with_credit=True)
        only = {
            row["segment_id"] for row in contract["timeline"]
            if row["role"] in build_inputs.CONTRACT_ONLY_ROLES
        }
        self.assertEqual(only, {"SOURCE_CREDIT"})
        kept = [r for r in contract["timeline"] if r["role"] not in build_inputs.CONTRACT_ONLY_ROLES]
        order = [i for i in contract["approved_actual_order"] if i not in only]
        self.assertEqual({r["segment_id"] for r in kept}, {r["segment_id"] for r in rows})
        self.assertEqual(order, [r["segment_id"] for r in rows])

    def test_both_gates_read_the_same_exclusion_set(self):
        self.assertIs(readback.CONTRACT_ONLY_ROLES, build_inputs.CONTRACT_ONLY_ROLES)

    def test_a_contract_without_a_credit_is_unaffected(self):
        rows = self._rows()
        contract = self._contract(rows, with_credit=False)
        kept = [r for r in contract["timeline"] if r["role"] not in build_inputs.CONTRACT_ONLY_ROLES]
        self.assertEqual(kept, rows)


class SourceCreditDesignLockRoleTest(unittest.TestCase):
    """SOURCE_CREDIT is legal and full-span, but only when a plan declares it."""

    @staticmethod
    def _timeline(credit=None):
        rows = [
            {"segment_id": "V01", "role": "VIDEO", "start": 0, "duration": 8_000_000},
            {"segment_id": "T1_FULL", "role": "T1", "start": 0, "duration": 8_000_000,
             "text": "제목 하나", "content_type": "TITLE"},
            {"segment_id": "T2_FULL", "role": "T2", "start": 0, "duration": 8_000_000,
             "text": "제목 둘", "content_type": "TITLE"},
            {"segment_id": "SCREEN_WHITE_FULL", "role": "SCREEN_WHITE", "start": 0, "duration": 8_000_000},
            {"segment_id": "SCREEN_EFFECT_FULL", "role": "SCREEN_EFFECT", "start": 0, "duration": 8_000_000},
        ]
        if credit is not None:
            rows.append({"segment_id": "SOURCE_CREDIT", "role": "SOURCE_CREDIT", **credit})
        return {"segments": rows}

    def _codes(self, timeline):
        return {row["code"] for row in validate_design_lock.validate_role_contract(timeline)}

    def test_source_credit_is_a_legal_role(self):
        self.assertIn("SOURCE_CREDIT", validate_design_lock.LEGAL_ROLES)

    def test_a_timeline_without_a_credit_still_passes(self):
        codes = self._codes(self._timeline())
        self.assertNotIn("ROLE_ANCHOR_INVALID", codes)
        self.assertNotIn("FULL_SPAN_ANCHOR_INVALID", codes)

    def test_a_declared_credit_must_span_the_whole_timeline(self):
        partial = self._timeline({"start": 0, "duration": 4_000_000, "text": "출처 : 채널"})
        self.assertIn("FULL_SPAN_ANCHOR_INVALID", self._codes(partial))

    def test_a_declared_credit_must_carry_text(self):
        blank = self._timeline({"start": 0, "duration": 8_000_000, "text": "   "})
        self.assertIn("TITLE_TEXT_REQUIRED", self._codes(blank))

    def test_an_overlong_credit_is_rejected(self):
        limit = validate_design_lock.MAX_LINE_LENGTH_BY_ROLE["SOURCE_CREDIT"]
        long_credit = self._timeline({"start": 0, "duration": 8_000_000, "text": "가" * (limit + 1)})
        self.assertIn("CAPTION_LINE_TOO_LONG", self._codes(long_credit))


if __name__ == "__main__":
    unittest.main()

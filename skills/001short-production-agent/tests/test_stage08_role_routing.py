import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace


SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import build_episode_capcut as builder
import validate_capcut_project as readback
import validate_design_lock


def approved_timeline():
    rows = [
        ("video", "VIDEO", 0, 1_000, {}),
        ("t1", "T1", 0, 1_000, {"text": "서울 첫날"}),
        ("t2", "T2", 0, 1_000, {"text": "청계천 감탄"}),
        ("speaker-primary", "A10_TEXT", 0, 400, {
            "text": "정말 멋져", "content_type": "SPEAKER", "caption_role": "A10_TEXT",
            "speaker_id": "SPK_01", "color_role": "WHITE",
        }),
        ("speaker-other", "A10_TEXT", 400, 400, {
            "text": "나도 좋아", "content_type": "SPEAKER", "caption_role": "A10_TEXT",
            "speaker_id": "SPK_02", "color_role": "YELLOW",
        }),
        ("state", "STATE", 800, 200, {
            "text": "첫눈에 감탄", "content_type": "SITUATION", "caption_role": "STATE",
            "state_effect": "FLICKER_RAVE",
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
        "VIDEO", "SCREEN_EFFECT", "SCREEN_WHITE", "STATE_FLICKER", "STATE_GLITCH",
        "STATE_LASER", "A10_TEXT_WHITE", "A10_TEXT_YELLOW", "A9_TEXT", "T2", "T1",
        "A9", "A10", "A11", "A12",
    ]
    materials, tracks = [], []
    for index, role in enumerate(roles):
        material_id = f"m-{role}"
        material = {"id": material_id, "type": "text", "role": role,
                    "content": json.dumps({"text": "seed", "styles": [{"range": [0, 4]}]})}
        if role in {"VIDEO", "A9", "A10", "A11", "A12"}:
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
        long_state = approved_timeline(); row(long_state, "state")["text"] = "아주길고의미있는상황설명"
        cases.append((long_state, "STATE_TEXT_TOO_LONG"))
        for timeline, code in cases:
            with self.subTest(code=code):
                self.assertIn(code, {row["code"] for row in validate_design_lock.validate_role_contract(timeline)})

    def test_plan_to_builder_to_readback_routes_titles_speaker_and_state(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            project = root / "project"; (project / "Resources" / "media").mkdir(parents=True)
            video = root / "source.mp4"; video.write_bytes(b"video")
            timeline_path = root / "timeline.json"
            timeline = approved_timeline(); timeline_path.write_text(json.dumps(timeline), encoding="utf-8")
            document = project / "draft_content.json"; payload = project_payload()
            document.write_text(json.dumps(payload), encoding="utf-8")
            (project / "draft_meta_info.json").write_text(
                json.dumps({"draft_id": "fixture"}), encoding="utf-8"
            )
            config = {
                "episode_id": "EP", "clean_video": str(video), "duration_us": 1_000,
                "approved_timeline_path": str(timeline_path), "T1": "서울 첫날", "T2": "청계천 감탄",
                "state_cues": [{"text": "첫눈에 감탄", "start_us": 800, "end_us": 1_000}],
                "audio_role": None,
            }
            manifest = {"urakkai": {"video_clips": [{
                "clip_id": "video", "source_range_us": [0, 1_000], "target_range_us": [0, 1_000]
            }]}, "source_audio": []}
            builder._normalize_source(project, config, None, manifest)
            built = json.loads(document.read_text(encoding="utf-8"))
            model = SimpleNamespace(tracks=built["tracks"], materials=built["materials"])
            contract_rows = [
                {**row, "end": row["start"] + row["duration"]}
                for row in timeline["segments"]
            ]
            self.assertEqual(readback.validate_v2_role_routing(model, {
                "track_layout_version": "shrt_white_base_v2", "timeline": contract_rows,
                "approved_title_text": {"T1": "서울 첫날", "T2": "청계천 감탄"},
                "primary_speaker_id": "SPK_01",
            }), [])

    def test_builder_rejects_title_mismatch(self):
        timeline = approved_timeline()
        with self.assertRaisesRegex(RuntimeError, "TITLE_TEXT_MISMATCH:T2"):
            builder.validate_approved_role_rows({"T1": "서울 첫날", "T2": "다른 제목"}, timeline)

    def test_readback_rejects_cross_track_placement(self):
        model = SimpleNamespace(tracks=project_payload()["tracks"], materials=project_payload()["materials"])
        model.tracks[3]["segments"] = [{"id": "speaker-primary", "role": "A10_TEXT", "color_role": "WHITE"}]
        contract = {"track_layout_version": "shrt_white_base_v2", "timeline": approved_timeline()["segments"],
                    "approved_title_text": {"T1": "서울 첫날", "T2": "청계천 감탄"}}
        self.assertIn("A10_TEXT_TRACK_MISMATCH", {
            row["code"] for row in readback.validate_v2_role_routing(model, contract)
        })


if __name__ == "__main__":
    unittest.main()

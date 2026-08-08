import json
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch


SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import build_episode_capcut as builder
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
        "A9", "A10", "A11", "A12_RESERVED_EMPTY",
    ]
    materials, tracks = [], []
    for index, role in enumerate(roles):
        material_id = f"m-{role}"
        material = {
            "id": material_id, "type": "text", "role": role,
            "content": json.dumps({"text": "seed", "styles": [{"range": [0, 4]}]}),
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


if __name__ == "__main__":
    unittest.main()

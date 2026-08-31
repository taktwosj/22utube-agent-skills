import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPTS = Path(__file__).resolve().parents[1]
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import build_politics_v8_project as v8
import prepare_politics_v8_rebuild_cards as prepare


def segment(material_id: str, spec: dict | None = None) -> dict:
    value = {"material_id": material_id, "target_timerange": {"start": 0, "duration": 1}}
    if spec is not None:
        value["clip"] = {
            "scale": {"x": spec["scale"], "y": spec["scale"]},
            "rotation": spec.get("rotation", 0.0),
            "transform": {"x": spec["x"], "y": spec["y"]},
            "alpha": 1.0,
        }
    return value


class V8RootHarnessTests(unittest.TestCase):
    def root_document(self) -> dict:
        tracks = []
        for index in range(12):
            track_type = v8.V8_TRACK_TYPES[index]
            tracks.append({"type": track_type, "segments": []})
        document = {
            "tracks": tracks,
            "materials": {
                "videos": [], "shapes": [], "texts": [], "audios": [],
            },
        }
        for index, spec in v8.V8_MEDIA_SPECS.items():
            material_id = f"MEDIA_{index}"
            document["materials"]["videos"].append(
                {"id": material_id, "type": spec["type"], "width": spec["width"], "height": spec["height"]}
            )
            tracks[index]["segments"] = [segment(material_id, spec)]
        for index, spec in v8.V8_SHAPE_SPECS.items():
            material_id = f"SHAPE_{index}"
            document["materials"]["shapes"].append(
                {"id": material_id, "shape_size": list(spec["shape_size"]), "global_alpha": 0.5, "border_width": 4.0, "border_color": "#CCCCCC"}
            )
            tracks[index]["segments"] = [segment(material_id, {**spec, "scale": 1.0, "rotation": 0.0})]
        for index, spec in v8.V8_TEXT_SPECS.items():
            material_id = f"TEXT_{index}"
            document["materials"]["texts"].append(
                {
                    "id": material_id,
                    "font_size": spec["font_size"],
                    "fixed_width": spec["fixed_width"],
                    "alignment": spec["alignment"],
                    "line_spacing": spec["line_spacing"],
                    "content": json.dumps(
                        {
                            "text": spec["text"],
                            "styles": [{
                                "fill": {"content": {"solid": {"color": list(spec["fill"])}}},
                                "strokes": [{"width": spec["stroke"]}],
                            }],
                        },
                        ensure_ascii=False,
                    ),
                }
            )
            tracks[index]["segments"] = [segment(material_id, spec)]
        document["materials"]["audios"] = [{"id": "AUDIO_11"}]
        tracks[11]["segments"] = [segment("AUDIO_11")]
        return document

    def test_root_contract_accepts_only_declared_v8_static_lanes(self):
        v8.assert_v8_root_layout(self.root_document())
        broken = self.root_document()
        broken["tracks"][3]["type"] = "video"
        with self.assertRaisesRegex(RuntimeError, "V8_ROOT_TRACK_ROLE_INVALID:3"):
            v8.assert_v8_root_layout(broken)

    def test_root_contract_rejects_card_geometry_that_differs_from_manual_v8(self):
        broken = self.root_document()
        broken["tracks"][4]["segments"][0]["clip"]["scale"] = {"x": 2 / 3, "y": 2 / 3}
        with self.assertRaisesRegex(RuntimeError, "V8_ROOT_CLIP_GEOMETRY_INVALID:4"):
            v8.assert_v8_root_layout(broken)

    def test_cleanliness_harness_catches_backup_and_case_variant_file_path(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "draft_content.json").write_text(
                json.dumps({"material": {"file_Path": "C:/old/00_build/V8_TEST.wav"}}),
                encoding="utf-8",
            )
            (root / "draft_content.json.bak").write_text("backup", encoding="utf-8")
            hits = v8.root_artifact_hits(root)
            self.assertIn("draft_content.json.bak", hits)
            self.assertIn("draft_content.json.material:file_Path", hits)
            with self.assertRaisesRegex(RuntimeError, "V8_ROOT_ARTIFACT_LEAK"):
                v8.assert_v8_clean_tree(root)

    def test_media_templates_follow_declared_tracks_not_asset_names(self):
        document = self.root_document()
        document["tracks"][0]["segments"] = [segment("SOURCE")]
        document["tracks"][4]["segments"] = [segment("IMAGE")]
        document["materials"]["videos"].extend([
            {"id": "SOURCE", "type": "video", "material_name": "anything.mp4"},
            {"id": "IMAGE", "type": "photo", "material_name": "unrelated.png"},
        ])
        source = v8.media_template(document, track_index=0, material_type="video")
        image = v8.media_template(document, track_index=4, material_type="photo")
        self.assertEqual(source[2]["id"], "SOURCE")
        self.assertEqual(image[2]["id"], "IMAGE")

    def test_delivery_report_carries_editorial_metadata_without_rewriting(self):
        report = v8.delivery_report(
            {
                "publication_report": {
                    "title": "Fixture title",
                    "content": {
                        "simple_summary": "Fixture summary",
                        "timeline": [{"at": "00:00", "label": "Opening"}],
                        "sources": [{"label": "Fixture source", "url": None}],
                    },
                    "thumbnail": {
                        "words": ["책임", "패배", "함께"],
                        "sentences": ["Strongest", "Second", "Third"],
                    },
                }
            },
            "PROJECT_NAME",
            Path("C:/Projects/PROJECT_NAME"),
            Path("C:/Media/PROJECT_NAME"),
        )
        self.assertEqual(report["project_name"], "PROJECT_NAME")
        self.assertEqual(report["content"]["timeline"][0]["at"], "00:00")
        self.assertEqual(report["thumbnail"]["words"], ["책임", "패배", "함께"])
        self.assertEqual(report["thumbnail"]["sentences_ranked"][0], {"rank": 1, "text": "Strongest"})

    def test_v8_caption_prepare_emits_only_single_line_cues(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "source.srt"
            target = root / "target.srt"
            source.write_text(
                "1\n00:00:00,000 --> 00:00:04,000\n정책 방향은 같았지만 시행 준비는 충분했나\n",
                encoding="utf-8",
            )

            prepare.reflow_srt(source, target)

            cues = prepare.read_srt(target)
            self.assertGreater(len(cues), 1)
            self.assertTrue(all("\n" not in text for _, _, text in cues))
            self.assertTrue(all(prepare.visible_length(text) <= 15 for _, _, text in cues))

    def test_v8_prepare_preserves_independent_chapter_label_and_falls_back_source_channel(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            cards = root / "episode_cards.json"
            output = root / "episode_cards_v8.json"
            cards.write_text(
                json.dumps(
                    {
                        "cards": [
                            {
                                "card_id": "C00_HOOK_01",
                                "card_type": "SOURCE_VIDEO",
                                "chapter_title": "본인이 만든 기준",
                                "chapter_label": "오프닝",
                                "source_channel": "뉴스공장",
                                "source_display_label": "",
                                "lower_mode": "NONE",
                            }
                        ]
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )

            result = subprocess.run(
                [
                    sys.executable,
                    "-B",
                    str(SCRIPTS / "prepare_politics_v8_rebuild_cards.py"),
                    "--cards",
                    str(cards),
                    "--out",
                    str(output),
                    "--caption-dir",
                    str(root / "captions"),
                    "--project-name",
                    "PL_TEST_V8",
                ],
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            prepared = json.loads(output.read_text(encoding="utf-8"))["cards"][0]
            self.assertEqual(prepared["chapter_title"], "본인이 만든 기준")
            self.assertEqual(prepared["chapter_label"], "오프닝")
            self.assertEqual(prepared["source_display_label"], "뉴스공장")


if __name__ == "__main__":
    unittest.main()

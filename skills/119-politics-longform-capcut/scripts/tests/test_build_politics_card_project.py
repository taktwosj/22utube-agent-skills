import json
import hashlib
import zipfile
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path, PureWindowsPath
from types import SimpleNamespace
from unittest import mock


SCRIPTS = Path(__file__).resolve().parents[1]
BUILDER_PATH = SCRIPTS / "build_politics_card_project.py"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import build_politics_card_project as builder


class BuilderRootBundleSeamTests(unittest.TestCase):
    def test_remap_ids_rebases_portable_and_legacy_bundle_paths_to_target_profile(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            stage = root / "staging" / "Project"
            old_timeline = "11111111-1111-4111-8111-111111111111"
            timeline = stage / "Timelines" / old_timeline
            timeline.mkdir(parents=True)
            legacy_root = "C:/Users/source/AppData/Local/CapCut/ARCHIVE_ROOT"
            portable_root = "C:/__CAPCUT_ROOT_BUNDLE__"
            document = {
                "id": old_timeline,
                "materials": {
                    "videos": [
                        {
                            "id": "V",
                            "path": legacy_root + "/Resources/media/main.png",
                        }
                    ]
                },
            }
            (stage / "draft_content.json").write_text(
                json.dumps(document), encoding="utf-8"
            )
            (stage / "draft_meta_info.json").write_text(
                json.dumps(
                    {
                        "draft_fold_path": legacy_root,
                        "draft_root_path": "C:/Users/source/AppData/Local/CapCut",
                        "draft_cover": legacy_root + "/draft_cover.jpg",
                        "attachment": {
                            "asset_path": portable_root + "/Resources/media/main.png"
                        },
                    }
                ),
                encoding="utf-8",
            )
            (timeline / "template.json").write_text(
                json.dumps(
                    {"attachment": {"asset_path": portable_root + "/Resources/media/main.png"}}
                ),
                encoding="utf-8",
            )
            final_root = root / "target-profile" / "Project"

            builder.remap_ids(stage, final_root, "Project", "ARCHIVE_ROOT")

            target = final_root.as_posix()
            remapped_document = json.loads(
                (stage / "draft_content.json").read_text(encoding="utf-8")
            )
            remapped_meta = json.loads(
                (stage / "draft_meta_info.json").read_text(encoding="utf-8")
            )
            new_timeline = next((stage / "Timelines").iterdir())
            remapped_template = json.loads(
                (new_timeline / "template.json").read_text(encoding="utf-8")
            )
            self.assertEqual(
                remapped_document["materials"]["videos"][0]["path"],
                target + "/Resources/media/main.png",
            )
            self.assertEqual(remapped_meta["draft_fold_path"], target)
            self.assertEqual(
                remapped_meta["draft_cover"], target + "/draft_cover.jpg"
            )
            self.assertEqual(
                remapped_meta["draft_root_path"], final_root.parent.as_posix()
            )
            self.assertEqual(
                remapped_meta["attachment"]["asset_path"],
                target + "/Resources/media/main.png",
            )
            self.assertEqual(
                remapped_template["attachment"]["asset_path"],
                target + "/Resources/media/main.png",
            )

    def test_normalize_cards_allows_a_narration_image_cold_open(self):
        cards, total = builder.normalize_cards({
            "cta_like_subscribe": "ON",
            "cards": [{
                "card_id": "N001_HOOK",
                "card_type": "NARRATION_IMAGE",
                "target_start_us": 0,
                "target_duration_us": 1_000_000,
                "lower_mode": "NONE",
                "cta_like_subscribe": "ON",
            }],
        })

        self.assertEqual(total, 1_000_000)
        self.assertEqual(cards[0]["card_type"], "NARRATION_IMAGE")

    def test_commentary_input_lines_become_sequential_single_line_segments(self):
        template = {
            "id": "TEXT_TEMPLATE",
            "content": json.dumps({"text": "TTS", "styles": [{"range": [0, 3]}]}),
        }
        segment = {
            "id": "SEGMENT_TEMPLATE",
            "material_id": template["id"],
            "target_timerange": {"start": 0, "duration": 4_000_000},
        }
        document = {"materials": {"texts": []}}
        track = {"segments": []}

        builder.clone_sequential_single_line_text(
            document, template, segment, track, "첫 문장\n둘째 문장", 0, 4_000_000
        )

        values = {item["id"]: builder.text_of(item) for item in document["materials"]["texts"]}
        self.assertEqual([values[item["material_id"]] for item in track["segments"]], ["첫 문장", "둘째 문장"])
        self.assertEqual(
            [item["target_timerange"] for item in track["segments"]],
            [{"start": 0, "duration": 2_000_000}, {"start": 2_000_000, "duration": 2_000_000}],
        )

    def minimal_document_for_chapter_titles(self) -> dict:
        def text(material_id: str, value: str) -> dict:
            return {
                "id": material_id,
                "content": json.dumps(
                    {"text": value, "styles": [{"range": [0, len(value)]}]},
                    ensure_ascii=False,
                    separators=(",", ":"),
                ),
            }

        def segment(segment_id: str, material_id: str) -> dict:
            return {
                "id": segment_id,
                "material_id": material_id,
                "target_timerange": {"start": 0, "duration": 1_000_000},
                "source_timerange": {"start": 0, "duration": 1_000_000},
                "clip": {},
            }

        return {
            "materials": {
                "texts": [
                    text("T_INTRO", "__INTRO_HOOK_LINE_1__"),
                    text("T_CHAPTER", "__CHAPTER__"),
                    text("T_SOURCE", "출처 __SOURCE__\n__DATE__"),
                    text("T_LOWER", "__LOWER_LINE_1__\n__LOWER_LINE_2__"),
                    text("T_CTA", "구독은 fixture"),
                ],
                "videos": [
                    {"id": "V_MAIN", "type": "video", "duration": 1_000_000},
                    {"id": "V_PHOTO", "type": "photo", "duration": 1_000_000},
                ],
            },
            "tracks": [
                {"id": "INTRO", "type": "text", "segments": [segment("S_INTRO", "T_INTRO")]},
                {"id": "CHAPTER", "type": "text", "segments": [segment("S_CHAPTER", "T_CHAPTER")]},
                {"id": "SOURCE", "type": "text", "segments": [segment("S_SOURCE", "T_SOURCE")]},
                {"id": "LOWER", "type": "text", "segments": [segment("S_LOWER", "T_LOWER")]},
                {"id": "CTA", "type": "text", "segments": [segment("S_CTA", "T_CTA")]},
                {"id": "V_MAIN_TRACK", "type": "video", "segments": [segment("S_MAIN", "V_MAIN")]},
                {"id": "V_PHOTO_TRACK", "type": "video", "segments": [segment("S_PHOTO", "V_PHOTO")]},
            ],
        }

    @staticmethod
    def source_record() -> dict:
        return {
            "offline_path": "C:/relink/C027.mp4",
            "filename": "C027.mp4",
            "width": 1920,
            "height": 1080,
            "source_start": 0,
            "source_duration": 24_000_000,
            "duration_us": 24_000_000,
            "has_audio": True,
        }

    def test_source_video_chapter_label_emits_chapter_track_text_at_c027_timing(self):
        start, duration = 449_360_000, 24_000_000
        built = builder.build_document(
            self.minimal_document_for_chapter_titles(),
            [{
                "card_id": "C027", "card_type": "SOURCE_VIDEO", "chapter_label": "결론의 기준",
                "target_start_us": start, "target_duration_us": duration,
                "source_display_label": "뉴스공장",
                "source_channel": "겸손은힘들다 뉴스공장", "source_date": "2026.08.13", "lower_mode": "NONE",
            }],
            start + duration,
            {"C027": self.source_record()},
            "chapter-title-regression",
        )
        text_by_id = {material["id"]: builder.text_of(material) for material in built["materials"]["texts"]}
        chapter_track = next(track for track in built["tracks"] if track["id"] == "CHAPTER")
        self.assertEqual(len(chapter_track["segments"]), 1)
        chapter_segment = chapter_track["segments"][0]
        self.assertEqual(text_by_id[chapter_segment["material_id"]], "결론의 기준")
        self.assertEqual(chapter_segment["target_timerange"], {"start": start, "duration": duration})

    def test_source_display_label_is_the_only_on_screen_source_credit(self):
        start, duration = 0, 4_000_000
        built = builder.build_document(
            self.minimal_document_for_chapter_titles(),
            [{
                "card_id": "C001", "card_type": "SOURCE_VIDEO", "chapter_label": "챕터 1",
                "target_start_us": start, "target_duration_us": duration,
                "source_display_label": "뉴스공장",
                "source_channel": "YouTube · 길고 불필요한 인터뷰 원본명",
                "source_date": "2026.08.29", "lower_mode": "NONE",
            }],
            duration,
            {"C001": self.source_record()},
            "source-display-label",
        )

        source_texts = [
            builder.text_of(material)
            for material in built["materials"]["texts"]
            if builder.text_of(material).startswith("출처 ")
        ]

        self.assertEqual(source_texts, ["출처 뉴스공장"])

    def test_narration_video_and_image_emit_the_same_upper_chapter_title(self):
        for card_type in ("NARRATION_VIDEO", "NARRATION_IMAGE"):
            with self.subTest(card_type=card_type):
                duration = 4_000_000
                record = self.source_record()
                record.update({"duration_us": duration, "source_duration": duration, "has_audio": False})
                record["narration_audio"] = {
                    "filename": "narration.wav",
                    "duration_us": duration,
                    "offline_path": "C:/relink/narration.wav",
                    "source_start": 0,
                    "source_duration": duration,
                }
                built = builder.build_document(
                    self.minimal_document_for_chapter_titles(),
                    [{
                        "card_id": "C001",
                        "card_type": card_type,
                        "chapter_label": "같은 상단 챕터",
                        "target_start_us": 0,
                        "target_duration_us": duration,
                        "lower_mode": "NONE",
                    }],
                    duration,
                    {"C001": record},
                    "narration-chapter-title",
                )
                text_by_id = {
                    material["id"]: builder.text_of(material)
                    for material in built["materials"]["texts"]
                }
                chapter_track = next(track for track in built["tracks"] if track["id"] == "CHAPTER")

                self.assertEqual(len(chapter_track["segments"]), 1)
                chapter_segment = chapter_track["segments"][0]
                self.assertEqual(text_by_id[chapter_segment["material_id"]], "같은 상단 챕터")
                self.assertEqual(
                    chapter_segment["target_timerange"],
                    {"start": 0, "duration": duration},
                )

    def test_inset_image_card_uses_the_manual_v8_root_geometry(self):
        duration = 4_000_000
        for width, height, scale in ((1920, 1080, 0.65),):
            with self.subTest(width=width, height=height):
                record = self.source_record()
                record.update({
                    "filename": f"V001_{width}.png",
                    "width": width,
                    "height": height,
                    "duration_us": duration,
                    "source_duration": duration,
                    "has_audio": False,
                    "narration_audio": {
                        "filename": "narration.wav",
                        "duration_us": duration,
                        "offline_path": "C:/relink/narration.wav",
                        "source_start": 0,
                        "source_duration": duration,
                    },
                })
                built = builder.build_document(
                    self.minimal_document_for_chapter_titles(),
                    [{
                        "card_id": "C001",
                        "card_type": "NARRATION_IMAGE",
                        "style_profile": "DEMOCRATIC_BLUE_INSET_CARD_V2",
                        "chapter_label": "비판은 했습니다",
                        "target_start_us": 0,
                        "target_duration_us": duration,
                        "lower_mode": "NONE",
                    }],
                    duration,
                    {"C001": record},
                    "inset-image-layout",
                )
                image = next(
                    material for material in built["materials"]["videos"]
                    if material.get("material_name") == f"V001_{width}.png"
                )
                image_segment = next(
                    segment for track in built["tracks"] for segment in track.get("segments", [])
                    if segment.get("material_id") == image["id"]
                )
                self.assertEqual(
                    image_segment["clip"].get("transform"),
                    {"x": 0.0, "y": 0.0},
                )
                self.assertEqual(image_segment["clip"].get("scale"), {"x": scale, "y": scale})

    def chapter_states(self, cards: list[dict], media: dict[str, dict]) -> list[tuple[str, dict]]:
        total = max(card["target_start_us"] + card["target_duration_us"] for card in cards)
        built = builder.build_document(
            self.minimal_document_for_chapter_titles(), cards, total, media, "chapter-state-test"
        )
        text_by_id = {
            material["id"]: builder.text_of(material)
            for material in built["materials"]["texts"]
        }
        chapter_track = next(track for track in built["tracks"] if track["id"] == "CHAPTER")
        return [
            (text_by_id[segment["material_id"]], segment["target_timerange"])
            for segment in chapter_track["segments"]
        ]

    def chapter_transition_cards(self, chapter_label, source_label) -> tuple[list[dict], dict]:
        cards = [
            {
                "card_id": "C001",
                "card_type": "CHAPTER_CARD",
                "chapter_label": chapter_label,
                "chapter_hook": "hook",
                "target_start_us": 0,
                "target_duration_us": 3_000_000,
                "lower_mode": "NONE",
            },
            {
                "card_id": "C002",
                "card_type": "SOURCE_VIDEO",
                "chapter_label": source_label,
                "target_start_us": 3_000_000,
                "target_duration_us": 7_000_000,
                "source_display_label": "channel",
                "source_channel": "channel",
                "source_date": "2026.08.14",
                "lower_mode": "NONE",
            },
        ]
        return cards, {"C001": self.source_record(), "C002": self.source_record()}

    def test_null_chapter_card_label_never_emits_none_and_preserves_following_source_label(self):
        cards, media = self.chapter_transition_cards(None, "Chapter B")

        states = self.chapter_states(cards, media)

        self.assertEqual(states, [("Chapter B", {"start": 3_000_000, "duration": 7_000_000})])
        self.assertNotIn("None", [text for text, _ in states])

    def test_same_label_chapter_to_source_is_one_non_overlapping_state(self):
        cards, media = self.chapter_transition_cards("Chapter A", "Chapter A")

        states = self.chapter_states(cards, media)

        self.assertEqual(states, [("Chapter A", {"start": 0, "duration": 10_000_000})])

    def test_different_label_chapter_to_source_preserves_each_exact_interval(self):
        cards, media = self.chapter_transition_cards("Chapter A", "Chapter B")

        states = self.chapter_states(cards, media)

        self.assertEqual(
            states,
            [
                ("Chapter A", {"start": 0, "duration": 3_000_000}),
                ("Chapter B", {"start": 3_000_000, "duration": 7_000_000}),
            ],
        )

    def invoke_main(self, arguments: list[str]) -> int:
        with mock.patch.object(sys, "argv", [str(BUILDER_PATH), *arguments]), mock.patch.object(
            builder, "require_capcut_closed", return_value=None
        ):
            return builder.main()

    def required_arguments(self, root: Path) -> list[str]:
        return [
            "--cards",
            str(root / "cards.json"),
            "--workspace-root",
            str(root / "workspace"),
            "--capcut-root",
            str(root / "capcut"),
            "--media-dir",
            str(root / "media"),
            "--report",
            str(root / "report.json"),
        ]

    @staticmethod
    def write_validation_project(root: Path, extra_materials: dict) -> None:
        timeline = root / "Timelines" / "TIMELINE"
        timeline.mkdir(parents=True)
        text = {"id": "TCTA", "content": json.dumps({"text": "구독은 fixture", "styles": []})}
        materials = {"texts": [text], "videos": []}
        materials.update(extra_materials)
        document = {
            "duration": 1_000_000,
            "materials": materials,
            "tracks": [
                {
                    "id": "CTA",
                    "type": "text",
                    "segments": [
                        {
                            "id": "SCTA",
                            "material_id": "TCTA",
                            "target_timerange": {"start": 0, "duration": 1_000_000},
                            "clip": {},
                        }
                    ],
                }
            ],
        }
        payload = json.dumps(document, ensure_ascii=False, separators=(",", ":"))
        for path in (
            root / "draft_content.json",
            root / "template-2.tmp",
            timeline / "draft_content.json",
            timeline / "template-2.tmp",
        ):
            path.write_text(payload, encoding="utf-8")

    def test_build_validator_allows_only_exact_relink_root_and_all_material_types(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self.write_validation_project(
                root,
                {
                    "videos": [{"id": "V", "path": "C:/__CAPCUT_RELINK_REQUIRED__/C001.mp4"}],
                    "audios": [{"id": "A", "path": "D:/foreign/audio.wav"}],
                },
            )

            with self.assertRaisesRegex(RuntimeError, "FOREIGN") as raised:
                builder.validate_build(root, {}, 1_000_000)

            self.assertIn("$.materials.audios[0].path", str(raised.exception))

    def test_build_validator_accepts_exact_relink_root(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self.write_validation_project(
                root,
                {
                    "videos": [],
                    "audios": [
                        {"id": "A", "path": "C:/__CAPCUT_RELINK_REQUIRED__/episode/Media/A.wav"}
                    ],
                },
            )

            result = builder.validate_build(root, {}, 1_000_000)

            self.assertEqual(result["status"], "PASS")

    def test_build_validator_rejects_relink_substring_spoof_and_nested_serialized_path(self):
        unsafe_materials = (
            ({"videos": [{"id": "V", "path": "D:/foreign/__CAPCUT_RELINK_REQUIRED__/C001.mp4"}]}, "FOREIGN"),
            ({"videos": [], "audios": [{"id": "A", "path": "D:/foreign/Resources/media/ghost.wav"}]}, "FOREIGN"),
            ({"videos": [], "audios": [{"id": "A", "path": "Resources/../escape.wav"}]}, "TRAVERSAL"),
            ({
                "videos": [],
                "audios": [
                    {"id": "A", "path": "C:/__CAPCUT_RELINK_REQUIRED__-evil/escape.wav"}
                ],
            }, "FOREIGN"),
            ({
                "videos": [],
                "audios": [
                    {
                        "id": "A",
                        "metadata": json.dumps(
                            json.dumps({"local_path": "D:/foreign/double.wav"})
                        ),
                    }
                ],
            }, "FOREIGN"),
        )
        for materials, code in unsafe_materials:
            with self.subTest(materials=materials), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                self.write_validation_project(root, materials)
                with self.assertRaisesRegex(RuntimeError, code):
                    builder.validate_build(root, {}, 1_000_000)

    def test_build_validator_rejects_malformed_wrapper_but_ignores_display_strings(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self.write_validation_project(
                root,
                {"audios": [{"id": "A", "metadata": '{"local_path":'}]},
            )
            with self.assertRaisesRegex(RuntimeError, "JSON_INVALID"):
                builder.validate_build(root, {}, 1_000_000)

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self.write_validation_project(
                root,
                {
                    "audios": [
                        {
                            "id": "A",
                            "name": "[Intro]",
                            "text": "{literal material name",
                            "visible": json.dumps({"local_path": "D:/display-only.wav"}),
                        }
                    ]
                },
            )
            self.assertEqual(builder.validate_build(root, {}, 1_000_000)["status"], "PASS")

    def test_builder_resolves_archive_only_from_workspace_active_pointer(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            workspace = root / "workspace"
            pointer = workspace / "00_asset_tools/templates/capcut/jungchilong/capcut_active_root_v1.json"
            pointer.parent.mkdir(parents=True)
            pointer.write_text(
                json.dumps(
                    {
                        "schema": "politics-longform-capcut-active-root.v1",
                        "active_root_version": "v5",
                        "contract": {"relative_path": "missing-contract.json", "sha256": "0" * 64},
                        "activation_basis": {"mode": "LEGACY_V5_STATIC_LOCK"},
                    }
                ),
                encoding="utf-8",
            )
            with self.assertRaises(RuntimeError) as caught:
                self.invoke_main(self.required_arguments(root))
            self.assertEqual(str(caught.exception), "WAIT_ROOT_BUNDLE_CONTRACT_NOT_FOUND")

    def test_builder_report_binds_contract_version_and_hash(self):
        resolved = SimpleNamespace(
            to_report=lambda: {
                "status": "PASS_ROOT_CONTRACT",
                "root_version": "v5",
                "contract_path": "contracts/capcut_root_contract_v5.json",
                "contract_sha256": "C" * 64,
                "archive_path": "root.zip",
                "archive_sha256": "A" * 64,
                "layout_path": "layout.json",
                "layout_sha256": "L" * 64,
                "evidence_path": "evidence.json",
                "evidence_sha256": "E" * 64,
                "root_visual_gate": "WAIT_USER_VISUAL_GATE",
                "root_post_open_validation": "WAIT_CAPCUT_OPEN_CLOSE",
                "episode_visual_gate_inherited": False,
            }
        )
        report = builder.build_report_payload(
            project=Path("project"),
            media_dir=Path("media"),
            cards=[],
            media_records={},
            static={"status": "PASS"},
            resolved_root=resolved,
        )
        self.assertEqual(report["root_bundle"]["root_version"], "v5")
        self.assertEqual(report["root_bundle"]["contract_sha256"], "C" * 64)
        self.assertEqual(report["root_bundle"]["root_visual_gate"], "WAIT_USER_VISUAL_GATE")
        self.assertEqual(report["VISUAL_GATE"], "WAIT_USER_VISUAL_GATE")
        self.assertFalse(report["root_bundle"]["episode_visual_gate_inherited"])

    def test_public_build_report_contains_only_portable_path_references(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            source = root / "Users" / "owner" / "Videos" / "source.mp4"
            project = root / "AppData" / "CapCut" / "project-name"
            media_dir = root / "Users" / "owner" / "Videos" / "Media"
            resolved = SimpleNamespace(
                to_report=lambda: {
                    "status": "PASS_ROOT_CONTRACT",
                    "root_version": "v5",
                    "contract_path": "00_asset_tools/templates/capcut/jungchilong/contracts/capcut_root_contract_v5.json",
                    "archive_path": "00_asset_tools/templates/capcut/jungchilong/root.zip",
                }
            )
            report = builder.build_report_payload(
                project=project,
                media_dir=media_dir,
                cards=[
                    {
                        "card_id": "C001",
                        "card_type": "SOURCE_VIDEO",
                        "source_file": str(source),
                    }
                ],
                media_records={
                    "C001": {
                        "file": str(media_dir / "C001_source.mp4"),
                        "filename": "C001_source.mp4",
                        "sha256": "A" * 64,
                        "offline_path": "C:/__CAPCUT_RELINK_REQUIRED__/episode/Media/C001_source.mp4",
                        "storage": "relink",
                    }
                },
                static={"status": "PASS"},
                resolved_root=resolved,
            )

        def strings(value):
            if isinstance(value, dict):
                for item in value.values():
                    yield from strings(item)
            elif isinstance(value, list):
                for item in value:
                    yield from strings(item)
            elif isinstance(value, str):
                yield value

        public_strings = list(strings(report))
        self.assertNotIn(str(root), json.dumps(report, ensure_ascii=False))
        self.assertFalse(
            [
                value
                for value in public_strings
                if Path(value).is_absolute() or PureWindowsPath(value).is_absolute()
            ]
        )
        self.assertTrue(report["root_bundle"]["contract_path"].startswith("00_asset_tools/"))

    def test_register_project_uses_project_metadata_when_archive_root_is_not_registered(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            meta_path = root / "root_meta_info.json"
            original_meta = {
                "all_draft_store": [
                    {
                        "draft_name": "unrelated-project",
                        "draft_id": "existing-id",
                    }
                ]
            }
            meta_path.write_text(json.dumps(original_meta), encoding="utf-8")
            original_bytes = meta_path.read_bytes()
            project_root = root / "final-project"
            project_root.mkdir()
            (project_root / "draft_meta_info.json").write_text(
                json.dumps(
                    {
                        "draft_name": "archive-root",
                        "draft_id": "archive-id",
                        "draft_fold_path": "C:/source/archive-root",
                        "draft_root_path": "C:/source",
                        "draft_cover": "C:/source/archive-root/draft_cover.jpg",
                        "draft_timeline_materials_size_": 123,
                        "draft_materials": [{"type": 0}],
                        "tm_duration": 180_000_000,
                    }
                ),
                encoding="utf-8",
            )

            returned = builder.register_project(
                meta_path,
                "archive-root",
                "final-project",
                project_root,
                1_221_350_000,
            )

            self.assertEqual(returned, original_bytes)
            updated = json.loads(meta_path.read_text(encoding="utf-8"))
            self.assertEqual(len(updated["all_draft_store"]), 2)
            self.assertFalse(
                any(item.get("draft_name") == "archive-root" for item in updated["all_draft_store"])
            )
            entry = updated["all_draft_store"][-1]
            project_posix = project_root.as_posix()
            self.assertEqual(entry["draft_name"], "final-project")
            self.assertNotEqual(entry["draft_id"], "archive-id")
            self.assertEqual(entry["draft_fold_path"], project_posix)
            self.assertEqual(entry["draft_json_file"], project_posix + "/draft_content.json")
            self.assertEqual(entry["draft_cover"], project_posix + "/draft_cover.jpg")
            self.assertEqual(entry["draft_root_path"], project_root.parent.as_posix())
            self.assertEqual(entry["draft_timeline_materials_size"], 123)
            self.assertNotIn("draft_timeline_materials_size_", entry)
            self.assertNotIn("draft_materials", entry)
            self.assertEqual(entry["tm_duration"], 1_221_350_000)
            self.assertFalse(entry["draft_cloud_sync"])
            self.assertTrue(entry["streaming_edit_draft_ready"])

    def test_builder_stops_before_extract_when_root_bundle_resolution_fails(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "workspace").mkdir()
            args = self.required_arguments(root)
            with mock.patch.object(builder, "extract_root", side_effect=AssertionError("extract called")):
                with self.assertRaises(RuntimeError) as caught:
                    self.invoke_main(args)
            self.assertEqual(str(caught.exception), "WAIT_ROOT_BUNDLE_POINTER_NOT_FOUND")
            self.assertFalse((root / "media").exists())
            self.assertFalse((root / "capcut").exists())

    def test_builder_cli_rejects_root_archive_and_root_sha256_bypass(self):
        result = subprocess.run(
            [
                sys.executable,
                str(BUILDER_PATH),
                "--cards",
                "cards.json",
                "--workspace-root",
                "workspace",
                "--capcut-root",
                "capcut",
                "--media-dir",
                "media",
                "--report",
                "report.json",
                "--root-archive",
                "bypass.zip",
                "--root-sha256",
                "0" * 64,
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 2)
        error_line = result.stderr.strip().splitlines()[-1]
        self.assertIn("unrecognized arguments", error_line)
        self.assertIn("--root-archive", error_line)
        self.assertIn("--root-sha256", error_line)
        self.assertNotIn("--workspace-root", error_line)

    def test_optional_intro_uses_non_five_second_root_content_boundary(self):
        cards = {
            "cards": [
                {
                    "card_id": "C001",
                    "card_type": "INTRO",
                    "target_start_us": 0,
                    "target_duration_us": 7_250_000,
                    "intro_text": "root-aware\nintro",
                    "lower_mode": "NONE",
                },
                {
                    "card_id": "C002",
                    "card_type": "SOURCE_VIDEO",
                    "target_start_us": 7_250_000,
                    "target_duration_us": 1_000_000,
                    "lower_mode": "NONE",
                },
            ]
        }

        normalized, total = builder.normalize_cards(cards, content_start_us=7_250_000)

        self.assertEqual(normalized[0]["target_duration_us"], 7_250_000)
        self.assertEqual(total, 8_250_000)

    def test_intro_duration_contradicting_root_content_boundary_is_rejected(self):
        cards = {
            "cards": [
                {
                    "card_id": "C001",
                    "card_type": "INTRO",
                    "target_start_us": 0,
                    "target_duration_us": 5_000_000,
                    "intro_text": "contradictory\nintro",
                    "lower_mode": "NONE",
                }
            ]
        }

        with self.assertRaisesRegex(RuntimeError, "INTRO_DURATION_CONTRADICTS_ROOT"):
            builder.normalize_cards(cards, content_start_us=7_250_000)

    def test_no_intro_keeps_first_source_at_zero_even_when_root_has_intro_boundary(self):
        cards = {
            "cards": [
                {
                    "card_id": "C001",
                    "card_type": "SOURCE_VIDEO",
                    "target_start_us": 0,
                    "target_duration_us": 1_000_000,
                    "lower_mode": "NONE",
                }
            ]
        }

        normalized, _ = builder.normalize_cards(cards, content_start_us=7_250_000)

        self.assertEqual(normalized[0]["target_start_us"], 0)

    def test_static_validation_requires_only_four_identical_official_mirrors(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            timeline = root / "Timelines" / "TIMELINE"
            timeline.mkdir(parents=True)
            text = {"id": "TCTA", "content": json.dumps({"text": "구독은 fixture", "styles": []})}
            document = {
                "duration": 1_000_000,
                "materials": {"texts": [text], "videos": []},
                "tracks": [
                    {
                        "id": "CTA",
                        "type": "text",
                        "segments": [
                            {
                                "id": "SCTA",
                                "material_id": "TCTA",
                                "target_timerange": {"start": 0, "duration": 1_000_000},
                                "clip": {},
                            }
                        ],
                    }
                ],
            }
            payload = json.dumps(document, ensure_ascii=False, separators=(",", ":"))
            mirrors = [
                root / "draft_content.json",
                root / "template-2.tmp",
                timeline / "draft_content.json",
                timeline / "template-2.tmp",
            ]
            for path in mirrors:
                path.write_text(payload, encoding="utf-8")

            result = builder.validate_build(root, {}, 1_000_000)

            self.assertEqual(result["status"], "PASS")
            self.assertFalse(any(root.rglob("helper_*")))
            self.assertEqual(
                result["mirror_sha256"],
                hashlib.sha256(mirrors[0].read_bytes()).hexdigest().upper(),
            )

    def test_adapter_root_stops_before_stock_builder_when_verified_v5_source_is_absent(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            archive = root / "root.zip"
            layout = root / "layout.json"
            layout.write_text(json.dumps({"content_start_us": 0}), encoding="utf-8")
            with zipfile.ZipFile(archive, "w") as package:
                package.writestr(
                    "root/runtime_adapters/v5_legacy_profile_adapter_v1.json",
                    "{}",
                )
            resolved = SimpleNamespace(
                archive_path=archive,
                archive_root="root",
                layout_path=layout,
            )
            with mock.patch.object(builder, "resolve_active_root", return_value=resolved):
                with self.assertRaisesRegex(RuntimeError, "WAIT_V5_ADAPTER_SOURCE_REQUIRED"):
                    self.invoke_main(self.required_arguments(root))


if __name__ == "__main__":
    unittest.main()

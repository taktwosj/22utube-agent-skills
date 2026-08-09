from __future__ import annotations

import copy
import contextlib
import hashlib
import importlib.util
import io
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock


SCRIPTS = Path(__file__).resolve().parents[1]
READBACK = SCRIPTS / "capture_politics_relink_readback.py"
sys.path.insert(0, str(SCRIPTS))


def load_builder():
    spec = importlib.util.spec_from_file_location(
        "build_politics_card_project_under_test",
        SCRIPTS / "build_politics_card_project.py",
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


BUILDER = load_builder()
READBACK_MODULE = None


def load_readback():
    global READBACK_MODULE
    if READBACK_MODULE is None:
        spec = importlib.util.spec_from_file_location(
            "capture_politics_relink_readback_under_test",
            READBACK,
        )
        module = importlib.util.module_from_spec(spec)
        assert spec.loader is not None
        spec.loader.exec_module(module)
        READBACK_MODULE = module
    return READBACK_MODULE


def text_material(material_id: str, text: str) -> dict:
    return {
        "id": material_id,
        "content": json.dumps({"text": text}, ensure_ascii=False),
    }


def text_track(track_id: str, segment_id: str, material_id: str, index: int, clip: dict) -> dict:
    return {
        "id": track_id,
        "type": "text",
        "segments": [
            {
                "id": segment_id,
                "material_id": material_id,
                "track_render_index": index,
                "target_timerange": {"start": 8_000_000, "duration": 4_000_000},
                "clip": clip,
            }
        ],
    }


def base_document(media_path: Path) -> dict:
    return {
        "duration": 12_000_000,
        "materials": {
            "videos": [
                {
                    "id": "source-video",
                    "path": str(media_path),
                    "material_name": media_path.name,
                    "duration": 4_000_000,
                    "online_id": "",
                    "request_id": "",
                }
            ],
            "texts": [
                text_material("chapter-text", "챕터 1"),
                text_material("source-text", "출처 MBCNEWS\n2026.08.02"),
                text_material("cta-text", "구독은 큰 힘이 됩니다.\n댓글로 의견 부탁드려요!"),
                text_material("lower-text", "첫 번째 줄\n두 번째 줄"),
            ],
        },
        "tracks": [
            {
                "id": "video-track",
                "type": "video",
                "segments": [
                    {
                        "id": "source-video-segment",
                        "material_id": "source-video",
                        "track_render_index": 0,
                        "target_timerange": {"start": 8_000_000, "duration": 4_000_000},
                        "clip": {"transform": {"x": 0.0, "y": 0.0, "scale_x": 1.0, "scale_y": 1.0}},
                    }
                ],
            },
            text_track(
                "chapter-track",
                "chapter-segment",
                "chapter-text",
                1,
                {"transform": {"x": 0.0, "y": 0.72, "scale_x": 1.0, "scale_y": 1.0}},
            ),
            text_track(
                "source-track",
                "source-segment",
                "source-text",
                2,
                {"transform": {"x": -0.77, "y": 0.62, "scale_x": 1.0, "scale_y": 1.0}},
            ),
            text_track(
                "cta-track",
                "cta-segment",
                "cta-text",
                3,
                {"transform": {"x": 0.77, "y": 0.62, "scale_x": 1.0, "scale_y": 1.0}},
            ),
            text_track(
                "lower-track",
                "lower-segment",
                "lower-text",
                4,
                {"transform": {"x": 0.0, "y": -0.72, "scale_x": 1.0, "scale_y": 1.0}},
            ),
        ],
    }


EXPECTED_PRESENTATION = {
    "source_date_hud": [
        {
            "material_id": "source-text",
            "segment_id": "source-segment",
            "text": "출처 MBCNEWS\n2026.08.02",
            "target_timerange": {"start": 8_000_000, "duration": 4_000_000},
            "track_type": "text",
            "track_index": 2,
            "track_id": "source-track",
            "clip_geometry": {"transform": {"x": -0.77, "y": 0.62, "scale_x": 1.0, "scale_y": 1.0}},
        }
    ],
    "cta_hud": {
        "material_id": "cta-text",
        "segment_id": "cta-segment",
        "text": "구독은 큰 힘이 됩니다.\n댓글로 의견 부탁드려요!",
        "target_timerange": {"start": 8_000_000, "duration": 4_000_000},
        "track_type": "text",
        "track_index": 3,
        "track_id": "cta-track",
        "clip_geometry": {"transform": {"x": 0.77, "y": 0.62, "scale_x": 1.0, "scale_y": 1.0}},
    },
    "lower_slots": [
        {
            "material_id": "lower-text",
            "segment_id": "lower-segment",
            "text": "첫 번째 줄\n두 번째 줄",
            "target_timerange": {"start": 8_000_000, "duration": 4_000_000},
            "track_type": "text",
            "track_index": 4,
            "track_id": "lower-track",
            "clip_geometry": {"transform": {"x": 0.0, "y": -0.72, "scale_x": 1.0, "scale_y": 1.0}},
        }
    ],
}


class ReadbackFixture:
    def __init__(self, root: Path):
        self.root = root
        self.project = root / "PL_TEST_capcut_v1"
        self.media_dir = root / "Media"
        self.media_dir.mkdir(parents=True)
        self.media = self.media_dir / "C003_source.mp4"
        self.media.write_bytes(b"real-fixture-media-bytes\x00\x01")
        self.media_sha256 = hashlib.sha256(self.media.read_bytes()).hexdigest().upper()
        self.report = root / "readback.json"
        self.build_report = root / "build.json"

    def write_project(self, document: dict) -> None:
        timeline = self.project / "Timelines" / "timeline-1"
        timeline.mkdir(parents=True)
        payload = json.dumps(document, ensure_ascii=False, indent=2) + "\n"
        for path in (
            self.project / "draft_content.json",
            self.project / "template-2.tmp",
            timeline / "draft_content.json",
            timeline / "template-2.tmp",
        ):
            path.write_text(payload, encoding="utf-8")

    def legacy_build_report(self) -> dict:
        return {
            "status": "PROJECT_CREATED_WAIT_MEDIA_RELINK",
            "kind": "politics-capcut-card-project",
            "media_filename": self.media.name,
            "media_sha256": self.media_sha256,
            "media_folder_to_select": str(self.media_dir),
            "requested_offline_path": "C:/__CAPCUT_RELINK_REQUIRED__/PL_TEST/Media/C003_source.mp4",
            "static_validation": {
                "status": "PASS",
                "presentation_contract": copy.deepcopy(EXPECTED_PRESENTATION),
            },
        }

    def full_builder_report(self) -> dict:
        return {
            "status": "PROJECT_CREATED_WAIT_MEDIA_RELINK",
            "project": str(self.project),
            "media_folder_to_select": str(self.media_dir),
            "cards": [
                {
                    "card_id": "C003",
                    "card_type": "SOURCE_VIDEO",
                    "target_start_us": 8_000_000,
                    "target_duration_us": 4_000_000,
                }
            ],
            "media": {
                "C003": {
                    "file": str(self.media),
                    "filename": self.media.name,
                    "sha256": self.media_sha256,
                    "offline_path": "C:/__CAPCUT_RELINK_REQUIRED__/PL_TEST/Media/C003_source.mp4",
                    "storage": "relink",
                    "duration_us": 4_000_000,
                    "kind": "video",
                }
            },
            "static_validation": {
                "status": "PASS",
                "presentation_contract": copy.deepcopy(EXPECTED_PRESENTATION),
            },
        }

    def portable_builder_report(self) -> dict:
        return BUILDER.build_report_payload(
            project=self.project,
            media_dir=self.media_dir,
            cards=[
                {
                    "card_id": "C003",
                    "card_type": "SOURCE_VIDEO",
                    "target_start_us": 8_000_000,
                    "target_duration_us": 4_000_000,
                }
            ],
            media_records={
                "C003": {
                    "file": str(self.media),
                    "filename": self.media.name,
                    "sha256": self.media_sha256,
                    "offline_path": "C:/__CAPCUT_RELINK_REQUIRED__/PL_TEST/Media/C003_source.mp4",
                    "storage": "relink",
                    "duration_us": 4_000_000,
                    "kind": "video",
                }
            },
            static={
                "status": "PASS",
                "presentation_contract": copy.deepcopy(EXPECTED_PRESENTATION),
            },
            resolved_root=SimpleNamespace(to_report=lambda: {"status": "PASS_ROOT_CONTRACT"}),
        )

    def run_readback(
        self, build: dict, *, media_dir: Path | None = None
    ) -> subprocess.CompletedProcess[str]:
        self.build_report.write_text(json.dumps(build, ensure_ascii=False, indent=2), encoding="utf-8")
        module = load_readback()
        argv = [
                str(READBACK),
                "--project",
                str(self.project),
                "--build-report",
                str(self.build_report),
                "--report",
                str(self.report),
        ]
        if media_dir is not None:
            argv.extend(["--media-dir", str(media_dir)])
        stdout = io.StringIO()
        stderr = io.StringIO()
        returncode = 0
        try:
            # The user's live CapCut process is external to this temporary
            # fixture.  Bypass only that process-state guard; main(), JSON
            # parsing, file/hash checks, comparisons, and report writes stay real.
            with mock.patch.object(module, "require_capcut_closed"), mock.patch.object(sys, "argv", argv), contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
                returncode = module.main()
        except SystemExit as error:
            returncode = int(error.code or 0)
        except Exception as error:
            returncode = 1
            stderr.write(f"{type(error).__name__}: {error}")
        return subprocess.CompletedProcess(argv, returncode, stdout.getvalue(), stderr.getvalue())


class PoliticsRelinkReadbackContractTests(unittest.TestCase):
    def test_portable_builder_report_reaches_readback_with_explicit_private_media_dir(self):
        with tempfile.TemporaryDirectory() as temporary:
            fixture = ReadbackFixture(Path(temporary))
            fixture.write_project(base_document(fixture.media))
            build = fixture.portable_builder_report()
            public_media_folder = build["media_folder_to_select"]

            result = fixture.run_readback(build, media_dir=fixture.media_dir)

            self.assertEqual(result.returncode, 0, result.stderr)
            serialized_report = fixture.report.read_text(encoding="utf-8")
            report = json.loads(serialized_report)
            self.assertEqual(report["status"], "MEDIA_RELINKED", report)
            self.assertEqual(report["MEDIA_RELINK"], "PASS", report)
            self.assertEqual(report["MEDIA_RESOLUTION"], "PASS", report)
            self.assertTrue(report["media_relink"]["persisted"], report)
            self.assertEqual(report["media_relink"]["media_sha256"], fixture.media_sha256)
            self.assertNotIn(
                str(fixture.media_dir.resolve()), serialized_report.replace("\\\\", "\\")
            )
            self.assertEqual(
                report["media_relink"]["expected_media_folder"], public_media_folder
            )
            self.assertEqual(
                report["media_relink"]["after_path"],
                f"{public_media_folder}/{fixture.media.name}",
            )

    def test_portable_builder_report_without_private_media_dir_fails_closed(self):
        with tempfile.TemporaryDirectory() as temporary:
            fixture = ReadbackFixture(Path(temporary))
            fixture.write_project(base_document(fixture.media))

            result = fixture.run_readback(fixture.portable_builder_report())

            self.assertNotEqual(result.returncode, 0)
            report = json.loads(fixture.report.read_text(encoding="utf-8"))
            self.assertEqual(report["status"], "WAIT_PRIVATE_MEDIA_DIR_REQUIRED", report)
            self.assertEqual(report["MEDIA_RELINK"], "WAIT", report)
            self.assertEqual(report["MEDIA_RESOLUTION"], "WAIT", report)

    def test_baseline_v1_build_without_presentation_snapshot_keeps_legacy_readback(self):
        with tempfile.TemporaryDirectory() as temporary:
            fixture = ReadbackFixture(Path(temporary))
            fixture.write_project(base_document(fixture.media))
            build = fixture.full_builder_report()
            build["static_validation"] = {
                "status": "PASS",
                "duration_sec": 12.0,
                "mirror_sha256": "baseline-v1-mirror-hash",
                "media_count": 1,
                "lower_slot_overlap": False,
            }

            result = fixture.run_readback(build)

            self.assertEqual(result.returncode, 0, result.stderr)
            report = json.loads(fixture.report.read_text(encoding="utf-8"))
            self.assertEqual(report["status"], "MEDIA_RELINKED", report)
            self.assertEqual(report["STATIC_STRUCTURE"], "PASS", report)
            self.assertEqual(
                {
                    "chapter_hud": report["presentation_contract"]["chapter_hud"],
                    "cta_hud": report["presentation_contract"]["cta_hud"],
                    "source_label_lines": report["presentation_contract"]["source_label_lines"],
                },
                {
                    "chapter_hud": {
                        "text": "챕터 1",
                        "start_us": 8_000_000,
                        "duration_us": 4_000_000,
                    },
                    "cta_hud": {
                        "text": "구독은 큰 힘이 됩니다.\n댓글로 의견 부탁드려요!",
                        "start_us": 8_000_000,
                        "duration_us": 4_000_000,
                    },
                    "source_label_lines": ["출처 MBCNEWS", "2026.08.02"],
                },
            )

    def test_full_builder_media_map_is_the_readback_input_contract(self):
        with tempfile.TemporaryDirectory() as temporary:
            fixture = ReadbackFixture(Path(temporary))
            fixture.write_project(base_document(fixture.media))

            result = fixture.run_readback(fixture.full_builder_report())

            self.assertEqual(result.returncode, 0, result.stderr)
            report = json.loads(fixture.report.read_text(encoding="utf-8"))
            self.assertEqual(report["status"], "MEDIA_RELINKED")
            self.assertEqual(report["media_relink"]["media_sha256"], fixture.media_sha256)

    def test_any_online_or_offline_placeholder_left_in_the_final_draft_fails_media_relink(self):
        mutations = {
            "online_id": lambda document: document["materials"]["videos"][0].update(online_id="online-asset-1"),
            "request_id": lambda document: document["materials"]["videos"][0].update(request_id="request-asset-1"),
            "onlineMaterial": lambda document: document["materials"].update(onlineMaterial=[{"id": "placeholder"}]),
            "offline_path": lambda document: document["materials"]["videos"].append(
                {
                    "id": "unused-placeholder",
                    "path": "C:/__CAPCUT_RELINK_REQUIRED__/PL_TEST/Media/missing.mp4",
                    "online_id": "",
                    "request_id": "",
                }
            ),
        }
        for label, mutate in mutations.items():
            with self.subTest(label=label), tempfile.TemporaryDirectory() as temporary:
                fixture = ReadbackFixture(Path(temporary))
                document = base_document(fixture.media)
                mutate(document)
                fixture.write_project(document)

                result = fixture.run_readback(fixture.legacy_build_report())

                self.assertNotEqual(result.returncode, 0, result.stderr)
                report = json.loads(fixture.report.read_text(encoding="utf-8"))
                self.assertEqual(report["status"], "FAIL_MEDIA_RELINK_PERSISTENCE")
                self.assertEqual(report["MEDIA_RESOLUTION"], "FAIL")

    def test_build_validation_snapshots_track_identity_and_clip_geometry(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "project"
            media = root / "Resources" / "media" / "source.mp4"
            media.parent.mkdir(parents=True)
            media.write_bytes(b"actual-hash-input")
            document = base_document(media)
            timeline = root / "Timelines" / "timeline-1"
            timeline.mkdir(parents=True)
            payload = json.dumps(document, ensure_ascii=False, indent=2) + "\n"
            for path in (
                root / "draft_content.json",
                root / "template-2.tmp",
                timeline / "draft_content.json",
                timeline / "template-2.tmp",
            ):
                path.write_text(payload, encoding="utf-8")

            result = BUILDER.validate_build(root, {}, 12_000_000)

            self.assertEqual(result.get("presentation_contract"), EXPECTED_PRESENTATION)

    def test_readback_compares_actual_presentation_to_the_build_snapshot(self):
        with tempfile.TemporaryDirectory() as temporary:
            fixture = ReadbackFixture(Path(temporary))
            document = base_document(fixture.media)
            document["tracks"][4]["segments"][0]["clip"]["transform"]["y"] = -0.2
            fixture.write_project(document)

            result = fixture.run_readback(fixture.legacy_build_report())

            self.assertNotEqual(result.returncode, 0, result.stderr)
            report = json.loads(fixture.report.read_text(encoding="utf-8"))
            self.assertEqual(report.get("STATIC_STRUCTURE"), "FAIL")
            self.assertFalse(report.get("presentation_contract", {}).get("matches", True))

    def test_readback_reports_static_media_visual_mp4_and_upload_as_separate_gates(self):
        with tempfile.TemporaryDirectory() as temporary:
            fixture = ReadbackFixture(Path(temporary))
            fixture.write_project(base_document(fixture.media))

            result = fixture.run_readback(fixture.legacy_build_report())

            self.assertEqual(result.returncode, 0, result.stderr)
            report = json.loads(fixture.report.read_text(encoding="utf-8"))
            self.assertEqual(
                {
                    "STATIC_STRUCTURE": report.get("STATIC_STRUCTURE"),
                    "MEDIA_RESOLUTION": report.get("MEDIA_RESOLUTION"),
                    "VISUAL_GATE": report.get("VISUAL_GATE"),
                    "MP4": report.get("MP4"),
                    "UPLOAD": report.get("UPLOAD"),
                },
                {
                    "STATIC_STRUCTURE": "PASS",
                    "MEDIA_RESOLUTION": "PASS",
                    "VISUAL_GATE": "WAIT_USER_VISUAL_GATE",
                    "MP4": "NOT_RUN",
                    "UPLOAD": "NOT_RUN",
                },
            )

    def test_cli_returns_nonzero_when_the_written_report_contains_a_failed_gate(self):
        mutations = {
            "placeholder": lambda document: document["materials"]["videos"][0].update(
                online_id="online-asset-1"
            ),
            "media": lambda document: document["materials"]["videos"][0].update(
                path="C:/missing/C003_source.mp4"
            ),
            "static": lambda document: document["tracks"][4]["segments"][0]["clip"][
                "transform"
            ].update(y=-0.2),
        }
        for label, mutate in mutations.items():
            with self.subTest(label=label), tempfile.TemporaryDirectory() as temporary:
                fixture = ReadbackFixture(Path(temporary))
                document = base_document(fixture.media)
                mutate(document)
                fixture.write_project(document)

                result = fixture.run_readback(fixture.legacy_build_report())

                report = json.loads(fixture.report.read_text(encoding="utf-8"))
                self.assertTrue(
                    "FAIL" in report["status"]
                    or "FAIL" in {
                        report.get("FINAL_DRAFT_PLACEHOLDER_SCAN"),
                        report.get("MEDIA_RESOLUTION"),
                        report.get("STATIC_STRUCTURE"),
                    },
                    report,
                )
                self.assertNotEqual(result.returncode, 0, report)

    def test_empty_online_material_key_fails_the_final_placeholder_scan(self):
        with tempfile.TemporaryDirectory() as temporary:
            fixture = ReadbackFixture(Path(temporary))
            document = base_document(fixture.media)
            document["materials"]["onlineMaterial"] = []
            fixture.write_project(document)

            fixture.run_readback(fixture.legacy_build_report())

            report = json.loads(fixture.report.read_text(encoding="utf-8"))
            self.assertEqual(report["FINAL_DRAFT_PLACEHOLDER_SCAN"], "FAIL")
            self.assertIn("$.materials.onlineMaterial", report["final_draft_placeholder_scan"]["paths"])

    def test_static_structure_fails_when_role_text_timing_or_cardinality_drifts(self):
        def drift_source_text(document: dict) -> None:
            document["materials"]["texts"][1]["content"] = json.dumps(
                {"text": "Source changed\n2026.08.03"}, ensure_ascii=False
            )

        def drift_target_timing(document: dict) -> None:
            document["tracks"][2]["segments"][0]["target_timerange"]["start"] = 7_000_000

        def duplicate_lower_segment(document: dict) -> None:
            duplicate = copy.deepcopy(document["tracks"][4]["segments"][0])
            duplicate["id"] = "unexpected-lower-segment"
            document["tracks"][4]["segments"].append(duplicate)

        def duplicate_lower_track(document: dict) -> None:
            duplicate = copy.deepcopy(document["tracks"][4])
            duplicate["id"] = "unexpected-lower-track"
            duplicate["segments"][0]["id"] = "unexpected-lower-track-segment"
            document["tracks"].append(duplicate)

        mutations = {
            "source_text": drift_source_text,
            "target_timing": drift_target_timing,
            "duplicate_lower_segment": duplicate_lower_segment,
            "duplicate_lower_track": duplicate_lower_track,
        }
        for label, mutate in mutations.items():
            with self.subTest(label=label), tempfile.TemporaryDirectory() as temporary:
                fixture = ReadbackFixture(Path(temporary))
                document = base_document(fixture.media)
                mutate(document)
                fixture.write_project(document)

                fixture.run_readback(fixture.legacy_build_report())

                report = json.loads(fixture.report.read_text(encoding="utf-8"))
                self.assertEqual(report["STATIC_STRUCTURE"], "FAIL", report)

    def test_new_material_and_text_on_an_extra_lower_track_is_unexpected(self):
        with tempfile.TemporaryDirectory() as temporary:
            fixture = ReadbackFixture(Path(temporary))
            document = base_document(fixture.media)
            document["materials"]["texts"].append(
                text_material("unexpected-lower-material", "추가 하단 문구\n새 두 번째 줄")
            )
            document["tracks"].append(
                text_track(
                    "unexpected-lower-track",
                    "unexpected-lower-segment",
                    "unexpected-lower-material",
                    5,
                    {
                        "transform": {
                            "x": 0.0,
                            "y": -0.72,
                            "scale_x": 1.0,
                            "scale_y": 1.0,
                        }
                    },
                )
            )
            fixture.write_project(document)

            result = fixture.run_readback(fixture.legacy_build_report())

            self.assertNotEqual(result.returncode, 0, result.stderr)
            report = json.loads(fixture.report.read_text(encoding="utf-8"))
            self.assertEqual(report["STATIC_STRUCTURE"], "FAIL", report)
            self.assertIn(
                "tracks[5].segments[unexpected-lower-segment]",
                report["presentation_contract"]["unexpected_role_segments"],
            )

    def test_project_build_is_not_pass_without_status_and_static_evidence(self):
        mutations = {
            "missing_status": lambda build: build.pop("status", None),
            "missing_static_validation": lambda build: build.pop("static_validation", None),
        }
        for label, mutate in mutations.items():
            with self.subTest(label=label), tempfile.TemporaryDirectory() as temporary:
                fixture = ReadbackFixture(Path(temporary))
                fixture.write_project(base_document(fixture.media))
                build = fixture.full_builder_report()
                mutate(build)

                fixture.run_readback(build)

                report = json.loads(fixture.report.read_text(encoding="utf-8"))
                self.assertNotEqual(report["PROJECT_BUILD"], "PASS", report)

    def test_embedded_only_media_map_does_not_fail_zero_relink_candidates(self):
        with tempfile.TemporaryDirectory() as temporary:
            fixture = ReadbackFixture(Path(temporary))
            fixture.write_project(base_document(fixture.media))
            build = fixture.full_builder_report()
            build["media"]["C003"]["storage"] = "embedded"
            build["media"]["C003"]["offline_path"] = ""

            result = fixture.run_readback(build)

            report = json.loads(fixture.report.read_text(encoding="utf-8"))
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn(report["MEDIA_RESOLUTION"], {"PASS", "NOT_APPLICABLE"}, report)
            self.assertNotEqual(report["status"], "FAIL_MEDIA_RELINK_PERSISTENCE", report)

    def test_legacy_single_media_readback_keeps_schema_v1_presentation_fields(self):
        with tempfile.TemporaryDirectory() as temporary:
            fixture = ReadbackFixture(Path(temporary))
            document = base_document(fixture.media)
            fixture.write_project(document)

            fixture.run_readback(fixture.legacy_build_report())

            report = json.loads(fixture.report.read_text(encoding="utf-8"))
            presentation = report["presentation_contract"]
            self.assertEqual(
                {
                    "chapter_hud": presentation.get("chapter_hud"),
                    "cta_hud": presentation.get("cta_hud"),
                    "source_label_lines": presentation.get("source_label_lines"),
                },
                {
                    "chapter_hud": {
                        "text": "챕터 1",
                        "start_us": 8_000_000,
                        "duration_us": 4_000_000,
                    },
                    "cta_hud": {
                        "text": "구독은 큰 힘이 됩니다.\n댓글로 의견 부탁드려요!",
                        "start_us": 8_000_000,
                        "duration_us": 4_000_000,
                    },
                    "source_label_lines": ["출처 MBCNEWS", "2026.08.02"],
                },
            )


if __name__ == "__main__":
    unittest.main()

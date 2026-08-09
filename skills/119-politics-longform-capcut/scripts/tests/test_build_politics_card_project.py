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

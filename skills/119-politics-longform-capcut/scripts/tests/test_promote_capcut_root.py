import hashlib
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


TESTS = Path(__file__).resolve().parent
SCRIPTS = TESTS.parent
for path in (SCRIPTS, TESTS):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

import promote_capcut_root as promoter
from test_root_bundle import BundleWorkspace, sha256_file, write_json


def clip() -> dict:
    return {
        "scale": {"x": 1.0, "y": 1.0},
        "rotation": 0.0,
        "transform": {"x": 0.0, "y": 0.0},
        "alpha": 1.0,
    }


def segment(material_id: str, start: int, duration: int) -> dict:
    return {
        "material_id": material_id,
        "target_timerange": {"start": start, "duration": duration},
        "clip": clip(),
    }


def text_material(material_id: str, text: str) -> dict:
    return {
        "id": material_id,
        "content": json.dumps(
            {"text": text, "styles": [{"range": [0, len(text)]}]},
            ensure_ascii=False,
            separators=(",", ":"),
        ),
    }


class PromotionWorkspace:
    def __init__(self, root: Path) -> None:
        self.active = BundleWorkspace(root)
        self.workspace = root
        self.capcut_root = root / "local-capcut-drafts"
        self.source_root = self.capcut_root / "candidate-source"
        self.capcut_root.mkdir()
        self._write_source_root()
        write_json(
            self.capcut_root / "root_meta_info.json",
            {
                "all_draft_store": [
                    {
                        "draft_name": self.source_root.name,
                        "draft_id": "SOURCE",
                        "draft_fold_path": self.source_root.as_posix(),
                    }
                ]
            },
        )

    def _write_source_root(self) -> None:
        timeline_id = "11111111-1111-4111-8111-111111111111"
        duration = 30_000_000
        content_start = 10_000_000
        document = {
            "id": timeline_id,
            "name": self.source_root.name,
            "duration": duration,
            "canvas_config": {"width": 1920, "height": 1080},
            "materials": {
                "videos": [{"id": "VINTRO", "path": ""}, {"id": "VMAIN", "path": ""}],
                "texts": [
                    text_material("TINTRO", "intro"),
                    text_material("TLOWER", "TTS"),
                ],
            },
            "tracks": [
                {"id": "TRACK_INTRO", "type": "video", "segments": [segment("VINTRO", 0, content_start)]},
                {
                    "id": "TRACK_MAIN",
                    "type": "video",
                    "segments": [segment("VMAIN", content_start, duration - content_start)],
                },
                {"id": "TRACK_INTRO_TEXT", "type": "text", "segments": [segment("TINTRO", 0, content_start)]},
                {
                    "id": "TRACK_LOWER_TEXT",
                    "type": "text",
                    "segments": [segment("TLOWER", content_start, duration - content_start)],
                },
            ],
        }
        timeline = self.source_root / "Timelines" / timeline_id
        timeline.mkdir(parents=True)
        for path in (
            self.source_root / "draft_content.json",
            self.source_root / "template-2.tmp",
            timeline / "draft_content.json",
            timeline / "template-2.tmp",
        ):
            write_json(path, document)

    def document_paths(self) -> list[Path]:
        timeline = next((self.source_root / "Timelines").iterdir())
        return [
            self.source_root / "draft_content.json",
            self.source_root / "template-2.tmp",
            timeline / "draft_content.json",
            timeline / "template-2.tmp",
        ]

    def add_legacy_resource_paths(self) -> None:
        legacy = "C:/Users/legacy/AppData/Local/CapCut/User Data/Projects/com.lveditor.draft/P0_OLD"
        for path in self.document_paths():
            document = json.loads(path.read_text(encoding="utf-8"))
            document["materials"]["videos"][0]["path"] = legacy + "/Resources/media/intro.mp4"
            document["materials"]["videos"][1]["path"] = legacy + "/Resources/media/main.png"
            write_json(path, document)

    def relative(self, path: Path) -> Path:
        return path.relative_to(self.workspace)

    def prepare_kwargs(self, **overrides) -> dict:
        values = {
            "workspace_root": self.workspace,
            "source_root": self.source_root,
            "capcut_root": self.capcut_root,
            "root_version": "v6",
            "root_profile": "jungchilong_v6_candidate",
            "base_layout_profile": "jungchilong_base_v5_candidate",
            "parent_contract_relative_path": self.relative(self.active.contract),
            "ffmpeg": "ffmpeg-test-adapter",
            "content_start_sec": 10.0,
        }
        values.update(overrides)
        return values


def fake_copy_resources(source_root: Path, stage: Path, ffmpeg: str, final_root: Path) -> dict[str, str]:
    del source_root, ffmpeg, final_root
    for relative, content in (
        (Path("Resources/media/intro.mp4"), b"intro"),
        (Path("Resources/media/main.png"), b"main"),
        (Path("Resources/fonts/lower.ttf"), b"font"),
    ):
        target = stage / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)
    return {}


def fake_update_root_meta(meta_path: Path, *args) -> bytes:
    del args
    return meta_path.read_bytes()


def approve_candidate(candidate) -> None:
    report = json.loads(candidate.report_path.read_text(encoding="utf-8"))
    report["visual_gate"] = "PASS_USER_VISUAL_GATE"
    report["post_open_validation"] = "PASS_CAPCUT_OPEN_CLOSE"
    write_json(candidate.report_path, report)

    evidence = json.loads(candidate.evidence_path.read_text(encoding="utf-8"))
    evidence["visual_gate"] = "PASS_USER_VISUAL_GATE"
    evidence["post_open_validation"] = "PASS_CAPCUT_OPEN_CLOSE"
    evidence["promotion_report"]["sha256"] = sha256_file(candidate.report_path)
    write_json(candidate.evidence_path, evidence)

    contract = json.loads(candidate.contract_path.read_text(encoding="utf-8"))
    contract["promotion_evidence"]["sha256"] = sha256_file(candidate.evidence_path)
    write_json(candidate.contract_path, contract)


def rebind_candidate_manifest(candidate, **identity) -> None:
    manifest = json.loads(candidate.manifest_path.read_text(encoding="utf-8"))
    manifest.update(identity)
    write_json(candidate.manifest_path, manifest)

    evidence = json.loads(candidate.evidence_path.read_text(encoding="utf-8"))
    evidence["manifest"]["sha256"] = sha256_file(candidate.manifest_path)
    write_json(candidate.evidence_path, evidence)

    contract = json.loads(candidate.contract_path.read_text(encoding="utf-8"))
    contract["manifest"]["sha256"] = sha256_file(candidate.manifest_path)
    contract["promotion_evidence"]["sha256"] = sha256_file(candidate.evidence_path)
    write_json(candidate.contract_path, contract)


def rebind_candidate_static_gate(candidate, static_gate: str) -> None:
    report = json.loads(candidate.report_path.read_text(encoding="utf-8"))
    report["status"] = static_gate
    write_json(candidate.report_path, report)

    evidence = json.loads(candidate.evidence_path.read_text(encoding="utf-8"))
    evidence["static_gate"] = static_gate
    evidence["promotion_report"]["sha256"] = sha256_file(candidate.report_path)
    write_json(candidate.evidence_path, evidence)

    contract = json.loads(candidate.contract_path.read_text(encoding="utf-8"))
    contract["promotion_evidence"]["required_static_gate"] = static_gate
    contract["promotion_evidence"]["sha256"] = sha256_file(candidate.evidence_path)
    write_json(candidate.contract_path, contract)


class PromoteCapcutRootTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.fixture = PromotionWorkspace(Path(self.temporary.name))
        self.adapters = [
            mock.patch.object(promoter, "copy_required_resources", side_effect=fake_copy_resources),
            mock.patch.object(promoter, "update_root_meta", side_effect=fake_update_root_meta),
            mock.patch.object(promoter, "ensure_capcut_closed", return_value=None, create=True),
        ]
        for adapter in self.adapters:
            adapter.start()

    def tearDown(self) -> None:
        for adapter in reversed(self.adapters):
            adapter.stop()
        self.temporary.cleanup()

    def prepare(self, **overrides):
        return promoter.prepare_candidate(**self.fixture.prepare_kwargs(**overrides))

    def pointer_bytes(self) -> bytes:
        return self.fixture.active.pointer.read_bytes()

    def assert_pointer_unchanged(self, before: bytes) -> None:
        self.assertEqual(self.pointer_bytes(), before)

    def test_prepare_rebases_embedded_resources_from_an_older_root(self):
        self.fixture.add_legacy_resource_paths()

        candidate = self.prepare()

        draft = json.loads(
            (candidate.capcut_project_path / "draft_content.json").read_text(encoding="utf-8")
        )
        paths = [item["path"] for item in draft["materials"]["videos"]]
        self.assertEqual(
            paths,
            [
                (candidate.capcut_project_path / "Resources/media/intro.mp4").as_posix(),
                (candidate.capcut_project_path / "Resources/media/main.png").as_posix(),
            ],
        )

    def test_rebase_embedded_resource_paths_accepts_single_backslashes_only_for_safe_relative_paths(self):
        root = Path("C:/new-root")
        self.assertEqual(
            promoter.rewrite_embedded_resource_paths(
                r"C:\old\Resources\media\main.png", root
            ),
            "C:/new-root/Resources/media/main.png",
        )
        for unsafe in (
            "C:/old/Resources/D:/escape.mp4",
            r"C:\old\Resources\..\escape.mp4",
            "C:/old/Resources/./escape.mp4",
        ):
            with self.subTest(unsafe=unsafe):
                self.assertEqual(
                    promoter.rewrite_embedded_resource_paths(unsafe, root), unsafe
                )

    def test_prepare_requires_version_profile_base_layout_and_parent_contract(self):
        required = (
            "root_version",
            "root_profile",
            "base_layout_profile",
            "parent_contract_relative_path",
        )
        for field in required:
            with self.subTest(field=field):
                values = self.fixture.prepare_kwargs()
                values.pop(field)
                with self.assertRaises(TypeError):
                    promoter.prepare_candidate(**values)

    def test_prepare_rejects_v5_and_any_existing_bundle_target(self):
        before = self.pointer_bytes()
        with self.assertRaisesRegex(RuntimeError, "ROOT_VERSION"):
            self.prepare(root_version="v5")
        self.assert_pointer_unchanged(before)

        candidate = self.prepare()
        with self.assertRaisesRegex(RuntimeError, "EXISTS"):
            self.prepare()
        self.assertTrue(candidate.contract_path.is_file())
        self.assert_pointer_unchanged(before)

    def test_prepare_writes_candidate_bundle_without_changing_active_pointer(self):
        before = self.pointer_bytes()
        candidate = self.prepare()
        self.assert_pointer_unchanged(before)
        self.assertEqual(candidate.status, "CANDIDATE_ROOT_BUNDLE_PREPARED")
        for path in (
            candidate.archive_path,
            candidate.manifest_path,
            candidate.layout_path,
            candidate.report_path,
            candidate.evidence_path,
            candidate.contract_path,
        ):
            self.assertTrue(path.is_file(), path)
        self.assertEqual(
            candidate.contract_path.name,
            "capcut_root_contract_v6_jungchilong_v6_candidate.json",
        )

    def test_prepare_manifest_uses_requested_root_and_base_layout_profiles(self):
        candidate = self.prepare(
            root_profile="jungchilong_v6_new_visual",
            base_layout_profile="jungchilong_base_v5_locked",
        )
        manifest = json.loads(candidate.manifest_path.read_text(encoding="utf-8"))
        self.assertEqual(manifest["root_profile"], "jungchilong_v6_new_visual")
        self.assertEqual(manifest["base_layout_profile"], "jungchilong_base_v5_locked")
        self.assertEqual(manifest["template_profile"], "jungchilong_base_v5_locked")

    def test_prepare_records_static_pass_but_visual_and_post_open_wait(self):
        candidate = self.prepare()
        evidence = json.loads(candidate.evidence_path.read_text(encoding="utf-8"))
        self.assertEqual(evidence["static_gate"], "PASS_ROOT_PROMOTION_STATIC")
        self.assertEqual(evidence["visual_gate"], "WAIT_USER_VISUAL_GATE")
        self.assertEqual(evidence["post_open_validation"], "WAIT_CAPCUT_OPEN_CLOSE")
        self.assertFalse(evidence["episode_visual_gate_inherited"])
        self.assertFalse(candidate.active)

    def test_activate_rejects_visual_or_post_open_wait_for_v6(self):
        candidate = self.prepare()
        before = self.pointer_bytes()
        with self.assertRaisesRegex(RuntimeError, "ACTIVATION_POLICY"):
            promoter.activate_candidate(self.fixture.workspace, candidate.contract_relative_path)
        self.assert_pointer_unchanged(before)

    def test_activate_rejects_hash_consistent_non_pass_static_gate_for_v6(self):
        candidate = self.prepare()
        approve_candidate(candidate)
        rebind_candidate_static_gate(candidate, "NOT_STATIC_PASS")
        before = self.pointer_bytes()

        with self.assertRaisesRegex(RuntimeError, "ACTIVATION_POLICY"):
            promoter.activate_candidate(self.fixture.workspace, candidate.contract_relative_path)

        self.assert_pointer_unchanged(before)

    def test_candidate_output_paths_include_version_and_profile(self):
        root = self.fixture.workspace
        capcut = self.fixture.capcut_root
        v6 = promoter._candidate_paths(root, capcut, "v6", "shared_profile")
        v7 = promoter._candidate_paths(root, capcut, "v7", "shared_profile")

        self.assertEqual(set(v6), set(v7))
        for key in v6:
            with self.subTest(output=key):
                self.assertNotEqual(v6[key], v7[key])
                self.assertIn("v6", v6[key].name)
                self.assertIn("shared_profile", v6[key].name)

    def test_activate_rejects_hash_consistent_manifest_identity_drift(self):
        candidate = self.prepare()
        approve_candidate(candidate)
        rebind_candidate_manifest(
            candidate,
            root_version="v999",
            root_profile="manifest-drift",
            base_layout_profile="manifest-base-drift",
        )
        before = self.pointer_bytes()

        with self.assertRaisesRegex(RuntimeError, "PROFILE_RELATION"):
            promoter.activate_candidate(self.fixture.workspace, candidate.contract_relative_path)

        self.assert_pointer_unchanged(before)

    def test_archive_write_failure_cleans_temporary_sibling_and_publishes_nothing(self):
        before = self.pointer_bytes()
        paths = promoter._candidate_paths(
            self.fixture.workspace,
            self.fixture.capcut_root,
            "v6",
            "jungchilong_v6_candidate",
        )

        with mock.patch.object(
            promoter.zipfile.ZipFile,
            "write",
            side_effect=OSError("forced zip write failure"),
        ):
            with self.assertRaisesRegex(OSError, "forced zip write failure"):
                self.prepare()

        self.assert_pointer_unchanged(before)
        self.assertFalse(paths["archive"].exists())
        self.assertEqual(
            list(paths["archive"].parent.glob(f".{paths['archive'].name}.*.tmp")),
            [],
        )
        for path in paths.values():
            self.assertFalse(path.exists(), path)

    def test_activate_rejects_contract_or_artifact_hash_drift(self):
        candidate = self.prepare()
        approve_candidate(candidate)
        before = self.pointer_bytes()

        contract = json.loads(candidate.contract_path.read_text(encoding="utf-8"))
        contract["root_profile"] = "drifted-profile"
        write_json(candidate.contract_path, contract)
        with self.assertRaisesRegex(RuntimeError, "PROFILE_RELATION"):
            promoter.activate_candidate(self.fixture.workspace, candidate.contract_relative_path)
        self.assert_pointer_unchanged(before)

        contract["root_profile"] = "jungchilong_v6_candidate"
        write_json(candidate.contract_path, contract)
        candidate.archive_path.write_bytes(candidate.archive_path.read_bytes() + b"drift")
        with self.assertRaisesRegex(RuntimeError, "ARCHIVE_HASH"):
            promoter.activate_candidate(self.fixture.workspace, candidate.contract_relative_path)
        self.assert_pointer_unchanged(before)

    def test_activate_rejects_non_monotonic_version_or_wrong_parent(self):
        candidate = self.prepare()
        approve_candidate(candidate)
        before = self.pointer_bytes()

        contract = json.loads(candidate.contract_path.read_text(encoding="utf-8"))
        contract["parent_root_version"] = "v4"
        write_json(candidate.contract_path, contract)
        with self.assertRaisesRegex(RuntimeError, "PARENT"):
            promoter.activate_candidate(self.fixture.workspace, candidate.contract_relative_path)
        self.assert_pointer_unchanged(before)

        contract["parent_root_version"] = "v5"
        contract["root_version"] = "v5"
        write_json(candidate.contract_path, contract)
        current = self.pointer_bytes()
        with self.assertRaisesRegex(RuntimeError, "ROOT_VERSION"):
            promoter.activate_candidate(self.fixture.workspace, candidate.contract_relative_path)
        self.assert_pointer_unchanged(current)

    def test_activate_updates_active_pointer_last_and_atomically(self):
        candidate = self.prepare()
        approve_candidate(candidate)
        before = self.pointer_bytes()
        real_replace = os.replace
        destinations: list[Path] = []

        def recording_replace(source, destination):
            destinations.append(Path(destination))
            return real_replace(source, destination)

        with mock.patch.object(promoter.os, "replace", side_effect=recording_replace):
            resolved = promoter.activate_candidate(
                self.fixture.workspace, candidate.contract_relative_path
            )

        self.assertEqual(resolved.root_version, "v6")
        self.assertNotEqual(self.pointer_bytes(), before)
        self.assertEqual(destinations[-1], self.fixture.active.pointer)
        pointer = json.loads(self.pointer_bytes().decode("utf-8"))
        self.assertEqual(
            pointer,
            {
                "schema": "politics-longform-capcut-active-root.v1",
                "active_root_version": "v6",
                "contract": {
                    "relative_path": candidate.contract_relative_path.as_posix(),
                    "sha256": hashlib.sha256(candidate.contract_path.read_bytes()).hexdigest().upper(),
                },
                "activation_basis": {"mode": "VERIFIED_VISUAL_AND_POST_OPEN"},
            },
        )

    def test_activation_failure_leaves_original_pointer_bytes_unchanged(self):
        candidate = self.prepare()
        approve_candidate(candidate)
        before = self.pointer_bytes()
        real_replace = os.replace

        def fail_pointer_replace(source, destination):
            if Path(destination) == self.fixture.active.pointer:
                raise OSError("simulated atomic pointer replace failure")
            return real_replace(source, destination)

        with mock.patch.object(promoter.os, "replace", side_effect=fail_pointer_replace):
            with self.assertRaisesRegex(OSError, "simulated atomic pointer replace failure"):
                promoter.activate_candidate(
                    self.fixture.workspace, candidate.contract_relative_path
                )

        self.assert_pointer_unchanged(before)
        self.assertTrue(candidate.contract_path.is_file())
        self.assertEqual(
            list(self.fixture.active.pointer.parent.glob(f".{self.fixture.active.pointer.name}.*.tmp")),
            [],
        )


if __name__ == "__main__":
    unittest.main()

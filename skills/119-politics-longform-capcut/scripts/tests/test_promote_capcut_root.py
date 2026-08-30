import hashlib
import json
import os
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest import mock


TESTS = Path(__file__).resolve().parent
SCRIPTS = TESTS.parent
for path in (SCRIPTS, TESTS):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

import promote_capcut_root as promoter
from test_root_bundle import BundleWorkspace, sha256_file, write_json


REAL_COPY_REQUIRED_RESOURCES = promoter.copy_required_resources


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

    def mutate_documents(self, mutate) -> None:
        for path in self.document_paths():
            document = json.loads(path.read_text(encoding="utf-8"))
            mutate(document)
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

    def test_prepare_rejects_missing_external_legacy_resource_before_candidate_pass(self):
        foreign = "D:/foreign/Resources/media/ghost.mp4"
        self.fixture.mutate_documents(
            lambda document: document["materials"]["videos"][0].update(path=foreign)
        )
        before = self.pointer_bytes()

        with self.assertRaisesRegex(RuntimeError, "TARGET_MISSING") as raised:
            self.prepare()

        self.assertIn(foreign, str(raised.exception))
        self.assert_pointer_unchanged(before)
        paths = promoter._candidate_paths(
            self.fixture.workspace,
            self.fixture.capcut_root,
            "v6",
            "jungchilong_v6_candidate",
        )
        self.assertTrue(all(not path.exists() for path in paths.values()))

    def test_prepare_exact_cache_rewrite_uses_redirected_localappdata_source(self):
        with tempfile.TemporaryDirectory() as temporary:
            local_appdata = Path(temporary) / "redirected-local-appdata"
            cache = local_appdata / "CapCut" / "User Data" / "Cache"
            required = {
                "onlineMaterial/ef5698ccb230899728b7a842abf9ec39.mp4": b"intro-source",
                "onlineMaterial/1e65543d3133b8129357b0b0b4c1211e.png": b"main-source",
                "onlineMaterial/74ce29b9d8294a2c88c345a10249e987": b"texture-source",
                "effect/7528305055972199681/0e4893968fe2d82714917f69c69826aa/font.ttf": b"font-source",
            }
            for relative, payload in required.items():
                path = cache / Path(relative)
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(payload)
            actual_intro = (cache / "onlineMaterial/ef5698ccb230899728b7a842abf9ec39.mp4").as_posix()
            actual_main = (cache / "onlineMaterial/1e65543d3133b8129357b0b0b4c1211e.png").as_posix()
            self.fixture.mutate_documents(
                lambda document: (
                    document["materials"]["videos"][0].update(path=actual_intro),
                    document["materials"]["videos"][1].update(path=actual_main),
                )
            )

            def fake_ffmpeg(command, **kwargs):
                del kwargs
                Path(command[-1]).write_bytes(b"intro-output")
                return mock.Mock(returncode=0, stdout="", stderr="")

            with mock.patch.dict(os.environ, {"LOCALAPPDATA": str(local_appdata)}), mock.patch.object(
                promoter, "copy_required_resources", side_effect=REAL_COPY_REQUIRED_RESOURCES
            ), mock.patch.object(promoter.subprocess, "run", side_effect=fake_ffmpeg):
                candidate = self.prepare()

        draft = json.loads(
            (candidate.capcut_project_path / "draft_content.json").read_text(encoding="utf-8")
        )
        self.assertEqual(
            [material["path"] for material in draft["materials"]["videos"]],
            [
                (candidate.capcut_project_path / "Resources/media/123123.mp4").as_posix(),
                (candidate.capcut_project_path / "Resources/media/main-video-slot.png").as_posix(),
            ],
        )

    def test_prepare_rejects_foreign_video_without_deleting_original_evidence(self):
        foreign = "D:/foreign/original.mp4"
        self.fixture.mutate_documents(
            lambda document: document["materials"]["videos"][0].update(path=foreign)
        )
        source_bytes = {path: path.read_bytes() for path in self.fixture.document_paths()}
        before = self.pointer_bytes()

        with self.assertRaisesRegex(RuntimeError, "FOREIGN") as raised:
            self.prepare()

        self.assertIn(foreign, str(raised.exception))
        self.assert_pointer_unchanged(before)
        self.assertEqual(source_bytes, {path: path.read_bytes() for path in self.fixture.document_paths()})
        paths = promoter._candidate_paths(
            self.fixture.workspace,
            self.fixture.capcut_root,
            "v6",
            "jungchilong_v6_candidate",
        )
        self.assertTrue(all(not path.exists() for path in paths.values()))

    def test_prepare_rejects_foreign_audio_and_nested_material_metadata(self):
        mutations = (
            lambda document: document["materials"].update(
                audios=[{"id": "A", "path": "D:/foreign/audio.wav"}]
            ),
            lambda document: document["materials"]["videos"][0].update(
                metadata={"nested": {"local_path": "D:/foreign/nested.wav"}}
            ),
            lambda document: document["materials"]["videos"][0].update(
                metadata=json.dumps(json.dumps({"local_path": "D:/foreign/double.wav"}))
            ),
        )
        for mutate in mutations:
            with self.subTest(mutate=mutate), tempfile.TemporaryDirectory() as temporary:
                fixture = PromotionWorkspace(Path(temporary))
                fixture.mutate_documents(mutate)
                with mock.patch.object(
                    promoter, "copy_required_resources", side_effect=fake_copy_resources
                ), mock.patch.object(
                    promoter, "update_root_meta", side_effect=fake_update_root_meta
                ), mock.patch.object(promoter, "ensure_capcut_closed", return_value=None):
                    with self.assertRaisesRegex(RuntimeError, "FOREIGN"):
                        promoter.prepare_candidate(**fixture.prepare_kwargs())

    def test_prepare_rejects_traversal_drive_relative_and_malformed_wrapper_before_rewrite(self):
        cases = (
            (lambda document: document["materials"]["videos"][0].update(path="Resources/../escape.mp4"), "TRAVERSAL"),
            (lambda document: document["materials"]["videos"][0].update(path=r"C:old\Resources\media\main.mp4"), "DRIVE_RELATIVE"),
            (lambda document: document["materials"]["videos"][0].update(metadata='{"path":'), "JSON_INVALID"),
            (
                lambda document: document["materials"]["videos"][0].update(
                    metadata=json.dumps(json.dumps(json.dumps({"path": "Resources/a"})))
                ),
                "DEPTH_EXCEEDED",
            ),
        )
        for mutate, code in cases:
            with self.subTest(code=code), tempfile.TemporaryDirectory() as temporary:
                fixture = PromotionWorkspace(Path(temporary))
                fixture.mutate_documents(mutate)
                with mock.patch.object(
                    promoter, "copy_required_resources", side_effect=fake_copy_resources
                ), mock.patch.object(
                    promoter, "update_root_meta", side_effect=fake_update_root_meta
                ), mock.patch.object(promoter, "ensure_capcut_closed", return_value=None):
                    with self.assertRaisesRegex(RuntimeError, code):
                        promoter.prepare_candidate(**fixture.prepare_kwargs())

    def test_prepare_rejects_lexical_candidate_root_prefix_collision(self):
        candidate_root = promoter._candidate_paths(
            self.fixture.workspace,
            self.fixture.capcut_root,
            "v6",
            "jungchilong_v6_candidate",
        )["root"]
        collision = candidate_root.with_name(candidate_root.name + "-evil") / "escape.wav"
        self.fixture.mutate_documents(
            lambda document: document["materials"].update(
                audios=[{"id": "A", "path": collision.as_posix()}]
            )
        )

        with self.assertRaisesRegex(RuntimeError, "FOREIGN"):
            self.prepare()

    def test_prepare_does_not_decode_arbitrary_display_strings(self):
        self.fixture.mutate_documents(
            lambda document: document["materials"]["videos"][0].update(
                name="[Intro]",
                text="{literal material name",
                visible=json.dumps({"local_path": "D:/display-only.wav"}),
            )
        )

        candidate = self.prepare()

        self.assertEqual(candidate.status, "CANDIDATE_ROOT_BUNDLE_PREPARED")

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

    def test_prepare_archive_is_portable_while_local_candidate_keeps_local_paths(self):
        source_root = self.fixture.source_root.as_posix()

        def add_root_paths(document):
            document["draft_meta_info"] = {
                "draft_fold_path": source_root,
                "draft_root_path": self.fixture.source_root.parent.as_posix(),
                "draft_cover": source_root + "/draft_cover.jpg",
                "attachment": {
                    "asset_path": source_root + "/Resources/media/intro.mp4"
                },
            }

        self.fixture.mutate_documents(add_root_paths)

        candidate = self.prepare()

        local = json.loads(
            (candidate.capcut_project_path / "draft_content.json").read_text(encoding="utf-8")
        )
        local_root = candidate.capcut_project_path.as_posix()
        self.assertEqual(local["draft_meta_info"]["draft_fold_path"], local_root)
        self.assertEqual(
            local["draft_meta_info"]["draft_cover"], local_root + "/draft_cover.jpg"
        )
        self.assertEqual(
            local["draft_meta_info"]["draft_root_path"],
            candidate.capcut_project_path.parent.as_posix(),
        )
        self.assertEqual(
            local["draft_meta_info"]["attachment"]["asset_path"],
            local_root + "/Resources/media/intro.mp4",
        )

        with zipfile.ZipFile(candidate.archive_path) as package:
            payloads = [
                package.read(entry).decode("utf-8")
                for entry in package.namelist()
                if Path(entry).suffix.lower() in {".json", ".tmp"}
            ]
        archive_text = "\n".join(payloads)
        self.assertNotIn(source_root, archive_text)
        self.assertNotIn(local_root, archive_text)
        self.assertIn("C:/__CAPCUT_ROOT_BUNDLE__", archive_text)
        self.assertIn("C:/__CAPCUT_DRAFT_ROOT_BUNDLE__", archive_text)

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

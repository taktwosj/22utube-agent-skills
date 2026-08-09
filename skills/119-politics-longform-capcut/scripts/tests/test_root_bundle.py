import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path


SCRIPTS = Path(__file__).resolve().parents[1]
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from root_bundle import resolve_active_root


RESOLVER_CLI = SCRIPTS / "resolve_politics_capcut_root.py"
MISSING = object()


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest().upper()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


class BundleWorkspace:
    bundle_relative = Path("00_asset_tools/templates/capcut/jungchilong")

    def __init__(self, root: Path) -> None:
        self.root = root
        self.bundle = root / self.bundle_relative
        self.pointer = self.bundle / "capcut_active_root_v1.json"
        self.contract = self.bundle / "contracts/capcut_root_contract_v5.json"
        self.archive = self.bundle / "root.zip"
        self.manifest = self.bundle / "manifest.json"
        self.layout = self.bundle / "layout.json"
        self.evidence = self.bundle / "evidence.json"
        self.promotion_report = self.bundle / "promotion.json"
        self.archive_root = "ROOT_V5/"
        self._create()

    def relative(self, path: Path) -> str:
        return path.relative_to(self.root).as_posix()

    def read(self, path: Path) -> dict:
        return json.loads(path.read_text(encoding="utf-8"))

    def _create(self) -> None:
        self.bundle.mkdir(parents=True)
        draft = {
            "duration": 100,
            "canvas_config": {"width": 1920, "height": 1080},
            "materials": {"videos": [{"id": "M1"}], "texts": []},
            "tracks": [
                {
                    "id": "T1",
                    "type": "video",
                    "segments": [
                        {
                            "material_id": "M1",
                            "target_timerange": {"start": 0, "duration": 100},
                            "clip": {
                                "scale": {"x": 1.0, "y": 1.0},
                                "rotation": 0.0,
                                "transform": {"x": 0.0, "y": 0.0},
                                "alpha": 1.0,
                            },
                        }
                    ],
                }
            ],
        }
        archive_files = {
            "draft_content.json": json.dumps(draft, separators=(",", ":")).encode("utf-8"),
            "asset.bin": b"root-bundle-fixture",
        }
        with zipfile.ZipFile(self.archive, "w", compression=zipfile.ZIP_STORED) as package:
            for name, content in archive_files.items():
                package.writestr(f"{self.archive_root}{name}", content)

        manifest = {
            "status": "PASS_ARCHIVE_INTEGRITY",
            "template_profile": "base-layout-v4",
            "source_candidate": "candidate-v5",
            "archive_root": self.archive_root,
            "archive_sha256": sha256_file(self.archive),
            "files": [
                {"path": name, "bytes": len(content), "sha256": sha256_bytes(content)}
                for name, content in archive_files.items()
            ],
        }
        write_json(self.manifest, manifest)
        layout = {
            "schema": "politics-longform-capcut-layout.v1",
            "root_version": "v5",
            "root_profile": "root-profile-v5",
            "base_layout_profile": "base-layout-v4",
            "canvas": {"width": 1920, "height": 1080},
            "duration_us": 100,
            "content_start_us": 0,
            "track_count": 1,
            "roles": [
                {
                    "role": "PRIMARY_VIDEO_SLOT",
                    "track_index": 0,
                    "track_id": "T1",
                    "track_type": "video",
                    "material_selector": {"kind": "material_id", "value": "M1"},
                    "seed_target_range_us": {"start": 0, "duration": 100},
                    "clip": {
                        "scale": {"x": 1.0, "y": 1.0},
                        "rotation": 0.0,
                        "transform": {"x": 0.0, "y": 0.0},
                        "alpha": 1.0,
                    },
                }
            ],
        }
        write_json(self.layout, layout)
        promotion = {
            "status": "PASS_ROOT_PROMOTION_STATIC",
            "source_root": r"C:\staging\candidate-v5",
            "visual_gate": "WAIT_USER_VISUAL_GATE",
            "post_open_validation": "WAIT_CAPCUT_OPEN_CLOSE",
        }
        write_json(self.promotion_report, promotion)
        evidence = {
            "schema": "politics-longform-capcut-root-evidence.v1",
            "root_version": "v5",
            "root_profile": "root-profile-v5",
            "source_candidate": "candidate-v5",
            "archive": {"relative_path": self.relative(self.archive), "sha256": sha256_file(self.archive)},
            "manifest": {"relative_path": self.relative(self.manifest), "sha256": sha256_file(self.manifest)},
            "promotion_report": {
                "relative_path": self.relative(self.promotion_report),
                "sha256": sha256_file(self.promotion_report),
            },
            "static_gate": "PASS_ROOT_PROMOTION_STATIC",
            "visual_gate": "WAIT_USER_VISUAL_GATE",
            "post_open_validation": "WAIT_CAPCUT_OPEN_CLOSE",
            "episode_visual_gate_inherited": False,
        }
        write_json(self.evidence, evidence)
        contract = {
            "schema": "politics-longform-capcut-root-bundle.v1",
            "root_version": "v5",
            "root_profile": "root-profile-v5",
            "base_layout_profile": "base-layout-v4",
            "immutable": True,
            "parent_root_version": "v4",
            "source_candidate": "candidate-v5",
            "archive": {
                "relative_path": self.relative(self.archive),
                "sha256": sha256_file(self.archive),
                "archive_root": self.archive_root,
                "file_count": len(archive_files),
            },
            "manifest": {
                "relative_path": self.relative(self.manifest),
                "sha256": sha256_file(self.manifest),
                "required_status": "PASS_ARCHIVE_INTEGRITY",
            },
            "layout_contract": {
                "relative_path": self.relative(self.layout),
                "sha256": sha256_file(self.layout),
                "required_schema": "politics-longform-capcut-layout.v1",
            },
            "promotion_evidence": {
                "relative_path": self.relative(self.evidence),
                "sha256": sha256_file(self.evidence),
                "required_static_gate": "PASS_ROOT_PROMOTION_STATIC",
            },
            "activation_policy": {
                "mode": "LEGACY_V5_STATIC_LOCK",
                "allows_historical_visual_wait": True,
                "allows_historical_post_open_wait": True,
                "episode_visual_gate_inherited": False,
            },
        }
        write_json(self.contract, contract)
        self.rebind_pointer("LEGACY_V5_STATIC_LOCK")

    def rebind_pointer(self, mode: str | None = None) -> None:
        old = self.read(self.pointer) if self.pointer.exists() else {}
        contract = self.read(self.contract)
        pointer = {
            "schema": "politics-longform-capcut-active-root.v1",
            "active_root_version": contract["root_version"],
            "contract": {"relative_path": self.relative(self.contract), "sha256": sha256_file(self.contract)},
            "activation_basis": {"mode": mode or old.get("activation_basis", {}).get("mode", "LEGACY_V5_STATIC_LOCK")},
        }
        write_json(self.pointer, pointer)

    def rebind_contract_artifact(self, field: str, path: Path) -> None:
        contract = self.read(self.contract)
        contract[field]["sha256"] = sha256_file(path)
        write_json(self.contract, contract)
        self.rebind_pointer()

    def set_version_and_policy(self, version: str, mode: str, *, pass_gates: bool) -> None:
        layout = self.read(self.layout)
        layout["root_version"] = version
        layout["root_profile"] = f"root-profile-{version}"
        write_json(self.layout, layout)
        manifest = self.read(self.manifest)
        manifest["root_version"] = version
        manifest["root_profile"] = f"root-profile-{version}"
        manifest["base_layout_profile"] = "base-layout-v4"
        write_json(self.manifest, manifest)
        promotion = self.read(self.promotion_report)
        evidence = self.read(self.evidence)
        evidence["root_version"] = version
        evidence["root_profile"] = f"root-profile-{version}"
        evidence["manifest"]["sha256"] = sha256_file(self.manifest)
        if pass_gates:
            evidence["visual_gate"] = "PASS_USER_VISUAL_GATE"
            evidence["post_open_validation"] = "PASS_CAPCUT_OPEN_CLOSE"
            promotion["visual_gate"] = evidence["visual_gate"]
            promotion["post_open_validation"] = evidence["post_open_validation"]
        write_json(self.promotion_report, promotion)
        evidence["promotion_report"]["sha256"] = sha256_file(self.promotion_report)
        write_json(self.evidence, evidence)
        contract = self.read(self.contract)
        contract["root_version"] = version
        contract["root_profile"] = f"root-profile-{version}"
        contract["parent_root_version"] = f"v{int(version[1:]) - 1}"
        contract["manifest"]["sha256"] = sha256_file(self.manifest)
        contract["layout_contract"]["sha256"] = sha256_file(self.layout)
        contract["promotion_evidence"]["sha256"] = sha256_file(self.evidence)
        contract["activation_policy"] = {
            "mode": mode,
            "allows_historical_visual_wait": False,
            "allows_historical_post_open_wait": False,
            "episode_visual_gate_inherited": False,
        }
        write_json(self.contract, contract)
        self.rebind_pointer(mode)


class RootBundleTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.fixture = BundleWorkspace(Path(self.temporary.name))

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def assert_code(self, code: str, action) -> None:
        with self.assertRaises(RuntimeError) as caught:
            action()
        self.assertEqual(str(caught.exception), code)

    def test_resolves_active_v5_bundle_and_reports_historical_wait_without_episode_promotion(self):
        resolved = resolve_active_root(self.fixture.root)
        report = resolved.to_report()
        self.assertEqual(resolved.root_version, "v5")
        self.assertEqual(resolved.root_profile, "root-profile-v5")
        self.assertEqual(resolved.base_layout_profile, "base-layout-v4")
        self.assertEqual(resolved.archive_path, self.fixture.archive.resolve())
        self.assertEqual(resolved.archive_sha256, sha256_file(self.fixture.archive))
        self.assertEqual(report["status"], "PASS_ROOT_CONTRACT")
        self.assertEqual(report["root_visual_gate"], "WAIT_USER_VISUAL_GATE")
        self.assertEqual(report["root_post_open_validation"], "WAIT_CAPCUT_OPEN_CLOSE")
        self.assertFalse(report["episode_visual_gate_inherited"])

    def test_allows_unrelated_archive_canvas_metadata(self):
        with zipfile.ZipFile(self.fixture.archive) as source:
            contents = {item.filename: source.read(item) for item in source.infolist()}
        draft_name = f"{self.fixture.archive_root}draft_content.json"
        draft = json.loads(contents[draft_name].decode("utf-8"))
        draft["canvas_config"].update({"ratio": "original", "background": None})
        contents[draft_name] = json.dumps(draft, separators=(",", ":")).encode("utf-8")
        with zipfile.ZipFile(self.fixture.archive, "w", compression=zipfile.ZIP_STORED) as package:
            for name, content in contents.items():
                package.writestr(name, content)
        manifest = self.fixture.read(self.fixture.manifest)
        manifest["archive_sha256"] = sha256_file(self.fixture.archive)
        for item in manifest["files"]:
            content = contents[f"{self.fixture.archive_root}{item['path']}"]
            item.update({"bytes": len(content), "sha256": sha256_bytes(content)})
        write_json(self.fixture.manifest, manifest)
        evidence = self.fixture.read(self.fixture.evidence)
        evidence["archive"]["sha256"] = sha256_file(self.fixture.archive)
        evidence["manifest"]["sha256"] = sha256_file(self.fixture.manifest)
        write_json(self.fixture.evidence, evidence)
        contract = self.fixture.read(self.fixture.contract)
        contract["archive"]["sha256"] = sha256_file(self.fixture.archive)
        contract["manifest"]["sha256"] = sha256_file(self.fixture.manifest)
        contract["promotion_evidence"]["sha256"] = sha256_file(self.fixture.evidence)
        write_json(self.fixture.contract, contract)
        self.fixture.rebind_pointer()
        self.assertEqual(resolve_active_root(self.fixture.root).root_version, "v5")

    def test_rejects_pointer_contract_hash_mismatch(self):
        pointer = self.fixture.read(self.fixture.pointer)
        pointer["contract"]["sha256"] = "0" * 64
        write_json(self.fixture.pointer, pointer)
        self.assert_code("FAIL_ROOT_BUNDLE_CONTRACT_HASH", lambda: resolve_active_root(self.fixture.root))

    def test_rejects_v5_when_all_rebound_static_gates_are_wait(self):
        promotion = self.fixture.read(self.fixture.promotion_report)
        promotion["status"] = "WAIT_ROOT_PROMOTION_STATIC"
        write_json(self.fixture.promotion_report, promotion)
        evidence = self.fixture.read(self.fixture.evidence)
        evidence["static_gate"] = "WAIT_ROOT_PROMOTION_STATIC"
        evidence["promotion_report"]["sha256"] = sha256_file(self.fixture.promotion_report)
        write_json(self.fixture.evidence, evidence)
        contract = self.fixture.read(self.fixture.contract)
        contract["promotion_evidence"]["required_static_gate"] = "WAIT_ROOT_PROMOTION_STATIC"
        contract["promotion_evidence"]["sha256"] = sha256_file(self.fixture.evidence)
        write_json(self.fixture.contract, contract)
        self.fixture.rebind_pointer()
        self.assert_code("FAIL_ROOT_BUNDLE_ACTIVATION_POLICY", lambda: resolve_active_root(self.fixture.root))

    def test_v6_requires_exact_verified_visual_and_post_open_activation_mode(self):
        with tempfile.TemporaryDirectory() as temporary:
            fixture = BundleWorkspace(Path(temporary))
            fixture.set_version_and_policy("v6", "ARBITRARY_FUTURE_MODE", pass_gates=True)
            self.assert_code("FAIL_ROOT_BUNDLE_ACTIVATION_POLICY", lambda: resolve_active_root(fixture.root))

    def test_v6_rejects_arbitrary_pass_looking_visual_and_post_open_gates(self):
        with tempfile.TemporaryDirectory() as temporary:
            fixture = BundleWorkspace(Path(temporary))
            fixture.set_version_and_policy("v6", "VERIFIED_VISUAL_AND_POST_OPEN", pass_gates=True)
            promotion = fixture.read(fixture.promotion_report)
            promotion["visual_gate"] = "PASS_NOT_DECLARED_VISUAL"
            promotion["post_open_validation"] = "PASS_NOT_DECLARED_POST_OPEN"
            write_json(fixture.promotion_report, promotion)
            evidence = fixture.read(fixture.evidence)
            evidence["visual_gate"] = promotion["visual_gate"]
            evidence["post_open_validation"] = promotion["post_open_validation"]
            evidence["promotion_report"]["sha256"] = sha256_file(fixture.promotion_report)
            write_json(fixture.evidence, evidence)
            contract = fixture.read(fixture.contract)
            contract["promotion_evidence"]["sha256"] = sha256_file(fixture.evidence)
            write_json(fixture.contract, contract)
            fixture.rebind_pointer("VERIFIED_VISUAL_AND_POST_OPEN")
            self.assert_code("FAIL_ROOT_BUNDLE_ACTIVATION_POLICY", lambda: resolve_active_root(fixture.root))

    def test_rejects_promotion_report_from_different_source_candidate(self):
        promotion = self.fixture.read(self.fixture.promotion_report)
        promotion["source_root"] = r"C:\staging\OTHER_CANDIDATE"
        write_json(self.fixture.promotion_report, promotion)
        evidence = self.fixture.read(self.fixture.evidence)
        evidence["promotion_report"]["sha256"] = sha256_file(self.fixture.promotion_report)
        write_json(self.fixture.evidence, evidence)
        contract = self.fixture.read(self.fixture.contract)
        contract["promotion_evidence"]["sha256"] = sha256_file(self.fixture.evidence)
        write_json(self.fixture.contract, contract)
        self.fixture.rebind_pointer()
        self.assert_code("FAIL_ROOT_BUNDLE_RELATION", lambda: resolve_active_root(self.fixture.root))

    def test_rejects_layout_content_start_that_differs_from_archive_role_boundary(self):
        layout = self.fixture.read(self.fixture.layout)
        layout["content_start_us"] = 99
        write_json(self.fixture.layout, layout)
        self.fixture.rebind_contract_artifact("layout_contract", self.fixture.layout)
        self.assert_code("FAIL_ROOT_BUNDLE_LAYOUT", lambda: resolve_active_root(self.fixture.root))

    def test_content_start_ignores_intro_hook_when_computing_archive_boundary(self):
        with zipfile.ZipFile(self.fixture.archive) as source:
            contents = {item.filename: source.read(item) for item in source.infolist()}
        draft_name = f"{self.fixture.archive_root}draft_content.json"
        draft = json.loads(contents[draft_name].decode("utf-8"))
        draft["tracks"][0]["segments"][0]["target_timerange"] = {"start": 0, "duration": 10}
        draft["materials"]["videos"].append({"id": "M2"})
        second_track = json.loads(json.dumps(draft["tracks"][0]))
        second_track["id"] = "T2"
        second_track["segments"][0]["material_id"] = "M2"
        second_track["segments"][0]["target_timerange"] = {"start": 10, "duration": 90}
        draft["tracks"].append(second_track)
        contents[draft_name] = json.dumps(draft, separators=(",", ":")).encode("utf-8")
        with zipfile.ZipFile(self.fixture.archive, "w", compression=zipfile.ZIP_STORED) as package:
            for name, content in contents.items():
                package.writestr(name, content)

        layout = self.fixture.read(self.fixture.layout)
        layout["roles"][0]["role"] = "INTRO_HOOK"
        layout["roles"][0]["seed_target_range_us"] = {"start": 0, "duration": 10}
        content_role = json.loads(json.dumps(layout["roles"][0]))
        content_role.update({"role": "PRIMARY_VIDEO_SLOT", "track_index": 1, "track_id": "T2"})
        content_role["material_selector"]["value"] = "M2"
        content_role["seed_target_range_us"] = {"start": 10, "duration": 90}
        layout.update({"content_start_us": 10, "track_count": 2, "roles": [layout["roles"][0], content_role]})
        write_json(self.fixture.layout, layout)

        manifest = self.fixture.read(self.fixture.manifest)
        manifest["archive_sha256"] = sha256_file(self.fixture.archive)
        for item in manifest["files"]:
            content = contents[f"{self.fixture.archive_root}{item['path']}"]
            item.update({"bytes": len(content), "sha256": sha256_bytes(content)})
        write_json(self.fixture.manifest, manifest)
        evidence = self.fixture.read(self.fixture.evidence)
        evidence["archive"]["sha256"] = sha256_file(self.fixture.archive)
        evidence["manifest"]["sha256"] = sha256_file(self.fixture.manifest)
        write_json(self.fixture.evidence, evidence)
        contract = self.fixture.read(self.fixture.contract)
        contract["archive"]["sha256"] = sha256_file(self.fixture.archive)
        contract["manifest"]["sha256"] = sha256_file(self.fixture.manifest)
        contract["layout_contract"]["sha256"] = sha256_file(self.fixture.layout)
        contract["promotion_evidence"]["sha256"] = sha256_file(self.fixture.evidence)
        write_json(self.fixture.contract, contract)
        self.fixture.rebind_pointer()
        self.assertEqual(resolve_active_root(self.fixture.root).root_version, "v5")

    def test_reports_workspace_relative_authority_paths_while_resolved_paths_remain_private(self):
        resolved = resolve_active_root(self.fixture.root)
        self.assertTrue(resolved.archive_path.is_absolute())
        report = resolved.to_report()
        expected = {
            "contract_path": self.fixture.relative(self.fixture.contract),
            "archive_path": self.fixture.relative(self.fixture.archive),
            "manifest_path": self.fixture.relative(self.fixture.manifest),
            "layout_path": self.fixture.relative(self.fixture.layout),
            "evidence_path": self.fixture.relative(self.fixture.evidence),
        }
        for field, relative_path in expected.items():
            with self.subTest(field=field):
                self.assertEqual(report[field], relative_path)
                self.assertNotIn(str(self.fixture.root), report[field])

    def malform_manifest_bytes(self, fixture: BundleWorkspace) -> None:
        manifest = fixture.read(fixture.manifest)
        manifest["files"][0]["bytes"] = "not-an-integer"
        write_json(fixture.manifest, manifest)
        evidence = fixture.read(fixture.evidence)
        evidence["manifest"]["sha256"] = sha256_file(fixture.manifest)
        write_json(fixture.evidence, evidence)
        contract = fixture.read(fixture.contract)
        contract["manifest"]["sha256"] = sha256_file(fixture.manifest)
        contract["promotion_evidence"]["sha256"] = sha256_file(fixture.evidence)
        write_json(fixture.contract, contract)
        fixture.rebind_pointer()

    def rebind_role_timing(self, fixture: BundleWorkspace, field: str, value: object) -> None:
        with zipfile.ZipFile(fixture.archive) as source:
            contents = {item.filename: source.read(item) for item in source.infolist()}
        draft_name = f"{fixture.archive_root}draft_content.json"
        draft = json.loads(contents[draft_name].decode("utf-8"))
        segment = draft["tracks"][0]["segments"][0]
        layout = fixture.read(fixture.layout)
        role = layout["roles"][0]
        if field == "target_timerange":
            if value is MISSING:
                segment.pop("target_timerange")
                role.pop("seed_target_range_us")
            else:
                segment["target_timerange"] = value
                role["seed_target_range_us"] = value
        else:
            target_range = segment["target_timerange"]
            seed_range = role["seed_target_range_us"]
            if value is MISSING:
                target_range.pop(field)
                seed_range.pop(field)
            else:
                target_range[field] = value
                seed_range[field] = value
            if field == "start" and value is True:
                layout["content_start_us"] = True
        contents[draft_name] = json.dumps(draft, separators=(",", ":")).encode("utf-8")
        with zipfile.ZipFile(fixture.archive, "w", compression=zipfile.ZIP_STORED) as package:
            for name, content in contents.items():
                package.writestr(name, content)
        write_json(fixture.layout, layout)

        manifest = fixture.read(fixture.manifest)
        manifest["archive_sha256"] = sha256_file(fixture.archive)
        for item in manifest["files"]:
            content = contents[f"{fixture.archive_root}{item['path']}"]
            item.update({"bytes": len(content), "sha256": sha256_bytes(content)})
        write_json(fixture.manifest, manifest)
        evidence = fixture.read(fixture.evidence)
        evidence["archive"]["sha256"] = sha256_file(fixture.archive)
        evidence["manifest"]["sha256"] = sha256_file(fixture.manifest)
        write_json(fixture.evidence, evidence)
        contract = fixture.read(fixture.contract)
        contract["archive"]["sha256"] = sha256_file(fixture.archive)
        contract["manifest"]["sha256"] = sha256_file(fixture.manifest)
        contract["layout_contract"]["sha256"] = sha256_file(fixture.layout)
        contract["promotion_evidence"]["sha256"] = sha256_file(fixture.evidence)
        write_json(fixture.contract, contract)
        fixture.rebind_pointer()

    def malformed_role_timing_cases(self) -> list[tuple[str, str, object]]:
        return [
            ("target_missing", "target_timerange", MISSING),
            ("target_bad", "target_timerange", "bad"),
            ("target_wrong_type", "target_timerange", []),
            ("start_missing", "start", MISSING),
            ("start_bad", "start", "bad"),
            ("start_wrong_type", "start", None),
            ("start_bool", "start", True),
            ("duration_missing", "duration", MISSING),
            ("duration_bad", "duration", "bad"),
            ("duration_wrong_type", "duration", None),
            ("duration_bool", "duration", True),
        ]

    def test_malformed_role_timing_is_normalized_to_layout_runtime_error(self):
        for label, field, value in self.malformed_role_timing_cases():
            with self.subTest(label=label), tempfile.TemporaryDirectory() as temporary:
                fixture = BundleWorkspace(Path(temporary))
                self.rebind_role_timing(fixture, field, value)
                self.assert_code("FAIL_ROOT_BUNDLE_LAYOUT", lambda: resolve_active_root(fixture.root))

    def test_cli_reports_malformed_role_timing_as_exit_2_without_traceback(self):
        for label, field, value in self.malformed_role_timing_cases():
            with self.subTest(label=label), tempfile.TemporaryDirectory() as temporary:
                fixture = BundleWorkspace(Path(temporary))
                self.rebind_role_timing(fixture, field, value)
                result = subprocess.run(
                    [sys.executable, str(RESOLVER_CLI), "--workspace-root", str(fixture.root)],
                    capture_output=True,
                    text=True,
                    check=False,
                )
                self.assertEqual(result.returncode, 2)
                self.assertEqual(result.stderr.strip(), "FAIL_ROOT_BUNDLE_LAYOUT")
                self.assertNotIn("Traceback", result.stderr)

    def test_malformed_manifest_bytes_is_normalized_to_inventory_runtime_error(self):
        self.malform_manifest_bytes(self.fixture)
        self.assert_code("FAIL_ROOT_BUNDLE_INVENTORY", lambda: resolve_active_root(self.fixture.root))

    def test_cli_reports_malformed_manifest_bytes_as_exit_2_without_traceback(self):
        self.malform_manifest_bytes(self.fixture)
        result = subprocess.run(
            [sys.executable, str(RESOLVER_CLI), "--workspace-root", str(self.fixture.root)],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 2)
        self.assertEqual(result.stderr.strip(), "FAIL_ROOT_BUNDLE_INVENTORY")
        self.assertNotIn("Traceback", result.stderr)

    def test_rejects_missing_layout_or_evidence(self):
        for path, code in (
            (self.fixture.layout, "WAIT_ROOT_BUNDLE_LAYOUT_NOT_FOUND"),
            (self.fixture.evidence, "WAIT_ROOT_BUNDLE_EVIDENCE_NOT_FOUND"),
        ):
            with self.subTest(path=path.name):
                content = path.read_bytes()
                path.unlink()
                self.assert_code(code, lambda: resolve_active_root(self.fixture.root))
                path.write_bytes(content)

    def test_rejects_manifest_layout_or_evidence_hash_mismatch(self):
        for path, code in (
            (self.fixture.manifest, "FAIL_ROOT_BUNDLE_MANIFEST_HASH"),
            (self.fixture.layout, "FAIL_ROOT_BUNDLE_LAYOUT_HASH"),
            (self.fixture.evidence, "FAIL_ROOT_BUNDLE_EVIDENCE_HASH"),
        ):
            with self.subTest(path=path.name):
                content = path.read_bytes()
                path.write_bytes(content + b" ")
                self.assert_code(code, lambda: resolve_active_root(self.fixture.root))
                path.write_bytes(content)

    def test_rejects_root_profile_base_layout_profile_relation_mismatch(self):
        layout = self.fixture.read(self.fixture.layout)
        layout["base_layout_profile"] = "wrong-layout"
        write_json(self.fixture.layout, layout)
        self.fixture.rebind_contract_artifact("layout_contract", self.fixture.layout)
        self.assert_code("FAIL_ROOT_BUNDLE_PROFILE_RELATION", lambda: resolve_active_root(self.fixture.root))

    def test_rejects_archive_root_file_count_or_inventory_mismatch(self):
        contract = self.fixture.read(self.fixture.contract)
        contract["archive"]["file_count"] += 1
        write_json(self.fixture.contract, contract)
        self.fixture.rebind_pointer()
        self.assert_code("FAIL_ROOT_BUNDLE_INVENTORY", lambda: resolve_active_root(self.fixture.root))

        self.tearDown()
        self.setUp()
        manifest = self.fixture.read(self.fixture.manifest)
        manifest["files"][0]["sha256"] = "0" * 64
        write_json(self.fixture.manifest, manifest)
        evidence = self.fixture.read(self.fixture.evidence)
        evidence["manifest"]["sha256"] = sha256_file(self.fixture.manifest)
        write_json(self.fixture.evidence, evidence)
        contract = self.fixture.read(self.fixture.contract)
        contract["manifest"]["sha256"] = sha256_file(self.fixture.manifest)
        contract["promotion_evidence"]["sha256"] = sha256_file(self.fixture.evidence)
        write_json(self.fixture.contract, contract)
        self.fixture.rebind_pointer()
        self.assert_code("FAIL_ROOT_BUNDLE_INVENTORY", lambda: resolve_active_root(self.fixture.root))

    def test_rejects_non_relative_or_escaping_paths(self):
        pointer = self.fixture.read(self.fixture.pointer)
        pointer["contract"]["relative_path"] = str(self.fixture.contract.resolve())
        write_json(self.fixture.pointer, pointer)
        self.assert_code("FAIL_ROOT_BUNDLE_PATH", lambda: resolve_active_root(self.fixture.root))

        self.tearDown()
        self.setUp()
        contract = self.fixture.read(self.fixture.contract)
        contract["archive"]["relative_path"] = "../escape.zip"
        write_json(self.fixture.contract, contract)
        self.fixture.rebind_pointer()
        self.assert_code("FAIL_ROOT_BUNDLE_PATH", lambda: resolve_active_root(self.fixture.root))

    def test_allows_legacy_v5_static_lock_only_for_v5(self):
        self.assertEqual(resolve_active_root(self.fixture.root).activation_mode, "LEGACY_V5_STATIC_LOCK")
        self.fixture.set_version_and_policy("v6", "LEGACY_V5_STATIC_LOCK", pass_gates=True)
        self.assert_code("FAIL_ROOT_BUNDLE_ACTIVATION_POLICY", lambda: resolve_active_root(self.fixture.root))

    def test_future_activation_requires_declared_visual_and_post_open_pass(self):
        self.fixture.set_version_and_policy("v6", "VERIFIED_VISUAL_AND_POST_OPEN", pass_gates=False)
        self.assert_code("FAIL_ROOT_BUNDLE_ACTIVATION_POLICY", lambda: resolve_active_root(self.fixture.root))
        self.fixture.set_version_and_policy("v6", "VERIFIED_VISUAL_AND_POST_OPEN", pass_gates=True)
        resolved = resolve_active_root(self.fixture.root)
        self.assertEqual(resolved.root_visual_gate, "PASS_USER_VISUAL_GATE")
        self.assertEqual(resolved.root_post_open_validation, "PASS_CAPCUT_OPEN_CLOSE")
        self.assertFalse(resolved.episode_visual_gate_inherited)


if __name__ == "__main__":
    unittest.main()

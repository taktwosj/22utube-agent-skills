import hashlib
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


SKILL = Path(__file__).resolve().parents[1]
SCRIPTS = SKILL / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))


def load_script(name):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class V2ReleaseContractTest(unittest.TestCase):
    def test_structure_snapshot_contract_is_v2(self):
        model = load_script("capcut_model")
        schema = json.loads(
            (SKILL / "schemas" / "structure_snapshot.schema.json").read_text(encoding="utf-8")
        )
        self.assertEqual(
            model.capture_structure_from_content({"tracks": []})["schema_version"],
            "001short-structure-snapshot-v2",
        )
        self.assertEqual(
            schema["properties"]["schema_version"]["const"],
            "001short-structure-snapshot-v2",
        )

    def test_project_validator_reports_v1_snapshot_migration_explicitly(self):
        validator = load_script("validate_capcut_project")
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            project = root / "project"
            project.mkdir()
            snapshot = root / "snapshot.json"
            snapshot.write_text(json.dumps({
                "schema_version": "001short-structure-snapshot-v1",
            }), encoding="utf-8")
            contract = root / "build-contract.json"
            contract.write_text("{}", encoding="utf-8")
            result = validator.validate_capcut_project(project, snapshot, contract)
        self.assertEqual(result["status"], "FAIL")
        self.assertEqual(result["errors"][0]["code"], "STRUCTURE_SNAPSHOT_MIGRATION_REQUIRED")

    def test_builder_keeps_source_authority_immutable_and_mutates_only_working_clone(self):
        builder = load_script("build_episode_capcut")
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source = root / "source-template"
            (source / "Timelines").mkdir(parents=True)
            (source / "draft_content.json").write_text('{"tracks": [], "materials": {}}', encoding="utf-8")
            (source / "draft_meta_info.json").write_text("{}", encoding="utf-8")
            (source / "Timelines" / "project.json").write_text("{}", encoding="utf-8")
            source_before = builder.clone_and_sync.hash_project_core(source)
            video = root / "source.mp4"
            video.write_bytes(b"video")
            design_evidence = root / "design.json"
            design_evidence.write_text("{}", encoding="utf-8")
            working = root / "work" / "working_project"
            normalized_paths = []

            def normalize(project, _config, _audio_source, _manifest):
                project = Path(project).resolve()
                normalized_paths.append(project)
                media = project / "Resources" / "media"
                media.mkdir(parents=True, exist_ok=True)
                (media / "episode-asset.bin").write_bytes(b"episode")
                (project / "draft_content.json").write_text(
                    '{"tracks": [], "materials": {}, "episode": true}', encoding="utf-8"
                )
                return []

            config = {
                "episode_root": str(root / "episode"),
                "local_capcut_root": str(root / "capcut"),
                "project_name": "episode-project",
                "work_root": str(root / "work"),
                "template_zip": str(root / "root.zip"),
                "_visual_input": {"video_input_path": str(video)},
            }
            prerequisites = {
                "audio_source": None,
                "build_manifest": {},
                "design_evidence": design_evidence,
            }
            with (
                patch.object(builder, "_ensure_media_tools"),
                patch.object(builder, "_validate_config"),
                patch.object(builder, "_extract_template", return_value=source),
                patch.object(builder, "_normalize_source", side_effect=normalize),
                patch.object(builder.apply_capcut_polish_profile, "apply_project", return_value={}),
                patch.object(builder.validate_capcut_polish_profile, "validate_project", return_value={"status": "PASS"}),
                patch.object(builder.clone_and_sync, "sync_project_ids", return_value={"status": "PASS"}),
                patch.object(builder.capcut_model, "load_project", return_value=object()),
                patch.object(builder.capcut_model, "capture_structure", return_value={"schema_version": "001short-structure-snapshot-v2", "track_order": [], "tracks": []}),
                patch.object(builder, "_assert_capcut_closed_for_target", side_effect=RuntimeError("STOP_AFTER_PREPARE")),
            ):
                with self.assertRaisesRegex(RuntimeError, "STOP_AFTER_PREPARE"):
                    builder._build_episode_once(config, prerequisites=prerequisites)

            self.assertEqual(builder.clone_and_sync.hash_project_core(source), source_before)
            self.assertFalse((source / "Resources" / "media" / "episode-asset.bin").exists())
            self.assertEqual(normalized_paths, [working.resolve()])
            self.assertTrue((working / "Resources" / "media" / "episode-asset.bin").is_file())
            snapshot = json.loads(
                (root / "episode" / "50_capcut_project" / "structure_snapshot.json").read_text(
                    encoding="utf-8"
                )
            )
            self.assertEqual(snapshot["authority"]["captured_from"], "working_project")
            self.assertEqual(
                snapshot["authority"]["source_structure_sha256"],
                builder.manifest_sha256(
                    {"schema_version": "001short-structure-snapshot-v2", "track_order": [], "tracks": []}
                ),
            )

    def test_protocol_requires_immutable_root_zip_and_clone_only_assembly(self):
        protocol = json.loads((SKILL / "protocol.json").read_text(encoding="utf-8"))
        contract = protocol["capcut_root_clone_contract"]
        self.assertTrue(contract["root_contract_validation_required"])
        self.assertTrue(contract["root_zip_immutable"])
        self.assertEqual(contract["extract_target"], "source_authority")
        self.assertTrue(contract["source_authority_immutable"])
        self.assertEqual(contract["assembly_target"], "working_project_clone_only")
        self.assertEqual(contract["new_ids"], ["project_id", "draft_id", "timeline_id"])
        self.assertTrue(contract["assembled_clone_validation_required"])

    def test_automation_terminal_state_remains_user_capcut_check(self):
        protocol = json.loads((SKILL / "protocol.json").read_text(encoding="utf-8"))
        workflow = json.loads((SKILL / "workflow.json").read_text(encoding="utf-8"))
        self.assertEqual(protocol["manual_finalization"]["automation_terminal_state"], "WAIT_USER_CAPCUT_CHECK")
        self.assertEqual(workflow["manual_finalization"]["automation_terminal_state"], "WAIT_USER_CAPCUT_CHECK")
        self.assertEqual(workflow["production_stages"][-1]["pass"], "WAIT_USER_CAPCUT_CHECK")

    def test_a11_is_sfx_and_a12_is_reserved_empty(self):
        protocol = json.loads((SKILL / "protocol.json").read_text(encoding="utf-8"))
        workflow = json.loads((SKILL / "workflow.json").read_text(encoding="utf-8"))
        tools = json.loads((SKILL / "tools.json").read_text(encoding="utf-8"))
        builder = load_script("build_episode_capcut")

        self.assertEqual(protocol["anchors"]["A11"], "sound effects")
        self.assertEqual(protocol["anchors"]["A12"], "reserved empty")
        roles = {row["id"]: row["role"] for row in tools["production_tools"]}
        self.assertEqual(roles["A11"], "sound effects")
        self.assertEqual(roles["A12_RESERVED_EMPTY"], "reserved empty")
        matrix = workflow["blueprint_frontend"]["matrix"]["vertical"]
        self.assertIn("A11_SFX", matrix)
        self.assertIn("A12_UNUSED", matrix)
        builder.assert_a12_empty([])
        with self.assertRaisesRegex(RuntimeError, "A12_RESERVED_EMPTY"):
            builder.assert_a12_empty([{"role": "A12"}])

    def test_onedrive_0000shrt_episode_root_contract(self):
        resolver = load_script("resolve_episode_root")
        with tempfile.TemporaryDirectory() as td:
            factory = Path(td) / "22factory_20260628"
            episode = factory / "0000shrt" / "260808_launch-demo_abc123"
            resolved = resolver.resolve_episode_root(factory, "260808_launch-demo_abc123")
            self.assertEqual(resolved, episode.resolve())
            self.assertEqual(resolver.required_episode_paths(resolved)["source_media"], episode / "00_input" / "source.mp4")
            with self.assertRaisesRegex(ValueError, "EPISODE_ROOT_NAME_INVALID"):
                resolver.resolve_episode_root(factory, "bad name")

    def test_source_intake_receipt_requires_verified_duration_and_immutable_locator_binding(self):
        validator = load_script("validate_source_intake")
        for intake_kind, locator, source_id in (
            ("GOOGLE_DRIVE", "https://drive.google.com/file/d/1a2B3c4D5e6F/view", "1a2B3c4D5e6F"),
            ("GOOGLE_DRIVE", "https://drive.google.com/drive/folders/1a2B3c4D5e6F", "1a2B3c4D5e6F"),
            ("URL", "https://www.youtube.com/watch?v=abc123", "abc123"),
            ("DESKTOP", "C:/Users/example/Desktop/source.mp4", "desktop-source"),
        ):
            with self.subTest(intake_kind=intake_kind), tempfile.TemporaryDirectory() as td:
                root = Path(td)
                media = root / "source.mp4"
                subprocess.run([
                    "ffmpeg", "-y", "-f", "lavfi", "-i", "color=c=black:s=16x16:d=0.2",
                    "-an", str(media),
                ], check=True, capture_output=True)
                media_sha = hashlib.sha256(media.read_bytes()).hexdigest()
                duration_us = round(float(subprocess.run([
                    "ffprobe", "-v", "error", "-show_entries", "format=duration",
                    "-of", "default=nw=1:nk=1", str(media),
                ], check=True, capture_output=True, text=True).stdout.strip()) * 1_000_000)
                identity = root / "source_identity.json"
                identity.write_text(json.dumps({
                    "schema_version": "source-identity-v1",
                    "episode_id": "EP_001",
                    "source_id": source_id,
                    "source_fingerprint": "fixture",
                    "media_path": "source.mp4",
                    "media_sha256": media_sha,
                }), encoding="utf-8")
                receipt = root / "source_intake_receipt.json"
                receipt.write_text(json.dumps({
                    "schema_version": "001short-source-intake-receipt-v1",
                    "episode_id": "EP_001",
                    "source_id": source_id,
                    "intake_kind": intake_kind,
                    "source_locator": locator,
                    "local_media_path": "source.mp4",
                    "local_media_sha256": media_sha,
                    "local_media_duration_us": duration_us,
                    "source_identity_path": "source_identity.json",
                    "source_identity_sha256": hashlib.sha256(identity.read_bytes()).hexdigest(),
                }), encoding="utf-8")
                self.assertEqual(validator.validate_receipt(receipt), [])

                payload = json.loads(receipt.read_text(encoding="utf-8"))
                payload["schema_version"] = "001short-source-intake-receipt-v2"
                payload["original_analysis_contract_version"] = "001short-original-source-transcript-v1"
                receipt.write_text(json.dumps(payload), encoding="utf-8")
                self.assertEqual(validator.validate_receipt(receipt), [])
                del payload["original_analysis_contract_version"]
                receipt.write_text(json.dumps(payload), encoding="utf-8")
                self.assertIn(
                    "INTAKE_RECEIPT_ORIGINAL_ANALYSIS_CONTRACT_REQUIRED",
                    validator.validate_receipt(receipt),
                )

                payload["schema_version"] = "001short-source-intake-receipt-v1"
                payload["source_id"] = "wrong"
                receipt.write_text(json.dumps(payload), encoding="utf-8")
                self.assertIn("INTAKE_RECEIPT_SOURCE_ID_MISMATCH", validator.validate_receipt(receipt))

    def test_source_intake_rejects_missing_or_mismatched_duration_and_accepts_drive_id_locator(self):
        validator = load_script("validate_source_intake")
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            media = root / "source.mp4"
            subprocess.run([
                "ffmpeg", "-y", "-f", "lavfi", "-i", "color=c=black:s=16x16:d=0.2",
                "-an", str(media),
            ], check=True, capture_output=True)
            media_sha = hashlib.sha256(media.read_bytes()).hexdigest()
            duration_us = round(float(subprocess.run([
                "ffprobe", "-v", "error", "-show_entries", "format=duration",
                "-of", "default=nw=1:nk=1", str(media),
            ], check=True, capture_output=True, text=True).stdout.strip()) * 1_000_000)
            identity = root / "source_identity.json"
            identity.write_text(json.dumps({
                "schema_version": "source-identity-v1", "episode_id": "EP_001",
                "source_id": "1a2B3c4D5e6F", "source_fingerprint": "fixture",
                "media_path": "source.mp4", "media_sha256": media_sha,
            }), encoding="utf-8")
            receipt = root / "source_intake_receipt.json"
            payload = {
                "schema_version": "001short-source-intake-receipt-v1", "episode_id": "EP_001",
                "source_id": "1a2B3c4D5e6F", "intake_kind": "GOOGLE_DRIVE",
                "source_locator": "https://drive.google.com/file/d/1a2B3c4D5e6F/view",
                "local_media_path": "source.mp4", "local_media_sha256": media_sha,
                "local_media_duration_us": duration_us,
                "source_identity_path": "source_identity.json",
                "source_identity_sha256": hashlib.sha256(identity.read_bytes()).hexdigest(),
            }
            receipt.write_text(json.dumps(payload), encoding="utf-8")
            self.assertEqual(validator.validate_receipt(receipt), [])
            payload.pop("local_media_duration_us")
            receipt.write_text(json.dumps(payload), encoding="utf-8")
            self.assertIn("INTAKE_RECEIPT_FIELD_REQUIRED:local_media_duration_us", validator.validate_receipt(receipt))
            payload["local_media_duration_us"] = duration_us + 1_000_000
            receipt.write_text(json.dumps(payload), encoding="utf-8")
            self.assertIn("INTAKE_RECEIPT_MEDIA_DURATION_MISMATCH", validator.validate_receipt(receipt))
            payload["local_media_duration_us"] = duration_us
            payload["source_locator"] = "1a2B3c4D5e6F"
            receipt.write_text(json.dumps(payload), encoding="utf-8")
            self.assertEqual(validator.validate_receipt(receipt), [])

    def test_thin_router_retains_handoff_compatibility(self):
        router = (SKILL / "SKILL.md").read_text(encoding="utf-8")
        orchestrator = SKILL / "references" / "production-orchestrator.md"
        self.assertTrue(orchestrator.is_file())
        self.assertIn("references/production-orchestrator.md", router)
        self.assertIn("schemas/conversation_handoff.schema.json", router)
        self.assertIn("scripts/validate_conversation_handoff.py", router)
        self.assertIn("HANDOFF_SECRET_MATERIAL_FORBIDDEN", router)
        self.assertLess(len(router.split()), 500)


if __name__ == "__main__":
    unittest.main()

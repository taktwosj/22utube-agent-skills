import hashlib
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


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

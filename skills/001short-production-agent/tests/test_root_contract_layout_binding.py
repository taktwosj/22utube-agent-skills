from __future__ import annotations

import hashlib
import json
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = SKILL_ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import resolve_shorts_capcut_root as resolver
import track_template_matrix as templates


TRACK_TYPES = (
    "video", "effect", "video", "text", "text", "text", "text", "text",
    "text", "text", "text", "audio", "audio", "audio", "audio",
)
LAYOUT_ROLES = (
    "VIDEO", "SCREEN_EFFECT", "SCREEN_WHITE", "SOURCE_CREDIT", "STATE_EFFECT_2",
    "STATE_EFFECT_1", "A10_TEXT_WHITE", "A10_TEXT_YELLOW", "A9_TEXT", "T2",
    "T1", "A9", "A10", "A11_SFX", "A12",
)


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def make_contract(
    root: Path,
    track_types: tuple[str, ...] = TRACK_TYPES,
) -> tuple[Path, Path]:
    archive = root / "templates" / "root.zip"
    archive.parent.mkdir(parents=True)
    tracks = [
        {"id": f"track-{index}", "type": track_type, "segments": []}
        for index, track_type in enumerate(track_types)
    ]
    with zipfile.ZipFile(archive, "w") as bundle:
        bundle.writestr("fixture/draft_content.json", json.dumps({"tracks": tracks}))
        bundle.writestr("fixture/draft_meta_info.json", "{}")
    archive_sha = hashlib.sha256(archive.read_bytes()).hexdigest()

    manifest = root / "templates" / "manifest.json"
    write_json(manifest, {
        "template_profile": templates.V3_TEMPLATE_PROFILE,
        "sha256": archive_sha,
    })
    layout = root / "templates" / "layout.json"
    write_json(layout, {
        "contract_version": "1.0.0",
        "template_profile": templates.V3_TEMPLATE_PROFILE,
        "archive_sha256": archive_sha,
        "tracks": [
            {
                "index": index,
                "track_id": track["id"],
                "type": track["type"],
                "role": LAYOUT_ROLES[index],
                "identity": {
                    "archive_sha256": archive_sha,
                    "track_id": track["id"],
                    "type": track["type"],
                },
            }
            for index, track in enumerate(tracks)
        ],
    })
    contract = root / "templates" / "root.json"
    write_json(contract, {
        "schema_version": "shorts-capcut-root-contract-v1",
        "workspace_relative": True,
        "assembly_mode": "clean_staging_copy",
        "profiles": {
            "fixture": {
                "template_profile": templates.V3_TEMPLATE_PROFILE,
                "archive_relative_path": "templates/root.zip",
                "manifest_relative_path": "templates/manifest.json",
                "layout_contract_relative_path": "templates/layout.json",
                "archive_sha256": archive_sha,
            }
        },
    })
    return contract, layout


class RootContractLayoutBindingTest(unittest.TestCase):
    def test_known_legacy_profile_without_layout_remains_explicitly_unbound(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            contract, _layout = make_contract(root)
            payload = json.loads(contract.read_text(encoding="utf-8"))
            profile = payload["profiles"]["fixture"]
            profile["template_profile"] = "shrt_white_base_v1"
            profile.pop("layout_contract_relative_path")
            write_json(contract, payload)
            manifest = root / profile["manifest_relative_path"]
            manifest_payload = json.loads(manifest.read_text(encoding="utf-8"))
            manifest_payload["template_profile"] = "shrt_white_base_v1"
            write_json(manifest, manifest_payload)

            resolved = resolver.resolve_root_contract(root, "fixture", contract)

            self.assertIsNone(resolved["layout_contract"])
            self.assertEqual(resolved["layout_contract_version"], "LEGACY_UNBOUND")
            self.assertEqual(resolved["track_count"], len(TRACK_TYPES))
            self.assertIs(resolved["legacy_layout_unbound"], True)

    def test_unknown_profile_without_layout_still_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            contract, _layout = make_contract(root)
            payload = json.loads(contract.read_text(encoding="utf-8"))
            profile = payload["profiles"]["fixture"]
            profile["template_profile"] = "custom_unbound_profile"
            profile.pop("layout_contract_relative_path")
            write_json(contract, payload)
            manifest = root / profile["manifest_relative_path"]
            manifest_payload = json.loads(manifest.read_text(encoding="utf-8"))
            manifest_payload["template_profile"] = "custom_unbound_profile"
            write_json(manifest, manifest_payload)

            with self.assertRaisesRegex(ValueError, "ROOT_CONTRACT_LAYOUT_MISSING"):
                resolver.resolve_root_contract(root, "fixture", contract)

    def test_resolver_binds_layout_profile_sha_and_archive_track_identities(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            contract, layout = make_contract(root)
            resolved = resolver.resolve_root_contract(root, "fixture", contract)

            self.assertEqual(resolved["layout_contract"], str(layout))
            self.assertEqual(resolved["layout_contract_version"], "1.0.0")
            self.assertEqual(resolved["track_count"], len(templates.CANONICAL_TRACKS))

    def test_layout_sha_and_archive_track_identity_mismatches_fail_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            contract, layout = make_contract(root)
            payload = json.loads(layout.read_text(encoding="utf-8"))
            payload["tracks"][3]["identity"]["track_id"] = "wrong-track"
            write_json(layout, payload)
            with self.assertRaisesRegex(
                ValueError, "ROOT_CONTRACT_LAYOUT_TRACK_IDENTITY_MISMATCH"
            ):
                resolver.resolve_root_contract(root, "fixture", contract)

    def test_profile_expected_track_type_and_role_order_cannot_be_self_consistent_lies(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            swapped = list(TRACK_TYPES)
            swapped[0], swapped[11] = swapped[11], swapped[0]
            contract, _layout = make_contract(root, tuple(swapped))
            with self.assertRaisesRegex(
                ValueError, "ROOT_CONTRACT_LAYOUT_TRACK_TYPE_MISMATCH"
            ):
                resolver.resolve_root_contract(root, "fixture", contract)

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            contract, layout = make_contract(root)
            payload = json.loads(layout.read_text(encoding="utf-8"))
            payload["tracks"][3]["role"] = "STATE_EFFECT_3"
            write_json(layout, payload)
            with self.assertRaisesRegex(
                ValueError, "ROOT_CONTRACT_LAYOUT_TRACK_ROLE_MISMATCH"
            ):
                resolver.resolve_root_contract(root, "fixture", contract)

            payload["tracks"][3]["identity"]["track_id"] = "track-3"
            payload["archive_sha256"] = "0" * 64
            write_json(layout, payload)
            with self.assertRaisesRegex(
                ValueError, "ROOT_CONTRACT_LAYOUT_SHA_MISMATCH"
            ):
                resolver.resolve_root_contract(root, "fixture", contract)


if __name__ == "__main__":
    unittest.main()

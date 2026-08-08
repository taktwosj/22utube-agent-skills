import hashlib
import json
import os
import subprocess
import sys
import unittest
import zipfile
from pathlib import Path, PurePosixPath


WORKSPACE_ROOT = Path(
    os.environ.get(
        "WORKSPACE_ROOT",
        Path.home() / "OneDrive" / "22utube" / "22factory_20260628",
    )
).resolve()
BUNDLE_RELATIVE = Path("00_asset_tools/templates/capcut/jungchilong")
BUNDLE_ROOT = WORKSPACE_ROOT / BUNDLE_RELATIVE
SKILL_ROOT = Path(__file__).resolve().parents[1] / "skills" / "119-politics-longform-capcut"

ACTIVE_POINTER = BUNDLE_ROOT / "capcut_active_root_v1.json"
V5_CONTRACT = BUNDLE_ROOT / "contracts" / "capcut_root_contract_v5.json"
V5_LAYOUT = (
    BUNDLE_ROOT
    / "layout_contracts"
    / "jungchilong_v5_layout_contract_v1.json"
)
V5_EVIDENCE = (
    BUNDLE_ROOT / "evidence" / "jungchilong_v5_promotion_evidence_v1.json"
)
V5_ARCHIVE = BUNDLE_ROOT / "jungchilong_v5_chapter_image_lower2_CAPCUT_20260803.zip"
V5_MANIFEST = BUNDLE_ROOT / "template_manifest_v5_chapter_image_lower2.json"
PROMOTION_REPORT = BUNDLE_ROOT / "promotion_reports" / "promotion_relinkprobev3_to_v5.json"
RESTORE_NOTES = BUNDLE_ROOT / "RESTORE_NOTES.md"
ROOT_BUNDLE_REFERENCE = SKILL_ROOT / "references" / "root-bundle-contract.md"
PROMOTER = SKILL_ROOT / "scripts" / "promote_capcut_root.py"

V5_ARCHIVE_SHA256 = "5D6241ED9816DD6F4123446DF35D54DF51318E61FEFF53CA13A96EE5E84A7F60"
V5_MANIFEST_SHA256 = "59AFDAF7BE780205CA17FAB4AB5D6E33B0D3A794F81B575392F3E356287658B8"
V5_ARCHIVE_ROOT = "P0_ROOT_jungchilong_v5_chapter_image_lower2/"

EXPECTED_TRACKS = [
    (0, "CFA8AA4D-4183-4B2B-90DF-EAD865D78FA7", "video", "ROOT_INTRO_BACKGROUND"),
    (1, "B85D9009-6BE0-428A-8979-230A57D08967", "video", "PRIMARY_VIDEO_SLOT"),
    (2, "C917C24A-730B-4BEA-801C-385B44D194F2", "sticker", "LOWER_RAIL"),
    (3, "5A7C7C19-F89A-41F1-B77C-95CAAA6F7ECD", "sticker", "UPPER_RAIL"),
    (4, "3A2EF03A-79F8-4429-9C76-47790D7BA74D", "text", "CTA"),
    (5, "A55954D1-1E93-4309-8367-383E59C528B6", "text", "CHAPTER_HOOK_SEED"),
    (5, "A55954D1-1E93-4309-8367-383E59C528B6", "text", "LOWER_TWO_LINE_SLOT"),
    (6, "BAD824D4-EBBB-4FDD-A572-F58458B2AF2F", "text", "INTRO_HOOK"),
    (7, "77215B57-6407-4628-9D9A-8019C9502585", "text", "CHAPTER_TITLE"),
    (8, "64BBB006-B1B7-4C11-9826-E08A7E26F3E3", "text", "SOURCE_AND_DATE"),
]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def workspace_path(relative_path: str) -> Path:
    relative = Path(relative_path)
    if relative.is_absolute():
        raise AssertionError(f"authority path must be WORKSPACE_ROOT-relative: {relative_path}")
    resolved = (WORKSPACE_ROOT / relative).resolve()
    if resolved != WORKSPACE_ROOT and WORKSPACE_ROOT not in resolved.parents:
        raise AssertionError(f"authority path escapes WORKSPACE_ROOT: {relative_path}")
    return resolved


def archive_inventory(archive: zipfile.ZipFile) -> tuple[list[zipfile.ZipInfo], set[str]]:
    entries = archive.infolist()
    files = [entry for entry in entries if not entry.is_dir()]
    relative_files = {
        PurePosixPath(entry.filename).relative_to(V5_ARCHIVE_ROOT.rstrip("/")).as_posix()
        for entry in files
    }
    return entries, relative_files


def draft_from_archive(archive: zipfile.ZipFile) -> dict:
    draft_path = f"{V5_ARCHIVE_ROOT}draft_content.json"
    return json.loads(archive.read(draft_path).decode("utf-8"))


def text_by_material_id(draft: dict) -> dict[str, str]:
    result = {}
    for material in draft["materials"]["texts"]:
        result[material["id"]] = json.loads(material["content"])["text"]
    return result


def segment_for_role(draft: dict, role: dict) -> dict:
    track = draft["tracks"][role["track_index"]]
    selector = role["material_selector"]
    if selector["kind"] == "material_id":
        matches = [
            segment
            for segment in track["segments"]
            if segment["material_id"] == selector["value"]
        ]
    else:
        texts = text_by_material_id(draft)
        if selector["kind"] == "text_exact":
            matches = [
                segment
                for segment in track["segments"]
                if texts.get(segment["material_id"]) == selector["value"]
            ]
        elif selector["kind"] == "text_prefix":
            matches = [
                segment
                for segment in track["segments"]
                if texts.get(segment["material_id"], "").startswith(selector["value"])
            ]
        else:
            raise AssertionError(f"unknown material selector kind: {selector['kind']}")
    if len(matches) != 1:
        raise AssertionError(
            f"role {role['role']} selector resolved {len(matches)} archive segments"
        )
    return matches[0]


class PoliticsRootBundleContractTests(unittest.TestCase):
    def require_path(self, path: Path) -> None:
        self.assertTrue(path.is_file(), f"required Task 1 artifact missing: {path}")

    def test_active_pointer_binds_versioned_contract_by_hash(self):
        self.require_path(ACTIVE_POINTER)
        pointer = load_json(ACTIVE_POINTER)

        self.assertEqual(
            set(pointer),
            {"schema", "active_root_version", "contract", "activation_basis"},
        )
        self.assertEqual(pointer["schema"], "politics-longform-capcut-active-root.v1")
        self.assertEqual(pointer["active_root_version"], "v5")
        self.assertEqual(set(pointer["contract"]), {"relative_path", "sha256"})
        self.assertEqual(pointer["activation_basis"], {"mode": "LEGACY_V5_STATIC_LOCK"})
        self.assertNotEqual(
            pointer["contract"]["relative_path"],
            f"{BUNDLE_RELATIVE.as_posix()}/capcut_root_contract_v1.json",
        )

        contract_path = workspace_path(pointer["contract"]["relative_path"])
        self.assertEqual(contract_path, V5_CONTRACT)
        self.assertEqual(sha256_file(contract_path), pointer["contract"]["sha256"])
        self.assertEqual(load_json(contract_path)["root_version"], "v5")

    def test_v5_contract_binds_archive_manifest_layout_and_evidence_by_hash(self):
        self.require_path(V5_CONTRACT)
        contract = load_json(V5_CONTRACT)

        self.assertEqual(contract["schema"], "politics-longform-capcut-root-bundle.v1")
        bound = (
            ("archive", V5_ARCHIVE),
            ("manifest", V5_MANIFEST),
            ("layout_contract", V5_LAYOUT),
            ("promotion_evidence", V5_EVIDENCE),
        )
        for field, expected_path in bound:
            artifact = contract[field]
            actual_path = workspace_path(artifact["relative_path"])
            self.assertEqual(actual_path, expected_path)
            self.assertEqual(sha256_file(actual_path), artifact["sha256"])

        self.assertEqual(contract["archive"]["archive_root"], V5_ARCHIVE_ROOT)
        self.assertEqual(contract["archive"]["file_count"], 43)
        self.assertEqual(contract["manifest"]["required_status"], "PASS_ARCHIVE_INTEGRITY")
        self.assertEqual(
            contract["layout_contract"]["required_schema"],
            "politics-longform-capcut-layout.v1",
        )
        self.assertEqual(
            contract["promotion_evidence"]["required_static_gate"],
            "PASS_ROOT_PROMOTION_STATIC",
        )

    def test_v5_identity_distinguishes_root_and_base_layout_profiles(self):
        self.require_path(V5_CONTRACT)
        contract = load_json(V5_CONTRACT)

        self.assertEqual(contract["root_version"], "v5")
        self.assertEqual(contract["root_profile"], "jungchilong_v5_chapter_image_lower2")
        self.assertEqual(
            contract["base_layout_profile"], "jungchilong_base_v4_hook10_lower2"
        )
        self.assertNotEqual(contract["root_profile"], contract["base_layout_profile"])
        self.assertTrue(contract["immutable"])
        self.assertEqual(contract["parent_root_version"], "v4")
        self.assertEqual(contract["source_candidate"], "PL_20260802_relink_probe_3m_v3")
        self.assertEqual(contract["activation_policy"]["mode"], "LEGACY_V5_STATIC_LOCK")
        self.assertTrue(contract["activation_policy"]["allows_historical_visual_wait"])
        self.assertTrue(contract["activation_policy"]["allows_historical_post_open_wait"])
        self.assertFalse(contract["activation_policy"]["episode_visual_gate_inherited"])

    def test_v5_layout_declares_exact_nine_track_roles_and_geometry(self):
        self.require_path(V5_LAYOUT)
        layout = load_json(V5_LAYOUT)

        self.assertEqual(layout["schema"], "politics-longform-capcut-layout.v1")
        self.assertEqual(layout["canvas"], {"width": 1920, "height": 1080})
        self.assertEqual(layout["duration_us"], 180000000)
        self.assertEqual(layout["content_start_us"], 10000000)
        self.assertEqual(layout["track_count"], 9)
        roles = layout["roles"]
        self.assertEqual(
            [
                (role["track_index"], role["track_id"], role["track_type"], role["role"])
                for role in roles
            ],
            EXPECTED_TRACKS,
        )
        physical_tracks = {
            (role["track_index"], role["track_id"], role["track_type"])
            for role in roles
        }
        self.assertEqual(len(physical_tracks), 9)

        with zipfile.ZipFile(V5_ARCHIVE, "r") as archive:
            draft = draft_from_archive(archive)
        self.assertEqual(draft["duration"], layout["duration_us"])
        self.assertEqual(
            {
                "width": draft["canvas_config"]["width"],
                "height": draft["canvas_config"]["height"],
            },
            layout["canvas"],
        )
        self.assertEqual(len(draft["tracks"]), layout["track_count"])

        for role in roles:
            archive_track = draft["tracks"][role["track_index"]]
            self.assertEqual(archive_track["id"], role["track_id"])
            self.assertEqual(archive_track["type"], role["track_type"])
            segment = segment_for_role(draft, role)
            self.assertEqual(segment["target_timerange"], role["seed_target_range_us"])
            self.assertEqual(segment["clip"]["scale"], role["clip"]["scale"])
            self.assertEqual(segment["clip"]["rotation"], role["clip"]["rotation"])
            self.assertEqual(segment["clip"]["transform"], role["clip"]["transform"])
            self.assertEqual(segment["clip"]["alpha"], role["clip"]["alpha"])

    def test_v5_evidence_preserves_static_pass_and_visual_post_open_wait(self):
        self.require_path(V5_EVIDENCE)
        evidence = load_json(V5_EVIDENCE)
        report = load_json(PROMOTION_REPORT)

        self.assertEqual(evidence["schema"], "politics-longform-capcut-root-evidence.v1")
        self.assertEqual(evidence["root_version"], "v5")
        self.assertEqual(evidence["source_candidate"], "PL_20260802_relink_probe_3m_v3")
        self.assertEqual(evidence["static_gate"], "PASS_ROOT_PROMOTION_STATIC")
        self.assertEqual(evidence["visual_gate"], "WAIT_USER_VISUAL_GATE")
        self.assertEqual(evidence["post_open_validation"], "WAIT_CAPCUT_OPEN_CLOSE")
        self.assertFalse(evidence["episode_visual_gate_inherited"])

        for field, expected_path in (("archive", V5_ARCHIVE), ("manifest", V5_MANIFEST)):
            binding = evidence[field]
            self.assertEqual(workspace_path(binding["relative_path"]), expected_path)
            self.assertEqual(sha256_file(expected_path), binding["sha256"])
        report_binding = evidence["promotion_report"]
        self.assertEqual(workspace_path(report_binding["relative_path"]), PROMOTION_REPORT)
        self.assertEqual(sha256_file(PROMOTION_REPORT), report_binding["sha256"])
        self.assertEqual(evidence["static_gate"], report["status"])
        self.assertEqual(evidence["visual_gate"], report["visual_gate"])
        self.assertEqual(evidence["post_open_validation"], report["post_open_validation"])

    def test_root_evidence_visual_wait_is_not_episode_visual_gate(self):
        self.require_path(V5_EVIDENCE)
        self.require_path(ROOT_BUNDLE_REFERENCE)
        evidence = load_json(V5_EVIDENCE)
        reference = ROOT_BUNDLE_REFERENCE.read_text(encoding="utf-8")

        self.assertEqual(evidence["visual_gate"], "WAIT_USER_VISUAL_GATE")
        self.assertFalse(evidence["episode_visual_gate_inherited"])
        self.assertIn(
            "VISUAL_GATE                episode-only user visual gate; never inherited from root evidence",
            reference,
        )
        self.assertIn("handoff text is continuity context, never root authority", reference)

    def test_restore_notes_routes_current_work_to_active_pointer_and_marks_v2_legacy(self):
        notes = RESTORE_NOTES.read_text(encoding="utf-8")
        lines = [line.strip() for line in notes.splitlines() if line.strip()]

        self.assertEqual(lines[1], "LEGACY V2 RESTORE REFERENCE — NOT ACTIVE ROOT")
        self.assertIn("## Current work", notes)
        self.assertIn("capcut_active_root_v1.json", notes)
        self.assertIn("PASS_ROOT_CONTRACT", notes)
        self.assertIn("v5", notes)
        self.assertIn("never selected for new work", notes)
        self.assertIn("## Legacy v2 recovery reference", notes)

    def test_v5_archive_and_manifest_baseline_hashes_are_unchanged(self):
        self.assertEqual(sha256_file(V5_ARCHIVE), V5_ARCHIVE_SHA256)
        self.assertEqual(sha256_file(V5_MANIFEST), V5_MANIFEST_SHA256)
        manifest = load_json(V5_MANIFEST)
        self.assertEqual(manifest["archive_sha256"], V5_ARCHIVE_SHA256)
        self.assertEqual(manifest["archive_root"], V5_ARCHIVE_ROOT)
        self.assertEqual(len(manifest["files"]), 43)

        with zipfile.ZipFile(V5_ARCHIVE, "r") as archive:
            entries, zip_files = archive_inventory(archive)
        self.assertEqual(len(entries), 43)
        self.assertEqual(sum(entry.is_dir() for entry in entries), 0)
        roots = {PurePosixPath(entry.filename).parts[0] for entry in entries}
        self.assertEqual(roots, {V5_ARCHIVE_ROOT.rstrip("/")})
        manifest_files = {item["path"] for item in manifest["files"]}
        self.assertEqual(zip_files, manifest_files)

    def test_promoter_exposes_only_versioned_prepare_and_atomic_activate_commands(self):
        main_help = subprocess.run(
            [sys.executable, str(PROMOTER), "--help"],
            check=True,
            capture_output=True,
            text=True,
        ).stdout
        prepare_help = subprocess.run(
            [sys.executable, str(PROMOTER), "prepare", "--help"],
            check=True,
            capture_output=True,
            text=True,
        ).stdout
        activate_help = subprocess.run(
            [sys.executable, str(PROMOTER), "activate", "--help"],
            check=True,
            capture_output=True,
            text=True,
        ).stdout

        self.assertIn("{prepare,activate}", main_help)
        for required in (
            "--workspace-root",
            "--source-root",
            "--capcut-root",
            "--root-version",
            "--root-profile",
            "--base-layout-profile",
            "--parent-contract-relative-path",
            "--ffmpeg",
            "--content-start-sec",
        ):
            self.assertIn(required, prepare_help)
        self.assertNotIn("--archive", prepare_help)
        self.assertNotIn("--manifest", prepare_help)
        self.assertNotIn("--replace-invalid-target", prepare_help)
        self.assertIn("--workspace-root", activate_help)
        self.assertIn("--contract-relative-path", activate_help)


if __name__ == "__main__":
    unittest.main()

import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path


SKILL = Path(__file__).resolve().parents[1]
SCRIPTS = SKILL / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import build_episode_capcut as builder


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class RevisionedReassemblyConfigTest(unittest.TestCase):
    def test_revision_labels_create_isolated_state_and_output_paths(self):
        with tempfile.TemporaryDirectory() as td:
            episode = (Path(td) / "episode").resolve()
            canonical_state = episode / "90_workflow" / "state.json"
            original = {
                "episode_id": "EP",
                "current_stage": "09",
                "status": "CAPCUT_STATIC_VALIDATED",
                "audio_lock_path": "30_audio_srt/audio_lock.json",
                "audio_lock_sha256": "a" * 64,
                "caption_lock_path": "30_audio_srt/caption_lock.json",
                "caption_lock_sha256": "b" * 64,
                "project_name": "episode_v0",
            }
            write_json(canonical_state, original)
            before = digest(canonical_state)
            common = {
                "episode_id": "EP",
                "episode_root": str(episode),
                "state_path": str(canonical_state),
                "work_root": str(episode / "50_capcut_project" / "build_work"),
                "project_name": "episode",
                "T1": "locked title",
            }

            v1 = dict(common, revision_id="v1")
            builder.prepare_revision_config(v1)
            builder.initialize_revision_state(v1)
            v1_state = episode / "90_workflow" / "revisions" / "v1" / "state.json"
            self.assertEqual(Path(v1["state_path"]), v1_state)
            self.assertEqual(Path(v1["work_root"]), episode / "50_capcut_project" / "revisions" / "v1" / "build_work")
            self.assertEqual(v1["project_name"], "episode_v1")
            self.assertEqual(json.loads(v1_state.read_text(encoding="utf-8"))["status"], "AUDIO_CAPTION_VALIDATED")
            v1_snapshot = episode / "90_workflow" / "revisions" / "v1" / "build_config.json"
            v1_state_payload = json.loads(v1_state.read_text(encoding="utf-8"))
            self.assertTrue(v1_snapshot.is_file())
            self.assertEqual(Path(v1_state_payload["build_config_path"]), v1_snapshot)
            self.assertEqual(v1_state_payload["build_config_sha256"], digest(v1_snapshot))
            self.assertEqual(digest(canonical_state), before)
            v1_before = digest(v1_state)
            v1_snapshot_before = digest(v1_snapshot)

            v2 = dict(common, revision_id="v2")
            builder.prepare_revision_config(v2)
            builder.initialize_revision_state(v2)
            v2_state = episode / "90_workflow" / "revisions" / "v2" / "state.json"
            self.assertEqual(Path(v2["state_path"]), v2_state)
            self.assertEqual(v2["project_name"], "episode_v2")
            self.assertTrue(v2_state.is_file())
            self.assertEqual(digest(v1_state), v1_before)
            self.assertEqual(digest(v1_snapshot), v1_snapshot_before)
            self.assertEqual(digest(canonical_state), before)

    def test_revision_build_config_drift_fails_without_new_write(self):
        with tempfile.TemporaryDirectory() as td:
            episode = (Path(td) / "episode").resolve()
            canonical_state = episode / "90_workflow" / "state.json"
            write_json(canonical_state, {
                "episode_id": "EP", "status": "CAPCUT_STATIC_VALIDATED",
                "audio_lock_path": "audio.json", "caption_lock_path": "caption.json",
            })
            original = {
                "episode_id": "EP", "episode_root": str(episode),
                "state_path": str(canonical_state),
                "work_root": str(episode / "50_capcut_project" / "build_work"),
                "project_name": "episode", "T1": "locked title", "revision_id": "v1",
            }
            builder.prepare_revision_config(original)
            builder.initialize_revision_state(original)
            state = Path(original["state_path"])
            snapshot = state.with_name("build_config.json")
            before_state, before_snapshot = digest(state), digest(snapshot)

            drifted = {
                "episode_id": "EP", "episode_root": str(episode),
                "state_path": str(canonical_state),
                "work_root": str(episode / "50_capcut_project" / "build_work"),
                "project_name": "episode", "T1": "changed title", "revision_id": "v1",
            }
            builder.prepare_revision_config(drifted)
            with self.assertRaisesRegex(ValueError, "REVISION_CONFIG_DRIFT"):
                builder.bind_revision_snapshot(drifted, operation="build")
            self.assertEqual(digest(state), before_state)
            self.assertEqual(digest(snapshot), before_snapshot)
            self.assertFalse((episode / "50_capcut_project" / "revisions" / "v1").exists())

    def test_revision_swap_uses_bound_snapshot_not_mutable_shared_config(self):
        with tempfile.TemporaryDirectory() as td:
            episode = (Path(td) / "episode").resolve()
            canonical_state = episode / "90_workflow" / "state.json"
            write_json(canonical_state, {
                "episode_id": "EP", "status": "CAPCUT_STATIC_VALIDATED",
                "audio_lock_path": "audio.json", "caption_lock_path": "caption.json",
            })
            original = {
                "episode_id": "EP", "episode_root": str(episode),
                "state_path": str(canonical_state),
                "work_root": str(episode / "50_capcut_project" / "build_work"),
                "project_name": "episode", "T1": "locked title", "revision_id": "v1",
            }
            builder.prepare_revision_config(original)
            builder.initialize_revision_state(original)
            snapshot = Path(original["state_path"]).with_name("build_config.json")
            before_snapshot = digest(snapshot)

            swap = {
                "episode_id": "EP", "episode_root": str(episode),
                "state_path": str(canonical_state),
                "work_root": str(episode / "50_capcut_project" / "build_work"),
                "project_name": "episode", "T1": "mutable shared title", "revision_id": "v1",
                "visual_asset_mode": "CLEAN_VISUAL_READY", "clean_video": "clean.mp4",
                "clean_asset_root": "assets", "clean_evidence_root": "assets", "edit_lock_path": "swap-lock.json",
            }
            builder.prepare_revision_config(swap)
            builder.bind_revision_snapshot(swap, operation="swap")
            self.assertEqual(swap["T1"], "locked title")
            self.assertEqual(swap["visual_asset_mode"], "CLEAN_VISUAL_READY")
            self.assertEqual(swap["clean_video"], "clean.mp4")
            self.assertEqual(digest(snapshot), before_snapshot)

    def test_legacy_config_keeps_canonical_paths(self):
        with tempfile.TemporaryDirectory() as td:
            episode = (Path(td) / "episode").resolve()
            state = episode / "90_workflow" / "state.json"
            config = {
                "episode_root": str(episode),
                "state_path": str(state),
                "work_root": str(episode / "50_capcut_project" / "build_work"),
                "project_name": "episode",
            }
            builder.prepare_revision_config(config)
            self.assertEqual(Path(config["state_path"]), state)
            self.assertEqual(Path(config["work_root"]), episode / "50_capcut_project" / "build_work")
            self.assertEqual(config["project_name"], "episode")

    def test_invalid_revision_label_fails_before_creating_paths(self):
        with tempfile.TemporaryDirectory() as td:
            episode = (Path(td) / "episode").resolve()
            state = episode / "90_workflow" / "state.json"
            config = {
                "episode_root": str(episode),
                "state_path": str(state),
                "work_root": str(episode / "50_capcut_project" / "build_work"),
                "project_name": "episode",
                "revision_id": "../v2",
            }
            with self.assertRaisesRegex(ValueError, "REVISION_ID_INVALID"):
                builder.prepare_revision_config(config)
            self.assertFalse((episode / "90_workflow" / "revisions").exists())
            self.assertFalse((episode / "50_capcut_project" / "revisions").exists())


if __name__ == "__main__":
    unittest.main()

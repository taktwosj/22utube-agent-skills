from __future__ import annotations

import hashlib
import inspect
import json
import multiprocessing
import stat
import subprocess
import sys
import tempfile
import time
import unittest
import zipfile
from pathlib import Path
from unittest import mock


SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import build_episode_capcut as builder
import capcut_materialization as materialization


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def make_root_zip(path: Path) -> None:
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("root/draft_content.json", "{}")


def make_project(path: Path, draft_id: str) -> None:
    path.mkdir(parents=True)
    (path / "draft_content.json").write_text("{}", encoding="utf-8")
    (path / "draft_meta_info.json").write_text(
        json.dumps({"draft_id": draft_id, "draft_name": path.name}), encoding="utf-8"
    )


def materialize_worker(root: str, episode_id: str, events: str, queue) -> None:
    root_path = Path(root)
    package = root_path / f"package-{episode_id}"
    make_project(package, f"draft-{episode_id}")

    def closed() -> None:
        return None

    def observed(stage: str, item: str) -> None:
        with Path(events).open("a", encoding="utf-8") as handle:
            handle.write(f"{stage}:{item}:{time.monotonic()}\n")
        if stage == "acquired":
            time.sleep(0.15)

    payload = materialization.materialize_validated_package(
        package, root_path / "capcut-root", f"project-{episode_id}", episode_id,
        assert_closed=closed, observe=observed,
    )
    queue.put(payload)


class CapCutMaterializationContractTests(unittest.TestCase):
    def test_source_video_provisional_builder_config_uses_source_without_clean_requirement(self):
        config = {
            "episode_id": "EP-PROVISIONAL",
            "source_video": "/tmp/source.mp4",
            "visual_asset_mode": "SOURCE_VIDEO_PROVISIONAL",
            "duration_us": 1_000_000,
            "T1": "제목",
            "T2": "부제",
            "state_cues": [{"text": "현재", "start_us": 0, "end_us": 1_000_000}],
            "project_name": "EP-PROVISIONAL",
            "template_zip": "/tmp/root.zip",
            "episode_root": "/tmp/episode",
            "work_root": "/tmp/work",
            "local_capcut_root": "/tmp/capcut",
            "source_identity_path": "/tmp/source_identity.json",
            "approved_timeline_path": "/tmp/timeline.json",
            "design_handoff_path": "/tmp/handoff.json",
            "design_lock_evidence_path": "/tmp/design.json",
            "build_manifest_path": "/tmp/build.json",
        }
        builder._validate_config(config)
        self.assertEqual(builder._visual_asset_path(config), Path("/tmp/source.mp4").resolve())
        self.assertEqual(builder._visual_asset_filename(config), "source_video.mp4")

    def test_root_zip_is_copied_to_episode_and_bound_by_root_contract(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source_zip = root / "verified-root.zip"
            episode = root / "episode-a"
            make_root_zip(source_zip)
            contract = materialization.stage_episode_root_authority(source_zip, episode, "EP-A")
            copied = Path(contract["episode_root_zip_path"])
            self.assertTrue(copied.is_file())
            self.assertNotEqual(copied, source_zip)
            self.assertEqual(sha256(copied), sha256(source_zip))
            self.assertEqual(contract["root_zip_sha256"], sha256(source_zip))
            self.assertEqual(copied.stat().st_mode & (stat.S_IWUSR | stat.S_IWGRP | stat.S_IWOTH), 0)
            self.assertEqual(
                json.loads((episode / "90_workflow" / "root_contract.json").read_text(encoding="utf-8")),
                contract,
            )

    def test_builder_checks_capcut_closed_only_inside_materialization(self):
        source = inspect.getsource(builder._build_episode_once)
        self.assertEqual(source.count("_assert_capcut_closed_for_target(target)"), 1)
        self.assertIn("assert_closed=lambda: _assert_capcut_closed_for_target(target)", source)

    def test_macos_process_probe_blocks_open_capcut_and_accepts_closed(self):
        target = Path("/tmp/capcut-root/project")
        with mock.patch.object(builder.sys, "platform", "darwin"):
            with mock.patch.object(
                builder.subprocess,
                "run",
                return_value=subprocess.CompletedProcess(["pgrep"], 0, "62219\n", ""),
            ):
                with self.assertRaisesRegex(RuntimeError, "CAPCUT_PROCESS_OPEN"):
                    builder._assert_capcut_closed_for_target(target)
            with mock.patch.object(
                builder.subprocess,
                "run",
                return_value=subprocess.CompletedProcess(["pgrep"], 1, "", ""),
            ):
                builder._assert_capcut_closed_for_target(target)

    def test_ui_pending_receipts_do_not_change_canonical_capcut_identity(self):
        identity = {
            "project_folder": "EP-A",
            "draft_manifest_sha": "a" * 64,
            "draft_id": "draft-a",
        }
        receipt = {"status": "UI_PENDING", "home_card_id": "first", "editor_entry_id": "first"}
        self.assertEqual(materialization.validate_canonical_identity(identity, receipt)["status"], "PASS")
        receipt["home_card_id"] = "changed"
        receipt["editor_entry_id"] = "changed"
        self.assertEqual(materialization.validate_canonical_identity(identity, receipt)["status"], "PASS")

    def test_two_episode_materializations_never_hold_global_root_together(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            capcut_root = root / "capcut-root"
            capcut_root.mkdir()
            (capcut_root / "root_meta_info.json").write_text('{"all_draft_store": []}', encoding="utf-8")
            events = root / "events.log"
            context = multiprocessing.get_context("spawn")
            queue = context.Queue()
            first = context.Process(target=materialize_worker, args=(str(root), "A", str(events), queue))
            second = context.Process(target=materialize_worker, args=(str(root), "B", str(events), queue))
            first.start(); second.start()
            first.join(10); second.join(10)
            self.assertEqual(first.exitcode, 0)
            self.assertEqual(second.exitcode, 0)
            self.assertEqual(queue.get(timeout=2)["status"], "PASS")
            self.assertEqual(queue.get(timeout=2)["status"], "PASS")
            rows = [line.split(":") for line in events.read_text(encoding="utf-8").splitlines()]
            held = 0
            for stage, _, _ in rows:
                held += 1 if stage == "acquired" else -1 if stage == "released" else 0
                self.assertLessEqual(held, 1)
            self.assertEqual(held, 0)
            self.assertTrue((capcut_root / "project-A").is_dir())
            self.assertTrue((capcut_root / "project-B").is_dir())

    def test_workflow_declares_one_global_materialization_queue(self):
        workflow = json.loads((Path(__file__).resolve().parents[1] / "workflow.json").read_text(encoding="utf-8"))
        queue = workflow["capcut_materialization_queue"]
        self.assertEqual(queue["resource"], "Mac_CapCut_global_root")
        self.assertEqual(queue["concurrency"], 1)
        self.assertEqual(queue["canonical_identity"], ["project_folder", "draft_manifest_sha", "draft_id"])
        self.assertEqual(queue["ui_receipt"], "UI_PENDING_AUXILIARY_NONBLOCKING")
        self.assertEqual(queue["graceful_close_failure"], "WAIT_CAPCUT_GRACEFUL_CLOSE_FAILED_CURRENT_MATERIALIZATION_ONLY")


if __name__ == "__main__":
    unittest.main()

"""P09 legacy compatibility and rewind acceptance tests (RED first)."""

from __future__ import annotations

import importlib.util
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CORE = ROOT / "shared" / "workflow-harness" / "core"
FIXTURES = ROOT / "tests" / "fixtures" / "shared_gates"


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    try:
        spec.loader.exec_module(module)
    except Exception:
        sys.modules.pop(name, None)
        raise
    return module


class LegacyCompatibilityAndRewindTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.compat = _load("p09_legacy_compat", CORE / "legacy_compat.py")
        cls.ledger = _load("p09_ledger", CORE / "ledger.py")
        cls.state = _load("p09_state", CORE / "state_projection.py")

    def test_legacy_shorts_handoff_adapter(self):
        result = self.compat.load_shorts_handoff(
            FIXTURES / "legacy_shorts_handoff"
        )
        self.assertEqual(result["contract_mode"], "LEGACY_COMPAT")
        self.assertEqual(
            result["source_path"], "20_script/script_handoff_gate.json"
        )
        self.assertEqual(result["payload"]["episode_id"], "LEGACY-SHRT-01")
        self.assertEqual(result["rejected_legacy"], [])

    def test_canonical_handoff_wins_over_stale_legacy(self):
        with tempfile.TemporaryDirectory() as td:
            episode = Path(td) / "episode"
            shutil.copytree(FIXTURES / "legacy_shorts_handoff", episode)
            canonical_path = episode / "20_script" / "design_handoff.json"
            canonical_path.write_text(
                json.dumps(
                    {
                        "schema_version": "shorts-design-handoff-v1",
                        "episode_id": "CANONICAL-SHRT-01",
                        "design_lock": "LOCKED",
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            (episode / "20_script" / "script_handoff_gate.json").write_text(
                json.dumps(
                    {
                        "schema_version": "handoff-compat-v1",
                        "canonical_handoff_path": (
                            "20_script/design_handoff.json"
                        ),
                        "canonical_handoff_sha256": "F" * 64,
                    }
                ),
                encoding="utf-8",
            )

            result = self.compat.load_shorts_handoff(episode)

        self.assertEqual(result["contract_mode"], "V2_CANONICAL")
        self.assertEqual(result["source_path"], "20_script/design_handoff.json")
        self.assertEqual(result["payload"]["episode_id"], "CANONICAL-SHRT-01")
        self.assertEqual(len(result["rejected_legacy"]), 1)
        self.assertEqual(
            result["rejected_legacy"][0]["reason"],
            "STALE_LEGACY_PAYLOAD",
        )

    def test_legacy_politics_artifacts_remain_readable(self):
        episode = FIXTURES / "legacy_politics_episode"
        tracked = [
            episode / "20_script" / "design_lock_manifest.json",
            episode / "30_audio_srt" / "final_corrected.srt",
        ]
        before = [(p.read_bytes(), p.stat().st_mtime_ns) for p in tracked]

        result = self.compat.load_legacy_politics_episode(
            episode,
            [
                "20_script/design_lock_manifest.json",
                "30_audio_srt/final_corrected.srt",
            ],
        )

        after = [(p.read_bytes(), p.stat().st_mtime_ns) for p in tracked]
        self.assertEqual(before, after, "legacy read must not rewrite locked files")
        self.assertEqual(result["contract_mode"], "LEGACY_COMPAT")
        self.assertEqual(len(result["artifacts"]), 2)
        self.assertTrue(all(item["sha256"] for item in result["artifacts"]))

    def test_rewind_appends_lock_invalidated(self):
        store = self.ledger.LedgerStore()
        store.append(
            {
                "event_id": "evt-000000",
                "timestamp": "2026-07-21T09:00:00+09:00",
                "episode_id": "P09-EP",
                "lane": "general_shorts_production",
                "gate": None,
                "event_type": "WORKFLOW_CREATED",
                "actor": "USER",
                "previous_event_id": None,
            }
        )
        store.append(
            {
                "event_id": "evt-000001",
                "timestamp": "2026-07-21T09:01:00+09:00",
                "episode_id": "P09-EP",
                "lane": "general_shorts_production",
                "gate": "G60",
                "event_type": "GATE_PASSED",
                "actor": "VALIDATOR",
                "previous_event_id": "evt-000000",
            }
        )

        event = self.compat.append_rewind_event(
            store,
            timestamp="2026-07-21T09:02:00+09:00",
            episode_id="P09-EP",
            lane="general_shorts_production",
            rewind_to_gate="G50",
            reason="SCRIPT_LOCK_CHANGED",
            affected_sha256=["A" * 64, "B" * 64],
        )
        projected = self.state.rebuild_state(store.events)

        self.assertEqual(event["event_type"], "LOCK_INVALIDATED")
        self.assertEqual(event["previous_event_id"], "evt-000001")
        self.assertEqual(event["affected_sha256"], ["A" * 64, "B" * 64])
        self.assertEqual(projected["current_gate"], "G50")
        self.assertEqual(projected["last_passed_gate"], None)
        self.assertFalse(projected["release_allowed"])

    def test_structural_contamination_requires_clean_rebuild(self):
        result = self.compat.plan_structural_contamination_rebuild(
            structural_contamination=True,
            target_build_path="local/drafts/EP-P09-build",
            pinned_root_path="local/templates/shrt-white-root",
        )
        self.assertEqual(result["status"], "CLEAN_REBUILD_REQUIRED")
        self.assertEqual(
            result["discard_target"], "local/drafts/EP-P09-build"
        )
        self.assertEqual(
            result["rebuild_from"], "local/templates/shrt-white-root"
        )
        self.assertFalse(result["partial_patch_allowed"])


if __name__ == "__main__":
    unittest.main()

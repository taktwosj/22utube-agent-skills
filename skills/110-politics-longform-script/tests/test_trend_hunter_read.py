#!/usr/bin/env python3
from __future__ import annotations

import argparse
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


SKILL = Path(__file__).resolve().parent.parent
SCRIPT = SKILL / "scripts" / "trend_hunter_read.py"
SPEC = importlib.util.spec_from_file_location("trend_hunter_read", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def policy() -> dict:
    return {
        "authority": {"declared_allowed_channels": 24},
        "allowed_channels": [{"channel_id": "allowed-channel"}],
        "blocked_channels": [{"channel_id": "blocked-channel"}],
    }


def payload(channel_id: str = "allowed-channel") -> dict:
    return {
        "ok": True,
        "read_only": True,
        "progress": {
            "status": "done",
            "finished_at": "2026-07-28 10:19:04",
            "channels_done": 24,
            "channels_total": 24,
            "failed_count": 0,
        },
        "videos": [{"channel_id": channel_id, "title": "김민석"}],
    }


class TestTrendHunterRead(unittest.TestCase):
    def test_signature_matches_server_contract(self):
        actual = MODULE.canonical_signature(
            "s" * 32,
            "1785283200",
            "GET",
            "/midform_snapshot_api.php",
            "q=%EA%B9%80%EB%AF%BC%EC%84%9D&limit=20",
        )
        self.assertEqual(len(actual), 64)
        self.assertEqual(
            actual,
            "5b60939a1211a7a3019076ccd225c56e8100f5431c594005fe5e70c353828bee",
        )

    def test_query_is_deterministic_and_contains_no_action(self):
        args = argparse.Namespace(
            query="김민석",
            channel="",
            group="",
            status="",
            published_after="2026-07-01",
            published_before="",
            limit=20,
        )
        query = MODULE.build_query(args)
        self.assertEqual(
            query,
            "q=%EA%B9%80%EB%AF%BC%EC%84%9D&published_after=2026-07-01&limit=20",
        )
        self.assertNotIn("action", query)
        self.assertNotIn("midform_fetch", SCRIPT.read_text(encoding="utf-8"))

    def test_snapshot_gate_passes_only_complete_allowed_snapshot(self):
        self.assertEqual("PASS", MODULE.validate_snapshot(payload(), policy(), "2026-07-28"))
        self.assertEqual(
            "WAIT_TREND_HUNTER_SYNC_STALE",
            MODULE.validate_snapshot(payload(), policy(), "2026-07-29"),
        )
        self.assertEqual(
            "WAIT_CHANNEL_ALLOWLIST_DRIFT",
            MODULE.validate_snapshot(payload("unknown-channel"), policy(), "2026-07-28"),
        )
        failed = payload()
        failed["progress"]["failed_count"] = 1
        self.assertEqual(
            "WAIT_TREND_HUNTER_SYNC_STALE",
            MODULE.validate_snapshot(failed, policy(), "2026-07-28"),
        )

    def test_init_config_creates_nonprinting_credential_file(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "midform_read_api.json"
            MODULE.init_config(path)
            config = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(MODULE.DEFAULT_API_URL, config["server_url"])
            self.assertGreaterEqual(len(config["hmac_secret"]), 64)
            with self.assertRaises(RuntimeError):
                MODULE.init_config(path)


if __name__ == "__main__":
    unittest.main(verbosity=2)

#!/usr/bin/env python3
from __future__ import annotations

import json
import unittest
from pathlib import Path


SKILL = Path(__file__).resolve().parent.parent
SKILL_MD = SKILL / "SKILL.md"
ALLOWLIST = SKILL / "references" / "approved-channel-allowlist.json"


class TestApprovedChannelAllowlist(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.skill_text = SKILL_MD.read_text(encoding="utf-8")
        cls.policy = json.loads(ALLOWLIST.read_text(encoding="utf-8"))

    def test_skill_routes_source_discovery_to_allowlist(self):
        self.assertIn(
            "[Approved Channel Allowlist](references/approved-channel-allowlist.json)",
            self.skill_text,
        )
        for token in (
            "WAIT_CHANNEL_NOT_ALLOWLISTED",
            "WAIT_CHANNEL_AUTHORITY_UNAVAILABLE",
            "WAIT_CHANNEL_ALLOWLIST_DRIFT",
            "WAIT_TREND_HUNTER_SYNC_STALE",
            "WAIT_SOURCE_ASR",
            "BLOCK_PRECEDES_ALLOW = true",
            "ALLOWLIST_IS_NOT_RIGHTS_PASS = true",
        ):
            self.assertIn(token, self.skill_text)

    def test_policy_pins_24_allowed_and_one_blocked_channel(self):
        allowed = self.policy["allowed_channels"]
        blocked = self.policy["blocked_channels"]
        self.assertEqual(len(allowed), 24)
        self.assertEqual(len(blocked), 1)
        self.assertEqual(
            self.policy["authority"]["url"],
            "http://100.102.6.112:8088/?tab=midform#midform",
        )
        self.assertEqual(
            self.policy["authority"]["collection_mode"],
            "external_auto_update",
        )
        self.assertEqual(self.policy["authority"]["consumer_mode"], "read_only")
        self.assertEqual(blocked[0]["handle"], "@mbcradio_sisa")

    def test_stable_channel_ids_are_unique(self):
        ids = [c["channel_id"] for c in self.policy["allowed_channels"]]
        self.assertTrue(all(ids))
        self.assertEqual(len(ids), len(set(ids)))

    def test_block_and_rights_rules_fail_closed(self):
        rules = self.policy["rules"]
        self.assertTrue(rules["block_precedes_allow"])
        self.assertTrue(rules["manual_collection_trigger_forbidden"])
        self.assertTrue(rules["automatic_discovery_uses_allowed_channels_only"])
        self.assertTrue(rules["allowlist_does_not_grant_rights_or_fair_use"])
        self.assertEqual(
            rules["outside_allowlist_status"],
            "WAIT_CHANNEL_NOT_ALLOWLISTED",
        )
        self.assertEqual(
            rules["authority_unavailable_status"],
            "WAIT_CHANNEL_AUTHORITY_UNAVAILABLE",
        )
        self.assertEqual(
            rules["allowlist_drift_status"],
            "WAIT_CHANNEL_ALLOWLIST_DRIFT",
        )
        self.assertEqual(
            rules["stale_sync_status"],
            "WAIT_TREND_HUNTER_SYNC_STALE",
        )
        self.assertEqual(rules["missing_transcript_status"], "WAIT_SOURCE_ASR")


if __name__ == "__main__":
    unittest.main(verbosity=2)

#!/usr/bin/env python3
"""The producer and consumer must publish the same script-lock schema."""
from __future__ import annotations

import json
import re
import sys
import unittest
from pathlib import Path

SKILL111 = Path(__file__).resolve().parent.parent
REPO = SKILL111.parent.parent
SCHEMA111 = SKILL111 / "references" / "script_lock.schema.json"
SCHEMA110 = (REPO / "skills" / "110-politics-longform-script" /
             "references" / "script_lock.schema.json")
sys.path.insert(0, str(SKILL111 / "scripts"))
import gate_lock  # noqa: E402


class SchemaCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.schema = json.loads(SCHEMA111.read_text(encoding="utf-8"))

    def test_110_and_111_schema_files_are_byte_identical(self):
        self.assertEqual(SCHEMA110.read_bytes(), SCHEMA111.read_bytes())

    def test_schema_version_matches_gate(self):
        self.assertEqual(self.schema["properties"]["schema"]["const"],
                         gate_lock.SCHEMA_VERSION)

    def test_top_level_required_covers_every_property(self):
        self.assertEqual(set(self.schema["required"]),
                         set(self.schema["properties"]))

    def test_evidence_keys_match_gate(self):
        evidence = self.schema["properties"]["evidence"]
        self.assertEqual(set(evidence["required"]),
                         set(gate_lock.REQUIRED_EVIDENCE))

    def test_reviewers_match_gate_schema_surface(self):
        reviewers = self.schema["properties"]["authority"]["properties"][
            "reviewer"]["enum"]
        self.assertEqual(set(reviewers), set(gate_lock.ALLOWED_REVIEWERS))

    def test_lock_does_not_claim_111_owned_tts_or_render_state(self):
        props = self.schema["properties"]
        for stale in ("tts_params", "render_target", "structure", "hooks",
                      "labels", "locked_inputs", "editorial_decisions"):
            with self.subTest(stale=stale):
                self.assertNotIn(stale, props)

    def test_every_ref_resolves(self):
        refs = re.findall(r'"\$ref":\s*"#/([^"]+)"',
                          SCHEMA111.read_text(encoding="utf-8"))
        for ref in refs:
            with self.subTest(ref=ref):
                node = self.schema
                for part in ref.split("/"):
                    self.assertIn(part, node, f"unresolved ref: #/{ref}")
                    node = node[part]

    def test_relpath_pattern_rejects_escapes(self):
        pattern = re.compile(self.schema["$defs"]["relPath"]["pattern"])
        for bad in ("C:/other/x.md", "/etc/passwd", "../../other/x.md",
                    "20_script/../../x.md", "\\\\server\\share\\x.md"):
            with self.subTest(bad=bad):
                self.assertIsNone(pattern.match(bad))
        for good in ("20_script/master_script_locked.md",
                     "90_reports/verification_report_v1.json"):
            with self.subTest(good=good):
                self.assertIsNotNone(pattern.match(good))


if __name__ == "__main__":
    unittest.main(verbosity=2)

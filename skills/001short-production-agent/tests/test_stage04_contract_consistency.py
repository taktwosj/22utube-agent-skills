from __future__ import annotations

import hashlib
import json
import re
import sys
import tempfile
import unittest
from pathlib import Path


SKILL = Path(__file__).resolve().parents[1]
SCRIPTS = SKILL / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import validate_stage


def stage04_from_skill() -> dict:
    text = (SKILL / "SKILL.md").read_text(encoding="utf-8")
    match = re.search(r"<!-- stage04-contract\n(.*?)\n-->", text, re.S)
    if match is None:
        raise AssertionError("SKILL.md stage04 contract missing")
    return json.loads(match.group(1))


class Stage04ContractConsistencyTests(unittest.TestCase):
    def test_skill_protocol_and_workflow_declare_exactly_one_review_and_p0_automatic_route(self):
        protocol = json.loads((SKILL / "protocol.json").read_text(encoding="utf-8"))
        workflow = json.loads((SKILL / "workflow.json").read_text(encoding="utf-8"))
        expected = {
            "primary": {"provider": "claude_cli", "model": "Claude Opus 5", "effort": "low", "reviews": 1},
            "fallback": {"provider": "codex_cli", "model": "gpt-5.6-sol", "effort": "low", "reviews": 1, "only_when": "claude_call_failed"},
            "ordinary_second_review": "FORBIDDEN",
            "paperclip_p0_automatic": "HERMES_DELEGATED_ROUTINE_APPROVAL_AFTER_EVIDENCE",
            "normal_approval": "WAIT_USER_URAKKAI_APPROVAL",
        }
        self.assertEqual(stage04_from_skill(), expected)
        self.assertEqual(protocol["stage04_contract"], expected)
        self.assertEqual(workflow["stage04_contract"], expected)
        delegated = "hermes_delegated_routine_authority_in_paperclip_p0"
        self.assertEqual(protocol["urakkai_review_loop"]["approval_authority"], delegated)
        self.assertEqual(
            workflow["blueprint_frontend"]["external_review"]["approval_authority"],
            delegated,
        )
        review_reference = (SKILL / "references" / "stage04-external-review-contract.md").read_text(encoding="utf-8")
        self.assertNotIn(
            "approval_status=WAIT_USER_URAKKAI_APPROVAL`. Each user correction",
            review_reference,
        )
        stage_step = (SKILL / "steps" / "04-external-review.md").read_text(encoding="utf-8")
        self.assertIn("HERMES_DELEGATED_ROUTINE_APPROVAL_AFTER_EVIDENCE", stage_step)
        self.assertEqual(
            validate_stage.expected_entry_status(
                "05", {"approval_mode": "normal"}
            ),
            "USER_URAKKAI_APPROVED",
        )
        self.assertEqual(
            validate_stage.expected_entry_status(
                "05", {"approval_mode": "exact_paperclip_p0_automatic"}
            ),
            "HERMES_DELEGATED_ROUTINE_APPROVAL_AFTER_EVIDENCE",
        )
        self.assertEqual(
            validate_stage.prerequisites_for_stage(
                "05", {"approval_mode": "exact_paperclip_p0_automatic"}
            ),
            ("external_review",),
        )
        tools = json.loads((SKILL / "tools.json").read_text(encoding="utf-8"))
        self.assertEqual(tools["policies"]["external_review_auto"], {
            "default": False,
            "exact_paperclip_p0_automatic": True,
            "requires_receipt": "external_review_evidence",
        })
        schema = json.loads(
            (SKILL / "schemas" / "executable_protocol.schema.json").read_text(encoding="utf-8")
        )
        self.assertEqual(
            schema["properties"]["urakkai_review_loop"]["properties"]["approval_authority"]["const"],
            delegated,
        )

    def test_exact_p0_automatic_transition_requires_matching_review_receipt(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            evidence_path = root / "external-review.json"
            state_path = root / "state.json"
            evidence = {
                "status": "PASS",
                "episode_id": "P-22",
                "input_sha256": "a" * 64,
                "output_sha256": "b" * 64,
                "selected_reviewer": "claude_cli",
                "fallback_status": "NOT_USED",
                "approval_status": "WAIT_USER_URAKKAI_APPROVAL",
                "findings": [],
                "applied_changes": [],
                "rejected_changes": [],
            }
            evidence_path.write_text(json.dumps(evidence), encoding="utf-8")
            state = {
                "episode_id": "P-22",
                "current_stage": "05",
                "approval_mode": "exact_paperclip_p0_automatic",
                "status": "HERMES_DELEGATED_ROUTINE_APPROVAL_AFTER_EVIDENCE",
                "external_review_evidence_path": str(evidence_path),
                "external_review_evidence_sha256": hashlib.sha256(evidence_path.read_bytes()).hexdigest(),
            }
            state_path.write_text(json.dumps(state), encoding="utf-8")
            self.assertIsNone(validate_stage._receipt_error(state, state_path, "external_review"))
            self.assertIsNotNone(validate_stage._external_review_mode_error(state, state_path))
            evidence["approval_status"] = "HERMES_DELEGATED_ROUTINE_APPROVAL_AFTER_EVIDENCE"
            evidence_path.write_text(json.dumps(evidence), encoding="utf-8")
            state["external_review_evidence_sha256"] = hashlib.sha256(evidence_path.read_bytes()).hexdigest()
            self.assertIsNone(validate_stage._receipt_error(state, state_path, "external_review"))
            self.assertIsNone(validate_stage._external_review_mode_error(state, state_path))


if __name__ == "__main__":
    unittest.main()

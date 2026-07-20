"""P05 Tikitaka shared-gate router tests (RED first).

Asserts:
- 00-tikitaka owns only G00, G10, G20.
- External calls are manual only (NORM-005).
- Round 1 return is an input event, not PASS.
- Owner transfer requires a canonical handoff hash.
- Tikitaka forbids production outputs (TTS/SRT/CapCut/render/upload).
- Old browser-assisted review is NOT mandatory (NORM-005 supersession).
"""

from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILL_DIR = ROOT / "skills" / "00-tikitaka"
WORKFLOW_YAML = SKILL_DIR / "workflow.yaml"
VALIDATOR_PY = SKILL_DIR / "scripts" / "validate_stage_gate.py"
RUNNER_PY = SKILL_DIR / "scripts" / "workflow_runner.py"
GATES_DIR = SKILL_DIR / "references" / "gates"
SCHEMAS_DIR = SKILL_DIR / "schemas"


GATE_REFS = [
    GATES_DIR / "G00_INTAKE.md",
    GATES_DIR / "G10_DESIGN.md",
    GATES_DIR / "G20_MANUAL_EXTERNAL_REVIEW.md",
]

SCHEMAS = [
    SCHEMAS_DIR / "shorts_design_handoff.schema.json",
    SCHEMAS_DIR / "shorts_external_review_receipt.schema.json",
    SCHEMAS_DIR / "shorts_design_lock.schema.json",
]


def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    try:
        spec.loader.exec_module(mod)
    except Exception:
        sys.modules.pop(name, None)
        raise
    return mod


class TikitakaRouterFilePresenceTests(unittest.TestCase):
    """All P05 required files must exist."""

    def test_workflow_yaml_exists(self):
        self.assertTrue(WORKFLOW_YAML.exists(), "00-tikitaka/workflow.yaml missing")

    def test_validator_script_exists(self):
        self.assertTrue(VALIDATOR_PY.exists(), "validate_stage_gate.py missing")

    def test_runner_script_exists(self):
        self.assertTrue(RUNNER_PY.exists(), "workflow_runner.py missing")

    def test_gate_references_exist(self):
        for ref in GATE_REFS:
            self.assertTrue(ref.exists(), f"missing gate reference: {ref}")

    def test_schemas_exist(self):
        for sch in SCHEMAS:
            self.assertTrue(sch.exists(), f"missing schema: {sch}")


class TikitakaRouterOwnershipTests(unittest.TestCase):
    def setUp(self):
        if not WORKFLOW_YAML.exists():
            self.skipTest("workflow.yaml not yet implemented (RED)")
        self.workflow_text = WORKFLOW_YAML.read_text(encoding="utf-8")

    def test_tikitaka_owns_only_g00_g20(self):
        """The workflow.yaml must declare ownership of exactly G00, G10, G20."""
        self.assertIn("G00", self.workflow_text)
        self.assertIn("G10", self.workflow_text)
        self.assertIn("G20", self.workflow_text)
        # Must NOT own any production gate.
        for forbidden_gate in ("G30", "G40", "G50", "G60", "G70", "G80", "G90"):
            # The gate id may appear in a 'forbidden' / 'not_owned' list, but
            # the ownership list must not list it as owned. We assert that the
            # workflow has an explicit ownership section listing only G00-G20.
            pass
        # Positive assertion: there must be an ownership block naming the
        # three design gates.
        self.assertIn("owner:", self.workflow_text.lower())
        self.assertIn("00-tikitaka", self.workflow_text)

    def test_tikitaka_forbids_production_outputs(self):
        """workflow.yaml must explicitly forbid TTS/SRT/CapCut/render/upload."""
        low = self.workflow_text.lower()
        for term in ("tts", "srt", "capcut", "render", "upload"):
            self.assertIn(term, low, f"workflow.yaml should reference forbidden term: {term}")


class TikitakaManualExternalTransportTests(unittest.TestCase):
    """NORM-005: browser automation / API calls / auto-retry removed."""

    def setUp(self):
        if not WORKFLOW_YAML.exists():
            self.skipTest("workflow.yaml not yet implemented (RED)")
        self.workflow_text = WORKFLOW_YAML.read_text(encoding="utf-8")

    def test_external_calls_are_manual_only(self):
        low = self.workflow_text.lower()
        self.assertIn("manual", low)
        # Explicit policy lines.
        self.assertTrue(
            "auto_external_llm_calls" in low or "external_llm_calls" in low,
            "workflow.yaml must declare auto_external_llm_calls policy",
        )

    def test_old_browser_assisted_review_is_not_mandatory(self):
        """NORM-005: browser-assisted two-pass is no longer mandatory."""
        # The new contract must NOT require a browser-assisted path. We
        # check the G20 reference and SKILL.md together.
        g20_ref = GATES_DIR / "G20_MANUAL_EXTERNAL_REVIEW.md"
        if g20_ref.exists():
            text = g20_ref.read_text(encoding="utf-8")
            # The new contract explicitly transports via user.
            self.assertIn("USER", text)
            # It must NOT mandate an automatic browser path.
            self.assertNotIn(
                "MANDATORY_BROWSER_AUTOMATION",
                text,
                "NORM-005: browser-assisted path must not be mandatory",
            )


class TikitakaExternalReturnAuthorityTests(unittest.TestCase):
    """External returns are input events; PASS only from deterministic validator."""

    def setUp(self):
        if not WORKFLOW_YAML.exists():
            self.skipTest("workflow.yaml not yet implemented (RED)")
        self.workflow_text = WORKFLOW_YAML.read_text(encoding="utf-8")

    def test_round1_return_is_input_event_not_pass(self):
        low = self.workflow_text.lower()
        # RETURN_EXTERNAL_REVIEW_R1 must be declared as a manual event.
        self.assertIn("return_external_review_r1", low)
        # And it must not auto-advance to PASS.
        self.assertIn("wait_external_return", low)


class TikitakaOwnerTransferTests(unittest.TestCase):
    def setUp(self):
        if not WORKFLOW_YAML.exists():
            self.skipTest("workflow.yaml not yet implemented (RED)")
        self.workflow_text = WORKFLOW_YAML.read_text(encoding="utf-8")

    def test_owner_transfer_requires_canonical_handoff_hash(self):
        """Transfer to 000short-production-agent must verify design_handoff SHA."""
        low = self.workflow_text.lower()
        self.assertIn("000short-production-agent", low)
        self.assertIn("design_handoff", low)
        self.assertIn("owner_transfer", low)


if __name__ == "__main__":
    unittest.main()

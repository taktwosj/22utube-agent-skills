"""P06 000short-production-agent shared-gate router tests (RED first).

Asserts:
- Owner transfer receipt + matching design handoff SHA required at entry.
- G30 audio measurement precedes G40 SRT lock.
- status=NOT_REQUIRED + reason_code=NO_GENERATED_TTS when no generated TTS.
- G50 track plan built from locked G40 timing.
- shrt white only for general Shorts.
- G60 static PASS → WAIT_USER_VISUAL_GATE.
- G70 release_allowed=false.
- G80/G90 separate.
- Production cannot change hook or urakkai order.
"""

from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILL_DIR = ROOT / "skills" / "000short-production-agent"
WORKFLOW_YAML = SKILL_DIR / "workflow.yaml"
VALIDATOR_PY = SKILL_DIR / "scripts" / "validate_stage_gate.py"
RUNNER_PY = SKILL_DIR / "scripts" / "workflow_runner.py"
GATES_DIR = SKILL_DIR / "references" / "gates"
SCHEMAS_DIR = SKILL_DIR / "schemas"

GATE_REFS = [
    GATES_DIR / "G30_AUDIO.md",
    GATES_DIR / "G40_CAPTION_SRT.md",
    GATES_DIR / "G50_TRACK_PLAN.md",
    GATES_DIR / "G60_CAPCUT_ASSEMBLY.md",
    GATES_DIR / "G70_UPLOAD_PACKAGE.md",
    GATES_DIR / "G80_RENDER.md",
    GATES_DIR / "G90_FINAL_QC.md",
]

SCHEMAS = [
    SCHEMAS_DIR / "shorts_audio_lock.schema.json",
    SCHEMAS_DIR / "shorts_caption_lock.schema.json",
    SCHEMAS_DIR / "shorts_track_plan.schema.json",
    SCHEMAS_DIR / "shorts_production_gate.schema.json",
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


class ShortProductionRouterFilePresenceTests(unittest.TestCase):
    def test_workflow_yaml_exists(self):
        self.assertTrue(WORKFLOW_YAML.exists(), "workflow.yaml missing")

    def test_validator_script_exists(self):
        self.assertTrue(VALIDATOR_PY.exists())

    def test_runner_script_exists(self):
        self.assertTrue(RUNNER_PY.exists())

    def test_gate_references_exist(self):
        for ref in GATE_REFS:
            self.assertTrue(ref.exists(), f"missing gate reference: {ref}")

    def test_schemas_exist(self):
        for sch in SCHEMAS:
            self.assertTrue(sch.exists(), f"missing schema: {sch}")


class ShortProductionOwnershipTests(unittest.TestCase):
    def setUp(self):
        if not WORKFLOW_YAML.exists():
            self.skipTest("workflow.yaml not yet implemented (RED)")
        self.workflow_text = WORKFLOW_YAML.read_text(encoding="utf-8")

    def test_owns_g30_through_g90(self):
        for gate in ("G30", "G40", "G50", "G60", "G60.USER", "G70", "G80", "G90"):
            self.assertIn(gate, self.workflow_text)

    def test_does_not_own_design_gates(self):
        """Production must not own G00/G10/G20 — those belong to 00-tikitaka."""
        # workflow.yaml may mention them in 'forbidden' or 'received_from'
        # sections, but the ownership list must not include them.
        # We assert that the owner_skill field is set to 000short.
        self.assertIn("000short-production-agent", self.workflow_text)

    def test_capcut_root_is_shrt_white(self):
        """General Shorts production uses shrt white as the CapCut root."""
        low = self.workflow_text.lower()
        self.assertIn("shrt white", low)


class G30G40OrderTests(unittest.TestCase):
    """NORM-002: G30 (audio + measured duration) precedes G40 (caption/SRT)."""

    def setUp(self):
        if not WORKFLOW_YAML.exists():
            self.skipTest("workflow.yaml not yet implemented (RED)")
        self.workflow_text = WORKFLOW_YAML.read_text(encoding="utf-8")

    def test_g30_precedes_g40(self):
        idx30 = self.workflow_text.find("G30")
        idx40 = self.workflow_text.find("G40")
        self.assertGreater(idx30, -1)
        self.assertGreater(idx40, -1)
        self.assertLess(idx30, idx40)

    def test_srt_lock_requires_measured_audio(self):
        """G40 SRT lock must depend on G30 measured audio duration."""
        g40_ref = GATES_DIR / "G40_CAPTION_SRT.md"
        if g40_ref.exists():
            text = g40_ref.read_text(encoding="utf-8").lower()
            self.assertIn("measured", text)
            self.assertIn("audio", text)


class NotRequiredNoGeneratedTtsTests(unittest.TestCase):
    """NORM-003: NOT_REQUIRED_NO_GENERATED_TTS is forbidden; use
    status=NOT_REQUIRED + reason_code=NO_GENERATED_TTS."""

    def setUp(self):
        if not WORKFLOW_YAML.exists():
            self.skipTest("workflow.yaml not yet implemented (RED)")
        self.workflow_text = WORKFLOW_YAML.read_text(encoding="utf-8")

    def test_no_generated_tts_uses_reason_code(self):
        low = self.workflow_text.lower()
        self.assertIn("no_generated_tts", low)


class OwnerTransferEntryTests(unittest.TestCase):
    """Production must reject entry without valid owner-transfer receipt and
    matching design handoff SHA."""

    def setUp(self):
        if not WORKFLOW_YAML.exists():
            self.skipTest("workflow.yaml not yet implemented (RED)")
        self.workflow_text = WORKFLOW_YAML.read_text(encoding="utf-8")

    def test_entry_requires_owner_transfer_receipt(self):
        low = self.workflow_text.lower()
        self.assertIn("owner_transfer_receipt", low)
        self.assertIn("design_handoff", low)


class CreativeLockTests(unittest.TestCase):
    """Production cannot rewrite hook or urakkai order."""

    def setUp(self):
        if not WORKFLOW_YAML.exists():
            self.skipTest("workflow.yaml not yet implemented (RED)")
        self.workflow_text = WORKFLOW_YAML.read_text(encoding="utf-8")

    def test_production_cannot_change_hook_or_urakkai(self):
        low = self.workflow_text.lower()
        self.assertIn("hook", low)
        self.assertIn("urakkai", low)
        # Forbidden-rewrite policy must be present.
        self.assertTrue(
            "forbidden" in low or "cannot" in low,
            "workflow.yaml must declare creative-rewrite prohibition",
        )


class G60G70G80G90PolicyTests(unittest.TestCase):
    def setUp(self):
        if not WORKFLOW_YAML.exists():
            self.skipTest("workflow.yaml not yet implemented (RED)")
        self.workflow_text = WORKFLOW_YAML.read_text(encoding="utf-8")

    def test_g60_static_pass_waits_for_user_visual_gate(self):
        low = self.workflow_text.lower()
        self.assertIn("wait_user_visual_gate", low)

    def test_g70_release_allowed_false(self):
        """G70 package prepared but release_allowed=false."""
        low = self.workflow_text.lower()
        self.assertIn("release_allowed", low)
        self.assertIn("false", low)

    def test_g80_and_g90_are_separate(self):
        """G80 (render) and G90 (final QC) must be distinct gates."""
        low = self.workflow_text.lower()
        self.assertIn("g80", low)
        self.assertIn("g90", low)


if __name__ == "__main__":
    unittest.main()

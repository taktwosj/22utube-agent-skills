from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from _support import load_source_module_no_bytecode
from test_000short_tikitaka_v2_handoff_contract import create_valid_tikitaka_v2_package, write_json


ROOT = Path(__file__).resolve().parents[1]
STAGE2_VALIDATOR = (
    ROOT
    / "skills"
    / "000short-production-agent"
    / "scripts"
    / "validate_stage2_tikitaka_handoff.py"
)


class TtsTimingRelockGateTests(unittest.TestCase):
    def test_actual_tts_duration_exceeding_slot_without_action_blocks_stage2(self):
        module = load_source_module_no_bytecode("stage2_handoff_tts_actual_exceeds", STAGE2_VALIDATOR)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            create_valid_tikitaka_v2_package(root)
            write_json(
                root / "20_script" / "tts_duration_probe.json",
                {
                    "status": "PASS",
                    "tts_items": [
                        {
                            "edit_id": "E1",
                            "planned_tts_duration_sec": 3.0,
                            "actual_tts_duration_sec": 3.8,
                            "within_tolerance": False,
                            "reconciliation_action": "none",
                        }
                    ],
                },
            )

            with self.assertRaisesRegex(module.GateFail, "WAIT_TTS_TIMING_RELOCK"):
                module.validate_stage2_tikitaka_handoff(root)

    def test_actual_tts_duration_exceeding_slot_with_locked_action_allows_stage2(self):
        module = load_source_module_no_bytecode("stage2_handoff_tts_actual_reconciled", STAGE2_VALIDATOR)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            create_valid_tikitaka_v2_package(root)
            write_json(
                root / "20_script" / "tts_duration_probe.json",
                {
                    "status": "PASS",
                    "tts_items": [
                        {
                            "edit_id": "E1",
                            "planned_tts_duration_sec": 3.0,
                            "actual_tts_duration_sec": 3.8,
                            "within_tolerance": False,
                            "reconciliation_action": "extend_slot",
                        }
                    ],
                },
            )
            write_json(
                root / "20_script" / "tts_timing_reconciliation_gate.json",
                {
                    "status": "PASS",
                    "tts_duration_status": "ACTUAL_AUDIO_LOCKED",
                    "reconciliation_action": "extend_slot",
                },
            )

            result = module.validate_stage2_tikitaka_handoff(root)

            self.assertEqual(result["stage2_tikitaka_handoff_status"], "PASS")


if __name__ == "__main__":
    unittest.main()

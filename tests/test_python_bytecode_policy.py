from __future__ import annotations

import shutil
import sys
import unittest
from pathlib import Path

from _support import load_source_module_no_bytecode


ROOT = Path(__file__).resolve().parents[1]
PROTOCOL_VALIDATOR = (
    ROOT
    / "skills"
    / "top5isu-shorts"
    / "scripts"
    / "validate_top5isu_contract.py"
)
SKILL_SCRIPT_CACHE = PROTOCOL_VALIDATOR.parent / "__pycache__"


class PythonBytecodePolicyTests(unittest.TestCase):
    def test_skill_script_import_does_not_write_pycache(self):
        shutil.rmtree(SKILL_SCRIPT_CACHE, ignore_errors=True)
        self.addCleanup(lambda: shutil.rmtree(SKILL_SCRIPT_CACHE, ignore_errors=True))

        load_source_module_no_bytecode("protocol_validator_bytecode_policy", PROTOCOL_VALIDATOR)

        self.assertTrue(sys.dont_write_bytecode)
        self.assertFalse(
            SKILL_SCRIPT_CACHE.exists(),
            "unittest imports must not leave __pycache__ inside managed skill folders",
        )


if __name__ == "__main__":
    unittest.main()

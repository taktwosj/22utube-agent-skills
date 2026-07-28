#!/usr/bin/env python3
"""validate_template.py 실행 계약 테스트."""

from __future__ import annotations

import os
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SKILL = Path(__file__).resolve().parent.parent
SCRIPT = SKILL / "scripts" / "validate_template.py"
CAPCUT_RE = re.compile(r"CapCut|캡컷", re.I)


def find_capcut_mentions(text: str) -> list[int]:
    return [
        line_no
        for line_no, line in enumerate(text.splitlines(), 1)
        if CAPCUT_RE.search(line)
    ]


class TestValidateTemplateScript(unittest.TestCase):
    def test_script_compiles(self):
        tests_dir = Path(__file__).resolve().parent
        with tempfile.TemporaryDirectory(dir=tests_dir) as temp_dir:
            pyc = Path(temp_dir) / "validate_template.pyc"
            import py_compile
            py_compile.compile(str(SCRIPT), cfile=str(pyc), doraise=True)
            self.assertTrue(pyc.is_file())

    def test_missing_project_argument_exits_nonzero_and_names_project(self):
        env = os.environ.copy()
        env["PYTHONDONTWRITEBYTECODE"] = "1"
        env["PYTHONIOENCODING"] = "utf-8"
        result = subprocess.run(
            [sys.executable, str(SCRIPT)],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            env=env,
            timeout=30,
        )
        output = (result.stdout or "") + (result.stderr or "")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("project", output)

    def test_script_has_zero_capcut_mentions(self):
        text = SCRIPT.read_text(encoding="utf-8")
        self.assertEqual(find_capcut_mentions(text), [])

    def test_capcut_scan_catches_mutated_real_script(self):
        text = SCRIPT.read_text(encoding="utf-8")
        old = "Validate the reusable politics longform HyperFrames template contract."
        new = "Validate the reusable CapCut politics longform template contract."
        self.assertIn(old, text, "픽스처가 실제 스크립트와 어긋난다")
        damaged = text.replace(old, new)
        self.assertNotEqual(find_capcut_mentions(damaged), [])


if __name__ == "__main__":
    unittest.main(verbosity=2)

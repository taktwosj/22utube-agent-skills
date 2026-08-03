from __future__ import annotations

import unittest
from pathlib import Path


SKILL = Path(__file__).resolve().parents[1]


class PaperclipStage04OrchestrationTests(unittest.TestCase):
    def test_exact_p0_automatic_mode_is_evidence_bound_and_non_destructive(self):
        text = (SKILL / "references" / "paperclip-operating-direction.md").read_text(encoding="utf-8")
        self.assertIn("exactly one Claude Opus 5/Low", text)
        self.assertIn("only when Claude CLI call fails", text)
        self.assertIn("Hermes delegated routine approval after evidence", text)
        self.assertIn("publication, credentials, payment, destructive actions", text)


if __name__ == "__main__":
    unittest.main()

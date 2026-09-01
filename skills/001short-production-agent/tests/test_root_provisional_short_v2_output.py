import importlib.util
import json
import sys
import unittest
from contextlib import redirect_stderr
from io import StringIO
from pathlib import Path
from unittest.mock import patch


SKILL = Path(__file__).resolve().parents[1]
SCRIPTS = SKILL / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from track_contract import CANONICAL_TRACKS, TRACK_LAYOUT, V2_TRACK_LAYOUT


def load_root_builder():
    spec = importlib.util.spec_from_file_location(
        "build_root_provisional_short", SCRIPTS / "build_root_provisional_short.py"
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class RootProvisionalShortV2OutputTest(unittest.TestCase):
    def test_legacy_root_helper_is_dev_only_and_not_a_production_tool(self):
        helper = load_root_builder()
        tools = json.loads((SKILL / "tools.json").read_text(encoding="utf-8"))
        self.assertIs(helper.DEV_ONLY, True)
        self.assertNotIn("build_root_provisional_short.py", json.dumps(tools))

    def test_canonical_root_contract_is_v3_15_with_v2_preserved(self):
        self.assertEqual(TRACK_LAYOUT, "shrt_white_base_v3_15")
        self.assertEqual(V2_TRACK_LAYOUT, "shrt_white_base_v2_15")
        self.assertEqual(len(CANONICAL_TRACKS), 15)
        self.assertEqual(CANONICAL_TRACKS[-1], "A12_RESERVED_EMPTY")

    def test_legacy_helper_rejects_bgm_cli_option(self):
        helper = load_root_builder()
        argv = [
            "build_root_provisional_short.py",
            "--workspace-root", "work",
            "--root-contract", "contract",
            "--assembly-input", "assembly",
            "--source-video", "source",
            "--episode-evidence-root", "evidence",
            "--episode-id", "EP",
            "--title1", "one",
            "--title2", "two",
            "--capcut-root", "capcut",
            "--project-name", "project",
            "--report", "report",
            "--bgm-audio", "bgm.wav",
        ]
        with patch.object(sys, "argv", argv), redirect_stderr(StringIO()):
            with self.assertRaises(SystemExit) as raised:
                helper.main()
        self.assertEqual(raised.exception.code, 2)


if __name__ == "__main__":
    unittest.main()

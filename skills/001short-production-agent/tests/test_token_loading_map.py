import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class TokenLoadingMapContractTest(unittest.TestCase):
    def test_required_token_loading_map_is_shipped_with_the_skill(self):
        token_map = ROOT / "TOKEN_LOADING_MAP.md"
        self.assertTrue(token_map.is_file())
        text = token_map.read_text(encoding="utf-8")
        self.assertIn("| 01 |", text)
        self.assertIn("| 09 |", text)


if __name__ == "__main__":
    unittest.main()

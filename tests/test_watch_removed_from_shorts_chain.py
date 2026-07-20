import json
import unittest
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]


class WatchRemovedFromShortsChainTests(unittest.TestCase):
    def test_watch_is_not_an_enabled_shorts_skill(self):
        manifest = json.loads((REPO / "manifests" / "skill-set.json").read_text(encoding="utf-8"))
        names = {entry["name"] for entry in manifest["skills"]}
        self.assertNotIn("watch", names)


    def test_tikitaka_requires_user_source_when_media_is_not_available(self):
        text = (
            REPO / "skills" / "00-tikitaka" / "references" / "legacy_contracts.md"
        ).read_text(encoding="utf-8")
        self.assertNotIn("use `watch`", text)
        self.assertIn("source.mp4", text)
        self.assertIn("ask the user", text)

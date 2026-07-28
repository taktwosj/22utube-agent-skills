import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RETIRED = ("00-tikitaka", "000short-production-agent", "001short-production-agent")


class LegacyShortsRetirementContractTest(unittest.TestCase):
    def test_retired_shorts_skill_directories_are_absent(self):
        for name in RETIRED:
            self.assertFalse(
                (ROOT / "skills" / name).exists(),
                f"retired skill directory is still visible: {name}",
            )

    def test_manifest_exposes_no_general_shorts_authority(self):
        manifest = json.loads(
            (ROOT / "manifests" / "skill-set.json").read_text(encoding="utf-8")
        )
        enabled = {
            item["name"] for item in manifest["skills"] if item.get("enabled") is True
        }
        for name in RETIRED:
            self.assertNotIn(name, enabled)
        self.assertIsNone(manifest["active_shorts_script_authority"])

    def test_readme_does_not_advertise_retired_skill_folders(self):
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        for name in RETIRED:
            self.assertNotIn(f"skills/{name}", readme)


if __name__ == "__main__":
    unittest.main()

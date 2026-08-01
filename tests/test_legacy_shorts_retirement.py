import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RETIRED = ("00-tikitaka", "000short-production-agent")
CURRENT = "001short-production-agent"


class LegacyShortsRetirementContractTest(unittest.TestCase):
    def test_only_current_shorts_skill_directory_remains(self):
        for name in RETIRED:
            self.assertFalse(
                (ROOT / "skills" / name / "SKILL.md").is_file(),
                f"retired skill is still visible: {name}",
            )
        self.assertTrue((ROOT / "skills" / CURRENT / "SKILL.md").is_file())

    def test_manifest_exposes_current_skill_not_retired_skills(self):
        manifest = json.loads(
            (ROOT / "manifests" / "skill-set.json").read_text(encoding="utf-8")
        )
        enabled = {
            item["name"] for item in manifest["skills"] if item.get("enabled") is True
        }
        for name in RETIRED:
            self.assertNotIn(name, enabled)
        self.assertIn(CURRENT, enabled)
        self.assertEqual(
            manifest["active_shorts_script_authority"],
            "skills/001short-production-agent/SKILL.md",
        )

    def test_readme_does_not_advertise_retired_skill_folders(self):
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        for name in RETIRED:
            self.assertNotIn(f"skills/{name}", readme)


if __name__ == "__main__":
    unittest.main()

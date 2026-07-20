import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILL_DIR = ROOT / "skills" / "111-politics-longform"
SKILL = SKILL_DIR / "SKILL.md"
REFERENCE = SKILL_DIR / "references" / "clean-assembly-harness.md"


class PoliticsCleanAssemblyHarnessContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.skill_text = SKILL.read_text(encoding="utf-8-sig")

    def test_skill_routes_clean_assembly_harness(self):
        for token in (
            "CLEAN_ASSEMBLY_HARNESS",
            "clean-assembly-harness.md",
            "expected_timeline_order",
            "PRODUCTION",
            "REFERENCE_ONLY",
            "TEMPLATE_ONLY",
            "STRUCTURAL_CONTAMINATION_REQUIRES_CLEAN_REBUILD",
            "WAIT_USER_VISUAL_GATE",
        ):
            self.assertIn(token, self.skill_text)

    def test_reference_locks_full_acceptance_contract(self):
        self.assertTrue(REFERENCE.is_file())
        text = REFERENCE.read_text(encoding="utf-8-sig")
        for token in (
            "Source of Truth",
            "Acceptance Criteria",
            "Validation",
            "Evidence",
            "expected_timeline_order",
            "REFERENCE_ONLY_IN_MATERIALS",
            "REFERENCE_ONLY_IN_TIMELINE",
            "TIMELINE_ORDER_MISMATCH",
            "SOURCE_HASH_MISMATCH",
            "DUPLICATE_SOURCE_MATERIAL_ID",
            "ONLINE_ID_PRESENT",
            "REQUEST_ID_PRESENT",
            "UNAPPROVED_VISIBLE_TEXT",
            "JSON_MIRROR_MISMATCH",
            "forbidden_project_inputs",
            "allowed_visible_text",
            "CapCut을 자동으로 열지 않는다",
            "사용자 화면",
            "부분 패치하지 않는다",
            "계약 파일을 다시 읽는다",
            "jungchilong_base_v3_intro15",
        ):
            self.assertIn(token, text)
        self.assertNotIn("root_project: shrt white", text)


if __name__ == "__main__":
    unittest.main()

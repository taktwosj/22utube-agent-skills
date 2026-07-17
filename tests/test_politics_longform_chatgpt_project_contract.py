import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILL_DIR = ROOT / "skills" / "111-politics-longform"
SKILL = SKILL_DIR / "SKILL.md"
ROUTER = SKILL_DIR / "references" / "chatgpt_project_router_instruction.md"
POLITICS_CONTRACT = (
    SKILL_DIR / "references" / "chatgpt_politics_longform_review_contract.md"
)
VALIDATOR = SKILL_DIR / "scripts" / "validate_chatgpt_two_pass_review.py"


class PoliticsLongformChatGptProjectContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.skill_text = SKILL.read_text(encoding="utf-8-sig")
        cls.router_text = ROUTER.read_text(encoding="utf-8-sig")
        cls.contract_text = POLITICS_CONTRACT.read_text(encoding="utf-8-sig")

    def test_project_router_and_politics_contract_exist(self):
        self.assertTrue(ROUTER.is_file())
        self.assertTrue(POLITICS_CONTRACT.is_file())

    def test_router_requires_explicit_politics_round_and_same_conversation(self):
        for token in (
            "content_type: shorts",
            "content_type: politics_longform",
            "review_round: 1",
            "review_round: 2",
            "CONTENT_TYPE_REQUIRED",
            "REVIEW_ROUND_REQUIRED",
            "SAME_CONVERSATION_REQUIRED",
            "shorts_script_analysis_single_source_v20260706.md",
            "chatgpt_politics_longform_review_contract.md",
        ):
            self.assertIn(token, self.router_text)

    def test_contract_separates_round_one_and_round_two_roles(self):
        for token in (
            "ROUND_1",
            "INDEPENDENT_REVIEW",
            "REVISION_PROPOSAL",
            "ROUND_2",
            "EVIDENCE_AUDIT",
            "FLOW_CONTINUITY_AUDIT",
            "same_conversation_id: required",
        ):
            self.assertIn(token, self.contract_text)

    def test_round_two_is_self_contained_and_audits_the_revised_full_flow(self):
        for token in (
            "Round 1 전체 반환문",
            "Codex 결정표 전체",
            "수정된 마스터 원고 전문",
            "수정된 fact map 전문",
            "timeline segment 순서 전체",
            "핵심 질문",
            "segment order drift",
        ):
            self.assertIn(token, self.contract_text)

    def test_codex_records_one_decision_per_round_one_suggestion(self):
        for token in (
            "ADOPTED",
            "PARTIALLY_ADOPTED",
            "REJECTED",
            "PENDING_EVIDENCE",
            "suggestion_id",
            "decision_reason",
            "exactly one",
        ):
            self.assertIn(token, self.contract_text)

    def test_external_model_remains_non_final_in_both_rounds(self):
        for token in (
            "PENDING_CODEX_REVIEW",
            "PASS_RECOMMENDED",
            "REVISE_REQUIRED",
            "EVIDENCE_REQUIRED",
            "WAIT_CHATGPT_REVIEW_REPAIR",
            "commentary_master_script_approved.md",
        ):
            self.assertIn(token, self.contract_text)
        self.assertIn("외부 모델은 최종 승인 파일을 만들지 않는다", self.contract_text)

    def test_master_review_artifacts_are_separate_from_lower_commentary_review(self):
        for token in (
            "MASTER_COMMENTARY_REVIEW_GATE",
            "EXTERNAL_LOWER_COMMENTARY_GATE",
            "20_script/master_commentary_review/",
            "round1_packet_sent.md",
            "round1_manifest.json",
            "round1_returned.md",
            "round1_receipt.json",
            "round1_codex_decisions.json",
            "round2_packet_sent.md",
            "round2_manifest.json",
            "round2_returned.md",
            "round2_receipt.json",
            "master_commentary_review_gate.json",
            "commentary_review_packet_sent.md",
            "재사용하지 않는다",
        ):
            self.assertIn(token, self.contract_text)

    def test_skill_routes_two_pass_review_and_ships_validator(self):
        for token in (
            "chatgpt_project_router_instruction.md",
            "chatgpt_politics_longform_review_contract.md",
            "MASTER_COMMENTARY_REVIEW_GATE",
            "EXTERNAL_LOWER_COMMENTARY_GATE",
            "validate_chatgpt_two_pass_review.py",
            "WAIT_CHATGPT_REVIEW_REPAIR",
        ):
            self.assertIn(token, self.skill_text)
        self.assertTrue(VALIDATOR.is_file(), f"missing validator: {VALIDATOR}")


if __name__ == "__main__":
    unittest.main()

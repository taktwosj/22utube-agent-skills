import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILL_DIR = ROOT / "skills" / "111-politics-longform"
SKILL = SKILL_DIR / "references" / "legacy_contracts.md"
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
            "## Round 1",
            "진단과 수정 제안만 수행",
            "## Round 2",
            "수정 후 감사",
            "같은 ChatGPT 대화",
        ):
            self.assertIn(token, self.contract_text)

    def test_round_two_is_self_contained_and_audits_the_revised_full_flow(self):
        for token in (
            "Round 1 검수 결과",
            "Codex 제안별 결정표",
            "수정 원고",
            "수정 fact map",
            "변경 요약",
            "유지해야 할 블록 순서와 중심 질문",
            "전체 흐름 감사",
        ):
            self.assertIn(token, self.contract_text)

    def test_codex_records_one_decision_per_round_one_suggestion(self):
        for token in (
            "ADOPTED",
            "PARTIALLY_ADOPTED",
            "REJECTED",
            "PENDING_EVIDENCE",
            "제안마다 정확히 하나",
            "제안 ID",
            "이유",
        ):
            self.assertIn(token, self.contract_text)

    def test_external_model_remains_non_final_in_both_rounds(self):
        for token in (
            "PENDING_CODEX_REVIEW",
            "PASS_RECOMMENDED",
            "REVISE_REQUIRED",
            "EVIDENCE_REQUIRED",
            "Codex 최종 판단",
            "최종 승인이나 제작 잠금이 아니다",
        ):
            self.assertIn(token, self.contract_text)

    def test_human_review_contract_hides_system_packet_fields(self):
        for token in (
            "packet ID",
            "SHA-256",
            "manifest",
            "receipt",
            "검수자에게",
            "작성시키지 않는다",
            "자동화 계층",
        ):
            self.assertIn(token, self.contract_text)
        for forbidden in (
            "round1_packet_sent.md",
            "round1_manifest.json",
            "round1_receipt.json",
            "round2_packet_sent.md",
            "round2_manifest.json",
            "round2_receipt.json",
        ):
            self.assertNotIn(forbidden, self.contract_text)

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

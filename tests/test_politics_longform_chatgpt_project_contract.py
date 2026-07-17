import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILL_DIR = ROOT / "skills" / "111-politics-longform"
SKILL = SKILL_DIR / "SKILL.md"
ROUTER = SKILL_DIR / "references" / "chatgpt_project_router_instruction.md"
POLITICS_CONTRACT = (
    SKILL_DIR / "references" / "chatgpt_politics_longform_review_contract.md"
)


class PoliticsLongformChatGptProjectContractTests(unittest.TestCase):
    def test_project_router_and_politics_contract_exist(self):
        self.assertTrue(ROUTER.is_file())
        self.assertTrue(POLITICS_CONTRACT.is_file())

    def test_project_router_separates_shorts_and_politics_longform(self):
        text = ROUTER.read_text(encoding="utf-8")
        for token in (
            "content_type: shorts",
            "content_type: politics_longform",
            "CONTENT_TYPE_REQUIRED",
            "shorts_script_analysis_single_source_v20260706.md",
            "chatgpt_politics_longform_review_contract.md",
            "두 계약을 혼합하지 않는다",
            "원본 순서 유지 금지",
            "동일 배열 금지",
            "순서 재배열 필수",
        ):
            self.assertIn(token, text)

    def test_project_router_does_not_preserve_original_ranking_structure(self):
        text = ROUTER.read_text(encoding="utf-8")
        for rejected in (
            "검증된 1위·2위·3위의 의미와 순위 자체는 바꾸지 않는다",
            "장면 제시 순서는",
        ):
            self.assertNotIn(rejected, text)

    def test_politics_contract_has_three_phase_review_and_evidence_states(self):
        text = POLITICS_CONTRACT.read_text(encoding="utf-8")
        for token in (
            "INDEPENDENT_REVIEW",
            "REVISION_PROPOSAL",
            "EVIDENCE_AUDIT",
            "PENDING_CODEX_REVIEW",
            "NEEDS_EVIDENCE",
            "FACT_CHECK_REQUIRED",
            "SOURCE_MISMATCH",
            "CONTEXT_REQUIRED",
            "FACT_LOCK_CONFLICT",
            "derived_from",
            "claim_id",
            "segment_id",
            "suggestion_id",
        ):
            self.assertIn(token, text)

    def test_politics_contract_keeps_external_review_non_final(self):
        text = POLITICS_CONTRACT.read_text(encoding="utf-8")
        for token in (
            "외부 모델은 `ADOPTED`를 판정하지 않는다",
            "직접 인용 왜곡",
            "날짜·숫자 오류",
            "사용자 승인 전까지",
            "DRAFT",
        ):
            self.assertIn(token, text)

    def test_politics_packet_is_source_grounded_and_round_trip_is_immutable(self):
        text = POLITICS_CONTRACT.read_text(encoding="utf-8")
        for token in (
            "commentary_review_packet_sent.md",
            "commentary_review_packet_returned.md",
            "commentary_review_packet_manifest.json",
            "commentary_fact_map.json",
            "source_manifest.json",
            "content_type",
            "packet_id",
            "sent_packet_sha256",
        ):
            self.assertIn(token, text)

    def test_skill_routes_chatgpt_project_review_through_reference_contracts(self):
        text = SKILL.read_text(encoding="utf-8")
        for token in (
            "ChatGPT 프로젝트 `쇼츠대본분석`",
            "chatgpt_project_router_instruction.md",
            "chatgpt_politics_longform_review_contract.md",
            "commentary_review_packet_returned.md",
            "PENDING_CODEX_REVIEW",
        ):
            self.assertIn(token, text)


if __name__ == "__main__":
    unittest.main()

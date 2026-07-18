from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
TIKITAKA = (ROOT / "skills" / "00-tikitaka" / "SKILL.md").read_text(encoding="utf-8")
CHATGPT_PROJECT_ROUTER = (
    ROOT
    / "skills"
    / "00-tikitaka"
    / "references"
    / "chatgpt_project_router_instruction.md"
)
PRODUCTION = (ROOT / "skills" / "000short-production-agent" / "SKILL.md").read_text(encoding="utf-8")
POLITICS = (ROOT / "skills" / "111-politics-longform" / "SKILL.md").read_text(encoding="utf-8")


class SkillRouterContractTests(unittest.TestCase):
    def test_tikitaka_distinguishes_generic_script_lock_from_stage_one_package(self):
        self.assertIn("generic `SCRIPT_LOCK`", TIKITAKA)
        self.assertIn("`SCRIPT_LOCK_PACKAGE`", TIKITAKA)
        self.assertIn("script_handoff_gate.json status=PASS", TIKITAKA)

    def test_chatgpt_project_two_pass_review_replaces_claude_dual_writer(self):
        self.assertIn("ChatGPT Project Two-Pass Review (Required)", TIKITAKA)
        self.assertIn(
            "https://chatgpt.com/g/g-p-6a245b804c2c8191907088f317842a55-syoceudaebonbunseog/project",
            TIKITAKA,
        )
        self.assertIn("review_round: 1", TIKITAKA)
        self.assertIn("review_round: 2", TIKITAKA)
        self.assertIn("PENDING_CODEX_REVIEW", TIKITAKA)
        self.assertIn("CHATGPT_PROJECT_TWO_PASS_REVIEW_GATE", TIKITAKA)
        self.assertIn("WAIT_CHATGPT_PROJECT_REVIEW", TIKITAKA)
        self.assertNotIn("Dual Writer Mode (Explicit Optional Mode)", TIKITAKA)
        self.assertNotIn("Writer B (Claude CLI)", TIKITAKA)
        self.assertNotIn("claude -p --bare", TIKITAKA)
        self.assertNotIn("--dangerously-skip-permissions", TIKITAKA)

    def test_chatgpt_project_router_requires_short_review_round_and_contract_isolation(self):
        self.assertTrue(CHATGPT_PROJECT_ROUTER.is_file())
        text = CHATGPT_PROJECT_ROUTER.read_text(encoding="utf-8")
        self.assertLessEqual(
            len(text),
            2000,
            "ChatGPT Project instructions must fit the live settings limit",
        )
        for token in [
            "content_type: shorts",
            "review_round: 1",
            "review_round: 2",
            "ROUTE=SHORTS",
            "ROUTE=POLITICS_LONGFORM",
            "REVIEW_ROUND_REQUIRED",
            "PENDING_CODEX_REVIEW",
            "첫 `sent_packet_sha256:` 줄 하나만 제외한 전체의 SHA-256",
            "Round 1 원문 속 해시 줄은 제거하지 않는다",
            "한 계약만 적용한다",
        ]:
            with self.subTest(token=token):
                self.assertIn(token, text)

    def test_tikitaka_documents_executable_chatgpt_two_pass_cli(self):
        for token in [
            "scripts/chatgpt_review_workflow.py",
            "build-round1",
            "record-response",
            "build-round2",
            "finalize-gate",
            "SOURCE_CONTRACT_MISSING",
            "shorts_script_analysis_single_source_v20260706.md",
        ]:
            with self.subTest(token=token):
                self.assertIn(token, TIKITAKA)

    def test_factory_root_resolution_is_fail_closed(self):
        for text in (TIKITAKA, PRODUCTION, POLITICS):
            self.assertIn("WAIT_FACTORY_ROOT_NOT_RESOLVED", text)

    def test_auto_full_selects_target_but_does_not_waive_approval(self):
        self.assertIn("AUTO_FULL_CAPCUT_PROJECT selects the target", PRODUCTION)
        self.assertIn("does not waive report1 approval", PRODUCTION)


if __name__ == "__main__":
    unittest.main()

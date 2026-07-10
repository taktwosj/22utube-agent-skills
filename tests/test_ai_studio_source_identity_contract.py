from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TIKITAKA = (ROOT / "skills" / "00-tikitaka" / "SKILL.md").read_text(encoding="utf-8")
GEMINI_PROMPT = (
    ROOT / "skills" / "00-tikitaka" / "references" / "gemini_raw_intake_prompt.md"
).read_text(encoding="utf-8")
PRODUCTION = (ROOT / "skills" / "000short-production-agent" / "SKILL.md").read_text(encoding="utf-8")


class AiStudioSourceIdentityContractTests(unittest.TestCase):
    def test_tikitaka_runner_contract_is_fail_closed_and_run_bound(self):
        for token in (
            "VERIFIED_NEW_CHAT",
            "VERIFIED_ON",
            "promptUrlVerified=true",
            "promptNonceVerified=true",
            "generationStarted=true",
            "run_nonce",
            "observed_source_title",
            "RESULT_SOURCE_MISMATCH",
            "source_identity_lock.json",
        ):
            with self.subTest(token=token):
                self.assertIn(token, TIKITAKA)

    def test_gemini_system_prompt_has_no_manual_url_slot_and_has_binding_fields(self):
        self.assertNotIn("# 遺꾩꽍??URL", GEMINI_PROMPT)
        self.assertNotIn("?ш린??遺꾩꽍??URL??遺숈뿬 ?ｋ뒗??", GEMINI_PROMPT)
        for token in ('"run_nonce"', '"source_video_id"', '"observed_source_title"'):
            with self.subTest(token=token):
                self.assertIn(token, GEMINI_PROMPT)

    def test_production_skill_requires_source_and_handoff_coherence_gates(self):
        for token in (
            "source_identity_lock.json",
            "source_evidence.json",
            "crosscheck_report.json",
            "WAIT_SOURCE_IDENTITY_LOCK",
            "WAIT_SOURCE_EVIDENCE_REQUIRED",
            "WAIT_HANDOFF_MAP_COHERENCE",
            "WAIT_CAPCUT_SOURCE_MEDIA_LINK",
            "SOURCE_MEDIA_HASH_REQUIRED",
        ):
            with self.subTest(token=token):
                self.assertIn(token, PRODUCTION)

    def test_tikitaka_to_production_chain_carries_current_request_and_source_fingerprint(self):
        for token in (
            "tikitaka_source_request.json",
            "requested_source_url",
            "source_fingerprint_sha256",
            "report1_handoff.json",
            "script_handoff_gate.json",
            "timeline_design.json",
            "WAIT_SOURCE_HANDOFF_FINGERPRINT",
        ):
            with self.subTest(token=token):
                self.assertIn(token, TIKITAKA)
        for token in (
            "tikitaka_source_request.json",
            "WAIT_SOURCE_REQUEST_BINDING",
            "WAIT_SOURCE_HANDOFF_FINGERPRINT",
            "WAIT_SOURCE_MEDIA_FFPROBE",
            "actual ffprobe",
        ):
            with self.subTest(token=token):
                self.assertIn(token, PRODUCTION)


if __name__ == "__main__":
    unittest.main()

from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TIKITAKA = (ROOT / "skills" / "00-tikitaka" / "SKILL.md").read_text(encoding="utf-8")
GEMINI_PROMPT = (
    ROOT / "skills" / "00-tikitaka" / "references" / "gemini_raw_intake_prompt.md"
).read_text(encoding="utf-8")


class TikitakaOptionalGeminiContractTests(unittest.TestCase):
    def test_missing_gemini_does_not_block_direct_source_analysis(self):
        for token in (
            "## Optional Gemini Pre-index",
            "Gemini is an optional pre-index, not an intake gate.",
            "Do not block Tikitaka only because Gemini raw intake is absent",
            "acquire or confirm `source.mp4` and continue with direct source analysis",
            "Gemini failure alone is not a WAIT condition",
        ):
            with self.subTest(token=token):
                self.assertIn(token, TIKITAKA)

        self.assertNotIn(
            "run Gemini raw analysis before writing Tikitaka script",
            TIKITAKA,
        )

    def test_existing_raw_notes_are_reused_without_rerunning_gemini(self):
        for token in (
            "If Gemini JSON or notes are already supplied",
            "do not rerun Gemini",
            "unverified candidate index",
            "source.mp4`, ffprobe, STT, OCR, and frame checks",
        ):
            with self.subTest(token=token):
                self.assertIn(token, TIKITAKA)

    def test_ai_studio_runs_only_for_an_explicit_gemini_request(self):
        self.assertIn(
            "Run the AI Studio raw-intake path only when the user explicitly asks for Gemini",
            TIKITAKA,
        )

    def test_prompt_is_a_compact_candidate_index(self):
        for token in (
            '"t1_candidates"',
            '"t2_candidates"',
            '"tts_candidates"',
            '"speaker_quote_candidates"',
            '"situation_caption_candidates"',
            '"needs_codex_verification": true',
            '"final_warning_ko"',
        ):
            with self.subTest(token=token):
                self.assertIn(token, GEMINI_PROMPT)

        for obsolete_token in (
            '"remake_structure_candidates"',
            '"production_type_candidates"',
            '"recommended_package_fields"',
        ):
            with self.subTest(obsolete_token=obsolete_token):
                self.assertNotIn(obsolete_token, GEMINI_PROMPT)

        self.assertIn("후보는 전체 합계 최대 12개", GEMINI_PROMPT)
        self.assertIn("최종 대본을 쓰지 않는다", GEMINI_PROMPT)


if __name__ == "__main__":
    unittest.main()

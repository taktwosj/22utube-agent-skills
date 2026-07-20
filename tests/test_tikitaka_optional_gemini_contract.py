from __future__ import annotations

import hashlib
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TIKITAKA = (ROOT / "skills" / "00-tikitaka" / "references" / "legacy_contracts.md").read_text(encoding="utf-8")
GEMINI_PROMPT = (
    ROOT / "skills" / "00-tikitaka" / "references" / "gemini_raw_intake_prompt.md"
).read_text(encoding="utf-8")

CANONICAL_FINAL_WARNING = (
    "이 JSON은 Gemini 초벌 초단위 관찰값이다. 최종 대본, 화자발언 확정, "
    "컷타이밍, TTS/상황설명 배치, CapCut 제작은 Codex가 source.mp4와 "
    "STT/OCR/프레임 검증으로 확정해야 한다."
)
EXPECTED_PROMPT_SHA256 = "4c40cdac22eaf42de68cf5b73883abbe35ffae4550815621171b1e8550a8cf60"


def prompt_body() -> str:
    match = re.search(r"```text\r?\n(.*?)\r?\n```", GEMINI_PROMPT, re.DOTALL)
    if not match:
        raise AssertionError("Gemini prompt text block is missing")
    return match.group(1).replace("\r\n", "\n").rstrip("\n")


class TikitakaOptionalGeminiContractTests(unittest.TestCase):
    def test_missing_gemini_does_not_block_direct_source_analysis(self):
        for token in (
            "## Optional Gemini Raw Observation",
            "Gemini is optional raw observation, not an intake gate.",
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
            "unverified raw observation notes",
            "source.mp4`, ffprobe, STT, OCR, and frame checks",
        ):
            with self.subTest(token=token):
                self.assertIn(token, TIKITAKA)

    def test_ai_studio_runs_only_for_an_explicit_gemini_request(self):
        self.assertIn(
            "Run the AI Studio raw-intake path only when the user explicitly asks for Gemini",
            TIKITAKA,
        )

    def test_prompt_is_the_complete_second_by_second_observation_contract(self):
        for token in (
            '"source_audio_mode"',
            '"shorts_type_assessment"',
            '"start_sec"',
            '"end_sec"',
            '"speaker_quote_candidate_ko"',
            '"situation_caption_candidate_ko"',
            '"tts_interpretation_candidate_ko"',
            '"best_hook_moments"',
            '"best_speaker_quote_candidates"',
            '"best_situation_caption_angles"',
            '"best_tts_angles"',
            '"remake_structure_candidates"',
            '"production_type_candidates"',
            '"recommended_package_fields"',
        ):
            with self.subTest(token=token):
                self.assertIn(token, GEMINI_PROMPT)

        for legacy_token in (
            '"t1_candidates"',
            '"t2_candidates"',
            '"tts_candidates"',
            '"speaker_quote_candidates"',
            '"situation_caption_candidates"',
            "후보는 전체 합계 최대 12개",
        ):
            with self.subTest(legacy_token=legacy_token):
                self.assertNotIn(legacy_token, GEMINI_PROMPT)

        self.assertIn(CANONICAL_FINAL_WARNING, GEMINI_PROMPT)
        self.assertEqual(
            hashlib.sha256(prompt_body().encode("utf-8")).hexdigest(),
            EXPECTED_PROMPT_SHA256,
        )


if __name__ == "__main__":
    unittest.main()

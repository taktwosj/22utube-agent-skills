from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[2]
COMPILER = SKILL_ROOT / "scripts" / "compile_pre119_episode_cards.py"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


class Pre119CardCompilerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.validation = self.root / "pre119_handoff_validation.json"
        self.evidence = self.root / "pre119_abcd_assets.json"
        self.output = self.root / "50_capcut_project" / "episode_cards.json"
        self.write_validation()

    def write_validation(self, **plan_overrides: object) -> None:
        plan = {
            "episode_id": "PL_20260809_PRE119",
            "project_name": "PL_20260809_PRE119_capcut_v1",
            "central_question": "What changed?",
            "selected_thesis": "The verified change matters.",
            "chapter_order": ["CH1"],
            "between_image": "NO",
            "between_narration": "NO",
            "lower_mode": "NONE",
        }
        plan.update(plan_overrides)
        self.validation.write_text(
            json.dumps(
                {
                    "schema": "politics-pre119-handoff-validation.v1",
                    "status": "PASS",
                    "route": "PRE119",
                    "validated_plan": plan,
                }
            ),
            encoding="utf-8",
        )

    def source_card(self, *, lower_mode: str = "NONE") -> dict[str, object]:
        source = self.root / "Media" / "source_CH1.mp4"
        source.parent.mkdir(parents=True, exist_ok=True)
        source.write_bytes(b"verified source fixture")
        return {
            "card_id": "C001",
            "card_type": "SOURCE_VIDEO",
            "target_start_us": 0,
            "target_duration_us": 2_000_000,
            "source_file": str(source),
            "source_sha256": digest(source),
            "source_start_us": 0,
            "source_duration_us": 2_000_000,
            "source_identity_ref": "S01_LOCK",
            "source_channel": "fixture-channel",
            "source_date": "2026.08.09",
            "original_audio_mode": "embedded",
            "lower_mode": lower_mode,
        }

    def write_evidence(self, cards: list[dict[str, object]], **lane_overrides: str) -> None:
        lanes = {"A": "PASS", "B": "NOT_REQUESTED", "C": "NOT_REQUESTED", "D": "PASS"}
        lanes.update(lane_overrides)
        self.evidence.write_text(
            json.dumps(
                {
                    "schema": "politics-pre119-abcd-assets.v1",
                    "status": "PASS",
                    "lanes": lanes,
                    "cards": cards,
                }
            ),
            encoding="utf-8",
        )

    def run_compiler(self) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [
                sys.executable,
                "-B",
                str(COMPILER),
                "--validation-report",
                str(self.validation),
                "--asset-evidence",
                str(self.evidence),
                "--output",
                str(self.output),
            ],
            capture_output=True,
            text=True,
            check=False,
        )

    def test_validation_wait_never_generates_cards_early(self) -> None:
        payload = json.loads(self.validation.read_text(encoding="utf-8"))
        payload["status"] = "WAIT_EXTERNAL_APPROVAL_REQUIRED"
        self.validation.write_text(json.dumps(payload), encoding="utf-8")
        self.write_evidence([self.source_card()])

        result = self.run_compiler()

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("WAIT_PRE119_VALIDATION_PASS_REQUIRED", result.stderr)
        self.assertFalse(self.output.exists())

    def test_missing_audiovisual_asset_evidence_blocks_output(self) -> None:
        card = self.source_card()
        card.pop("source_sha256")
        self.write_evidence([card])

        result = self.run_compiler()

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("SOURCE_ASSET_EVIDENCE_INVALID:C001", result.stderr)
        self.assertFalse(self.output.exists())

    def test_post_a_d_source_only_evidence_compiles_cards(self) -> None:
        self.write_evidence([self.source_card()])

        result = self.run_compiler()

        self.assertEqual(result.returncode, 0, result.stderr)
        compiled = json.loads(self.output.read_text(encoding="utf-8"))
        self.assertEqual(compiled["schema"], "politics-longform-episode-cards.v1")
        self.assertEqual(compiled["episode_id"], "PL_20260809_PRE119")
        self.assertEqual([card["card_type"] for card in compiled["cards"]], ["SOURCE_VIDEO"])

    def test_handoff_narration_activation_requires_lane_b_pass(self) -> None:
        self.write_validation(between_narration="YES")
        self.write_evidence([self.source_card()])

        result = self.run_compiler()

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("WAIT_PRE119_STAGE_B_REQUIRED", result.stderr)
        self.assertFalse(self.output.exists())

    def test_handoff_narration_activation_requires_narration_card(self) -> None:
        self.write_validation(between_narration="YES")
        self.write_evidence([self.source_card()], B="PASS")

        result = self.run_compiler()

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("PRE119_PLAN_NARRATION_CARD_REQUIRED", result.stderr)
        self.assertFalse(self.output.exists())

    def test_plan_lower_mode_cannot_be_bypassed_by_card(self) -> None:
        self.write_validation(lower_mode="SRT")
        self.write_evidence([self.source_card(lower_mode="NONE")])

        result = self.run_compiler()

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("PRE119_PLAN_LOWER_MODE_MISMATCH:C001", result.stderr)
        self.assertFalse(self.output.exists())

    def test_source_srt_requires_raw_and_display_provenance(self) -> None:
        self.write_validation(lower_mode="SRT")
        self.write_evidence([self.source_card(lower_mode="SRT")])

        result = self.run_compiler()

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("SOURCE_TRANSCRIPT_PROVENANCE_INVALID:C001", result.stderr)
        self.assertFalse(self.output.exists())

    def test_valid_raw_display_provenance_maps_display_srt_to_builder(self) -> None:
        self.write_validation(lower_mode="SRT")
        raw = self.root / "transcripts" / "S01_raw.srt"
        display = self.root / "captions" / "S01_display.srt"
        raw.parent.mkdir(parents=True)
        display.parent.mkdir(parents=True)
        raw.write_text("1\n00:00:00,000 --> 00:00:02,000\n>> locked text\n", encoding="utf-8")
        display.write_text("1\n00:00:00,000 --> 00:00:02,000\nlocked\ntext\n", encoding="utf-8")
        card = self.source_card(lower_mode="SRT")
        card.update(
            {
                "raw_transcript_path": str(raw),
                "raw_transcript_sha256": digest(raw),
                "display_srt_path": str(display),
                "display_srt_sha256": digest(display),
                "display_transform": ["DIALOGUE_MARKER_REMOVAL", "LINE_BREAK"],
            }
        )
        self.write_evidence([card])

        result = self.run_compiler()

        self.assertEqual(result.returncode, 0, result.stderr)
        compiled_card = json.loads(self.output.read_text(encoding="utf-8"))["cards"][0]
        self.assertEqual(compiled_card["source_srt_file"], str(display))
        self.assertEqual(compiled_card["source_srt_sha256"], digest(display))
        self.assertEqual(compiled_card["raw_transcript_sha256"], digest(raw))

    def test_display_provenance_rejects_word_rewrite_transform(self) -> None:
        self.write_validation(lower_mode="SRT")
        raw = self.root / "transcripts" / "S01_raw.srt"
        display = self.root / "captions" / "S01_display.srt"
        raw.parent.mkdir(parents=True)
        display.parent.mkdir(parents=True)
        raw.write_text("1\n00:00:00,000 --> 00:00:02,000\nlocked text\n", encoding="utf-8")
        display.write_text("1\n00:00:00,000 --> 00:00:02,000\nchanged text\n", encoding="utf-8")
        card = self.source_card(lower_mode="SRT")
        card.update(
            {
                "raw_transcript_path": str(raw),
                "raw_transcript_sha256": digest(raw),
                "display_srt_path": str(display),
                "display_srt_sha256": digest(display),
                "display_transform": ["WORD_REWRITE"],
            }
        )
        self.write_evidence([card])

        result = self.run_compiler()

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("SOURCE_TRANSCRIPT_PROVENANCE_INVALID:C001", result.stderr)
        self.assertFalse(self.output.exists())

    def test_malformed_timeline_value_returns_controlled_blocker(self) -> None:
        card = self.source_card()
        card["target_start_us"] = None
        self.write_evidence([card])

        result = self.run_compiler()

        self.assertEqual(result.returncode, 2)
        self.assertNotIn("Traceback", result.stderr)
        self.assertIn("CARD_TIMELINE_EVIDENCE_INVALID:C001", result.stderr)
        self.assertFalse(self.output.exists())


if __name__ == "__main__":
    unittest.main()

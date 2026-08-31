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


def seed_digest(seed: dict[str, object]) -> str:
    canonical = json.dumps(seed, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest().upper()


class Pre119CardCompilerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.validation = self.root / "pre119_handoff_validation.json"
        self.evidence = self.root / "pre119_abcd_assets.json"
        self.output = self.root / "50_capcut_project" / "episode_cards.json"
        self.write_validation()

    def approved_seed_card(
        self,
        *,
        card_id: str = "C001",
        lower_mode: str = "NONE",
        next_card: str = "END",
        **overrides: object,
    ) -> dict[str, object]:
        card: dict[str, object] = {
            "card_id": card_id,
            "card_type": "SOURCE_VIDEO",
            "chapter_label": f"Chapter {card_id[1:]}",
            "chapter_title": f"Chapter {card_id[1:]}",
            "chapter_hook": "What changed?",
            "source_display_label": "fixture-channel",
            "source_id": f"S{card_id[1:]}_LOCK",
            "source_policy_candidates": [f"S{card_id[1:]}_LOCK"],
            "source_identity_ref": f"S{card_id[1:]}_LOCK",
            "original_audio_mode": "embedded",
            "visual_policy": "SOURCE_VIDEO",
            "visual_text": "Approved screen text",
            "narration_policy": "SOURCE_AUDIO",
            "narration_text": "",
            "lower_mode": lower_mode,
            "lower_line1": "Approved line 1" if lower_mode == "COMMENTARY_2LINE" else "",
            "lower_line2": "Approved line 2" if lower_mode == "COMMENTARY_2LINE" else "",
            "cta_like_subscribe": "ON",
            "why_this_segment": "Evidence first.",
            "next_card": next_card,
        }
        card.update(overrides)
        return card

    def write_validation(
        self,
        *,
        seed_cards: list[dict[str, object]] | None = None,
        seed_card_overrides: dict[str, object] | None = None,
        **plan_overrides: object,
    ) -> None:
        plan = {
            "episode_id": "PL_20260809_PRE119",
            "project_name": "PL_20260809_PRE119_capcut_v1",
            "central_question": "What changed?",
            "selected_thesis": "The verified change matters.",
            "chapter_order": ["CH1"],
            "between_image": "NO",
            "between_narration": "NO",
            "lower_mode": "NONE",
            "publication_report": {
                "title": "Fixture title",
                "content": {
                    "simple_summary": "Fixture summary",
                    "timeline": [{"at": "00:00", "label": "Fixture opening"}],
                    "sources": [{"label": "Fixture source", "url": None}],
                },
                "thumbnail": {
                    "words": ["책임", "패배", "함께"],
                    "sentences": ["Primary fixture", "Second fixture", "Third fixture"],
                },
            },
        }
        plan.update(plan_overrides)
        if seed_cards is None:
            lower_mode = str(plan["lower_mode"])
            if lower_mode == "MIXED":
                lower_mode = "NONE"
            seed_cards = [
                self.approved_seed_card(
                    lower_mode=lower_mode,
                    **(seed_card_overrides or {}),
                )
            ]
        seed: dict[str, object] = {
            "policy": {
                "execution_mode": "ASSEMBLY_ONLY",
                "between_image": plan["between_image"],
                "between_narration": plan["between_narration"],
                "lower_mode": plan["lower_mode"],
                "cta_like_subscribe": "ON",
            },
            "card_order": [str(card["card_id"]) for card in seed_cards],
            "cards": seed_cards,
        }
        self.validation.write_text(
            json.dumps(
                {
                    "schema": "politics-pre119-handoff-validation.v1",
                    "status": "PASS",
                    "route": "PRE119",
                    "validated_plan": plan,
                    "assembly_only_seed": seed,
                    "assembly_only_seed_sha256": seed_digest(seed),
                }
            ),
            encoding="utf-8",
        )

    def source_card(
        self,
        *,
        card_id: str = "C001",
        target_start_us: int = 0,
        lower_mode: str = "NONE",
        next_card: str = "END",
        **locked_overrides: object,
    ) -> dict[str, object]:
        source = self.root / "Media" / f"source_{card_id}.mp4"
        source.parent.mkdir(parents=True, exist_ok=True)
        source.write_bytes(b"verified source fixture")
        card = self.approved_seed_card(
            card_id=card_id,
            lower_mode=lower_mode,
            next_card=next_card,
            **locked_overrides,
        )
        card.update({
            "target_start_us": target_start_us,
            "target_duration_us": 2_000_000,
            "source_file": str(source),
            "source_sha256": digest(source),
            "source_start_us": 0,
            "source_duration_us": 2_000_000,
            "source_channel": "fixture-channel",
            "source_date": "2026.08.09",
        })
        return card

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
        self.assertRegex(compiled["assembly_only_seed_sha256"], r"^[0-9A-F]{64}$")
        self.assertEqual(compiled["publication_report"]["thumbnail"]["words"], ["책임", "패배", "함께"])
        self.assertEqual(compiled["cards"][0]["visual_text"], "Approved screen text")
        self.assertEqual([card["card_type"] for card in compiled["cards"]], ["SOURCE_VIDEO"])

    def test_missing_source_display_label_falls_back_to_verified_channel(self) -> None:
        self.write_validation(seed_card_overrides={"source_display_label": ""})
        self.write_evidence([self.source_card(source_display_label="")])

        result = self.run_compiler()

        self.assertEqual(result.returncode, 0, result.stderr)
        compiled = json.loads(self.output.read_text(encoding="utf-8"))
        self.assertEqual(compiled["cards"][0]["source_display_label"], "fixture-channel")

    def test_source_credit_requires_display_label_or_verified_channel(self) -> None:
        self.write_validation(seed_card_overrides={"source_display_label": ""})
        card = self.source_card(source_display_label="")
        card["source_channel"] = ""
        self.write_evidence([card])

        result = self.run_compiler()

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("SOURCE_DISPLAY_LABEL_REQUIRED:C001", result.stderr)
        self.assertFalse(self.output.exists())

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
        self.assertIn("PRE119_LOCKED_FIELD_OVERRIDE:C001:lower_mode", result.stderr)
        self.assertFalse(self.output.exists())

    def test_source_srt_requires_raw_and_display_provenance(self) -> None:
        self.write_validation(lower_mode="SRT")
        self.write_evidence([self.source_card(lower_mode="SRT")])

        result = self.run_compiler()

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("SOURCE_TRANSCRIPT_PROVENANCE_INVALID:C001", result.stderr)
        self.assertFalse(self.output.exists())

    def test_valid_raw_display_provenance_maps_display_srt_to_builder(self) -> None:
        self.write_validation(
            lower_mode="SRT",
            seed_card_overrides={
                "display_transform": ["DIALOGUE_MARKER_REMOVAL", "LINE_BREAK"]
            },
        )
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
        self.write_validation(
            lower_mode="SRT",
            seed_card_overrides={"display_transform": ["DIALOGUE_MARKER_REMOVAL"]},
        )
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
        self.assertIn("PRE119_LOCKED_FIELD_OVERRIDE:C001:display_transform", result.stderr)
        self.assertFalse(self.output.exists())

    def test_evidence_card_order_must_match_approved_seed(self) -> None:
        seed_cards = [
            self.approved_seed_card(card_id="C001", next_card="C002"),
            self.approved_seed_card(card_id="C002"),
        ]
        self.write_validation(seed_cards=seed_cards)
        cards = [
            self.source_card(card_id="C001", next_card="C002"),
            self.source_card(card_id="C002", target_start_us=2_000_000),
        ]
        self.write_evidence(list(reversed(cards)))

        result = self.run_compiler()

        self.assertNotEqual(result.returncode, 0)
        self.assertIn(
            "PRE119_CARD_ORDER_MISMATCH:expected=C001,C002:actual=C002,C001",
            result.stderr,
        )
        self.assertFalse(self.output.exists())

    def test_missing_or_extra_evidence_card_is_blocked(self) -> None:
        two_seed_cards = [
            self.approved_seed_card(card_id="C001", next_card="C002"),
            self.approved_seed_card(card_id="C002"),
        ]
        cases = [
            (
                two_seed_cards,
                [self.source_card(card_id="C001", next_card="C002")],
                "PRE119_CARD_SET_MISMATCH:missing=C002:extra=-",
            ),
            (
                [self.approved_seed_card()],
                [
                    self.source_card(),
                    self.source_card(card_id="C002", target_start_us=2_000_000),
                ],
                "PRE119_CARD_SET_MISMATCH:missing=-:extra=C002",
            ),
        ]
        for seed_cards, evidence_cards, blocker in cases:
            with self.subTest(blocker=blocker):
                self.output.unlink(missing_ok=True)
                self.write_validation(seed_cards=seed_cards)
                self.write_evidence(evidence_cards)

                result = self.run_compiler()

                self.assertNotEqual(result.returncode, 0)
                self.assertIn(blocker, result.stderr)
                self.assertFalse(self.output.exists())

    def test_locked_card_type_change_is_rejected(self) -> None:
        card = self.source_card()
        card["card_type"] = "TEXT_EXPLAINER"
        self.write_evidence([card])

        result = self.run_compiler()

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("PRE119_LOCKED_FIELD_OVERRIDE:C001:card_type", result.stderr)
        self.assertFalse(self.output.exists())

    def test_locked_chapter_change_is_rejected(self) -> None:
        for field in ("chapter_title", "chapter_hook"):
            with self.subTest(field=field):
                card = self.source_card()
                card[field] = "Mutated chapter"
                self.write_evidence([card])

                result = self.run_compiler()

                self.assertNotEqual(result.returncode, 0)
                self.assertIn(f"PRE119_LOCKED_FIELD_OVERRIDE:C001:{field}", result.stderr)
                self.assertFalse(self.output.exists())

    def test_locked_editorial_text_change_is_rejected(self) -> None:
        for field in ("visual_text", "narration_text", "why_this_segment", "next_card"):
            with self.subTest(field=field):
                card = self.source_card()
                card[field] = "Mutated text"
                self.write_evidence([card])

                result = self.run_compiler()

                self.assertNotEqual(result.returncode, 0)
                self.assertIn(f"PRE119_LOCKED_FIELD_OVERRIDE:C001:{field}", result.stderr)
                self.assertFalse(self.output.exists())

    def test_locked_commentary_change_is_rejected(self) -> None:
        self.write_validation(lower_mode="COMMENTARY_2LINE")
        for field in ("lower_line1", "lower_line2"):
            with self.subTest(field=field):
                card = self.source_card(lower_mode="COMMENTARY_2LINE")
                card[field] = "Mutated commentary"
                self.write_evidence([card])

                result = self.run_compiler()

                self.assertNotEqual(result.returncode, 0)
                self.assertIn(f"PRE119_LOCKED_FIELD_OVERRIDE:C001:{field}", result.stderr)
                self.assertFalse(self.output.exists())

    def test_locked_cta_change_is_rejected(self) -> None:
        card = self.source_card()
        card["cta_like_subscribe"] = "OFF"
        self.write_evidence([card])

        result = self.run_compiler()

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("PRE119_LOCKED_FIELD_OVERRIDE:C001:cta_like_subscribe", result.stderr)
        self.assertFalse(self.output.exists())

    def test_unapproved_editorial_field_is_rejected(self) -> None:
        card = self.source_card()
        card["unapproved_screen_text"] = "Injected text"
        self.write_evidence([card])

        result = self.run_compiler()

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("PRE119_LOCKED_FIELD_EXTRA:C001:unapproved_screen_text", result.stderr)
        self.assertFalse(self.output.exists())

    def test_runtime_execution_bindings_are_accepted(self) -> None:
        card = self.source_card()
        runtime_bindings = {
            "audio_start_us": 100_000,
            "motion_profile": "ZOOM_SLOW",
            "source_audio_mode": "MUTE",
            "video_start_us": 100_000,
        }
        card.update(runtime_bindings)
        self.write_evidence([card])

        result = self.run_compiler()

        self.assertEqual(result.returncode, 0, result.stderr)
        compiled = json.loads(self.output.read_text(encoding="utf-8"))
        for field, value in runtime_bindings.items():
            with self.subTest(field=field):
                self.assertEqual(compiled["cards"][0][field], value)

    def test_valid_display_transform_evidence_is_accepted_when_not_seed_locked(self) -> None:
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
        compiled = json.loads(self.output.read_text(encoding="utf-8"))
        self.assertEqual(
            compiled["cards"][0]["display_transform"],
            ["DIALOGUE_MARKER_REMOVAL", "LINE_BREAK"],
        )

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

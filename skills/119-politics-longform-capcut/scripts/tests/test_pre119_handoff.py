from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[2]
VALIDATOR = SKILL_ROOT / "scripts" / "validate_pre119_handoff.py"
APPROVED_SCRIPT_TEMPLATE = SKILL_ROOT / "templates" / "pre119-approved-script.md"
if str(SKILL_ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(SKILL_ROOT / "scripts"))

import validate_pre119_handoff as pre119_validator


class Pre119HandoffTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.package = Path(self.temporary.name)

    @property
    def report_path(self) -> Path:
        return self.package / "90_reports" / "pre119_handoff_validation.json"

    def write_valid_packet(self, *, include_seed: bool = True) -> str:
        script_path = self.package / "20_script" / "119_final_script.md"
        script_path.parent.mkdir(parents=True)
        seed = """

[ASSEMBLY_ONLY_SEED]
execution_mode=ASSEMBLY_ONLY
between_image=NO
between_narration=NO
lower_mode=NONE
cta_like_subscribe=ON

[CARD]
card_id=C001
card_type=SOURCE_VIDEO
chapter_label=Chapter 1
chapter_title=Chapter 1
chapter_hook=What changed?
source_id=S01_LOCK
source_policy_candidates=["S01_LOCK"]
visual_policy=SOURCE_VIDEO
visual_text=Approved screen text
narration_policy=SOURCE_AUDIO
narration_text=
lower_mode=NONE
lower_line1=
lower_line2=
cta_like_subscribe=ON
why_this_segment=Evidence first.
next_card=END
"""
        script_path.write_bytes(
            ("# approved\n\nlocked bytes\n" + (seed if include_seed else "")).encode("utf-8")
        )
        digest = hashlib.sha256(script_path.read_bytes()).hexdigest().upper()
        handoff = {
            "schema": "togun-pre119-handoff-v3",
            "route": "TOGUN_PRE119_TO_119_DIRECT",
            "editorial_owner": "TOGUN_PRE119",
            "source_state": "PRE119_SOURCE_CANDIDATE",
            "episode_id": "PL_20260809_PRE119",
            "project_name": "PL_20260809_PRE119_capcut_v1",
            "central_question": "What changed?",
            "selected_thesis": "The verified change matters.",
            "chapter_order": ["CH1", "CH2"],
            "between_image": "NO",
            "between_narration": "NO",
            "lower_mode": "NONE",
            "script_lock": {
                "current_final_script_sha256": digest,
                "user_approved_final_script_sha256": "",
                "status": "WAIT",
            },
            "artifacts": {
                "final_script_path": "20_script/119_final_script.md",
                "source_packet_path": "00_source/source_packet.md",
            },
        }
        handoff_path = self.package / "20_script" / "pre119_handoff.json"
        handoff_path.write_text(json.dumps(handoff), encoding="utf-8")
        return digest

    def run_validator(
        self,
        *,
        approved_sha: str | None = None,
        evidence: str | None = None,
    ) -> subprocess.CompletedProcess[str]:
        command = [sys.executable, "-B", str(VALIDATOR), "--package-root", str(self.package)]
        if approved_sha is not None:
            command.extend(["--approved-script-sha256", approved_sha])
        if evidence is not None:
            command.extend(["--approval-evidence", evidence])
        return subprocess.run(command, capture_output=True, text=True, check=False)

    def read_report(self) -> dict[str, object]:
        self.assertTrue(self.report_path.is_file())
        return json.loads(self.report_path.read_text(encoding="utf-8"))

    def test_approved_script_template_covers_all_supported_composition_and_lower_modes(self) -> None:
        seed = pre119_validator.parse_assembly_only_seed(APPROVED_SCRIPT_TEMPLATE)

        self.assertEqual(
            [card["card_type"] for card in seed["cards"]],
            [
                "SOURCE_VIDEO",
                "CHAPTER_CARD",
                "SOURCE_VIDEO",
                "NARRATION_VIDEO",
                "SOURCE_VIDEO",
                "CHAPTER_CARD",
            ],
        )
        self.assertEqual(
            [card["lower_mode"] for card in seed["cards"]],
            ["SRT", "NONE", "SRT", "SRT", "COMMENTARY_2LINE", "NONE"],
        )
        self.assertTrue(all(str(card.get("chapter_label", "")).strip() for card in seed["cards"]))

    def test_approved_script_template_opens_with_montage_hook(self) -> None:
        seed = pre119_validator.parse_assembly_only_seed(APPROVED_SCRIPT_TEMPLATE)
        cards = seed["cards"]

        hook = cards[0]
        self.assertEqual(hook["card_type"], "SOURCE_VIDEO")
        self.assertTrue(str(hook["card_id"]).startswith("C00_HOOK"))
        self.assertEqual(hook["chapter_label"], "오프닝")
        self.assertEqual(hook["lower_mode"], "SRT")
        self.assertEqual(hook["source_audio"], "ON")
        self.assertEqual(hook["narration_audio"], "OFF")

        cta = cards[1]
        self.assertEqual(cta["card_id"], "C00_HOOK_CTA")
        self.assertEqual(cta["card_type"], "CHAPTER_CARD")
        self.assertEqual(cta["chapter_label"], "오프닝")
        self.assertEqual(cta["lower_mode"], "NONE")
        self.assertEqual(cta["next_card"], cards[2]["card_id"])

        body_labels = {card["chapter_label"] for card in cards[2:]}
        self.assertNotIn("오프닝", body_labels)

    def test_montage_contract_is_documented_for_the_authoring_gpt(self) -> None:
        template = APPROVED_SCRIPT_TEMPLATE.read_text(encoding="utf-8")
        self.assertIn("## 오프닝 몽타주", template)
        self.assertIn("시간 순서가 아니라 세기 순서로 배치한다", template)

        review = (
            APPROVED_SCRIPT_TEMPLATE.parent.parent
            / "references"
            / "chatgpt_politics_longform_review_contract.md"
        ).read_text(encoding="utf-8")
        self.assertIn("첫 45초가 본편 최강 발화 몽타주로 구성돼 있는지", review)
        self.assertIn("후킹이 적대 진영 비판에 머물러 결론이 예측되는지", review)

    def test_strong_marker_locks_pre119_before_direct_script_fallback(self) -> None:
        self.write_valid_packet()

        result = self.run_validator()

        self.assertNotEqual(result.returncode, 0)
        report = self.read_report()
        self.assertEqual(report["route"], "PRE119")
        self.assertEqual(report["status"], "WAIT_EXTERNAL_APPROVAL_REQUIRED")

    def test_one_auxiliary_marker_does_not_false_match_pre119(self) -> None:
        (self.package / "00_README.md").write_text("ordinary episode notes", encoding="utf-8")

        result = self.run_validator()

        self.assertEqual(result.returncode, 0, result.stderr)
        report = self.read_report()
        self.assertEqual(report["route"], "DIRECT_SCRIPT")
        self.assertEqual(report["status"], "NOT_PRE119")

    def test_packet_internal_pass_cannot_replace_external_approval(self) -> None:
        digest = self.write_valid_packet()
        handoff_path = self.package / "20_script" / "pre119_handoff.json"
        handoff = json.loads(handoff_path.read_text(encoding="utf-8"))
        handoff["script_lock"].update(
            {
                "status": "PASS",
                "user_approved_final_script_sha256": digest,
            }
        )
        handoff["user_approval"] = {"status": "PASS"}
        handoff_path.write_text(json.dumps(handoff), encoding="utf-8")

        result = self.run_validator(evidence="user_message:approved")

        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(self.read_report()["status"], "WAIT_EXTERNAL_APPROVAL_REQUIRED")

    def test_actual_packet_and_external_sha_must_all_match(self) -> None:
        digest = self.write_valid_packet()

        result = self.run_validator(
            approved_sha=digest,
            evidence="user_message:019fe54b-approved",
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        report = self.read_report()
        self.assertEqual(report["status"], "PASS")
        self.assertEqual(report["script_lock"]["actual_final_script_sha256"], digest)
        self.assertEqual(report["script_lock"]["packet_current_final_script_sha256"], digest)
        self.assertEqual(report["script_lock"]["external_approved_script_sha256"], digest)
        self.assertEqual(report["assembly_only_seed"]["card_order"], ["C001"])
        self.assertRegex(report["assembly_only_seed_sha256"], r"^[0-9A-F]{64}$")
        self.assertFalse((self.package / "50_capcut_project" / "episode_cards.json").exists())

    def test_body_card_without_chapter_label_is_rejected_before_assembly(self) -> None:
        digest = self.write_valid_packet()
        script_path = self.package / "20_script" / "119_final_script.md"
        script_path.write_text(
            script_path.read_text(encoding="utf-8").replace(
                "chapter_label=Chapter 1\n", "chapter_label=\n"
            ),
            encoding="utf-8",
        )
        digest = hashlib.sha256(script_path.read_bytes()).hexdigest().upper()
        handoff_path = self.package / "20_script" / "pre119_handoff.json"
        handoff = json.loads(handoff_path.read_text(encoding="utf-8"))
        handoff["script_lock"]["current_final_script_sha256"] = digest
        handoff_path.write_text(json.dumps(handoff), encoding="utf-8")

        result = self.run_validator(
            approved_sha=digest,
            evidence="user_message:chapter-label-required",
        )

        self.assertNotEqual(result.returncode, 0)
        report = self.read_report()
        self.assertEqual(report["status"], "FAIL_PRE119_ASSEMBLY_SEED_INVALID")
        self.assertEqual(report["seed_error"], "CARD_1_CHAPTER_LABEL_REQUIRED:C001")

    def test_approved_script_without_assembly_only_seed_is_blocked(self) -> None:
        digest = self.write_valid_packet(include_seed=False)

        result = self.run_validator(
            approved_sha=digest,
            evidence="user_message:approved",
        )

        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(self.read_report()["status"], "FAIL_PRE119_ASSEMBLY_SEED_REQUIRED")

    def test_hash_mismatch_is_blocked_and_reported(self) -> None:
        self.write_valid_packet()

        result = self.run_validator(
            approved_sha="0" * 64,
            evidence="user_message:approved",
        )

        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(self.read_report()["status"], "WAIT_APPROVAL_HASH_MISMATCH")

    def test_absolute_packet_path_is_rejected(self) -> None:
        digest = self.write_valid_packet()
        handoff_path = self.package / "20_script" / "pre119_handoff.json"
        handoff = json.loads(handoff_path.read_text(encoding="utf-8"))
        handoff["artifacts"]["source_packet_path"] = "C:/Users/person/source_packet.md"
        handoff_path.write_text(json.dumps(handoff), encoding="utf-8")

        result = self.run_validator(approved_sha=digest, evidence="user_message:approved")

        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(self.read_report()["status"], "FAIL_PACKET_PATH_UNSAFE")

    def test_parent_traversal_packet_path_is_rejected(self) -> None:
        digest = self.write_valid_packet()
        handoff_path = self.package / "20_script" / "pre119_handoff.json"
        handoff = json.loads(handoff_path.read_text(encoding="utf-8"))
        handoff["artifacts"]["source_packet_path"] = "../outside/source_packet.md"
        handoff_path.write_text(json.dumps(handoff), encoding="utf-8")

        result = self.run_validator(approved_sha=digest, evidence="user_message:approved")

        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(self.read_report()["status"], "FAIL_PACKET_PATH_UNSAFE")

    def test_invalid_handoff_identity_cannot_receive_pass(self) -> None:
        digest = self.write_valid_packet()
        handoff_path = self.package / "20_script" / "pre119_handoff.json"
        handoff = json.loads(handoff_path.read_text(encoding="utf-8"))
        handoff["schema"] = "untrusted-schema"
        handoff_path.write_text(json.dumps(handoff), encoding="utf-8")

        result = self.run_validator(approved_sha=digest, evidence="user_message:approved")

        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(self.read_report()["status"], "FAIL_PRE119_HANDOFF_IDENTITY")


if __name__ == "__main__":
    unittest.main()

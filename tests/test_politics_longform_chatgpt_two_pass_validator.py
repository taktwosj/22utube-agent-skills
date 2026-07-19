import hashlib
import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path


sys.dont_write_bytecode = True

ROOT = Path(__file__).resolve().parents[1]
VALIDATOR = (
    ROOT
    / "skills"
    / "111-politics-longform"
    / "scripts"
    / "validate_chatgpt_two_pass_review.py"
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def load_validator():
    if not VALIDATOR.is_file():
        raise AssertionError(f"missing validator: {VALIDATOR}")
    spec = importlib.util.spec_from_file_location(
        "politics_chatgpt_two_pass_validator", VALIDATOR
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def build_valid_review(root: Path) -> Path:
    review = root / "20_script" / "master_commentary_review"
    script = root / "20_script" / "commentary_master_script_draft.md"
    fact_map = root / "20_script" / "commentary_fact_map.json"
    timeline = root / "10_analysis" / "timeline_design_draft.json"

    write_text(script, "# 수정 원고\nS001에서 시작해 S002로 이어진다.\n")
    write_json(
        fact_map,
        {
            "claims": [
                {"claim_id": "CL001", "segment_id": "S001"},
                {"claim_id": "CL002", "segment_id": "S002"},
            ]
        },
    )
    write_json(timeline, {"ordered_segment_ids": ["S001", "S002"]})

    round1_packet = review / "round1_packet_sent.md"
    round1_returned = review / "round1_returned.md"
    round1_decisions = review / "round1_codex_decisions.json"
    write_text(round1_packet, "# ROUND_1\n초안과 근거 전체\n")
    write_text(
        round1_returned,
        "# ROUND_1 RETURN\n"
        "suggestion_id: SG001\n"
        "suggestion_id: SG002\n"
        "final_state: PENDING_CODEX_REVIEW\n",
    )

    write_json(
        review / "round1_manifest.json",
        {
            "schema_version": 1,
            "review_round": 1,
            "packet_id": "PKT-001",
            "sent_file": "round1_packet_sent.md",
            "sent_sha256": sha256(round1_packet),
            "master_script_file": "../commentary_master_script_draft.md",
            "master_script_sha256": sha256(script),
            "fact_map_file": "../commentary_fact_map.json",
            "fact_map_sha256": sha256(fact_map),
            "timeline_file": "../../10_analysis/timeline_design_draft.json",
            "timeline_sha256": sha256(timeline),
            "ordered_segment_ids": ["S001", "S002"],
        },
    )
    write_json(
        review / "round1_receipt.json",
        {
            "review_round": 1,
            "packet_id": "PKT-001",
            "conversation_id": "CHAT-001",
            "returned_file": "round1_returned.md",
            "returned_sha256": sha256(round1_returned),
            "external_review_status": "PENDING_CODEX_REVIEW",
            "suggestion_ids": ["SG001", "SG002"],
        },
    )
    write_json(
        round1_decisions,
        {
            "round1_return_sha256": sha256(round1_returned),
            "decisions": [
                {
                    "suggestion_id": "SG001",
                    "decision": "ADOPTED",
                    "decision_reason": "근거와 흐름을 개선한다.",
                },
                {
                    "suggestion_id": "SG002",
                    "decision": "REJECTED",
                    "decision_reason": "원문 범위를 넘어선다.",
                },
            ],
        },
    )

    round2_packet = review / "round2_packet_sent.md"
    round2_returned = review / "round2_returned.md"
    write_text(
        round2_packet,
        "\n".join(
            [
                "# ROUND_2",
                "<!-- ROUND1_RETURN_FULL -->",
                "Round 1 전체 반환문",
                "<!-- CODEX_DECISIONS_FULL -->",
                "Codex 결정표 전체",
                "<!-- REVISED_MASTER_SCRIPT_FULL -->",
                "수정된 마스터 원고 전문",
                "<!-- REVISED_FACT_MAP_FULL -->",
                "수정된 fact map 전문",
                "<!-- TIMELINE_ORDER_FULL -->",
                "S001,S002",
                "<!-- CORE_QUESTION -->",
                "이 흐름은 무엇을 설명하는가?",
            ]
        )
        + "\n",
    )
    write_text(
        round2_returned,
        "# ROUND_2 RETURN\n근거와 전체 흐름 모두 통과 권고\n"
        "final_state: PENDING_CODEX_REVIEW\n",
    )
    write_json(
        review / "round2_manifest.json",
        {
            "schema_version": 1,
            "review_round": 2,
            "packet_id": "PKT-002",
            "sent_file": "round2_packet_sent.md",
            "sent_sha256": sha256(round2_packet),
            "conversation_id": "CHAT-001",
            "round1_return_sha256": sha256(round1_returned),
            "round1_decisions_sha256": sha256(round1_decisions),
            "revised_script_file": "../commentary_master_script_draft.md",
            "revised_script_sha256": sha256(script),
            "revised_fact_map_file": "../commentary_fact_map.json",
            "revised_fact_map_sha256": sha256(fact_map),
            "timeline_file": "../../10_analysis/timeline_design_draft.json",
            "timeline_sha256": sha256(timeline),
            "ordered_segment_ids": ["S001", "S002"],
            "included_sections": [
                "round1_return_full",
                "codex_decisions_full",
                "revised_master_script_full",
                "revised_fact_map_full",
                "timeline_order_full",
                "core_question",
            ],
        },
    )
    write_json(
        review / "round2_receipt.json",
        {
            "review_round": 2,
            "packet_id": "PKT-002",
            "conversation_id": "CHAT-001",
            "returned_file": "round2_returned.md",
            "returned_sha256": sha256(round2_returned),
            "external_review_status": "PENDING_CODEX_REVIEW",
            "recommendation": "PASS_RECOMMENDED",
            "flow_continuity_status": "PASS",
            "remaining_blockers": [],
            "ordered_segment_ids": ["S001", "S002"],
        },
    )
    return review


def build_compact_review(root: Path) -> Path:
    review = root / "20_script" / "master_commentary_review"
    script = root / "20_script" / "commentary_master_script_draft.md"
    fact_map = root / "20_script" / "commentary_fact_map.json"
    timeline = root / "10_analysis" / "timeline_design_draft.json"
    round1 = review / "round1_returned.md"
    decisions = review / "round1_codex_decisions.json"
    round2 = review / "round2_returned.md"
    write_text(
        script,
        "# 검수 원고\n\n## N001. 시작\n문제 제기\n\n## N002. 결론\n최종 판단\n",
    )
    write_json(fact_map, {"claims": [{"claim_id": "FM01"}]})
    write_json(timeline, {"ordered_segment_ids": ["N001", "N002"]})
    write_text(
        round1,
        "# Round 1\n\n### R1-01\n문제: 근거 범위가 넓다.\n\n"
        "### R1-02\n문제: 결론이 빠르다.\n",
    )
    write_json(
        decisions,
        {
            "conversation_id": "CHAT-COMPACT",
            "decisions": [
                {
                    "suggestion_id": "R1-01",
                    "decision": "ADOPTED",
                    "decision_reason": "근거 범위를 좁혔다.",
                },
                {
                    "suggestion_id": "R1-02",
                    "decision": "PARTIALLY_ADOPTED",
                    "decision_reason": "결론 강도만 낮췄다.",
                },
            ],
        },
    )
    write_text(round2, "# Round 2\n\n권고: PASS_RECOMMENDED\n")
    write_json(
        review / "review_manifest.json",
        {
            "schema_version": "politics-chatgpt-two-pass-human-readable-v1",
            "conversation_id": "CHAT-COMPACT",
            "round1_returned_file": "round1_returned.md",
            "round1_returned_sha256": sha256(round1),
            "decisions_file": "round1_codex_decisions.json",
            "decisions_sha256": sha256(decisions),
            "round2_returned_file": "round2_returned.md",
            "round2_returned_sha256": sha256(round2),
            "revised_script_file": "../commentary_master_script_draft.md",
            "revised_script_sha256": sha256(script),
            "revised_fact_map_file": "../commentary_fact_map.json",
            "revised_fact_map_sha256": sha256(fact_map),
            "timeline_file": "../../10_analysis/timeline_design_draft.json",
            "timeline_sha256": sha256(timeline),
            "ordered_segment_ids": ["N001", "N002"],
            "recommendation": "PASS_RECOMMENDED",
            "flow_continuity_status": "PASS",
            "text_hygiene_status": "PASS",
            "remaining_blockers": [],
        },
    )
    return review


def error_codes(result: dict) -> set[str]:
    return {item["code"] for item in result["errors"]}


class PoliticsLongformChatGptTwoPassValidatorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.validator = load_validator()

    def validate(self, review: Path) -> dict:
        return self.validator.validate_review(review)

    def test_valid_two_pass_review_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = self.validate(build_valid_review(Path(tmp)))
        self.assertEqual(result["status"], "PASS", result)
        self.assertEqual(result["gate"], "MASTER_COMMENTARY_REVIEW_GATE")

    def test_compact_human_readable_review_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = self.validate(build_compact_review(Path(tmp)))
        self.assertEqual(result["status"], "PASS", result)
        self.assertEqual(
            result["contract"],
            "politics-chatgpt-two-pass-human-readable-v1",
        )

    def test_compact_review_hash_drift_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            review = build_compact_review(Path(tmp))
            write_text(review / "round2_returned.md", "tampered\n")
            result = self.validate(review)
        self.assertIn("HASH_MISMATCH", error_codes(result))

    def test_missing_round_two_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            review = build_valid_review(Path(tmp))
            (review / "round2_receipt.json").unlink()
            result = self.validate(review)
        self.assertIn("MISSING_ARTIFACT", error_codes(result))

    def test_round_two_must_use_the_same_conversation(self):
        with tempfile.TemporaryDirectory() as tmp:
            review = build_valid_review(Path(tmp))
            receipt_path = review / "round2_receipt.json"
            receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
            receipt["conversation_id"] = "CHAT-OTHER"
            write_json(receipt_path, receipt)
            result = self.validate(review)
        self.assertIn("SAME_CONVERSATION_REQUIRED", error_codes(result))

    def test_every_round_one_suggestion_requires_exactly_one_decision(self):
        with tempfile.TemporaryDirectory() as tmp:
            review = build_valid_review(Path(tmp))
            decisions_path = review / "round1_codex_decisions.json"
            decisions = json.loads(decisions_path.read_text(encoding="utf-8"))
            decisions["decisions"].pop()
            write_json(decisions_path, decisions)
            manifest_path = review / "round2_manifest.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["round1_decisions_sha256"] = sha256(decisions_path)
            write_json(manifest_path, manifest)
            result = self.validate(review)
        self.assertIn("INCOMPLETE_CODEX_DECISIONS", error_codes(result))

    def test_pending_evidence_blocks_the_gate(self):
        with tempfile.TemporaryDirectory() as tmp:
            review = build_valid_review(Path(tmp))
            decisions_path = review / "round1_codex_decisions.json"
            decisions = json.loads(decisions_path.read_text(encoding="utf-8"))
            decisions["decisions"][0]["decision"] = "PENDING_EVIDENCE"
            write_json(decisions_path, decisions)
            manifest_path = review / "round2_manifest.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["round1_decisions_sha256"] = sha256(decisions_path)
            write_json(manifest_path, manifest)
            result = self.validate(review)
        self.assertEqual(result["status"], "WAIT", result)
        self.assertIn("PENDING_EVIDENCE", error_codes(result))

    def test_hash_drift_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            review = build_valid_review(Path(tmp))
            write_text(review / "round1_packet_sent.md", "tampered\n")
            result = self.validate(review)
        self.assertIn("HASH_MISMATCH", error_codes(result))

    def test_revised_files_can_change_after_the_immutable_round_one_packet(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            review = build_valid_review(root)
            script = root / "20_script" / "commentary_master_script_draft.md"
            fact_map = root / "20_script" / "commentary_fact_map.json"
            write_text(script, "# 수정 원고 v2\nS001에서 S002로 더 자연스럽게 이어진다.\n")
            write_json(
                fact_map,
                {
                    "claims": [
                        {"claim_id": "CL001", "segment_id": "S001"},
                        {
                            "claim_id": "CL002",
                            "segment_id": "S002",
                            "revision": "SG001 반영",
                        },
                    ]
                },
            )
            manifest_path = review / "round2_manifest.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["revised_script_sha256"] = sha256(script)
            manifest["revised_fact_map_sha256"] = sha256(fact_map)
            write_json(manifest_path, manifest)
            result = self.validate(review)
        self.assertEqual(result["status"], "PASS", result)

    def test_receipt_suggestion_ids_must_match_the_returned_response(self):
        with tempfile.TemporaryDirectory() as tmp:
            review = build_valid_review(Path(tmp))
            returned = review / "round1_returned.md"
            write_text(
                returned,
                "# ROUND_1 RETURN\n"
                "suggestion_id: SG001\n"
                "suggestion_id: SG003\n"
                "final_state: PENDING_CODEX_REVIEW\n",
            )
            receipt_path = review / "round1_receipt.json"
            receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
            receipt["returned_sha256"] = sha256(returned)
            write_json(receipt_path, receipt)
            decisions_path = review / "round1_codex_decisions.json"
            decisions = json.loads(decisions_path.read_text(encoding="utf-8"))
            decisions["round1_return_sha256"] = sha256(returned)
            write_json(decisions_path, decisions)
            manifest_path = review / "round2_manifest.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["round1_return_sha256"] = sha256(returned)
            manifest["round1_decisions_sha256"] = sha256(decisions_path)
            write_json(manifest_path, manifest)
            result = self.validate(review)
        self.assertIn("SUGGESTION_ID_MISMATCH", error_codes(result))

    def test_segment_order_drift_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            review = build_valid_review(Path(tmp))
            receipt_path = review / "round2_receipt.json"
            receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
            receipt["ordered_segment_ids"] = ["S002", "S001"]
            write_json(receipt_path, receipt)
            result = self.validate(review)
        self.assertIn("SEGMENT_ORDER_DRIFT", error_codes(result))

    def test_flow_failure_or_remaining_blocker_waits_for_repair(self):
        with tempfile.TemporaryDirectory() as tmp:
            review = build_valid_review(Path(tmp))
            receipt_path = review / "round2_receipt.json"
            receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
            receipt["recommendation"] = "REVISE_REQUIRED"
            receipt["flow_continuity_status"] = "FAIL"
            receipt["remaining_blockers"] = ["S001에서 S002 전환 근거 보강"]
            write_json(receipt_path, receipt)
            result = self.validate(review)
        self.assertEqual(result["status"], "WAIT", result)
        self.assertIn("WAIT_CHATGPT_REVIEW_REPAIR", error_codes(result))

    def test_external_final_approval_claim_is_forbidden(self):
        with tempfile.TemporaryDirectory() as tmp:
            review = build_valid_review(Path(tmp))
            returned = review / "round2_returned.md"
            write_text(returned, "final_state: FINAL\n")
            receipt_path = review / "round2_receipt.json"
            receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
            receipt["returned_sha256"] = sha256(returned)
            write_json(receipt_path, receipt)
            result = self.validate(review)
        self.assertIn("FORBIDDEN_EXTERNAL_APPROVAL", error_codes(result))


if __name__ == "__main__":
    unittest.main()

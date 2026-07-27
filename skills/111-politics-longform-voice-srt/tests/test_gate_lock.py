#!/usr/bin/env python3
"""gate_lock.py 회귀 테스트.

게이트는 "막는 것"이 일이다. 통과 케이스보다 **차단 케이스**를 먼저 증명한다.

v1.0 의 15개 테스트는 "내가 생각한 것을 막는다"만 증명했고 우회 가능성을
증명하지 못했다. 리스크 리뷰에서 10건이 나왔고 그중 실증된 두 개가 아프다.

    RISK-002  v1.0 의 통과 픽스처는 locked_inputs 에 script 하나뿐이었다
              -> 맞는 대본 + 틀린 클립으로 제작 가능
    RISK-008  ep / "../../다른에피소드/x.md" 는 C:\\다른에피소드\\x.md 로 탈출

실행:
    py -3.14 -m unittest discover -s skills/112-politics-longform-hyperframes/tests
"""
import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

GATE = Path(__file__).resolve().parent.parent / "scripts" / "gate_lock.py"

# 1-based 줄번호 기준으로 세그먼트 범위를 잡는다.
SCRIPT_LINES = [
    "# 테스트 대본",                                                     # 1
    "",                                                                   # 2
    "# CHAPTER 1. 무엇이 문제인가",                                        # 3
    "",                                                                   # 4
    "비판의 초점은 내각의 성과가 아니라 대통령과 민주당의 관계에 놓여 있습니다.",  # 5
    "당 지배와 검찰개혁에 관한 특정한 선택이 계속될 경우 실패한다고 보았습니다.",  # 6
    "",                                                                   # 7
    "# CHAPTER 2. 남은 질문",                                             # 8
    "",                                                                   # 9
    "정부는 국민 통합을 국정 과제로 제시했습니다.",                          # 10
]
SCRIPT_BODY = "\n".join(SCRIPT_LINES) + "\n"

INPUT_FILES = {
    "script":             "20_script/master_script.md",
    "source_map":         "20_script/source_map.json",
    "clip_manifest":      "10_analysis/clip_manifest.json",
    "intake_manifest":    "10_analysis/intake_manifest.json",
    "episode_lexicon":    "10_analysis/episode_lexicon.json",
    "machine_audit":      "90_reports/script_audit.json",
    "project_gpt_ruling": "20_script/project_gpt_ruling.json",
}


def sha256_bytes(data):
    return hashlib.sha256(data).hexdigest()


class GateCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.ep = Path(self.tmp.name)
        self.shas = {}
        for name, rel in INPUT_FILES.items():
            p = self.ep / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            data = (SCRIPT_BODY if name == "script"
                    else json.dumps({"stub": name}, ensure_ascii=False)).encode("utf-8")
            p.write_bytes(data)
            self.shas[name] = sha256_bytes(data)
        self.lock = self._base_lock()

    def tearDown(self):
        self.tmp.cleanup()

    def _base_lock(self):
        return {
            "schema_version": "politics-longform-script-lock.v1",
            "episode_id": "PL_20260101_test",
            "status": "SCRIPT_LOCKED",
            "lock_version": 1,
            "locked_at": "2026-01-01T00:00:00Z",
            "authority": {"script_authority": "PROJECT_GPT",
                          "executor_editorial_authority": "NONE"},
            "locked_inputs": {n: {"path": r, "sha256": self.shas[n]}
                              for n, r in INPUT_FILES.items()},
            "ruling_summary": {
                "total_findings": 3, "approved_fix": 1, "rejected_no_change": 2,
                "deferred": 0, "unresolved": 0, "unresolved_high": 0,
                "unresolved_quote_mismatch": 0, "deferred_items": [],
            },
            "editorial_decisions": {
                "chapter_order_approved": True, "source_media_verified": True,
                "clip_timecodes_verified": True, "hook_selection_approved": True,
                "lexicon_review_approved": True, "quote_accuracy_approved": True,
                "lexicon_conflicts": 0,
            },
            "structure": {
                "chapter_count": 2, "narration_block_count": 2,
                "source_clip_count": 1, "logical_segment_count": 3,
                "chapters": [
                    {"no": 1, "title": "무엇이 문제인가",
                     "script_line_range": [3, 7], "segment_indices": [1, 2]},
                    {"no": 2, "title": "남은 질문",
                     "script_line_range": [8, 10], "segment_indices": [3]},
                ],
                "segments": [
                    {"index": 1, "segment_id": "SEG001", "kind": "NARRATION",
                     "chapter_no": 1, "script_line_range": [5, 6],
                     "source_id": None, "source_timecode": None},
                    {"index": 2, "segment_id": "SEG002", "kind": "SOURCE_VIDEO",
                     "chapter_no": 1, "script_line_range": [6, 6],
                     "source_id": "S05", "source_timecode": "00:08:50~00:09:09"},
                    {"index": 3, "segment_id": "SEG003", "kind": "NARRATION",
                     "chapter_no": 2, "script_line_range": [10, 10],
                     "source_id": None, "source_timecode": None},
                ],
            },
            "hooks": {"1": {
                "text": "비판의 초점은 내각의 성과가 아니라 대통령과 민주당의 관계에 놓여 있습니다.",
                "underline": "대통령과 민주당의 관계", "script_line": 5}},
            "labels": {"_rule": "세그먼트별", "1": ["당 지배", "검찰개혁"]},
            "tts_params": {"provider": "supertone", "voice_id": "x",
                           "model": "sona_speech_2", "speed": 1,
                           "pitch_shift": 0, "pitch_variance": 1},
            "render_target": {"canvas": "1920x1080", "fps": 30},
        }

    def write_lock(self, lock=None):
        (self.ep / "20_script" / "script_lock.json").write_text(
            json.dumps(lock if lock is not None else self.lock,
                       ensure_ascii=False), encoding="utf-8")

    def run_gate(self, stage="tts"):
        r = subprocess.run(
            [sys.executable, str(GATE), "--episode", str(self.ep),
             "--stage", stage, "--json"],
            capture_output=True, text=True, encoding="utf-8",
            errors="replace", timeout=120)
        try:
            payload = json.loads(r.stdout)
        except Exception:
            payload = {"failures": [], "raw": r.stdout + r.stderr}
        return r.returncode, payload

    def codes(self, payload):
        return {f["code"] for f in payload.get("failures", [])}

    def assertBlocked(self, code, stage="tts"):
        self.write_lock()
        rc, out = self.run_gate(stage)
        self.assertEqual(rc, 1, out)
        self.assertIn(code, self.codes(out), out)

    # ---------------------------------------------------------- 통과
    def test_valid_lock_passes_tts(self):
        self.write_lock()
        rc, out = self.run_gate("tts")
        self.assertEqual(rc, 0, out)
        self.assertGreater(out["checks"], 20)

    def test_rejected_no_change_does_not_block(self):
        """기각 판정은 해결된 것이다. 미해결로 세면 영원히 안 잠긴다."""
        self.lock["ruling_summary"].update(
            {"total_findings": 11, "approved_fix": 2,
             "rejected_no_change": 9, "deferred": 0, "unresolved": 0})
        self.write_lock()
        rc, out = self.run_gate("tts")
        self.assertEqual(rc, 0, out)

    def test_deferred_blocking_assembly_only_allows_tts(self):
        self.lock["ruling_summary"].update(
            {"total_findings": 4, "approved_fix": 1, "rejected_no_change": 2,
             "deferred": 1, "unresolved": 0,
             "deferred_items": [{"id": "SCA-014", "reason": "후속 확인",
                                 "blocks": ["ASSEMBLY"],
                                 "approved_by": "PROJECT_GPT",
                                 "resolution_plan": "자막 QC 때 확인"}]})
        self.write_lock()
        rc, out = self.run_gate("tts")
        self.assertEqual(rc, 0, out)

    # ---------------------------------------------- 기본 잠금 (v1.0 회귀)
    def test_missing_lock_blocks(self):
        rc, out = self.run_gate("tts")
        self.assertEqual(rc, 1)
        self.assertIn("LOCK_MISSING", self.codes(out))

    def test_status_not_locked_blocks(self):
        self.lock["status"] = "DRAFT"
        self.assertBlocked("STATUS_NOT_LOCKED")

    def test_script_edited_after_lock_blocks(self):
        self.write_lock()
        (self.ep / "20_script" / "master_script.md").write_text(
            SCRIPT_BODY + "\n덧붙인 문장입니다.\n", encoding="utf-8")
        rc, out = self.run_gate("tts")
        self.assertEqual(rc, 1)
        self.assertIn("LOCKED_INPUT_SHA_MISMATCH", self.codes(out))

    def test_unresolved_high_blocks(self):
        """지난 에피소드에서 뚫린 바로 그 조건."""
        self.lock["ruling_summary"].update(
            {"total_findings": 6, "approved_fix": 0, "rejected_no_change": 0,
             "deferred": 0, "unresolved": 6, "unresolved_high": 6})
        self.assertBlocked("RULING_UNRESOLVED")

    def test_ruling_count_inconsistent_blocks(self):
        self.lock["ruling_summary"]["total_findings"] = 99
        self.assertBlocked("RULING_COUNT_INCONSISTENT")

    # ---------------------------------------------- RISK-002 필수 입력
    def test_missing_each_required_input_blocks(self):
        for name in ("source_map", "clip_manifest", "intake_manifest",
                     "episode_lexicon", "machine_audit", "project_gpt_ruling"):
            with self.subTest(missing=name):
                self.lock = self._base_lock()
                del self.lock["locked_inputs"][name]
                self.write_lock()
                rc, out = self.run_gate("tts")
                self.assertEqual(rc, 1)
                self.assertIn("LOCKED_INPUT_REQUIRED_MISSING", self.codes(out))

    def test_malformed_sha_blocks(self):
        self.lock["locked_inputs"]["script"]["sha256"] = "not-a-sha"
        self.assertBlocked("LOCKED_INPUT_SHA_MALFORMED")

    # ---------------------------------------------- RISK-008 경로 탈출
    def test_absolute_locked_input_path_blocks(self):
        self.lock["locked_inputs"]["script"]["path"] = "C:\\다른프로젝트\\x.md"
        self.assertBlocked("LOCKED_INPUT_PATH_OUTSIDE_EPISODE")

    def test_parent_traversal_path_blocks(self):
        self.lock["locked_inputs"]["script"]["path"] = "../../다른에피소드/x.md"
        self.assertBlocked("LOCKED_INPUT_PATH_OUTSIDE_EPISODE")

    # ---------------------------------------------- RISK-003 순서 무결성
    def test_segments_missing_blocks(self):
        del self.lock["structure"]["segments"]
        self.assertBlocked("SEGMENT_ORDER_INTEGRITY_FAIL")

    def test_segment_index_gap_blocks(self):
        self.lock["structure"]["segments"][2]["index"] = 9
        self.assertBlocked("SEGMENT_ORDER_INTEGRITY_FAIL")

    def test_segment_id_duplicate_blocks(self):
        self.lock["structure"]["segments"][2]["segment_id"] = "SEG001"
        self.assertBlocked("SEGMENT_ORDER_INTEGRITY_FAIL")

    def test_segment_kind_count_mismatch_blocks(self):
        self.lock["structure"]["narration_block_count"] = 3
        self.assertBlocked("SEGMENT_KIND_COUNT_MISMATCH")

    def test_source_video_without_source_id_blocks(self):
        self.lock["structure"]["segments"][1]["source_id"] = None
        self.assertBlocked("SEGMENT_SOURCE_FIELDS_MISSING")

    def test_narration_with_source_id_blocks(self):
        self.lock["structure"]["segments"][0]["source_id"] = "S05"
        self.assertBlocked("SEGMENT_SOURCE_FIELDS_UNEXPECTED")

    def test_chapter_segment_mapping_mismatch_blocks(self):
        self.lock["structure"]["chapters"][1]["segment_indices"] = [7]
        self.assertBlocked("CHAPTER_SEGMENT_MAPPING_MISMATCH")

    def test_chapter_count_mismatch_blocks(self):
        self.lock["structure"]["chapter_count"] = 4
        self.assertBlocked("CHAPTER_COUNT_MISMATCH")

    # ---------------------------------------------- RISK-004 세그먼트 범위
    def test_label_from_other_segment_blocks(self):
        """`국민 통합`은 챕터 2에 실재한다. 전역 검사면 통과, 범위 검사면 차단."""
        self.lock["labels"]["1"] = ["당 지배", "국민 통합"]
        self.assertBlocked("SEGMENT_SCOPED_TEXT_MISMATCH")

    def test_hook_from_other_segment_blocks(self):
        self.lock["hooks"]["1"]["text"] = "정부는 국민 통합을 국정 과제로 제시했습니다."
        self.lock["hooks"]["1"]["underline"] = "국민 통합"
        self.assertBlocked("SEGMENT_SCOPED_TEXT_MISMATCH")

    def test_unknown_segment_key_blocks(self):
        self.lock["labels"]["99"] = ["당 지배"]
        self.assertBlocked("UNKNOWN_SEGMENT_KEY")

    def test_invented_label_blocks(self):
        """`실패 조건`처럼 시안이 만든 말이 라벨로 올라오는 것을 막는다."""
        self.lock["labels"]["1"] = ["당 지배", "실패 조건"]
        self.assertBlocked("SEGMENT_SCOPED_TEXT_MISMATCH")

    def test_underline_not_in_hook_blocks(self):
        self.lock["hooks"]["1"]["underline"] = "존재하지 않는 어구"
        self.assertBlocked("UNDERLINE_NOT_IN_HOOK")

    # ---------------------------------------------- RISK-006 편집 승인
    def test_missing_editorial_key_blocks(self):
        del self.lock["editorial_decisions"]["quote_accuracy_approved"]
        self.assertBlocked("EDITORIAL_DECISION_REQUIRED_MISSING")

    def test_misspelled_editorial_key_blocks(self):
        ed = self.lock["editorial_decisions"]
        ed["source_media_verifed"] = ed.pop("source_media_verified")
        self.assertBlocked("EDITORIAL_DECISION_REQUIRED_MISSING")

    def test_false_editorial_decision_blocks(self):
        self.lock["editorial_decisions"]["source_media_verified"] = False
        self.assertBlocked("EDITORIAL_NOT_APPROVED")

    # ---------------------------------------------- RISK-007 DEFER 우회
    def test_deferred_blocking_tts_blocks_lock(self):
        self.lock["ruling_summary"].update(
            {"total_findings": 4, "approved_fix": 1, "rejected_no_change": 2,
             "deferred": 1, "unresolved": 0,
             "deferred_items": [{"id": "SCA-014", "reason": "인명 확인 필요",
                                 "blocks": ["TTS"], "approved_by": "PROJECT_GPT",
                                 "resolution_plan": "원본 대조"}]})
        self.assertBlocked("DEFERRED_ITEM_BLOCKS_STAGE")

    def test_deferred_without_blocks_field_blocks(self):
        self.lock["ruling_summary"].update(
            {"total_findings": 4, "approved_fix": 1, "rejected_no_change": 2,
             "deferred": 1, "unresolved": 0,
             "deferred_items": [{"id": "SCA-014", "reason": "x",
                                 "approved_by": "PROJECT_GPT"}]})
        self.assertBlocked("DEFERRED_ITEM_BLOCKS_MISSING")

    def test_deferred_count_without_items_blocks(self):
        self.lock["ruling_summary"].update(
            {"total_findings": 4, "approved_fix": 1, "rejected_no_change": 2,
             "deferred": 1, "unresolved": 0, "deferred_items": []})
        self.assertBlocked("DEFERRED_ITEMS_MISSING")

    # ---------------------------------------------- 인자
    def test_missing_episode_arg_exits_2(self):
        r = subprocess.run([sys.executable, str(GATE), "--stage", "tts"],
                           capture_output=True, text=True, encoding="utf-8",
                           errors="replace", env={"PATH": ""}, timeout=120)
        self.assertEqual(r.returncode, 2)


if __name__ == "__main__":
    unittest.main(verbosity=2)

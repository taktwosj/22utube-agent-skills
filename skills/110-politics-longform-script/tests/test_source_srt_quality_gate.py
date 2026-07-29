#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SKILL = Path(__file__).resolve().parent.parent
GATE = SKILL / "scripts" / "gate_source_srt_quality.py"
PACKET = SKILL / "scripts" / "build_source_packet.py"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class TestSourceSrtQualityGate(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.episode = self.root / "episode"
        (self.episode / "00_source").mkdir(parents=True)
        (self.episode / "10_analysis" / "transcripts").mkdir(parents=True)
        (self.episode / "90_reports").mkdir(parents=True)
        self.registry = self.root / "registry.jsonl"
        record = {
            "schema_version": "politics_term_record_v1",
            "term_id": "pt_1111111111111111",
            "canonical": "검찰개혁",
            "normalized": "검찰개혁",
            "aliases": [],
            "asr_confusions": [
                {
                    "surface": "검찰개역",
                    "evidence": "fixture audio comparison",
                    "approved_by": "TEST_REVIEWER",
                    "approved_at": "2026-07-29T00:00:00+09:00",
                }
            ],
            "category": "legal_term",
            "status": "approved",
            "approval": {
                "approved_by": "TEST_REVIEWER",
                "approved_at": "2026-07-29T00:00:00+09:00",
                "evidence": "fixture canonical spelling review",
            },
            "rank": 1,
            "priority": 100,
            "evidence": {
                "source_id": "fixture",
                "document_frequency": 10,
                "total_mentions": 20,
                "title_mentions": 5,
                "corpus_score": 100,
            },
        }
        self.registry.write_text(
            json.dumps(record, ensure_ascii=False) + "\n", encoding="utf-8"
        )
        self.manifest = {
            "episode_id": "TEST",
            "sources": [
                {
                    "source_id": "S01",
                    "video_id": "v1",
                    "title": "검찰개혁",
                    "channel": "fixture",
                    "upload_date": "2026-07-29",
                    "url": "https://example.invalid/v1",
                    "duration_sec": 2,
                    "transcript_cue_count": 1,
                }
            ],
        }
        (self.episode / "00_source" / "source_manifest.json").write_text(
            json.dumps(self.manifest, ensure_ascii=False), encoding="utf-8"
        )
        self.srt = self.episode / "10_analysis" / "transcripts" / "S01.srt"
        self.srt.write_text(
            "1\n00:00:00,000 --> 00:00:02,000\n검찰개역을 추진합니다.\n",
            encoding="utf-8",
        )
        self.term_pack = self.episode / "10_analysis" / "episode_term_pack_v1.json"
        self.term_pack.write_text(
            json.dumps(
                {
                    "schema_version": "politics_episode_term_pack_v1",
                    "status": "PASS_110_EPISODE_TERMS_SELECTED",
                    "registry_sha256": sha(self.registry),
                    "terms": [
                        {
                            "term_id": record["term_id"],
                            "canonical": record["canonical"],
                        }
                    ],
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
        self.receipt = (
            self.episode / "90_reports" / "source_srt_review_receipt_v1.json"
        )
        self.candidates = (
            self.episode / "10_analysis" / "source_term_candidates_v1.json")
        self.write_candidate_queue()

    def tearDown(self):
        self.temporary.cleanup()

    def run_gate(self):
        return subprocess.run(
            [
                sys.executable,
                str(GATE),
                "--episode",
                str(self.episode),
                "--registry",
                str(self.registry),
            ],
            text=True,
            capture_output=True,
            check=False,
        )

    def write_receipt(self):
        self.receipt.write_text(
            json.dumps(
                {
                    "schema_version": "source_srt_review_receipt_v1",
                    "reviewed_by": "HUMAN_REVIEWER",
                    "reviewed_at": "2026-07-29T12:00:00+09:00",
                    "review_origin": "USER_AUDIO_REVIEW",
                    "recorded_by": "PROJECT_GPT",
                    "audio_compared": True,
                    "registry_sha256": sha(self.registry),
                    "term_pack_sha256": sha(self.term_pack),
                    "episode_candidates_sha256": sha(self.candidates),
                    "transcripts": {"S01": sha(self.srt)},
                    "decisions": [],
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

    def write_candidate_queue(self, candidates=None):
        self.candidates.write_text(json.dumps({
            "schema": "politics-longform-source-term-candidates.v1",
            "episode_id": self.manifest["episode_id"],
            "generated_by": "PROJECT_GPT",
            "transcripts": {"S01": sha(self.srt)},
            "candidates": candidates or [],
        }, ensure_ascii=False), encoding="utf-8")

    def test_known_confusion_blocks_before_source_packet(self):
        result = self.run_gate()
        self.assertEqual(result.returncode, 1)
        report = json.loads(
            (
                self.episode / "90_reports" / "source_srt_quality_report_v1.json"
            ).read_text(encoding="utf-8")
        )
        self.assertEqual(report["status"], "WAIT_SOURCE_ASR_REVIEW")
        self.assertEqual(report["issues"][0]["kind"], "APPROVED_ASR_CONFUSION")
        issue = report["issues"][0]
        self.assertEqual(issue["raw_asr"], "검찰개역을 추진합니다.")
        self.assertEqual(issue["candidate_text"], "검찰개혁을 추진합니다.")
        self.assertEqual(issue["audio_review_start_sec"], 0.0)
        self.assertEqual(issue["audio_review_end_sec"], 5.0)
        self.assertTrue(issue["reason"])
        self.assertEqual(issue["confidence"], "APPROVED_CONFUSION")
        packet = subprocess.run(
            [sys.executable, str(PACKET), "--episode", str(self.episode),
             "--registry", str(self.registry)],
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(packet.returncode, 1)
        self.assertIn("WAIT_SOURCE_ASR_REVIEW", packet.stderr)

    def test_project_gpt_first_seen_term_scan_is_mandatory(self):
        self.candidates.unlink()
        result = self.run_gate()
        self.assertEqual(result.returncode, 2)
        self.assertIn("first-seen term scan missing", result.stderr)

    def test_corrected_audio_reviewed_srt_passes_and_is_sha_bound(self):
        self.run_gate()
        self.srt.write_text(
            "1\n00:00:00,000 --> 00:00:02,000\n검찰개혁을 추진합니다.\n",
            encoding="utf-8",
        )
        self.write_candidate_queue()
        self.write_receipt()
        result = self.run_gate()
        self.assertEqual(result.returncode, 0, result.stderr)
        packet = subprocess.run(
            [sys.executable, str(PACKET), "--episode", str(self.episode),
             "--registry", str(self.registry)],
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(packet.returncode, 0, packet.stderr)
        payload = json.loads(
            (self.episode / "20_script" / "source_packet_v1.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(payload["lexicon"], ["검찰개혁"])
        self.assertEqual(
            payload["source_srt_review"]["status"],
            "PASS_110_SOURCE_SRT_REVIEWED",
        )

        self.srt.write_text(
            "1\n00:00:00,000 --> 00:00:02,000\n검찰 개혁을 추진합니다.\n",
            encoding="utf-8",
        )
        stale = subprocess.run(
            [sys.executable, str(PACKET), "--episode", str(self.episode),
             "--registry", str(self.registry)],
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(stale.returncode, 1)
        self.assertIn("BLOCKED_TRANSCRIPT_MISMATCH", stale.stderr)

    def test_receipt_must_prove_user_audio_review_origin(self):
        self.srt.write_text(
            "1\n00:00:00,000 --> 00:00:02,000\n검찰개혁을 추진합니다.\n",
            encoding="utf-8",
        )
        self.write_candidate_queue()
        self.write_receipt()
        payload = json.loads(self.receipt.read_text(encoding="utf-8"))
        payload["review_origin"] = "AUTOMATED_REVIEW"
        self.receipt.write_text(
            json.dumps(payload, ensure_ascii=False), encoding="utf-8")
        result = self.run_gate()
        self.assertEqual(result.returncode, 1)
        report = json.loads(
            (self.episode / "90_reports" / "source_srt_quality_report_v1.json")
            .read_text(encoding="utf-8"))
        self.assertIn(
            "review_origin must be USER_AUDIO_REVIEW",
            report["review_receipt"]["errors"],
        )

    def test_first_seen_term_is_reported_with_audio_window(self):
        self.srt.write_text(
            "1\n00:00:10,000 --> 00:00:12,000\n구분응선을 넘었습니다.\n",
            encoding="utf-8",
        )
        self.write_candidate_queue([{
                "source_id": "S01",
                "cue": 1,
                "raw_term": "구분응선",
                "proposed_term": "9부 능선",
                "confidence": "LOW",
                "reason": "FIRST_SEEN_POLITICAL_EXPRESSION",
            }])
        result = self.run_gate()
        self.assertEqual(result.returncode, 1)
        report = json.loads(
            (self.episode / "90_reports" / "source_srt_quality_report_v1.json")
            .read_text(encoding="utf-8"))
        issue = next(item for item in report["issues"]
                     if item["kind"] == "NEW_OR_UNKNOWN_TERM")
        self.assertEqual(issue["raw_asr"], "구분응선을 넘었습니다.")
        self.assertEqual(issue["candidate_text"], "9부 능선을 넘었습니다.")
        self.assertEqual(issue["audio_review_start_sec"], 7.0)
        self.assertEqual(issue["audio_review_end_sec"], 15.0)
        self.assertEqual(issue["confidence"], "LOW")


if __name__ == "__main__":
    unittest.main()

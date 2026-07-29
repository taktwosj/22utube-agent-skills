#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SKILL = Path(__file__).resolve().parent.parent
SCRIPTS = SKILL / "scripts"
REFERENCES = SKILL / "references"
sys.path.insert(0, str(SCRIPTS))

from politics_term_registry import RegistryError, load_registry  # noqa: E402


class TestPoliticsTermRegistry(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.registry_path = REFERENCES / "politics_terms_v1.jsonl"
        cls.records = load_registry(cls.registry_path)

    def test_initial_registry_has_5000_review_only_terms(self):
        self.assertEqual(len(self.records), 5000)
        self.assertEqual({item["status"] for item in self.records}, {"observed"})
        self.assertTrue(all(item["approval"] is None for item in self.records))
        self.assertTrue(all(not item["aliases"] for item in self.records))
        self.assertTrue(all(not item["asr_confusions"] for item in self.records))

    def test_registry_is_unique_and_deterministically_ranked(self):
        self.assertEqual(
            len({item["normalized"] for item in self.records}),
            len(self.records),
        )
        self.assertEqual(
            [item["rank"] for item in self.records],
            list(range(1, len(self.records) + 1)),
        )

    def test_preexisting_110_lexicon_is_not_lost(self):
        by_name = {item["canonical"]: item for item in self.records}
        required = {
            "보완수사권",
            "공소청",
            "중수청",
            "형사소송법",
            "직접수사권",
            "국가수사본부",
            "고위공직자범죄수사처",
            "합동수사본부",
        }
        self.assertTrue(required <= by_name.keys())
        self.assertTrue(all(by_name[name]["priority"] == 100 for name in required))

    def test_source_metadata_is_bound_to_registry(self):
        metadata = json.loads(
            (REFERENCES / "politics_term_sources_v1.json").read_text(
                encoding="utf-8"
            )
        )
        digest = hashlib.sha256(self.registry_path.read_bytes()).hexdigest()
        self.assertEqual(metadata["registry_sha256"], digest)
        self.assertEqual(metadata["record_count"], len(self.records))
        self.assertFalse(metadata["sources"][0]["article_text_retained"])
        self.assertFalse(
            metadata["authority_policy"]["silent_autocorrection"]
        )

    def test_duplicate_normalized_form_is_rejected(self):
        duplicate = dict(self.records[0])
        duplicate["term_id"] = "pt_" + "f" * 16
        duplicate["canonical"] = (
            duplicate["canonical"][0] + " " + duplicate["canonical"][1:]
        )
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "bad.jsonl"
            first = json.dumps(self.records[0], ensure_ascii=False)
            second = json.dumps(duplicate, ensure_ascii=False)
            path.write_text(first + "\n" + second + "\n", encoding="utf-8")
            with self.assertRaises(RegistryError):
                load_registry(path)

    def test_observed_term_cannot_carry_asr_confusion(self):
        record = json.loads(json.dumps(self.records[0], ensure_ascii=False))
        record["asr_confusions"] = [{
            "surface": "임의 오인식",
            "evidence": "fixture",
            "approved_by": "TEST",
            "approved_at": "2026-07-29T00:00:00+09:00",
        }]
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "bad.jsonl"
            path.write_text(
                json.dumps(record, ensure_ascii=False) + "\n", encoding="utf-8")
            with self.assertRaisesRegex(
                    RegistryError, "only approved terms may carry ASR confusion"):
                load_registry(path)

    def test_asr_confusion_requires_exact_reviewer_evidence(self):
        record = json.loads(json.dumps(self.records[0], ensure_ascii=False))
        record["status"] = "approved"
        record["approval"] = {
            "approved_by": "TEST",
            "approved_at": "2026-07-29T00:00:00+09:00",
            "evidence": "fixture canonical review",
        }
        record["asr_confusions"] = [{"surface": "임의 오인식"}]
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "bad.jsonl"
            path.write_text(
                json.dumps(record, ensure_ascii=False) + "\n", encoding="utf-8")
            with self.assertRaisesRegex(
                    RegistryError, "ASR confusion lacks approval evidence"):
                load_registry(path)

    def test_sqlite_index_round_trip(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "terms.sqlite"
            result = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPTS / "build_politics_term_index.py"),
                    "--registry",
                    str(self.registry_path),
                    "--output",
                    str(output),
                ],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            connection = sqlite3.connect(output)
            try:
                count = connection.execute("SELECT COUNT(*) FROM terms").fetchone()[0]
                approved = connection.execute(
                    "SELECT COUNT(*) FROM terms WHERE status='approved'"
                ).fetchone()[0]
            finally:
                connection.close()
            self.assertEqual(count, 5000)
            self.assertEqual(approved, 0)

    def test_article_candidate_builder_never_auto_approves(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "articles.csv"
            output = Path(tmp) / "candidates.jsonl"
            source.write_text(
                "title,content\n"
                '"검찰개혁 논의","국회에서 검찰개혁을 논의했다."\n'
                '"검찰개혁 추진","정부와 국회가 검찰개혁을 추진했다."\n'
                '"검찰개혁 쟁점","여야가 검찰개혁 쟁점을 다뤘다."\n',
                encoding="utf-8",
            )
            result = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPTS / "build_politics_term_candidates.py"),
                    "--input",
                    str(source),
                    "--source-id",
                    "fixture",
                    "--output",
                    str(output),
                    "--min-document-frequency",
                    "1",
                    "--limit",
                    "20",
                ],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            rows = [
                json.loads(line)
                for line in output.read_text(encoding="utf-8").splitlines()
            ]
            self.assertTrue(rows)
            self.assertEqual({row["status"] for row in rows}, {"observed"})
            self.assertTrue(all(not row["asr_confusions"] for row in rows))

    def test_explicit_review_can_approve_one_confusion_pair(self):
        target = next(
            row for row in self.records if row["canonical"] == "검찰개혁"
        )
        with tempfile.TemporaryDirectory() as tmp:
            review = Path(tmp) / "review.json"
            output = Path(tmp) / "reviewed.jsonl"
            review.write_text(
                json.dumps(
                    {
                        "schema_version": "politics_term_review_v1",
                        "reviewed_by": "HUMAN_REVIEWER",
                        "reviewed_at": "2026-07-29T12:00:00+09:00",
                        "decisions": [
                            {
                                "term_id": target["term_id"],
                                "canonical": target["canonical"],
                                "action": "approve",
                                "evidence": "표준 표기와 원본 음성을 확인함",
                                "asr_confusions": [
                                    {
                                        "surface": "검찰개역",
                                        "evidence": "S01 cue 12 실제 오인식",
                                    }
                                ],
                            }
                        ],
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            result = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPTS / "apply_politics_term_review.py"),
                    "--registry",
                    str(self.registry_path),
                    "--review",
                    str(review),
                    "--output",
                    str(output),
                ],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            updated = {
                row["canonical"]: row for row in load_registry(output)
            }["검찰개혁"]
            self.assertEqual(updated["status"], "approved")
            self.assertEqual(updated["approval"]["approved_by"], "HUMAN_REVIEWER")
            self.assertEqual(
                updated["asr_confusions"][0]["surface"], "검찰개역"
            )


if __name__ == "__main__":
    unittest.main()

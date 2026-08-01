from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SKILL = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SKILL / "scripts"))
from validate_clean_candidate import validate_clean_candidate
from validate_clean_visual import validate_clean_visual


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def make_video(path: Path, color: str) -> None:
    subprocess.run(
        [
            "ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-f", "lavfi",
            "-i", f"color=c={color}:s=16x16:d=0.4", "-r", "10", "-pix_fmt", "yuv420p", str(path),
        ],
        check=True,
    )


class CleanCandidateTests(unittest.TestCase):
    def _source_identity(self, root: Path, source: Path) -> Path:
        identity = root / "source_identity.json"
        identity.write_text(
            json.dumps(
                {
                    "schema_version": "source-identity-v1",
                    "episode_id": "candidate-fixture",
                    "source_id": "fixture",
                    "source_fingerprint": "fixture-fingerprint",
                    "media_path": source.name,
                    "media_sha256": sha256(source),
                }
            ),
            encoding="utf-8",
        )
        return identity

    def test_pass_is_technical_only_and_requires_user_visual_review(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "source.mp4"
            candidate = root / "candidate.mp4"
            evidence = root / "evidence"
            evidence.mkdir()
            make_video(source, "red")
            make_video(candidate, "blue")
            payload = validate_clean_candidate(
                self._source_identity(root, source), candidate, evidence / "candidate.json", evidence
            )
            self.assertEqual(payload["status"], "PASS")
            receipt = payload["evidence"]
            self.assertTrue(receipt["candidate_differs_from_source"])
            self.assertFalse(receipt["quality_evaluated"])
            self.assertTrue(receipt["user_visual_review_required"])
            self.assertEqual(receipt["final_clean_acceptance"], "NOT_DECIDED")

    def test_source_file_cannot_pass_as_clean_candidate(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "source.mp4"
            make_video(source, "red")
            payload = validate_clean_candidate(self._source_identity(root, source), source)
            self.assertEqual(payload["status"], "FAIL")
            self.assertIn("CLEAN_CANDIDATE_SAME_AS_SOURCE", [row["code"] for row in payload["errors"]])

    def test_final_clean_visual_validator_also_rejects_source_substitution(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "source.mp4"
            make_video(source, "red")
            identity = self._source_identity(root, source)
            handoff = root / "handoff.json"
            timeline = root / "timeline.json"
            handoff.write_text("{}", encoding="utf-8")
            timeline.write_text("{}", encoding="utf-8")
            design = root / "design.json"
            design.write_text(
                json.dumps(
                    {
                        "schema_version": "001short-design-lock-evidence-v1",
                        "status": "PASS",
                        "episode_id": "candidate-fixture",
                        "handoff_path": handoff.name,
                        "handoff_sha256": sha256(handoff),
                        "source_identity_path": identity.name,
                        "source_identity_sha256": sha256(identity),
                        "source_media_path": source.name,
                        "source_media_sha256": sha256(source),
                        "timeline_path": timeline.name,
                        "timeline_sha256": sha256(timeline),
                        "source_fingerprint": "fixture-fingerprint",
                    }
                ),
                encoding="utf-8",
            )
            manifest = root / "manifest.json"
            manifest.write_text(
                json.dumps(
                    {
                        "schema_version": "001short-clean-visual-manifest-v1",
                        "episode_id": "candidate-fixture",
                        "source_identity_path": identity.name,
                        "source_identity_sha256": sha256(identity),
                        "design_lock_evidence_path": design.name,
                        "design_lock_evidence_sha256": sha256(design),
                        "clean_source_path": source.name,
                        "clean_source_sha256": sha256(source),
                        "expected_duration_us": 400000,
                        "expected_width": 16,
                        "expected_height": 16,
                    }
                ),
                encoding="utf-8",
            )
            payload = validate_clean_visual(manifest, identity, design)
            self.assertEqual(payload["status"], "FAIL")
            self.assertIn("CLEAN_VISUAL_SAME_AS_SOURCE", [row["code"] for row in payload["errors"]])


if __name__ == "__main__":
    unittest.main()

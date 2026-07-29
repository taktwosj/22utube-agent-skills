#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SKILL = Path(__file__).resolve().parent.parent
SCRIPT = SKILL / "scripts" / "select_episode_terms.py"
INDEX_SCRIPT = SKILL / "scripts" / "build_politics_term_index.py"
REGISTRY = SKILL / "references" / "politics_terms_v1.jsonl"


class TestEpisodeTermSelection(unittest.TestCase):
    def make_episode(self, root: Path) -> Path:
        episode = root / "episode"
        source = episode / "00_source"
        source.mkdir(parents=True)
        manifest = {
            "episode_id": "TEST",
            "topic": "윤석열 대통령과 검찰 수사, 김민석의 대응",
            "sources": [
                {
                    "source_id": "S01",
                    "title": "윤석열 대통령 검찰 수사 논란",
                    "channel": "test",
                    "video_id": "v1",
                    "upload_date": "2026-07-29",
                    "url": "https://example.invalid/v1",
                    "duration_sec": 5,
                    "transcript_cue_count": 1,
                }
            ],
        }
        (source / "source_manifest.json").write_text(
            json.dumps(manifest, ensure_ascii=False), encoding="utf-8"
        )
        return episode

    def test_selects_only_terms_present_in_episode_context(self):
        with tempfile.TemporaryDirectory() as tmp:
            episode = self.make_episode(Path(tmp))
            index = subprocess.run(
                [
                    sys.executable,
                    str(INDEX_SCRIPT),
                    "--episode",
                    str(episode),
                    "--registry",
                    str(REGISTRY),
                ],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(index.returncode, 0, index.stderr)
            result = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "--episode",
                    str(episode),
                    "--registry",
                    str(REGISTRY),
                    "--limit",
                    "30",
                ],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            pack = json.loads(
                (episode / "10_analysis" / "episode_term_pack_v1.json").read_text(
                    encoding="utf-8"
                )
            )
            selected = {item["canonical"] for item in pack["terms"]}
            self.assertIn("윤석열", selected)
            self.assertIn("대통령", selected)
            self.assertIn("검찰", selected)
            self.assertIn("김민석", selected)
            self.assertNotIn("후쿠시마", selected)
            self.assertTrue(
                pack["selection_policy"]["observed_terms_are_not_correction_authority"]
            )
            self.assertEqual(pack["term_source"]["kind"], "sqlite_index")

    def test_imported_srt_alone_cannot_seed_term_pack(self):
        with tempfile.TemporaryDirectory() as tmp:
            episode = Path(tmp) / "episode"
            transcript_dir = episode / "10_analysis" / "transcripts"
            transcript_dir.mkdir(parents=True)
            (transcript_dir / "S01.srt").write_text(
                "1\n00:00:00,000 --> 00:00:01,000\n윤석열 대통령\n",
                encoding="utf-8",
            )
            result = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "--episode",
                    str(episode),
                    "--registry",
                    str(REGISTRY),
                ],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(result.returncode, 1)
            self.assertIn("WAIT_EPISODE_TERM_CONTEXT", result.stderr)


if __name__ == "__main__":
    unittest.main()

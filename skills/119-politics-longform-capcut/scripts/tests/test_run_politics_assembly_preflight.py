from __future__ import annotations

import hashlib
import json
import struct
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1]
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import run_politics_assembly_preflight as preflight


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


class PoliticsAssemblyPreflightTests(unittest.TestCase):
    def make_cards(self, root: Path) -> Path:
        raw = root / "raw.srt"
        display = root / "display.srt"
        raw.write_text(
            "1\n00:00:00,000 --> 00:00:02,000\n정책 방향은 같았다\n",
            encoding="utf-8",
        )
        display.write_text(raw.read_text(encoding="utf-8"), encoding="utf-8")
        cards = root / "episode_cards.json"
        cards.write_text(
            json.dumps(
                {
                    "schema": "politics-longform-episode-cards.v1",
                    "execution_mode": "ASSEMBLY_ONLY",
                    "episode_id": "PL_TEST",
                    "project_name": "PL_TEST_capcut",
                    "cta_like_subscribe": "OFF",
                    "cards": [
                        {
                            "card_id": "C001",
                            "card_type": "SOURCE_VIDEO",
                            "target_start_us": 0,
                            "target_duration_us": 2_000_000,
                            "source_start_us": 0,
                            "source_duration_us": 2_000_000,
                            "source_id": "S01",
                            "chapter_title": "챕터 1",
                            "chapter_label": "챕터 1",
                            "source_channel": "MBCNEWS",
                            "source_date": "2026.08.11",
                            "source_display_label": "MBC 뉴스",
                            "lower_mode": "SOURCE_TTS",
                            "source_srt_file": str(display),
                            "source_srt_sha256": digest(display),
                            "raw_transcript_path": str(raw),
                            "raw_transcript_sha256": digest(raw),
                            "display_srt_path": str(display),
                            "display_srt_sha256": digest(display),
                            "display_transform": [],
                            "cta_like_subscribe": "OFF",
                        }
                    ],
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
        return cards

    @staticmethod
    def write_png(path: Path, width: int, height: int) -> None:
        path.write_bytes(
            b"\x89PNG\r\n\x1a\n" + struct.pack(">I", 13) + b"IHDR" + struct.pack(">II", width, height) + b"\x00" * 17
        )

    def test_preflight_accepts_the_v8_root_1920_by_1080_card_raster(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            cards = self.make_cards(root)
            image = root / "V001.png"
            self.write_png(image, 1920, 1080)
            document = json.loads(cards.read_text(encoding="utf-8"))
            document["cards"].append(
                {
                    "card_id": "C002",
                    "card_type": "CHAPTER_CARD",
                    "chapter_title": "챕터 2",
                    "chapter_label": "챕터 2",
                    "target_start_us": 2_000_000,
                    "target_duration_us": 3_000_000,
                    "style_profile": "DEMOCRATIC_BLUE_INSET_CARD_V2",
                    "image_file": str(image),
                    "lower_mode": "NONE",
                }
            )
            cards.write_text(json.dumps(document, ensure_ascii=False), encoding="utf-8")

            result = preflight.run_preflight(cards, root / "report.json", root / "grid.md")

            self.assertEqual(result["status"], "PASS")

    def test_preflight_rejects_a_1280_by_720_card_raster(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            cards = self.make_cards(root)
            image = root / "V001.png"
            self.write_png(image, 1280, 720)
            document = json.loads(cards.read_text(encoding="utf-8"))
            document["cards"].append(
                {
                    "card_id": "C002",
                    "card_type": "CHAPTER_CARD",
                    "chapter_title": "챕터 2",
                    "chapter_label": "챕터 2",
                    "target_start_us": 2_000_000,
                    "target_duration_us": 3_000_000,
                    "style_profile": "DEMOCRATIC_BLUE_INSET_CARD_V2",
                    "image_file": str(image),
                    "lower_mode": "NONE",
                }
            )
            cards.write_text(json.dumps(document, ensure_ascii=False), encoding="utf-8")

            result = preflight.run_preflight(cards, root / "report.json", root / "grid.md")

            self.assertEqual(result["status"], "FAIL")
            self.assertIn("INSET_CARD_DIMENSION_INVALID", {row["code"] for row in result["findings"]})

    def test_preflight_fails_when_overlay_source_or_chapter_contract_is_missing(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            cards = self.make_cards(root)
            document = json.loads(cards.read_text(encoding="utf-8"))
            document["cards"][0].pop("chapter_label")
            document["cards"][0].pop("source_display_label")
            cards.write_text(json.dumps(document, ensure_ascii=False), encoding="utf-8")

            result = preflight.run_preflight(cards, root / "report.json", root / "grid.md")

            self.assertEqual(result["status"], "FAIL")
            self.assertIn(
                "CHAPTER_LABEL_REQUIRED",
                {row["code"] for row in result["findings"]},
            )
            self.assertIn(
                "SOURCE_DISPLAY_LABEL_REQUIRED",
                {row["code"] for row in result["findings"]},
            )

    def test_preflight_binds_cards_and_inputs(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            cards = self.make_cards(root)
            report = root / "preflight.json"
            grid = root / "grid.md"
            result = preflight.run_preflight(cards, report, grid)
            self.assertEqual(result["status"], "PASS")
            self.assertTrue(grid.is_file())
            verified = preflight.verify_preflight_report(cards, report)
            self.assertEqual(verified["status"], "PASS")

    def test_report_uses_portable_references(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            cards = self.make_cards(root)
            report = root / "reports" / "preflight.json"
            grid = root / "USER_FINAL_ASSEMBLY_GRID.md"
            result = preflight.run_preflight(cards, report, grid)
            serialized = json.dumps(result, ensure_ascii=False)
            self.assertNotIn(str(root.resolve()), serialized)
            self.assertEqual(result["cards_file"], "episode_cards.json")
            self.assertEqual(result["grid"]["relative_path"], "USER_FINAL_ASSEMBLY_GRID.md")
            self.assertTrue(all("path" not in row for row in result["inputs"]))

    def test_modified_srt_invalidates_pass_report(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            cards = self.make_cards(root)
            report = root / "preflight.json"
            grid = root / "grid.md"
            preflight.run_preflight(cards, report, grid)
            document = json.loads(cards.read_text(encoding="utf-8"))
            srt = Path(document["cards"][0]["source_srt_file"])
            srt.write_text(srt.read_text(encoding="utf-8") + "\n", encoding="utf-8")
            with self.assertRaisesRegex(RuntimeError, "ASSEMBLY_PREFLIGHT_INPUT_SHA_MISMATCH"):
                preflight.verify_preflight_report(cards, report)


if __name__ == "__main__":
    unittest.main()

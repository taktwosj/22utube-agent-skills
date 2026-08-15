import subprocess
import sys
import tempfile
import unittest
import json
import hashlib
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = SKILL_ROOT / "scripts" / "validate_capcut_grids.py"
ORIGINAL = SKILL_ROOT / "tests" / "fixtures" / "original_grid_8.pass.md"
URAKKAI = SKILL_ROOT / "tests" / "fixtures" / "urakkai_grid_8.pass.md"
if str(SKILL_ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(SKILL_ROOT / "scripts"))

import build_episode_capcut as builder
import validate_capcut_grids as grid_harness


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _two_column_grid(kind: str, *, declare_mixed: bool, target_mismatch: bool = False) -> str:
    if kind == "original":
        header = "| 레이어 \\ 원본 시간 | B01 0.0–1.0 | B02 1.0–2.0 |"
        transcript = """## 원본 5분류 대본

### B01 0.0–1.0
(상황설명) 첫 장면. 화면 OCR: 없음
\"화자발언\" \"hello\"
<나레이션> 없음
TTS화자발언 없음
TTS나레이션 없음

### B02 1.0–2.0
(상황설명) 둘째 장면. 화면 OCR: 없음
\"화자발언\" \"there\"
<나레이션> 없음
TTS화자발언 없음
TTS나레이션 없음

"""
    else:
        first_end = "0.9" if target_mismatch else "1.0"
        header = f"| 레이어 \\ 목표 시간 | V01 0.0–{first_end} B02 | V02 1.0–2.0 B01 |"
        transcript = ""
    mixed_a9 = ("나레이션", "비움") if declare_mixed else ("비움", "비움")
    rows = (
        ("T1", "title", "title"),
        ("T2", "subtitle", "subtitle"),
        ("A9_TEXT", *mixed_a9),
        ("A10_TEXT_YELLOW", "비움", "there"),
        ("A10_TEXT_WHITE", "hello", "비움"),
        ("STATE_LASER", "비움", "비움"),
        ("STATE_GLITCH", "비움", "비움"),
        ("STATE_FLICKER", "비움", "비움"),
        ("SCREEN_WHITE", "템플릿 유지", "템플릿 유지"),
        ("SCREEN_EFFECT", "W Flash", "W Flash"),
        ("VIDEO", "장면2", "장면1"),
        ("A9", *mixed_a9),
        ("A10", "분리 음성", "분리 음성"),
        ("A11", "비움", "비움"),
        ("A12_RESERVED_EMPTY", "비움", "비움"),
    )
    return transcript + "\n".join((header, "|---|---|---|", *("| " + " | ".join(row) + " |" for row in rows))) + "\n"


def _semantic_config(root: Path, *, declare_mixed: bool, target_mismatch: bool = False) -> dict:
    episode = root / "episode"
    script_root = episode / "20_script"
    script_root.mkdir(parents=True)
    (script_root / "original-capcut-grid.md").write_text(
        _two_column_grid("original", declare_mixed=declare_mixed), encoding="utf-8"
    )
    (script_root / "urakkai-capcut-grid.md").write_text(
        _two_column_grid("urakkai", declare_mixed=declare_mixed, target_mismatch=target_mismatch),
        encoding="utf-8",
    )
    rows = [
        {"segment_id": "T1", "role": "T1", "start": 0, "duration": 2_000_000, "text": "title"},
        {"segment_id": "T2", "role": "T2", "start": 0, "duration": 2_000_000, "text": "subtitle"},
        {"segment_id": "AW", "role": "A10_TEXT", "start": 0, "duration": 1_000_000, "text": "hello", "color_role": "WHITE"},
        {"segment_id": "AY", "role": "A10_TEXT", "start": 1_000_000, "duration": 1_000_000, "text": "there", "color_role": "YELLOW"},
        {"segment_id": "A10-1", "role": "A10", "start": 0, "duration": 1_000_000},
        {"segment_id": "A10-2", "role": "A10", "start": 1_000_000, "duration": 1_000_000},
        {"segment_id": "A9", "role": "A9", "start": 0, "duration": 1_000_000, "text": "나레이션", "cue_id": "A9T"},
        {"segment_id": "A9T", "role": "A9_TEXT", "start": 0, "duration": 1_000_000, "text": "나레이션", "cue_id": "A9T"},
    ]
    timeline = episode / "approved_timeline.json"
    _write_json(timeline, {"segments": rows})
    manifest = episode / "build_manifest.json"
    _write_json(manifest, {
        "urakkai": {"video_clips": [
            {"clip_id": "V2", "source_range_us": [1_000_000, 2_000_000], "target_range_us": [0, 1_000_000]},
            {"clip_id": "V1", "source_range_us": [0, 1_000_000], "target_range_us": [1_000_000, 2_000_000]},
        ]},
        "source_audio": [
            {"clip_id": "V2", "target_range_us": [0, 1_000_000], "mode": "duck"},
            {"clip_id": "V1", "target_range_us": [1_000_000, 2_000_000], "mode": "on"},
        ],
    })
    caption = episode / "caption_lock.json"
    _write_json(caption, {"cues": [
        {"cue_id": "A9T", "start_us": 0, "end_us": 1_000_000, "text": "나레이션", "layer": "A9_TEXT"},
        {"cue_id": "AW", "start_us": 0, "end_us": 1_000_000, "text": "hello", "layer": "A10_TEXT"},
        {"cue_id": "AY", "start_us": 1_000_000, "end_us": 2_000_000, "text": "there", "layer": "A10_TEXT"},
    ]})
    audio = episode / "audio_lock.json"
    _write_json(audio, {"role_files": [{"role": "A9"}, {"role": "A10"}]})
    evidence = episode / "design_lock_evidence.json"
    _write_json(evidence, {"status": "PASS"})
    state = episode / "90_workflow" / "state.json"
    _write_json(state, {
        "approved_timeline_path": str(timeline),
        "approved_timeline_sha256": _sha(timeline),
        "build_manifest_path": str(manifest),
        "build_manifest_sha256": _sha(manifest),
        "design_lock_evidence_path": str(evidence),
        "design_lock_evidence_sha256": _sha(evidence),
        "audio_lock_path": str(audio),
        "audio_lock_sha256": _sha(audio),
        "caption_lock_path": str(caption),
        "caption_lock_sha256": _sha(caption),
    })
    return {
        "episode_root": str(episode),
        "approved_timeline_path": str(timeline),
        "build_manifest_path": str(manifest),
        "design_lock_evidence_path": str(evidence),
        "state_path": str(state),
        "work_root": str(root / "work"),
        "local_capcut_root": str(root / "capcut"),
        "project_name": "must-not-exist",
    }


class CapCutGridHarnessTest(unittest.TestCase):
    def test_builder_uses_state_bound_original_contract_and_stops_before_writes(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            config = _semantic_config(root, declare_mixed=True)
            episode = Path(config["episode_root"])
            state_path = Path(config["state_path"])
            state = json.loads(state_path.read_text(encoding="utf-8"))
            state.update({
                "episode_id": "EP",
                "original_analysis_contract_version": "001short-original-source-transcript-v1",
            })
            _write_json(state_path, state)
            input_root = episode / "00_input"
            input_root.mkdir()
            _write_json(input_root / "source_intake_receipt.json", {
                "schema_version": "001short-source-intake-receipt-v2",
                "episode_id": "EP",
                "original_analysis_contract_version": "001short-original-source-transcript-v1",
            })
            with self.assertRaisesRegex(ValueError, "ORIGINAL_SOURCE_EVIDENCE_REQUIRED"):
                builder.build_episode(config)
            self.assertFalse((root / "work").exists())
            self.assertFalse((root / "capcut").exists())

    def test_cli_original_only_keeps_unversioned_legacy_fixture_compatible(self):
        completed = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "--original",
                str(ORIGINAL),
                "--original-only",
            ],
            text=True,
            encoding="utf-8",
            capture_output=True,
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        self.assertEqual(json.loads(completed.stdout), {"status": "PASS", "errors": []})

    def test_cli_emits_original_then_urakkai_complete_tables(self):
        completed = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "--original",
                str(ORIGINAL),
                "--urakkai",
                str(URAKKAI),
                "--emit-report",
            ],
            text=True,
            encoding="utf-8",
            capture_output=True,
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        self.assertLess(completed.stdout.index("원본표"), completed.stdout.index("우라까이표"))
        self.assertEqual(completed.stdout.count("| A12_RESERVED_EMPTY |"), 2)
        self.assertIn("검증: 원본표 8개 열, 우라까이표 8개 열, 15개 레이어, 빈 셀 없음 — PASS", completed.stdout)

    def test_rejects_implicit_empty_unverified_misordered_and_invalid_a12_cells(self):
        original_text = ORIGINAL.read_text(encoding="utf-8")
        cases = {
            "empty": (
                original_text.replace("| A9_TEXT | 비움 |", "| A9_TEXT |  |", 1),
                "TABLE_EMPTY_CELL_FORBIDDEN",
            ),
            "dash": (
                original_text.replace("| A9_TEXT | 비움 |", "| A9_TEXT | — |", 1),
                "TABLE_EMPTY_CELL_FORBIDDEN",
            ),
            "unverified": (
                original_text.replace("| A9_TEXT | 비움 |", "| A9_TEXT | 미확인 |", 1),
                "TABLE_UNVERIFIED_CELL",
            ),
            "row_order": (
                original_text.replace("| T1 |", "| TEMP |", 1)
                .replace("| T2 |", "| T1 |", 1)
                .replace("| TEMP |", "| T2 |", 1),
                "TABLE_ROW_ORDER_INVALID",
            ),
            "a12": (
                original_text.replace(
                    "| A12_RESERVED_EMPTY | 비움 |",
                    "| A12_RESERVED_EMPTY | 없음 |",
                    1,
                ),
                "A12_RESERVED_EMPTY",
            ),
            "header": (
                original_text.replace("| B01 00.0–03.9 |", "| V01 00.0–03.9 |", 1),
                "TABLE_HEADER_INVALID",
            ),
        }
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            for name, (text, expected) in cases.items():
                with self.subTest(name=name):
                    path = root / f"{name}.md"
                    path.write_text(text, encoding="utf-8")
                    result = grid_harness.validate_grids(path, URAKKAI)
                    self.assertEqual(result["status"], "FAIL")
                    self.assertIn(expected, {row["code"] for row in result["errors"]})

    def test_rejects_explicit_placeholder_markers_case_insensitively(self):
        original_text = ORIGINAL.read_text(encoding="utf-8")
        markers = ("PLACEHOLDER", "placeholder", "TODO", "tbd", "TBC", "N/A", "[장면 입력]", "<fill me>", "{caption}")
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            for index, marker in enumerate(markers):
                with self.subTest(marker=marker):
                    path = root / f"placeholder-{index}.md"
                    path.write_text(
                        original_text.replace("| A9_TEXT | 비움 |", f"| A9_TEXT | {marker} |", 1),
                        encoding="utf-8",
                    )
                    result = grid_harness.validate_grids(path, URAKKAI)
                    self.assertIn(
                        "TABLE_PLACEHOLDER_FORBIDDEN",
                        {row["code"] for row in result["errors"]},
                    )

    def test_rejects_a_sixteenth_or_additional_row(self):
        original_text = ORIGINAL.read_text(encoding="utf-8")
        extra = "| EXTRA | " + " | ".join("비움" for _ in range(8)) + " |\n"
        path_text = original_text.rstrip() + "\n" + extra
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "extra-row.md"
            path.write_text(path_text, encoding="utf-8")
            result = grid_harness.validate_grids(path, URAKKAI)
        self.assertIn("TABLE_ROW_COUNT_INVALID", {row["code"] for row in result["errors"]})

    def test_rejects_more_than_two_lines_or_more_than_15_characters(self):
        original_text = ORIGINAL.read_text(encoding="utf-8")
        cases = {
            "too_many_lines": original_text.replace(
                "| A9_TEXT | 비움 |",
                "| A9_TEXT | 첫째<br>둘째<br>셋째 |",
                1,
            ),
            "too_long": original_text.replace(
                "| STATE_LASER | 케이크도 이상 |",
                "| STATE_LASER | 열여섯글자를넘는상황설명문장입니다 |",
                1,
            ),
        }
        expected = {
            "too_many_lines": "TABLE_TEXT_TOO_MANY_LINES",
            "too_long": "TABLE_TEXT_LINE_TOO_LONG",
        }
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            for name, text in cases.items():
                with self.subTest(name=name):
                    path = root / f"{name}.md"
                    path.write_text(text, encoding="utf-8")
                    result = grid_harness.validate_grids(path, URAKKAI)
                    self.assertIn(expected[name], {row["code"] for row in result["errors"]})

    def test_builder_grid_gate_fails_before_work_or_target_creation(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            episode = root / "episode"
            script_root = episode / "20_script"
            script_root.mkdir(parents=True)
            invalid = ORIGINAL.read_text(encoding="utf-8").replace(
                "| A9_TEXT | 비움 |",
                "| A9_TEXT |  |",
                1,
            )
            (script_root / "original-capcut-grid.md").write_text(invalid, encoding="utf-8")
            (script_root / "urakkai-capcut-grid.md").write_text(
                URAKKAI.read_text(encoding="utf-8"),
                encoding="utf-8",
            )
            work_root = root / "work"
            local_root = root / "capcut"
            config = {
                "episode_root": str(episode),
                "work_root": str(work_root),
                "local_capcut_root": str(local_root),
                "project_name": "must-not-exist",
            }
            with self.assertRaisesRegex(ValueError, "TABLE_EMPTY_CELL_FORBIDDEN"):
                builder.build_episode(config)
            self.assertFalse(work_root.exists())
            self.assertFalse(local_root.exists())

    def test_external_grid_override_cannot_bypass_missing_canonical_grids(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            episode = root / "episode"
            episode.mkdir()
            work_root = root / "work"
            local_root = root / "capcut"
            config = {
                "episode_root": str(episode),
                "work_root": str(work_root),
                "local_capcut_root": str(local_root),
                "project_name": "must-not-exist",
                "original_grid_path": str(ORIGINAL),
                "urakkai_grid_path": str(URAKKAI),
            }
            with self.assertRaisesRegex(ValueError, "TABLE_PATH_OVERRIDE_FORBIDDEN"):
                builder.build_episode(config)
            self.assertFalse(work_root.exists())
            self.assertFalse(local_root.exists())

    def test_mixed_a9_actual_cannot_pass_when_urakkai_declares_a9_empty(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            config = _semantic_config(root, declare_mixed=False)
            with self.assertRaisesRegex(ValueError, "TABLE_ROLE_ACTUAL_PRESENT_DECLARED_EMPTY"):
                builder.build_episode(config)
            self.assertFalse((root / "work").exists())
            self.assertFalse((root / "capcut").exists())

    def test_source_target_range_mismatch_fails_before_writes(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            config = _semantic_config(root, declare_mixed=True, target_mismatch=True)
            with self.assertRaisesRegex(ValueError, "TABLE_VIDEO_RANGE_MISMATCH"):
                builder.build_episode(config)
            self.assertFalse((root / "work").exists())
            self.assertFalse((root / "capcut").exists())

    def test_populated_role_cannot_pass_when_locked_timeline_has_no_role(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            config = _semantic_config(root, declare_mixed=True)
            timeline = Path(config["approved_timeline_path"])
            payload = json.loads(timeline.read_text(encoding="utf-8"))
            payload["segments"] = [
                row for row in payload["segments"] if row.get("role") not in {"A9", "A9_TEXT"}
            ]
            _write_json(timeline, payload)
            state_path = Path(config["state_path"])
            state = json.loads(state_path.read_text(encoding="utf-8"))
            state["approved_timeline_sha256"] = _sha(timeline)
            _write_json(state_path, state)
            with self.assertRaisesRegex(ValueError, "TABLE_ROLE_DECLARED_POPULATED_ACTUAL_MISSING"):
                builder.build_episode(config)
            self.assertFalse((root / "work").exists())
            self.assertFalse((root / "capcut").exists())

    def test_wrong_a9_and_a10_grid_text_fails_before_writes(self):
        replacements = (
            ("| A9_TEXT | 나레이션 |", "| A9_TEXT | WRONG |"),
            ("| A10_TEXT_WHITE | hello |", "| A10_TEXT_WHITE | WRONG |"),
        )
        for old, new in replacements:
            with self.subTest(role=old.split("|")[1].strip()), tempfile.TemporaryDirectory() as td:
                root = Path(td)
                config = _semantic_config(root, declare_mixed=True)
                grid = root / "episode" / "20_script" / "urakkai-capcut-grid.md"
                grid.write_text(grid.read_text(encoding="utf-8").replace(old, new, 1), encoding="utf-8")
                with self.assertRaisesRegex(ValueError, "TABLE_CELL_TEXT_MISMATCH"):
                    builder.build_episode(config)
                self.assertFalse((root / "work").exists())
                self.assertFalse((root / "capcut").exists())

    def test_wrong_caption_lock_text_or_cue_id_fails_before_writes(self):
        for field, value in (("text", "WRONG"), ("cue_id", "WRONG")):
            with self.subTest(field=field), tempfile.TemporaryDirectory() as td:
                root = Path(td)
                config = _semantic_config(root, declare_mixed=True)
                state_path = Path(config["state_path"])
                state = json.loads(state_path.read_text(encoding="utf-8"))
                caption = Path(state["caption_lock_path"])
                payload = json.loads(caption.read_text(encoding="utf-8"))
                payload["cues"][0][field] = value
                _write_json(caption, payload)
                state["caption_lock_sha256"] = _sha(caption)
                _write_json(state_path, state)
                with self.assertRaisesRegex(ValueError, "TABLE_CAPTION_TEXT_MISMATCH"):
                    builder.build_episode(config)
                self.assertFalse((root / "work").exists())
                self.assertFalse((root / "capcut").exists())

    def test_extra_caption_lock_cue_fails_before_writes(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            config = _semantic_config(root, declare_mixed=True)
            state_path = Path(config["state_path"])
            state = json.loads(state_path.read_text(encoding="utf-8"))
            caption = Path(state["caption_lock_path"])
            payload = json.loads(caption.read_text(encoding="utf-8"))
            payload["schema_version"] = "001short-caption-lock-v2"
            payload["cues"].append({
                "cue_id": "EXTRA", "start_us": 0, "end_us": 500_000,
                "text": "extra", "layer": "STATE",
            })
            _write_json(caption, payload)
            timeline = Path(config["approved_timeline_path"])
            timeline_payload = json.loads(timeline.read_text(encoding="utf-8"))
            for row in timeline_payload["segments"]:
                if row.get("segment_id") in {"AW", "AY"}:
                    row["cue_id"] = row["segment_id"]
            _write_json(timeline, timeline_payload)
            state["approved_timeline_sha256"] = _sha(timeline)
            state["caption_lock_sha256"] = _sha(caption)
            _write_json(state_path, state)
            with self.assertRaisesRegex(ValueError, "CAPTION_LOCK_CUE_UNASSEMBLED"):
                builder.build_episode(config)
            self.assertFalse((root / "work").exists())
            self.assertFalse((root / "capcut").exists())

    def test_missing_a9_audio_role_fails_before_writes(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            config = _semantic_config(root, declare_mixed=True)
            state_path = Path(config["state_path"])
            state = json.loads(state_path.read_text(encoding="utf-8"))
            audio = Path(state["audio_lock_path"])
            _write_json(audio, {"role_files": [{"role": "A10"}]})
            state["audio_lock_sha256"] = _sha(audio)
            _write_json(state_path, state)
            with self.assertRaisesRegex(ValueError, "TABLE_AUDIO_LOCK_ROLE_MISSING.*A9"):
                builder.build_episode(config)
            self.assertFalse((root / "work").exists())
            self.assertFalse((root / "capcut").exists())

    def test_state_bound_manifest_sha_drift_fails_before_writes(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            config = _semantic_config(root, declare_mixed=True)
            manifest = Path(config["build_manifest_path"])
            manifest.write_text(manifest.read_text(encoding="utf-8") + "\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "TABLE_STATE_LOCK_SHA_MISMATCH.*build_manifest"):
                builder.build_episode(config)
            self.assertFalse((root / "work").exists())
            self.assertFalse((root / "capcut").exists())


if __name__ == "__main__":
    unittest.main()

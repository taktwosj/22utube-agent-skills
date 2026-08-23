import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[1]
if str(SKILL_ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(SKILL_ROOT / "scripts"))

import build_episode_locks as generator  # noqa: E402
import validate_executable_protocol  # noqa: E402
from schema_runtime import validate_schema  # noqa: E402


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _silent_wav(path: Path, duration_us: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        ["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i", "anullsrc=r=44100:cl=mono",
         "-t", f"{duration_us / 1_000_000:.6f}", "-c:a", "pcm_s16le", str(path)],
        check=True,
    )


def _black_mp4(path: Path, duration_us: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        ["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i", "color=c=black:s=64x64:r=30",
         "-t", f"{duration_us / 1_000_000:.6f}", "-pix_fmt", "yuv420p", str(path)],
        check=True,
    )


class EpisodeLocksGeneratorTest(unittest.TestCase):
    """The generator is the single place segment boundaries are transcribed from."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name) / "260101_fixture_abcdefghijk"
        # URAKKAI requires a real structural reorder, so V01 takes the second beat.
        self.v_rows = [
            ["V01", "B02", 0, 1_400_000, 1_400_000, 2_800_000],
            ["V02", "B01", 1_400_000, 3_000_000, 0, 1_600_000],
        ]
        self.duration = 3_000_000

        _black_mp4(self.root / "00_input" / "source.mp4", self.duration)
        _black_mp4(self.root / "40_assets_used" / "clean_source.mp4", self.duration)
        _silent_wav(self.root / "30_audio_srt" / "tts" / "V01_fit.wav", 1_400_000)
        _silent_wav(self.root / "30_audio_srt" / "tts" / "V02_fit.wav", 1_600_000)

        source_sha = _sha(self.root / "00_input" / "source.mp4")
        clean_sha = _sha(self.root / "40_assets_used" / "clean_source.mp4")
        _write_json(self.root / "00_input" / "source_identity.json", {
            "schema_version": "source-identity-v1", "episode_id": self.root.name,
            "source_id": "abcdefghijk", "source_fingerprint": source_sha,
            "media_path": "source.mp4", "media_sha256": source_sha,
            "source_locator": "https://example.invalid/shorts/abcdefghijk",
        })
        _write_json(self.root / "00_input" / "source_intake_receipt.json",
                    {"local_media_duration_us": self.duration})
        _write_json(self.root / "40_assets_used" / "vmake_final_download_evidence.json", {
            "provider": "vmake", "run_id": "run-1", "job_id": "job-1",
            "uploaded_source_sha256": source_sha, "downloaded_output_sha256": clean_sha,
            "final_download": True,
        })
        _write_json(self.root / "30_audio_srt" / "audio_lock.json", {"schema_version": "x"})
        (self.root / "20_script" / "original-capcut-grid.md").parent.mkdir(parents=True, exist_ok=True)
        (self.root / "20_script" / "original-capcut-grid.md").write_text("original", encoding="utf-8")
        (self.root / "20_script" / "urakkai-capcut-grid.md").write_text("urakkai", encoding="utf-8")

        _write_json(self.root / "20_script" / "v_plan.json", {
            "V": self.v_rows, "DUR": self.duration, "type": "2",
            "audio_policy": "TTS_ONLY_MUTE_SOURCE", "execution_strategy": "full_tts",
            "audio_source": "SILENCE", "T1": "제목 하나", "T2": "제목 둘",
            "cues": [
                ["V01", "A9_V01", "첫 줄", 1_400_000, 0, 1_400_000, "V01_fit.wav"],
                ["V02", "A9_V02", "둘째<br>줄", 1_600_000, 1_400_000, 3_000_000, "V02_fit.wav"],
            ],
        })
        segments = [
            {"segment_id": row[0], "role": "VIDEO", "start": row[2], "duration": row[3] - row[2],
             "source_ref": "abcdefghijk", "source_beat_id": row[1],
             "source_range_us": [row[4], row[5]], "target_range_us": [row[2], row[3]],
             "volume": 0, "timeline_order": index}
            for index, row in enumerate(self.v_rows, start=1)
        ]
        for offset, (role, suffix) in enumerate((("A9", ""), ("A9_TEXT", "_TEXT"))):
            for index, row in enumerate(self.v_rows):
                segments.append({
                    "segment_id": f"A9_{row[0]}{suffix}", "role": role, "start": row[2],
                    "duration": row[3] - row[2], "source_ref": "abcdefghijk",
                    "text": "첫 줄" if row[0] == "V01" else "둘째\n줄",
                    "content_type": "TTS", "cue_id": f"A9_{row[0]}",
                    "timeline_order": 10 + offset * 10 + index,
                })
        _write_json(self.root / "20_script" / "approved_timeline.json", {
            "schema_version": "001short-approved-timeline-v2", "episode_id": self.root.name,
            "source_fingerprint": source_sha, "production_mode": "URAKKAI",
            "audio_policy": "TTS_ONLY_MUTE_SOURCE", "execution_strategy": "full_tts",
            "segments": segments,
        })
        self.template_zip = Path(self._tmp.name) / "template.zip"
        self.template_zip.write_bytes(b"template")

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def _generate(self) -> dict:
        return generator.generate(
            episode_root=self.root,
            capcut_root=Path(self._tmp.name) / "capcut",
            workspace_root=Path(self._tmp.name) / "workspace",
            template_zip=self.template_zip,
            root_profile="test_profile",
            root_contract_path="contract.json",
            work_root=Path(self._tmp.name) / "work",
        )

    def _make_caption_only(self) -> None:
        """Rewrite the fixture as a type 1 episode: STATE captions, no voice at all."""
        source_sha = _sha(self.root / "00_input" / "source.mp4")
        _write_json(self.root / "20_script" / "v_plan.json", {
            "V": self.v_rows, "DUR": self.duration, "type": "1",
            "audio_policy": "CAPTION_ONLY_MUTE_SOURCE", "execution_strategy": "caption_only",
            "audio_source": "SILENCE", "T1": "제목 하나", "T2": "제목 둘", "cues": [],
        })
        segments = [
            {"segment_id": row[0], "role": "VIDEO", "start": row[2], "duration": row[3] - row[2],
             "source_ref": "abcdefghijk", "source_beat_id": row[1],
             "source_range_us": [row[4], row[5]], "target_range_us": [row[2], row[3]],
             "volume": 0, "timeline_order": index}
            for index, row in enumerate(self.v_rows, start=1)
        ]
        for index, row in enumerate(self.v_rows):
            segments.append({
                "segment_id": f"STATE_{row[0]}", "role": "STATE", "start": row[2],
                "duration": row[3] - row[2], "source_ref": "abcdefghijk",
                "text": "상황 하나" if row[0] == "V01" else "상황 둘",
                "content_type": "STATE", "cue_id": f"STATE_{row[0]}",
                "timeline_order": 20 + index,
            })
        _write_json(self.root / "20_script" / "approved_timeline.json", {
            "schema_version": "001short-approved-timeline-v2", "episode_id": self.root.name,
            "source_fingerprint": source_sha, "production_mode": "URAKKAI",
            "audio_policy": "CAPTION_ONLY_MUTE_SOURCE", "execution_strategy": "caption_only",
            "segments": segments,
        })

    def _make_original_audio_caption(self) -> None:
        """Rewrite the fixture as a type 3 episode: the original speaker audio rides
        A10 straight from the source, with its own captions on A10_TEXT and no TTS.
        SOURCE_ORDER_CLEAN_AUDIO is the one A10 policy that needs no Demucs stem."""
        source_sha = _sha(self.root / "00_input" / "source.mp4")
        _write_json(self.root / "20_script" / "v_plan.json", {
            "V": self.v_rows, "DUR": self.duration, "type": "3",
            "audio_policy": "SOURCE_ORDER_CLEAN_AUDIO",
            "execution_strategy": "original_audio_caption",
            "audio_source": "SOURCE_CLIP", "T1": "제목 하나", "T2": "제목 둘", "cues": [],
        })
        segments = [
            {"segment_id": row[0], "role": "VIDEO", "start": row[2], "duration": row[3] - row[2],
             "source_ref": "abcdefghijk", "source_beat_id": row[1],
             "source_range_us": [row[4], row[5]], "target_range_us": [row[2], row[3]],
             "volume": 0, "timeline_order": index}
            for index, row in enumerate(self.v_rows, start=1)
        ]
        for index, row in enumerate(self.v_rows, start=1):
            segments.append({
                "segment_id": f"A10_{row[0]}", "role": "A10", "start": row[2],
                "duration": row[3] - row[2], "source_ref": "abcdefghijk",
                "source_range_us": [row[4], row[5]], "target_range_us": [row[2], row[3]],
                "volume": 1, "timeline_order": 50 + index,
            })
            # validate_design_lock rejects an A10_TEXT row without SPEAKER content,
            # a caption_role, an assigned speaker and the colour that speaker maps
            # to, so a fixture missing them would never survive a real build.
            segments.append({
                "segment_id": f"A10_{row[0]}_TEXT", "role": "A10_TEXT", "start": row[2],
                "duration": row[3] - row[2], "source_ref": "abcdefghijk",
                "text": "화자 하나" if row[0] == "V01" else "화자 둘",
                "content_type": "SPEAKER", "caption_role": "A10_TEXT",
                "speaker_id": "SPK_A", "color_role": "WHITE",
                "cue_id": f"A10_{row[0]}", "timeline_order": 60 + index,
            })
        _write_json(self.root / "20_script" / "approved_timeline.json", {
            "schema_version": "001short-approved-timeline-v2", "episode_id": self.root.name,
            "source_fingerprint": source_sha, "production_mode": "URAKKAI",
            "audio_policy": "SOURCE_ORDER_CLEAN_AUDIO",
            "execution_strategy": "original_audio_caption",
            "primary_speaker_id": "SPK_A",
            "segments": segments,
        })

    def test_type_three_keeps_the_source_audio_lane_audible(self) -> None:
        """Every source_audio row used to be hardcoded mute, so build_episode_capcut
        emitted no A10 segment at all and type 3 rendered a silent draft."""
        self._make_original_audio_caption()
        self.assertEqual(self._generate()["status"], "PASS")
        manifest = json.loads(
            (self.root / "50_capcut_project" / "build_manifest.json").read_text(encoding="utf-8"))
        self.assertEqual({row["mode"] for row in manifest["source_audio"]}, {"on"})
        for row, v_row in zip(manifest["source_audio"], self.v_rows):
            # SOURCE_CLIP plays the untouched source, so CapCut has to seek to the
            # real original span rather than reusing the target range.
            self.assertEqual(row["capcut_source_range_us"], [v_row[4], v_row[5]])

    def test_type_three_emits_one_a10_placement_per_segment(self) -> None:
        """The urakkai table declares A10 populated; without these placements the
        grid harness fails TABLE_ROLE_DECLARED_POPULATED_ACTUAL_MISSING."""
        self._make_original_audio_caption()
        self._generate()
        plan = json.loads(
            (self.root / "20_script" / "production_plan.json").read_text(encoding="utf-8"))
        for anchor in ("A9", "A9_TEXT"):
            self.assertIn(anchor, plan["cleared_anchors"])
        for anchor in ("A10", "A10_TEXT"):
            self.assertNotIn(anchor, plan["cleared_anchors"])
        for row, v_row in zip(plan["timeline"], self.v_rows):
            a10 = [item for item in row["placements"] if item["anchor"] == "A10"]
            self.assertEqual(len(a10), 1)
            self.assertEqual(a10[0]["source_range_us"], [v_row[4], v_row[5]])
            self.assertEqual(a10[0]["target_range_us"], [v_row[2], v_row[3]])
            self.assertEqual(a10[0]["volume"], 1)
            captions = [item for item in row["placements"] if item["anchor"] == "A10_TEXT"]
            self.assertEqual(len(captions), 1)
            self.assertEqual(captions[0]["target_range_us"], [v_row[2], v_row[3]])
            self.assertEqual(
                captions[0]["text"], "화자 하나" if v_row[0] == "V01" else "화자 둘")

    def test_type_three_production_plan_passes_the_protocol_gate(self) -> None:
        """This is the gate that reported URAKKAI_VIDEO_AUDIO_COUNT_MISMATCH."""
        self._make_original_audio_caption()
        self._generate()
        plan = json.loads(
            (self.root / "20_script" / "production_plan.json").read_text(encoding="utf-8"))
        self.assertEqual(
            validate_executable_protocol.validate_production_plan(
                plan, validate_executable_protocol.load_protocol()
            ),
            [],
        )

    def _make_tts_intro_original_body(self) -> None:
        """Rewrite the fixture as a type 4 episode: a new A9 narration covers V01
        while the retained speaker keeps V02.  A10 has to duck under A9 and come
        back outside it, which is the pair of rules types 4 and 5 turn on."""
        source_sha = _sha(self.root / "00_input" / "source.mp4")
        intro, body = self.v_rows
        _write_json(self.root / "20_script" / "v_plan.json", {
            "V": self.v_rows, "DUR": self.duration, "type": "4",
            "audio_policy": "A9_TTS_PLUS_A10_REASSEMBLED",
            "execution_strategy": "tts_intro_original_body",
            "audio_source": "REASSEMBLED_VOCAL_STEM", "T1": "제목 하나", "T2": "제목 둘",
            # The cue spans the whole of V01: neither the protocol gate nor the
            # builder supports an A9 that covers only part of a Vxx.
            "cues": [["V01", "A9_V01", "도입 문장", intro[3] - intro[2],
                      intro[2], intro[3], "V01_fit.wav"]],
        })
        segments = [
            {"segment_id": row[0], "role": "VIDEO", "start": row[2], "duration": row[3] - row[2],
             "source_ref": "abcdefghijk", "source_beat_id": row[1],
             "source_range_us": [row[4], row[5]], "target_range_us": [row[2], row[3]],
             "volume": 0, "timeline_order": index}
            for index, row in enumerate(self.v_rows, start=1)
        ]
        for offset, (role, suffix) in enumerate((("A9", ""), ("A9_TEXT", "_TEXT"))):
            segments.append({
                "segment_id": f"A9_V01{suffix}", "role": role, "start": intro[2],
                "duration": intro[3] - intro[2], "source_ref": "abcdefghijk",
                "text": "도입 문장", "content_type": "TTS", "cue_id": "A9_V01",
                "timeline_order": 10 + offset * 10,
            })
        for index, row in enumerate(self.v_rows, start=1):
            segments.append({
                "segment_id": f"A10_{row[0]}", "role": "A10", "start": row[2],
                "duration": row[3] - row[2], "source_ref": "abcdefghijk",
                "source_range_us": [row[4], row[5]], "target_range_us": [row[2], row[3]],
                "volume": 0 if row[0] == intro[0] else 1, "timeline_order": 50 + index,
            })
        segments.append({
            "segment_id": f"A10_{body[0]}_TEXT", "role": "A10_TEXT", "start": body[2],
            "duration": body[3] - body[2], "source_ref": "abcdefghijk",
            "text": "화자 둘", "content_type": "SPEAKER", "caption_role": "A10_TEXT",
            "speaker_id": "SPK_A", "color_role": "WHITE",
            "cue_id": f"A10_{body[0]}", "timeline_order": 62,
        })
        _write_json(self.root / "20_script" / "approved_timeline.json", {
            "schema_version": "001short-approved-timeline-v2", "episode_id": self.root.name,
            "source_fingerprint": source_sha, "production_mode": "URAKKAI",
            "audio_policy": "A9_TTS_PLUS_A10_REASSEMBLED",
            "execution_strategy": "tts_intro_original_body",
            "primary_speaker_id": "SPK_A",
            "segments": segments,
        })

    def test_type_four_ducks_a10_under_the_a9_narration(self) -> None:
        """Marking every A10 lane "on" earns URAKKAI_MIXED_A10_NOT_MUTED_UNDER_A9,
        which is what kept types 4 and 5 from building at all."""
        self._make_tts_intro_original_body()
        self.assertEqual(self._generate()["status"], "PASS")
        manifest = json.loads(
            (self.root / "50_capcut_project" / "build_manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(
            {row["clip_id"]: row["mode"] for row in manifest["source_audio"]},
            {"V01": "duck", "V02": "on"},
        )
        # A reassembled stem is already in target order, so naming an original
        # source range would send CapCut to the wrong place in the stem.
        for row in manifest["source_audio"]:
            self.assertNotIn("capcut_source_range_us", row)
        plan = json.loads(
            (self.root / "20_script" / "production_plan.json").read_text(encoding="utf-8"))
        self.assertEqual(plan["cleared_anchors"], generator.ALWAYS_CLEARED)
        volumes = {
            row["target_segment_id"]: [
                item["volume"] for item in row["placements"] if item["anchor"] == "A10"
            ]
            for row in plan["timeline"]
        }
        self.assertEqual(volumes, {"V01": [0], "V02": [1]})

    def test_type_four_production_plan_passes_the_protocol_gate(self) -> None:
        """The mixed A9/A10 rules live in this gate, not in the builder alone."""
        self._make_tts_intro_original_body()
        self._generate()
        plan = json.loads(
            (self.root / "20_script" / "production_plan.json").read_text(encoding="utf-8"))
        self.assertEqual(
            validate_executable_protocol.validate_production_plan(
                plan, validate_executable_protocol.load_protocol()
            ),
            [],
        )

    def test_an_a9_cue_covering_part_of_a_segment_is_refused(self) -> None:
        """Partial overlap is unsupported downstream; failing here keeps the build
        from writing a PASS manifest it would have to walk back."""
        self._make_tts_intro_original_body()
        plan_path = self.root / "20_script" / "v_plan.json"
        v_plan = json.loads(plan_path.read_text(encoding="utf-8"))
        cue = v_plan["cues"][0]
        cue[5] = cue[5] - 200_000
        cue[3] = cue[5] - cue[4]
        _write_json(plan_path, v_plan)
        with self.assertRaises(ValueError) as caught:
            self._generate()
        self.assertIn("MIXED_A10_PARTIAL_OVERLAP_UNSUPPORTED", str(caught.exception))

    def test_an_order_preserving_trim_reads_as_a_structural_edit(self) -> None:
        """Dropping beats without reordering is a real URAKKAI edit.  original_order
        used to be derived from the surviving V rows alone, so the excluded beats
        vanished, final_order matched it exactly and every trim was rejected as
        URAKKAI_STRUCTURE_UNCHANGED."""
        self.v_rows = [
            ["V01", "B01", 0, 1_400_000, 0, 1_400_000],
            ["V02", "B03", 1_400_000, 3_000_000, 2_800_000, 4_400_000],
        ]
        self._make_original_audio_caption()
        plan_path = self.root / "20_script" / "v_plan.json"
        v_plan = json.loads(plan_path.read_text(encoding="utf-8"))
        v_plan["original_order"] = ["B01", "B02", "B03"]
        v_plan["urakkai_production_type"] = "TRIM_ONLY_NO_REORDER"
        _write_json(plan_path, v_plan)
        self._generate()

        manifest = json.loads(
            (self.root / "50_capcut_project" / "build_manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["urakkai"]["production_type"], "TRIM_ONLY_NO_REORDER")
        self.assertFalse(manifest["urakkai"]["reorder_required"])

        plan = json.loads(
            (self.root / "20_script" / "production_plan.json").read_text(encoding="utf-8"))
        self.assertEqual(plan["original_order"], ["B01", "B02", "B03"])
        self.assertEqual(plan["final_order"], ["B01", "B03"])
        self.assertEqual(
            validate_executable_protocol.validate_production_plan(
                plan, validate_executable_protocol.load_protocol()
            ),
            [],
        )

    def test_a_caption_only_episode_builds_without_any_audio(self) -> None:
        """Type 1 carries no voice, so both audio axes clear and no TTS cue is emitted."""
        self._make_caption_only()
        result = self._generate()
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["tts_cue_count"], 0)
        self.assertEqual(result["state_cue_count"], len(self.v_rows))
        plan = json.loads((self.root / "20_script" / "production_plan.json").read_text(encoding="utf-8"))
        for anchor in ("A9", "A9_TEXT", "A10", "A10_TEXT"):
            self.assertIn(anchor, plan["cleared_anchors"])
        config = json.loads((self.root / "50_capcut_project" / "build_config.json").read_text(encoding="utf-8"))
        self.assertNotIn("tts_cues", config)

    def test_a_state_caption_never_claims_speech_authority(self) -> None:
        """A STATE caption has no matching audio; labelling it SPEECH_AUDIO would lie."""
        self._make_caption_only()
        self._generate()
        evidence = json.loads(
            (self.root / "30_audio_srt" / "caption_timing_evidence.json").read_text(encoding="utf-8"))
        self.assertTrue(evidence["cues"])
        self.assertEqual({cue["authority"] for cue in evidence["cues"]}, {"STATE"})

    def test_design_handoff_matches_its_schema(self) -> None:
        """The build refuses a handoff whose schema_version is not the tikitaka constant."""
        self._generate()
        handoff = json.loads((self.root / "20_script" / "design_handoff.json").read_text(encoding="utf-8"))
        schema = json.loads((SKILL_ROOT / "schemas" / "design_handoff.schema.json").read_text(encoding="utf-8"))
        self.assertEqual(handoff["schema_version"], "tikitaka-design-handoff-v1")
        self.assertEqual(handoff["status"], "PASS")
        self.assertEqual(validate_schema(handoff, schema), [])

    def test_production_plan_passes_the_protocol_gate(self) -> None:
        """build_episode_capcut runs this exact gate before it will stage anything."""
        self._generate()
        plan = json.loads((self.root / "20_script" / "production_plan.json").read_text(encoding="utf-8"))
        self.assertEqual(plan["root_profile"], "test_profile")
        self.assertEqual(
            validate_executable_protocol.validate_production_plan(
                plan, validate_executable_protocol.load_protocol()
            ),
            [],
        )

    def test_generated_artifacts_share_one_set_of_boundaries(self) -> None:
        payload = self._generate()
        self.assertEqual(payload["status"], "PASS")
        self.assertEqual(payload["caption_cue_count"], 2)
        self.assertEqual(payload["tts_cue_count"], 2)

        manifest = json.loads((self.root / "50_capcut_project" / "build_manifest.json").read_text(encoding="utf-8"))
        plan = json.loads((self.root / "20_script" / "production_plan.json").read_text(encoding="utf-8"))
        config = json.loads((self.root / "50_capcut_project" / "build_config.json").read_text(encoding="utf-8"))
        evidence = json.loads(
            (self.root / "30_audio_srt" / "caption_timing_evidence.json").read_text(encoding="utf-8")
        )
        expected = [[row[2], row[3]] for row in self.v_rows]
        self.assertEqual([clip["target_range_us"] for clip in manifest["urakkai"]["video_clips"]], expected)
        self.assertEqual([row["target_range_us"] for row in plan["timeline"]], expected)
        self.assertEqual([row["target_range_us"] for row in evidence["mapping"]], expected)
        self.assertEqual(config["duration_us"], self.duration)

    def test_srt_is_written_from_the_same_timeline(self) -> None:
        self._generate()
        srt = (self.root / "30_audio_srt" / "final.srt").read_text(encoding="utf-8")
        self.assertIn("00:00:00,000 --> 00:00:01,400", srt)
        self.assertIn("00:00:01,400 --> 00:00:03,000", srt)
        lock = json.loads((self.root / "30_audio_srt" / "caption_lock.json").read_text(encoding="utf-8"))
        self.assertEqual(lock["final_srt_sha256"], _sha(self.root / "30_audio_srt" / "final.srt"))

    def test_missing_vmake_receipt_is_refused(self) -> None:
        """A generated tree must never claim a VMake download that has no receipt."""
        (self.root / "40_assets_used" / "vmake_final_download_evidence.json").unlink()
        with self.assertRaises(ValueError) as caught:
            self._generate()
        self.assertEqual(str(caught.exception), "VMAKE_FINAL_DOWNLOAD_EVIDENCE_REQUIRED")

    def test_vmake_receipt_for_a_different_file_is_refused(self) -> None:
        receipt = self.root / "40_assets_used" / "vmake_final_download_evidence.json"
        payload = json.loads(receipt.read_text(encoding="utf-8"))
        payload["downloaded_output_sha256"] = "0" * 64
        _write_json(receipt, payload)
        with self.assertRaises(ValueError) as caught:
            self._generate()
        self.assertEqual(str(caught.exception), "VMAKE_EVIDENCE_OUTPUT_SHA_MISMATCH")

    def test_caption_spanning_two_segments_is_refused(self) -> None:
        """validate_audio_caption requires every cue to sit inside one mapping row."""
        timeline_path = self.root / "20_script" / "approved_timeline.json"
        timeline = json.loads(timeline_path.read_text(encoding="utf-8"))
        for segment in timeline["segments"]:
            if segment["segment_id"] == "A9_V01_TEXT":
                segment["duration"] = 2_000_000
        _write_json(timeline_path, timeline)
        with self.assertRaises(ValueError) as caught:
            self._generate()
        self.assertTrue(str(caught.exception).startswith("CAPTION_CUE_SPANS_SEGMENTS:"))


if __name__ == "__main__":
    unittest.main()

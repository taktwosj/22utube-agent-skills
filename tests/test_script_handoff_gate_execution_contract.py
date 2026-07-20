from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
import wave
from pathlib import Path

from _support import load_source_module_no_bytecode, write_valid_source_mp4


ROOT = Path(__file__).resolve().parents[1]
SOURCE_FINGERPRINT = "a" * 64
TIKITAKA_HARNESS = ROOT / "skills" / "00-tikitaka" / "scripts" / "tikitaka_harness_runner.py"
CHATGPT_REVIEW_WORKFLOW = (
    ROOT / "skills" / "00-tikitaka" / "scripts" / "chatgpt_review_workflow.py"
)
PRODUCTION_GATE = (
    ROOT
    / "skills"
    / "000short-production-agent"
    / "scripts"
    / "validate_production_gate.py"
)


def write(path: Path, text: str = "ok") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def write_json(path: Path, text: str) -> None:
    write(path, text.strip() + "\n")


def create_source_identity_and_linked_draft(root: Path) -> None:
    source = root / "00_source" / "source.mp4"
    write_valid_source_mp4(source)
    source_sha256 = hashlib.sha256(source.read_bytes()).hexdigest()
    lock = {
        "status": "PASS",
        "canonical_url": "https://www.youtube.com/shorts/fixture123",
        "video_id": "fixture123",
        "local_source_path": "00_source/source.mp4",
        "sha256": source_sha256,
        "duration_sec": 8.0,
    }
    write_json(root / "10_analysis" / "source_identity_lock.json", json.dumps(lock))
    write_json(
        root / "10_analysis" / "source_evidence.json",
        json.dumps(
            {
                "status": "PASS",
                "video_id": "fixture123",
                "source_fingerprint_sha256": source_sha256,
                "ffprobe_status": "PASS",
                "has_video_stream": True,
                "probed_duration_sec": 8.0,
                "stt": {
                    "status": "PASS",
                    "verified_ranges": [{"start_sec": 0.0, "end_sec": 3.0}],
                },
            }
        ),
    )
    write_json(
        root / "10_analysis" / "crosscheck_report.json",
        json.dumps(
            {
                "status": "PASS",
                "video_id": "fixture123",
                "source_fingerprint_sha256": source_sha256,
                "hint_vs_evidence_compared": True,
            }
        ),
    )
    write_json(
        root / "00_source" / "source_manifest.json",
        json.dumps(
            {
                **lock,
                "source_identity_lock_path": "10_analysis/source_identity_lock.json",
                "source_evidence_path": "10_analysis/source_evidence.json",
                "crosscheck_report_path": "10_analysis/crosscheck_report.json",
            }
        ),
    )
    write_json(
        root / "10_analysis" / "tikitaka_source_request.json",
        json.dumps(
            {
                "status": "PASS",
                "owner_skill": "00-tikitaka",
                "requested_source_url": lock["canonical_url"],
                "requested_video_id": lock["video_id"],
                "user_stage_decision": "stage_2_full",
            }
        ),
    )
    write_json(
        root / "50_capcut_project" / "draft_content.json",
        json.dumps(
            {
                "materials": {
                    "videos": [
                        {
                            "id": "source-video",
                            "role": "source_video",
                            "path": str(source),
                            "active": True,
                            "audio_enabled": False,
                        }
                    ]
                }
            }
        ),
    )
    for relative in (
        "20_script/report1_handoff.json",
        "20_script/script_handoff_gate.json",
        "20_script/timeline_design.json",
    ):
        path = root / relative
        if not path.exists():
            continue
        payload = json.loads(path.read_text(encoding="utf-8"))
        payload["source_fingerprint_sha256"] = source_sha256
        write_json(path, json.dumps(payload))


def create_tikitaka_base_evidence(work_dir: Path) -> None:
    write(work_dir / "work_order.md")
    write(work_dir / "execution_spec.md")
    write(work_dir / "implementation_log.md")
    write(work_dir / "n8n_execution_id.txt", "n8n-ok")


def attach_source_fingerprint(path: Path) -> None:
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["source_fingerprint_sha256"] = SOURCE_FINGERPRINT
    write_json(path, json.dumps(payload))


def write_voice_separation_pass(work_dir: Path) -> None:
    duration_sec = 0.1
    frame_count = 4800
    lock = {
        "status": "PASS",
        "sha256": SOURCE_FINGERPRINT,
        "duration_sec": duration_sec,
    }
    write_json(
        work_dir / "10_analysis" / "source_identity_lock.json",
        json.dumps(lock),
    )

    audio_dir = work_dir / "10_analysis" / "audio"
    audio_dir.mkdir(parents=True, exist_ok=True)
    source_audio = audio_dir / "full_source_audio.wav"
    vocals = audio_dir / "vocals.wav"
    for path in (source_audio, vocals):
        with wave.open(str(path), "wb") as handle:
            handle.setnchannels(2)
            handle.setsampwidth(2)
            handle.setframerate(48000)
            handle.writeframes(b"\x00\x00\x00\x00" * frame_count)

    source_audio_sha = hashlib.sha256(source_audio.read_bytes()).hexdigest()
    vocals_sha = hashlib.sha256(vocals.read_bytes()).hexdigest()
    manifest = {
        "gate_name": "SOURCE_VOICE_SEPARATION_GATE",
        "status": "PASS",
        "owner_skill": "00-tikitaka",
        "source_fingerprint_sha256": SOURCE_FINGERPRINT,
        "separation_engine": "demucs",
        "separation_scope": "FULL_SOURCE_AUDIO",
        "source_audio_path": "10_analysis/audio/full_source_audio.wav",
        "source_audio_sha256": source_audio_sha,
        "demucs_input_sha256": source_audio_sha,
        "vocals_path": "10_analysis/audio/vocals.wav",
        "vocals_sha256": vocals_sha,
        "source_duration_sec": duration_sec,
        "source_audio_duration_sec": duration_sec,
        "vocals_duration_sec": duration_sec,
        "duration_tolerance_sec": 0.25,
        "sample_rate_hz": 48000,
        "channels": 2,
        "source_voice_music_removed": True,
        "q_segment_source": "10_analysis/audio/vocals.wav",
        "no_vocals_used": False,
        "created_by": "prepare_source_voice.py",
    }
    write_json(
        work_dir / "10_analysis" / "source_voice_separation.json",
        json.dumps(manifest),
    )


def write_chatgpt_review_pass(work_dir: Path) -> None:
    workflow = load_source_module_no_bytecode(
        "tikitaka_chatgpt_review_workflow_fixture",
        CHATGPT_REVIEW_WORKFLOW,
    )
    cycle_id = "fixture-cycle"
    round1 = workflow.build_round1(work_dir, cycle_id)
    round1_response = "\n".join(
        [
            "ROUTE=SHORTS",
            "review_round: 1",
            f"review_cycle_id: {cycle_id}",
            f"packet_id: {round1['packet_id']}",
            f"sent_packet_sha256: {round1['sent_packet_sha256']}",
            "suggestion_id: S1",
            "external_review_status: PENDING_CODEX_REVIEW",
            "",
        ]
    )
    round1_input = work_dir / "round1_fixture_response.md"
    write(round1_input, round1_response)
    workflow.record_response(work_dir, 1, round1_input)
    round1_input.unlink()

    write_json(
        work_dir / "chatgpt_review" / "round1_codex_decisions.json",
        json.dumps(
            {
                "status": "PASS",
                "all_suggestions_dispositioned": True,
                "decisions": [
                    {
                        "suggestion_id": "S1",
                        "disposition": "ADOPTED",
                    }
                ],
            }
        ),
    )
    round2 = workflow.build_round2(work_dir, cycle_id)
    round2_response = "\n".join(
        [
            "ROUTE=SHORTS",
            "review_round: 2",
            f"review_cycle_id: {cycle_id}",
            f"packet_id: {round2['packet_id']}",
            f"sent_packet_sha256: {round2['sent_packet_sha256']}",
            "recommendation: PASS_RECOMMENDED",
            "external_review_status: PENDING_CODEX_REVIEW",
            "",
        ]
    )
    round2_input = work_dir / "round2_fixture_response.md"
    write(round2_input, round2_response)
    workflow.record_response(work_dir, 2, round2_input)
    round2_input.unlink()
    workflow.finalize_gate(work_dir)


def write_vmake_reuse_pass(work_dir: Path) -> None:
    write(work_dir / "00_source" / "clean_source.mp4", "user-confirmed-clean")
    write_json(
        work_dir / "10_analysis" / "vmake_clean_source.json",
        json.dumps(
            {
                "gate_name": "VMAKE_CLEAN_SOURCE_GATE",
                "status": "USER_CONFIRMED_VMAKE_REUSE",
                "owner_skill": "00-tikitaka",
                "vmake_reuse_mode": "USER_CONFIRMED_NO_REDOWNLOAD_NO_RETEST",
                "user_vmake_confirmation": True,
                "analysis_authority": "original_sources",
                "timeline_authority": "existing_approved_design",
                "clean_visual_review_status": "USER_CONFIRMED",
                "clean_visual_paths": ["00_source/clean_source.mp4"],
                "embedded_audio_policy": "muted_always",
            }
        ),
    )


def create_script_lock_package_artifacts(work_dir: Path) -> None:
    write(
        work_dir / "design_blueprint.md",
        """# 설계도

## 기본 정보
fixture

## 제작 판단
fixture

## 자막 레이아웃 기준
caption_beat_map.json
TTS (T3): y=-900, max_chars_per_line=10, max_lines=1
화자발언 (T4/T5): y=-500, max_chars_per_line=10, max_lines=1
( ) 상황설명 (T6): y=700, max_chars_per_line=10, max_lines=1
video_scale=1.20
face_avoidance=fixed_lower_safe_zone_v1

## 상단 고정 문구
fixture

## 조립 역할 순서
| 편집 | 역할 |
|---|---|
| E1 | hook |

## 트랙별 타임라인
| 편집 | 시작 | 종료 |
|---|---:|---:|
| E1 | 00:00 | 00:03 |

## TTS 복사용 문구
테스트 중단

## 승인 전 점검
fixture
""",
    )
    write(work_dir / "original_structure_summary.md")
    write(work_dir / "urakkai_structure_plan.md")
    write(work_dir / "final_script_ko.md", "상단: 테스트 훅\n\ntimed 중단:\n테스트 중단")
    write_json(work_dir / "urakkai_structure_delta.json", '{"status":"PASS"}')
    write_json(
        work_dir / "timeline_design.json",
        """
        {
          "source_fingerprint_sha256": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
          "tracks": ["T1", "T2", "TTS", "speaker_quote_A", "situation_caption_A"],
          "segments": [
            {
              "edit_id": "E1",
              "source_ref": "S1",
              "source_order": 1,
              "timeline_order": 1,
              "assembly_role": "intro_narration",
              "time_start": "00:00",
              "time_end": "00:03",
              "track": "audio.narration_tts",
              "semantic_lane": "narration_tts",
              "resolved_capcut_track": null,
              "resolved_by": "000short-production-agent",
              "caption_type": "tts_narration",
              "visible_text_role": "tts_caption",
              "audio_role": "audio.narration_tts",
              "duration_basis": "estimated_tts_duration",
              "duration_status": "ESTIMATED_ACCEPTED",
              "tts_text_ref": "tts_001",
              "planned_tts_duration_sec": 3.0,
              "estimated_tts_duration_sec": 3.0,
              "tts_duration_status": "ESTIMATED_ACCEPTED",
              "visual_strategy": "hold_source_visual",
              "audio_policy": {"source_audio": "off", "tts": "on", "bgm": "optional"}
            }
          ]
        }
        """,
    )
    write_json(
        work_dir / "timeline_design_gate.json",
        """
        {
          "status": "PASS",
          "gate_name": "timeline_design_gate"
        }
        """,
    )
    write_json(
        work_dir / "caption_beat_map.json",
        """
        {
          "status": "PASS",
          "profile_version": "caption_profiles_v2",
          "video_scale": 1.2,
          "face_avoidance": "fixed_lower_safe_zone_v1",
          "beats": [
            {
              "beat_id": "E1_B01",
              "edit_id": "E1",
              "text": "테스트 나레이션",
              "start_sec": 0.0,
              "end_sec": 3.0,
              "caption_role": "tts_narration",
              "audio_basis": "tts_audio",
              "max_chars_per_line": 10,
              "max_lines": 1,
              "y": -900,
              "timing_source": "estimated_text"
            }
          ]
        }
        """,
    )
    write_json(
        work_dir / "block_map.json",
        """
        {
          "edit_block_sequence": ["E1"],
          "blocks": [
            {
              "edit_id": "E1",
              "source_block_id": "S1",
              "original_order": 1,
              "urakkai_order": 1,
              "caption_type": "tts_narration"
            }
          ]
        }
        """,
    )
    write_json(
        work_dir / "block_role_map.json",
        """
        {
          "roles": [
            {"edit_id": "E1", "caption_type": "tts_narration"}
          ]
        }
        """,
    )
    write_json(
        work_dir / "block_voice_switch_map.json",
        """
        {
          "switches": [
            {"edit_id": "E1", "source_audio": "off", "tts": "on"}
          ]
        }
        """,
    )
    write(work_dir / "tts_copy_text.txt", "테스트 나레이션")
    write_json(
        work_dir / "tts_duration_probe.json",
        """
        {
          "status": "PASS",
          "source": "estimated_text",
          "tts_items": [
            {
              "edit_id": "E1",
              "tts_text_ref": "tts_001",
              "text": "?뚯뒪???섎젅?댁뀡",
              "planned_duration_sec": 3.0,
              "actual_duration_sec": null,
              "estimated_duration_sec": 3.0,
              "delta_sec": 0.0,
              "within_tolerance": true,
              "reconciliation_action": null
            }
          ]
        }
        """,
    )
    write_json(
        work_dir / "tts_timing_reconciliation_gate.json",
        """
        {
          "status": "PASS",
          "gate_name": "TTS_TIMING_RECONCILIATION_GATE",
          "duration_basis": "estimated_text",
          "tts_duration_status": "ESTIMATED_ACCEPTED",
          "timeline_design_updated": false,
          "protected_fields_changed": false
        }
        """,
    )
    write_humanize_gate_pass(work_dir)
    write_voice_separation_pass(work_dir)
    write_chatgpt_review_pass(work_dir)
    write_vmake_reuse_pass(work_dir)


def write_humanize_gate_pass(work_dir: Path) -> None:
    write_json(
        work_dir / "humanize_korean_gate.json",
        """
        {
          "status": "PASS",
          "gate_name": "humanize_korean_gate",
          "scope": "visible_text_only",
          "structure_changed": false,
          "protected_fields_changed": false
        }
        """,
    )


def write_stage2_decision(work_dir: Path) -> None:
    write_json(
        work_dir / "job_state.json",
        """
        {
          "user_stage_decision": "stage_2_full",
          "report1_approved": true,
          "voice_audio_route_decided": true
        }
        """,
    )


def write_script_handoff_pass(work_dir: Path, relative_dir: str = "") -> None:
    base = work_dir / relative_dir if relative_dir else work_dir
    write_json(
        base / "script_handoff_gate.json",
        """
        {
          "gate_name": "SCRIPT_HANDOFF_GATE",
          "status": "PASS",
          "script_status": "SCRIPT_LOCK_PACKAGE",
          "capcut_allowed": true
        }
        """,
    )


def write_reentry_block_map(work_dir: Path, relative_dir: str = "") -> None:
    base = work_dir / relative_dir if relative_dir else work_dir
    write_json(
        base / "block_map.json",
        """
        {
          "edit_block_sequence": ["E1"],
          "blocks": [
            {
              "edit_id": "E1",
              "source_block_id": "S1",
              "original_order": 1,
              "urakkai_order": 1
            }
          ]
        }
        """,
    )


class ScriptHandoffGateExecutionContractTests(unittest.TestCase):
    def test_tikitaka_harness_generates_script_handoff_gate_from_lock_package(self):
        module = load_source_module_no_bytecode("tikitaka_harness_runner_exec", TIKITAKA_HARNESS)

        with tempfile.TemporaryDirectory() as tmp:
            work_dir = Path(tmp)
            create_tikitaka_base_evidence(work_dir)
            create_script_lock_package_artifacts(work_dir)
            write_stage2_decision(work_dir)

            state = module.audit(work_dir, "job-test")

            gate_path = work_dir / "script_handoff_gate.json"
            self.assertTrue(gate_path.is_file())
            gate = module.read_json(gate_path)
            self.assertEqual(gate["gate_name"], "SCRIPT_HANDOFF_GATE")
            self.assertEqual(gate["status"], "PASS")
            self.assertEqual(gate["generated_by"], "tikitaka_harness_runner")
            self.assertEqual(gate["script_status"], "SCRIPT_LOCK_PACKAGE")
            self.assertIs(gate["capcut_allowed"], True)
            self.assertEqual(gate["source_fingerprint_sha256"], SOURCE_FINGERPRINT)
            self.assertEqual(state["script_handoff_gate"]["status"], "PASS")

    def test_tikitaka_harness_rejects_legacy_caption_profile_values(self):
        module = load_source_module_no_bytecode("tikitaka_harness_runner_caption_profile", TIKITAKA_HARNESS)

        with tempfile.TemporaryDirectory() as tmp:
            work_dir = Path(tmp)
            create_tikitaka_base_evidence(work_dir)
            create_script_lock_package_artifacts(work_dir)
            beat_map_path = work_dir / "caption_beat_map.json"
            beat_map = module.read_json(beat_map_path)
            beat_map["beats"][0]["max_chars_per_line"] = 15
            beat_map["beats"][0]["max_lines"] = 2
            write_json(beat_map_path, json.dumps(beat_map, ensure_ascii=False))
            write_stage2_decision(work_dir)

            state = module.audit(work_dir, "job-test")

            gate = module.read_json(work_dir / "script_handoff_gate.json")
            self.assertEqual(gate["status"], "FAIL")
            self.assertIn("caption_beat_map", gate["missing_or_failed"])
            self.assertIn("FAIL_CAPTION_CHAR_LIMIT", gate["checks"]["caption_beat_map"]["reason"])
            self.assertEqual(state["script_handoff_gate"]["status"], "FAIL")

    def test_tikitaka_harness_writes_report1_handoff_to_000short(self):
        module = load_source_module_no_bytecode("tikitaka_harness_runner_report1_handoff", TIKITAKA_HARNESS)

        with tempfile.TemporaryDirectory() as tmp:
            work_dir = Path(tmp)
            create_script_lock_package_artifacts(work_dir)

            state = module.audit(work_dir, "job-test")

            handoff_path = work_dir / "report1_handoff.json"
            self.assertTrue(handoff_path.is_file())
            handoff = module.read_json(handoff_path)
            self.assertEqual(handoff["gate_name"], "REPORT1_HANDOFF_GATE")
            self.assertEqual(handoff["report"], "설계도")
            self.assertEqual(handoff["owner_skill"], "00-tikitaka")
            self.assertEqual(handoff["next_skill"], "000short-production-agent")
            self.assertEqual(handoff["next_stage"], "보고서2")
            self.assertEqual(handoff["next_gate"], "CAPCUT_OPENABLE_PROJECT")
            self.assertIn("report1_approved=true", handoff["required_before_next"])
            self.assertIn("voice_audio_route_decided=true", handoff["required_before_next"])
            self.assertEqual(handoff["status"], "WAIT")
            self.assertEqual(handoff["blocker"], "WAIT_REPORT1_APPROVAL_TTS_DECISION")
            self.assertEqual(handoff["source_fingerprint_sha256"], SOURCE_FINGERPRINT)
            self.assertEqual(state["report1_handoff_gate"]["next_skill"], "000short-production-agent")

            report = (work_dir / "stage_scope_report.md").read_text(encoding="utf-8")
            self.assertIn("다음 스킬: 000short-production-agent", report)
            self.assertIn("다음 단계: 보고서2 / CAPCUT_OPENABLE_PROJECT", report)
            self.assertIn("Use $000short-production-agent", report)
            self.assertIn("00-tikitaka는 보고서2를 작성하지 않는다", report)

    def test_tikitaka_handoff_pass_blocks_capcut_without_user_stage_decision(self):
        module = load_source_module_no_bytecode("tikitaka_harness_runner_stage_wait", TIKITAKA_HARNESS)

        with tempfile.TemporaryDirectory() as tmp:
            work_dir = Path(tmp)
            create_script_lock_package_artifacts(work_dir)

            state = module.audit(work_dir, "job-test")

            gate = module.read_json(work_dir / "script_handoff_gate.json")
            evidence = module.read_json(work_dir / "script_lock_evidence.json")
            self.assertEqual(gate["status"], "PASS")
            self.assertIs(gate["capcut_allowed"], False)
            self.assertEqual(gate["capcut_blocker"], "WAIT_USER_STAGE_DECISION")
            self.assertEqual(state["capcut_permission"], "WAIT_USER_STAGE_DECISION")
            self.assertEqual(state["production_status"], "WAIT_USER_STAGE_DECISION")
            self.assertIs(evidence["capcut_allowed"], False)
            self.assertEqual(evidence["capcut_blocker"], "WAIT_USER_STAGE_DECISION")

    def test_tikitaka_harness_fails_script_handoff_gate_when_humanize_gate_missing(self):
        module = load_source_module_no_bytecode("tikitaka_harness_runner_humanize_missing", TIKITAKA_HARNESS)

        with tempfile.TemporaryDirectory() as tmp:
            work_dir = Path(tmp)
            create_tikitaka_base_evidence(work_dir)
            create_script_lock_package_artifacts(work_dir)
            (work_dir / "humanize_korean_gate.json").unlink()
            write_stage2_decision(work_dir)

            state = module.audit(work_dir, "job-test")

            gate = module.read_json(work_dir / "script_handoff_gate.json")
            self.assertEqual(gate["status"], "FAIL")
            self.assertIn("humanize_korean_gate", gate["missing_or_failed"])
            self.assertEqual(state["script_lock"]["status"], "NOT_LOCKED")

    def test_tikitaka_harness_accepts_semantic_audio_tracks_in_timeline_design(self):
        module = load_source_module_no_bytecode("tikitaka_harness_runner_semantic_audio", TIKITAKA_HARNESS)

        with tempfile.TemporaryDirectory() as tmp:
            work_dir = Path(tmp)
            create_tikitaka_base_evidence(work_dir)
            create_script_lock_package_artifacts(work_dir)
            write_json(
                work_dir / "timeline_design.json",
                """
                {
                  "segments": [
                    {
                      "edit_id": "E1",
                      "source_ref": "S1",
                      "source_order": 1,
                      "timeline_order": 1,
                      "assembly_role": "intro_narration",
                      "time_start": "00:00",
                      "time_end": "00:03",
                      "track": "audio.narration_tts",
                      "semantic_lane": "narration_tts",
                      "resolved_capcut_track": null,
                      "resolved_by": "000short-production-agent",
                      "caption_type": "tts_narration",
                      "visible_text_role": "tts_caption",
                      "audio_role": "audio.narration_tts",
                      "duration_basis": "estimated_tts_duration",
                      "duration_status": "ESTIMATED_ACCEPTED",
                      "tts_text_ref": "tts_001",
                      "planned_tts_duration_sec": 3.0,
                      "estimated_tts_duration_sec": 3.0,
                      "tts_duration_status": "ESTIMATED_ACCEPTED",
                      "visual_strategy": "hold_source_visual",
                      "audio_policy": {"source_audio": "off", "tts": "on", "bgm": "optional"}
                    }
                  ]
                }
                """,
            )
            attach_source_fingerprint(work_dir / "timeline_design.json")
            write_stage2_decision(work_dir)

            state = module.audit(work_dir, "job-test")

            self.assertEqual(state["script_handoff_gate"]["status"], "PASS")

    def test_tikitaka_harness_rejects_capcut_audio_track_ids_in_timeline_design(self):
        module = load_source_module_no_bytecode("tikitaka_harness_runner_capcut_audio_track", TIKITAKA_HARNESS)

        with tempfile.TemporaryDirectory() as tmp:
            work_dir = Path(tmp)
            create_tikitaka_base_evidence(work_dir)
            create_script_lock_package_artifacts(work_dir)
            write_json(
                work_dir / "timeline_design.json",
                """
                {
                  "segments": [
                    {
                      "edit_id": "E1",
                      "time_start": "00:00",
                      "time_end": "00:03",
                      "track": "A9",
                      "caption_type": "tts_narration",
                      "audio_policy": "tts_on_source_off"
                    }
                  ]
                }
                """,
            )
            attach_source_fingerprint(work_dir / "timeline_design.json")
            write_stage2_decision(work_dir)

            state = module.audit(work_dir, "job-test")

            gate = module.read_json(work_dir / "script_handoff_gate.json")
            self.assertEqual(gate["status"], "FAIL")
            self.assertIn("timeline_design", gate["missing_or_failed"])
            self.assertEqual(state["script_lock"]["status"], "NOT_LOCKED")

    def test_tikitaka_harness_rejects_timeline_design_without_assembly_role(self):
        module = load_source_module_no_bytecode("tikitaka_harness_runner_missing_assembly_role", TIKITAKA_HARNESS)

        with tempfile.TemporaryDirectory() as tmp:
            work_dir = Path(tmp)
            create_tikitaka_base_evidence(work_dir)
            create_script_lock_package_artifacts(work_dir)
            write_json(
                work_dir / "timeline_design.json",
                """
                {
                  "segments": [
                    {
                      "edit_id": "E1",
                      "source_ref": "S1",
                      "source_order": 1,
                      "timeline_order": 1,
                      "time_start": "00:00",
                      "time_end": "00:03",
                      "track": "audio.speaker_source",
                      "semantic_lane": "speaker_source",
                      "resolved_capcut_track": null,
                      "resolved_by": "000short-production-agent",
                      "caption_type": "speaker_quote",
                      "visible_text_role": "speaker_quote",
                      "audio_role": "audio.speaker_source",
                      "duration_basis": "source_range",
                      "duration_status": "SOURCE_AUDIO_LOCKED",
                      "source_audio_range": "00:01-00:03",
                      "quote_verification_status": "VERIFIED_SOURCE_SPEECH",
                      "visual_strategy": "source_visual_action",
                      "audio_policy": {"source_audio": "on", "tts": "off", "bgm": "optional_duck"}
                    }
                  ]
                }
                """,
            )
            write_stage2_decision(work_dir)

            state = module.audit(work_dir, "job-test")

            gate = module.read_json(work_dir / "script_handoff_gate.json")
            self.assertEqual(gate["status"], "FAIL")
            self.assertIn("timeline_design", gate["missing_or_failed"])
            self.assertEqual(state["script_lock"]["status"], "NOT_LOCKED")

    def test_tikitaka_harness_requires_tts_timing_gate_only_for_narration_audio(self):
        module = load_source_module_no_bytecode("tikitaka_harness_runner_narration_timing_required", TIKITAKA_HARNESS)

        with tempfile.TemporaryDirectory() as tmp:
            work_dir = Path(tmp)
            create_tikitaka_base_evidence(work_dir)
            create_script_lock_package_artifacts(work_dir)
            (work_dir / "tts_duration_probe.json").unlink()
            (work_dir / "tts_timing_reconciliation_gate.json").unlink()
            write_stage2_decision(work_dir)

            state = module.audit(work_dir, "job-test")

            gate = module.read_json(work_dir / "script_handoff_gate.json")
            self.assertEqual(gate["status"], "FAIL")
            self.assertIn("tts_timing_reconciliation_gate", gate["missing_or_failed"])
            self.assertEqual(state["script_lock"]["status"], "NOT_LOCKED")

    def test_tikitaka_harness_allows_tts_caption_without_narration_timing_gate(self):
        module = load_source_module_no_bytecode("tikitaka_harness_runner_tts_caption_only", TIKITAKA_HARNESS)

        with tempfile.TemporaryDirectory() as tmp:
            work_dir = Path(tmp)
            create_tikitaka_base_evidence(work_dir)
            create_script_lock_package_artifacts(work_dir)
            write_json(
                work_dir / "timeline_design.json",
                """
                {
                  "segments": [
                    {
                      "edit_id": "E1",
                      "source_ref": "S1",
                      "source_order": 1,
                      "timeline_order": 1,
                      "assembly_role": "reaction_caption",
                      "time_start": "00:00",
                      "time_end": "00:03",
                      "track": "TTS",
                      "caption_type": "tts_caption",
                      "visible_text_role": "tts_caption",
                      "audio_role": "none",
                      "duration_basis": "fixed_design_duration",
                      "duration_status": "FIXED_DESIGN_LOCKED",
                      "visual_strategy": "source_visual_hold",
                      "audio_policy": {"source_audio": "off", "tts": "off", "bgm": "optional"}
                    }
                  ]
                }
                """,
            )
            attach_source_fingerprint(work_dir / "timeline_design.json")
            write_stage2_decision(work_dir)

            state = module.audit(work_dir, "job-test")

            self.assertEqual(state["script_handoff_gate"]["status"], "PASS")

    def test_tikitaka_harness_relocks_when_actual_tts_duration_exceeds_without_action(self):
        module = load_source_module_no_bytecode("tikitaka_harness_runner_tts_duration_relock", TIKITAKA_HARNESS)

        with tempfile.TemporaryDirectory() as tmp:
            work_dir = Path(tmp)
            create_tikitaka_base_evidence(work_dir)
            create_script_lock_package_artifacts(work_dir)
            write_json(
                work_dir / "tts_duration_probe.json",
                """
                {
                  "status": "PASS",
                  "source": "generated_tts",
                  "tts_items": [
                    {
                      "edit_id": "E1",
                      "tts_text_ref": "tts_001",
                      "text": "?뚯뒪???섎젅?댁뀡",
                      "planned_duration_sec": 3.0,
                      "actual_duration_sec": 4.0,
                      "estimated_duration_sec": null,
                      "delta_sec": 1.0,
                      "within_tolerance": false,
                      "reconciliation_action": null
                    }
                  ]
                }
                """,
            )
            write_stage2_decision(work_dir)

            state = module.audit(work_dir, "job-test")

            gate = module.read_json(work_dir / "script_handoff_gate.json")
            self.assertEqual(gate["status"], "FAIL")
            self.assertIn("tts_duration_probe", gate["missing_or_failed"])
            self.assertEqual(state["script_lock"]["status"], "NOT_LOCKED")

    def test_tikitaka_harness_allows_actual_tts_duration_with_locked_reconciliation_action(self):
        module = load_source_module_no_bytecode("tikitaka_harness_runner_tts_duration_reconciled", TIKITAKA_HARNESS)

        with tempfile.TemporaryDirectory() as tmp:
            work_dir = Path(tmp)
            create_tikitaka_base_evidence(work_dir)
            create_script_lock_package_artifacts(work_dir)
            write_json(
                work_dir / "timeline_design.json",
                """
                {
                  "segments": [
                    {
                      "edit_id": "E1",
                      "source_ref": "S1",
                      "source_order": 1,
                      "timeline_order": 1,
                      "assembly_role": "intro_narration",
                      "time_start": "00:00",
                      "time_end": "00:04",
                      "track": "audio.narration_tts",
                      "semantic_lane": "narration_tts",
                      "resolved_capcut_track": null,
                      "resolved_by": "000short-production-agent",
                      "caption_type": "tts_narration",
                      "visible_text_role": "tts_caption",
                      "audio_role": "audio.narration_tts",
                      "duration_basis": "actual_tts_duration",
                      "duration_status": "ACTUAL_AUDIO_LOCKED",
                      "tts_text_ref": "tts_001",
                      "planned_tts_duration_sec": 3.0,
                      "actual_tts_duration_sec": 4.0,
                      "tts_duration_status": "ACTUAL_AUDIO_LOCKED",
                      "visual_strategy": "hold_source_visual",
                      "audio_policy": {"source_audio": "off", "tts": "on", "bgm": "optional"}
                    }
                  ]
                }
                """,
            )
            attach_source_fingerprint(work_dir / "timeline_design.json")
            write_json(
                work_dir / "tts_duration_probe.json",
                """
                {
                  "status": "PASS",
                  "source": "generated_tts",
                  "tts_items": [
                    {
                      "edit_id": "E1",
                      "tts_text_ref": "tts_001",
                      "text": "?뚯뒪???섎젅?댁뀡",
                      "planned_duration_sec": 3.0,
                      "actual_duration_sec": 4.0,
                      "estimated_duration_sec": null,
                      "delta_sec": 1.0,
                      "within_tolerance": false,
                      "reconciliation_action": "extend_visual"
                    }
                  ]
                }
                """,
            )
            write_json(
                work_dir / "tts_timing_reconciliation_gate.json",
                """
                {
                  "status": "PASS",
                  "gate_name": "TTS_TIMING_RECONCILIATION_GATE",
                  "duration_basis": "actual_audio",
                  "tts_duration_status": "ACTUAL_AUDIO_LOCKED",
                  "timeline_design_updated": true,
                  "protected_fields_changed": true,
                  "reconciliation_action": "extend_visual"
                }
                """,
            )
            write_stage2_decision(work_dir)

            state = module.audit(work_dir, "job-test")

            self.assertEqual(state["script_handoff_gate"]["status"], "PASS")

    def test_tikitaka_harness_allows_none_when_actual_tts_fits_slot(self):
        module = load_source_module_no_bytecode("tikitaka_harness_runner_tts_duration_none", TIKITAKA_HARNESS)

        with tempfile.TemporaryDirectory() as tmp:
            work_dir = Path(tmp)
            create_tikitaka_base_evidence(work_dir)
            create_script_lock_package_artifacts(work_dir)
            write_json(
                work_dir / "tts_duration_probe.json",
                """
                {
                  "status": "PASS",
                  "source": "generated_tts",
                  "tts_items": [
                    {
                      "edit_id": "E1",
                      "tts_text_ref": "tts_001",
                      "text": "테스트 음성",
                      "planned_duration_sec": 4.0,
                      "actual_duration_sec": 3.4,
                      "within_tolerance": true,
                      "reconciliation_action": "none"
                    }
                  ]
                }
                """,
            )
            write_json(
                work_dir / "tts_timing_reconciliation_gate.json",
                """
                {
                  "status": "PASS",
                  "gate_name": "TTS_TIMING_RECONCILIATION_GATE",
                  "duration_basis": "actual_audio",
                  "tts_duration_status": "ACTUAL_AUDIO_LOCKED",
                  "timeline_design_updated": true,
                  "protected_fields_changed": false,
                  "reconciliation_action": "none"
                }
                """,
            )
            write_stage2_decision(work_dir)

            state = module.audit(work_dir, "job-test")

            self.assertEqual(state["script_handoff_gate"]["status"], "PASS")

    def test_tikitaka_harness_detects_stage1_request_text_and_writes_todo_report(self):
        module = load_source_module_no_bytecode("tikitaka_harness_runner_stage1_text", TIKITAKA_HARNESS)

        with tempfile.TemporaryDirectory() as tmp:
            work_dir = Path(tmp)
            create_script_lock_package_artifacts(work_dir)
            write(work_dir / "user_request.txt", "URL과 Gemini 분석본 줄게. 대본만 먼저 해.")

            state = module.audit(work_dir, "job-test")

            self.assertEqual(state["stage_scope_gate"]["status"], "WAIT")
            self.assertEqual(state["stage_scope_gate"]["decision"], "stage_1_script")
            self.assertEqual(state["user_stage_decision"], "stage_1_script")
            self.assertEqual(state["capcut_permission"], "WAIT_USER_STAGE_DECISION")

            todo = (work_dir / "stage_gate_todo.md").read_text(encoding="utf-8")
            self.assertIn("[x] G0: stage_1_script", todo)
            self.assertIn("[x] G2: stage 1 STOP", todo)
            self.assertIn("[ ] G3: stage 2 entry", todo)
            self.assertIn("설계도", todo)

            report = (work_dir / "stage_scope_report.md").read_text(encoding="utf-8")
            self.assertIn("# 설계도", report)
            self.assertIn("대본 승인용: 예", report)
            self.assertIn("CapCut 생성: 아니오", report)
            self.assertIn("TTS 생성: 아니오", report)
            self.assertIn("WAIT_USER_STAGE_DECISION", report)
            self.assertIn("reason: stage 1 script-only request; stop after 설계도", report)
            self.assertIn("중단 TTS 글자만 복사", report)
            self.assertIn("상단: 테스트 훅", report)
            self.assertIn("timed 중단:", report)
            self.assertIn("테스트 나레이션", report)
            self.assertNotIn("DRAFT_FAST 쇼츠공장 보고", report)

    def test_tikitaka_harness_detects_auto_mode_request_text_but_waits_for_report1_approval(self):
        module = load_source_module_no_bytecode("tikitaka_harness_runner_auto_text", TIKITAKA_HARNESS)

        with tempfile.TemporaryDirectory() as tmp:
            work_dir = Path(tmp)
            create_script_lock_package_artifacts(work_dir)
            write(work_dir / "user_request.txt", "자동모드로 끝까지. 캣컵 프로젝트 파일까지 만들어.")

            state = module.audit(work_dir, "job-test")

            self.assertEqual(state["stage_scope_gate"]["status"], "WAIT")
            self.assertEqual(state["stage_scope_gate"]["decision"], "stage_2_full")
            self.assertEqual(state["user_stage_decision"], "stage_2_full")
            self.assertEqual(state["capcut_permission"], "WAIT_REPORT1_APPROVAL_TTS_DECISION")

            todo = (work_dir / "stage_gate_todo.md").read_text(encoding="utf-8")
            self.assertIn("[x] G0: stage_2_full", todo)
            self.assertIn("[ ] G3: stage 2 entry", todo)

            report = (work_dir / "stage_scope_report.md").read_text(encoding="utf-8")
            self.assertIn("# 설계도", report)
            self.assertIn("대본 승인용: 예", report)
            self.assertIn("CapCut 생성: 아니오", report)
            self.assertIn("TTS 생성: 아니오", report)
            self.assertIn("WAIT_REPORT1_APPROVAL_TTS_DECISION", report)
            self.assertIn("중단 TTS 글자만 복사", report)
            self.assertIn("상단: 테스트 훅", report)
            self.assertIn("테스트 나레이션", report)
            self.assertIn("다음 단계: 보고서2 / CAPCUT_OPENABLE_PROJECT", report)
            self.assertNotIn("# 보고서2", report)
            self.assertNotIn("# Stage Scope Report", report)
            self.assertNotIn("DRAFT_FAST 쇼츠공장 보고", report)

    def test_tikitaka_harness_blocks_report1_when_visible_script_body_missing(self):
        module = load_source_module_no_bytecode("tikitaka_harness_runner_missing_script_body", TIKITAKA_HARNESS)

        with tempfile.TemporaryDirectory() as tmp:
            work_dir = Path(tmp)
            create_script_lock_package_artifacts(work_dir)
            (work_dir / "final_script_ko.md").unlink()
            write(work_dir / "user_request.txt", "대본만 먼저 해.")

            state = module.audit(work_dir, "job-test")

            self.assertEqual(state["script_handoff_gate"]["status"], "FAIL")
            self.assertIn("visible_script_body", state["script_handoff_gate"]["missing_or_failed"])
            report = (work_dir / "stage_scope_report.md").read_text(encoding="utf-8")
            self.assertIn("# 설계도 BLOCKED", report)
            self.assertIn("대본 승인용: 아니오", report)
            self.assertIn("FAIL_REPORT1_VISIBLE_SCRIPT_BODY_MISSING", report)
            self.assertNotIn("대본 승인용: 예", report)
            self.assertNotIn("본문 없음", report)

    def test_tikitaka_harness_blocks_report1_when_tts_copy_text_missing(self):
        module = load_source_module_no_bytecode("tikitaka_harness_runner_missing_tts_copy", TIKITAKA_HARNESS)

        with tempfile.TemporaryDirectory() as tmp:
            work_dir = Path(tmp)
            create_script_lock_package_artifacts(work_dir)
            (work_dir / "tts_copy_text.txt").unlink()
            write(work_dir / "user_request.txt", "대본만 먼저 해.")

            state = module.audit(work_dir, "job-test")

            self.assertEqual(state["script_handoff_gate"]["status"], "FAIL")
            self.assertIn("tts_copy_text", state["script_handoff_gate"]["missing_or_failed"])
            report = (work_dir / "stage_scope_report.md").read_text(encoding="utf-8")
            self.assertIn("# 설계도 BLOCKED", report)
            self.assertIn("대본 승인용: 아니오", report)
            self.assertIn("FAIL_REPORT1_TTS_COPY_TEXT_MISSING", report)
            self.assertNotIn("대본 승인용: 예", report)
            self.assertNotIn("본문 없음", report)

    def test_tikitaka_harness_blocks_tts_path_without_explicit_voice_route_decision(self):
        module = load_source_module_no_bytecode("tikitaka_harness_runner_tts_path_wait", TIKITAKA_HARNESS)

        with tempfile.TemporaryDirectory() as tmp:
            work_dir = Path(tmp)
            create_script_lock_package_artifacts(work_dir)
            write_json(
                work_dir / "job_state.json",
                """
                {
                  "user_tts_audio_path": "D:/Downloads/hook.mp3",
                  "report1_approved": true
                }
                """,
            )

            state = module.audit(work_dir, "job-test")

            self.assertEqual(state["stage_scope_gate"]["status"], "WAIT")
            self.assertEqual(state["stage_scope_gate"]["decision"], "stage_2_full")
            self.assertEqual(state["capcut_permission"], "WAIT_REPORT1_APPROVAL_TTS_DECISION")

    def test_tikitaka_harness_allows_stage2_after_report1_approval_and_voice_route(self):
        module = load_source_module_no_bytecode("tikitaka_harness_runner_auto_text_ready", TIKITAKA_HARNESS)

        with tempfile.TemporaryDirectory() as tmp:
            work_dir = Path(tmp)
            create_script_lock_package_artifacts(work_dir)
            write_json(
                work_dir / "job_state.json",
                """
                {
                  "user_stage_decision": "stage_2_full",
                  "report1_approved": true,
                  "voice_audio_route_decided": true
                }
                """,
            )

            state = module.audit(work_dir, "job-test")

            self.assertEqual(state["stage_scope_gate"]["status"], "PASS")
            self.assertEqual(state["stage_scope_gate"]["decision"], "stage_2_full")
            self.assertEqual(state["vmake_clean_source"]["status"], "PASS")
            self.assertEqual(
                state["vmake_clean_source"]["reason"],
                "USER_CONFIRMED_VMAKE_REUSE",
            )
            self.assertEqual(state["capcut_permission"], "CAPCUT_OPENABLE_PROJECT_ALLOWED")
            report = (work_dir / "stage_scope_report.md").read_text(encoding="utf-8")
            self.assertIn("# 2단계 인계 보고", report)
            self.assertNotIn("# Stage Scope Report", report)
            self.assertNotIn("[FINAL_LOCK 최종 보고]", report)
            self.assertIn("다음 단계: 보고서2 / CAPCUT_OPENABLE_PROJECT", report)
            self.assertNotIn("# 보고서2", report)

    def test_tikitaka_harness_blocks_missing_user_confirmed_vmake_file(self):
        module = load_source_module_no_bytecode(
            "tikitaka_harness_runner_missing_vmake_reuse",
            TIKITAKA_HARNESS,
        )

        with tempfile.TemporaryDirectory() as tmp:
            work_dir = Path(tmp)
            create_script_lock_package_artifacts(work_dir)
            write_stage2_decision(work_dir)
            (work_dir / "00_source" / "clean_source.mp4").unlink()

            state = module.audit(work_dir, "job-test")

            self.assertEqual(state["vmake_clean_source"]["status"], "FAILED")
            self.assertIn(
                "WAIT_EXISTING_VMAKE_CLEAN_FILE",
                state["vmake_clean_source"]["reason"],
            )
            self.assertEqual(state["capcut_permission"], "WAIT_VMAKE_CLEAN_SOURCE")

    def test_tikitaka_harness_reentry_classifies_existing_capcut_package(self):
        module = load_source_module_no_bytecode("tikitaka_harness_runner_reentry_capcut", TIKITAKA_HARNESS)

        with tempfile.TemporaryDirectory() as tmp:
            work_dir = Path(tmp)
            write_json(work_dir / "50_capcut_project" / "draft_content.json", '{"materials": {}}')
            write_script_handoff_pass(work_dir, "20_script")
            write_reentry_block_map(work_dir, "20_script")

            status = module.reentry_stage_status(work_dir)

            self.assertEqual(status["status"], "WAIT")
            self.assertEqual(status["resume_stage"], "capcut_rework")
            self.assertEqual(status["blocker"], "WAIT_REPORT1_APPROVAL_TTS_DECISION")
            self.assertIn("CapCut", status["report"])

            ready_status = module.reentry_stage_status(
                work_dir,
                {
                    "report1_approved": True,
                    "voice_audio_route_decided": True,
                },
            )
            self.assertEqual(ready_status["status"], "PASS")
            self.assertEqual(ready_status["resume_stage"], "capcut_rework")

    def test_tikitaka_harness_reentry_blocks_orphan_capcut_draft_without_handoff(self):
        module = load_source_module_no_bytecode("tikitaka_harness_runner_reentry_orphan_capcut", TIKITAKA_HARNESS)

        with tempfile.TemporaryDirectory() as tmp:
            work_dir = Path(tmp)
            write_json(work_dir / "50_capcut_project" / "draft_content.json", '{"materials": {}}')

            status = module.reentry_stage_status(work_dir)

            self.assertEqual(status["status"], "WAIT")
            self.assertEqual(status["resume_stage"], "stage_1_repair")
            self.assertEqual(status["blocker"], "WAIT_SCRIPT_HANDOFF_GATE")
            self.assertIn("script_handoff_gate", status["report"])

    def test_tikitaka_harness_reentry_routes_failed_handoff_to_stage1_repair(self):
        module = load_source_module_no_bytecode("tikitaka_harness_runner_reentry_failed_handoff", TIKITAKA_HARNESS)

        with tempfile.TemporaryDirectory() as tmp:
            work_dir = Path(tmp)
            write_json(
                work_dir / "script_handoff_gate.json",
                """
                {
                  "gate_name": "SCRIPT_HANDOFF_GATE",
                  "status": "FAIL",
                  "script_status": "SCRIPT_REWRITE",
                  "capcut_allowed": false
                }
                """,
            )

            status = module.reentry_stage_status(work_dir)

            self.assertEqual(status["status"], "WAIT")
            self.assertEqual(status["resume_stage"], "stage_1_repair")
            self.assertEqual(status["blocker"], "WAIT_SCRIPT_HANDOFF_GATE_REPAIR")
            self.assertIn("not PASS", status["report"])

    def test_tikitaka_harness_reentry_fails_invalid_capcut_draft(self):
        module = load_source_module_no_bytecode("tikitaka_harness_runner_reentry_invalid_capcut", TIKITAKA_HARNESS)

        with tempfile.TemporaryDirectory() as tmp:
            work_dir = Path(tmp)
            write(work_dir / "50_capcut_project" / "draft_content.json", "{")

            status = module.reentry_stage_status(work_dir)

            self.assertEqual(status["status"], "FAIL")
            self.assertEqual(status["resume_stage"], "capcut_rework")
            self.assertEqual(status["blocker"], "FAIL_CAPCUT_DRAFT_CONTENT_INVALID")

    def test_tikitaka_harness_reentry_classifies_script_handoff_package(self):
        module = load_source_module_no_bytecode("tikitaka_harness_runner_reentry_script", TIKITAKA_HARNESS)

        with tempfile.TemporaryDirectory() as tmp:
            work_dir = Path(tmp)
            write_json(
                work_dir / "script_handoff_gate.json",
                """
                {
                  "gate_name": "SCRIPT_HANDOFF_GATE",
                  "status": "PASS",
                  "script_status": "SCRIPT_LOCK_PACKAGE",
                  "capcut_allowed": false
                }
                """,
            )

            status = module.reentry_stage_status(work_dir)

            self.assertEqual(status["status"], "WAIT")
            self.assertEqual(status["resume_stage"], "stage_2_resume")
            self.assertEqual(status["blocker"], "WAIT_REPORT1_APPROVAL_TTS_DECISION")
            self.assertIn("stage 1", status["report"])

            ready_status = module.reentry_stage_status(
                work_dir,
                {
                    "report1_approved": True,
                    "voice_audio_route_decided": True,
                },
            )
            self.assertEqual(ready_status["status"], "PASS")
            self.assertEqual(ready_status["resume_stage"], "stage_2_resume")

    def test_tikitaka_harness_fails_script_handoff_gate_when_voice_switch_map_missing(self):
        module = load_source_module_no_bytecode("tikitaka_harness_runner_fail", TIKITAKA_HARNESS)

        with tempfile.TemporaryDirectory() as tmp:
            work_dir = Path(tmp)
            create_tikitaka_base_evidence(work_dir)
            create_script_lock_package_artifacts(work_dir)
            (work_dir / "block_voice_switch_map.json").unlink()

            state = module.audit(work_dir, "job-test")

            gate = module.read_json(work_dir / "script_handoff_gate.json")
            self.assertEqual(gate["status"], "FAIL")
            self.assertIs(gate["capcut_allowed"], False)
            self.assertIn("block_voice_switch_map", gate["missing_or_failed"])
            self.assertFalse(state["final_report_allowed"])

    def test_tikitaka_handoff_pass_allows_capcut_openable_even_when_final_lock_evidence_missing(self):
        module = load_source_module_no_bytecode("tikitaka_harness_runner_openable", TIKITAKA_HARNESS)

        with tempfile.TemporaryDirectory() as tmp:
            work_dir = Path(tmp)
            write_stage2_decision(work_dir)
            create_script_lock_package_artifacts(work_dir)

            state = module.audit(work_dir, "job-test")

            self.assertEqual(state["script_handoff_gate"]["status"], "PASS")
            self.assertEqual(state["script_handoff_gate"]["script_status"], "SCRIPT_LOCK_PACKAGE")
            self.assertIs(state["script_handoff_gate"]["capcut_allowed"], True)
            self.assertEqual(state["capcut_permission"], "CAPCUT_OPENABLE_PROJECT_ALLOWED")
            self.assertEqual(state["production_status"], "WAIT_CAPCUT_OPENABLE_PROJECT")
            self.assertFalse(state["final_report_allowed"])
            self.assertEqual(state["script_lock"]["status"], "NOT_LOCKED")

    def test_production_shared_requirements_fail_without_script_handoff_gate(self):
        module = load_source_module_no_bytecode("production_gate_missing_handoff", PRODUCTION_GATE)

        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(module.GateFail, "WAIT_SCRIPT_HANDOFF_GATE"):
                module.validate_shared_requirements({}, Path(tmp))

    def test_production_accepts_validator_generated_script_handoff_gate(self):
        module = load_source_module_no_bytecode("production_gate_handoff_pass", PRODUCTION_GATE)

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_json(
                root / "20_script" / "script_handoff_gate.json",
                """
                {
                  "gate_name": "SCRIPT_HANDOFF_GATE",
                  "status": "PASS",
                  "generated_by": "tikitaka_harness_runner",
                  "script_status": "SCRIPT_LOCK_PACKAGE",
                  "capcut_allowed": true,
                  "input_files": ["20_script/block_map.json"]
                }
                """,
            )
            write_json(
                root / "20_script" / "block_map.json",
                """
                {
                  "edit_block_sequence": ["E1"],
                  "blocks": [
                    {
                      "edit_id": "E1",
                      "source_block_id": "S1",
                      "original_order": 1,
                      "urakkai_order": 1
                    }
                  ],
                  "block_voice_switch_map": [
                    {"edit_id": "E1", "source_audio": "off", "tts": "on"}
                  ]
                }
                """,
            )

            result = module.validate_script_handoff_gate({}, root)

            self.assertEqual(result["script_handoff_gate_status"], "PASS")
            self.assertEqual(result["script_status"], "SCRIPT_LOCK_PACKAGE")
            self.assertEqual(result["capcut_permission"], "CAPCUT_OPENABLE_PROJECT_ALLOWED")

    def test_production_accepts_harness_input_files_relative_to_gate_directory(self):
        module = load_source_module_no_bytecode("production_gate_handoff_relative_inputs", PRODUCTION_GATE)

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_json(
                root / "20_script" / "script_handoff_gate.json",
                """
                {
                  "gate_name": "SCRIPT_HANDOFF_GATE",
                  "status": "PASS",
                  "generated_by": "tikitaka_harness_runner",
                  "script_status": "SCRIPT_LOCK_PACKAGE",
                  "capcut_allowed": true,
                  "input_files": ["block_map.json"]
                }
                """,
            )
            write_json(
                root / "20_script" / "block_map.json",
                """
                {
                  "edit_block_sequence": ["E1"],
                  "blocks": [
                    {
                      "edit_id": "E1",
                      "source_block_id": "S1",
                      "original_order": 1,
                      "urakkai_order": 1
                    }
                  ],
                  "block_voice_switch_map": [
                    {"edit_id": "E1", "source_audio": "off", "tts": "off"}
                  ]
                }
                """,
            )

            result = module.validate_script_handoff_gate({}, root)

            self.assertEqual(result["script_handoff_gate_status"], "PASS")

    def test_production_capcut_openable_entry_does_not_require_final_lock_fields(self):
        module = load_source_module_no_bytecode("production_gate_openable_entry", PRODUCTION_GATE)

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_json(
                root / "20_script" / "script_handoff_gate.json",
                """
                {
                  "gate_name": "SCRIPT_HANDOFF_GATE",
                  "status": "PASS",
                  "generated_by": "tikitaka_harness_runner",
                  "script_status": "SCRIPT_LOCK_PACKAGE",
                  "capcut_allowed": true,
                  "input_files": ["20_script/block_map.json"]
                }
                """,
            )
            write_json(
                root / "20_script" / "block_map.json",
                """
                {
                  "edit_block_sequence": ["E1"],
                  "blocks": [
                    {
                      "edit_id": "E1",
                      "source_block_id": "S1",
                      "original_order": 1,
                      "urakkai_order": 1
                    }
                  ],
                  "block_voice_switch_map": [
                    {"edit_id": "E1", "source_audio": "off", "tts": "off"}
                  ]
                }
                """,
            )
            write_json(
                root / "20_script" / "block_role_map.json",
                """
                {
                  "roles": [
                    {"edit_id": "E1", "caption_type": "speaker_quote"}
                  ]
                }
                """,
            )
            write_json(
                root / "20_script" / "block_voice_switch_map.json",
                """
                {
                  "switches": [
                    {"edit_id": "E1", "source_audio": "on", "tts": "off"}
                  ]
                }
                """,
            )
            write_json(
                root / "20_script" / "timeline_design.json",
                """
                {
                  "project_duration_sec": 3,
                  "segments": [
                    {
                      "edit_id": "E1",
                      "source_ref": "S1",
                      "source_order": 1,
                      "timeline_order": 1,
                      "assembly_role": "verified_speaker_quote",
                      "time_start": "00:00",
                      "time_end": "00:03",
                      "track": "audio.speaker_source",
                      "caption_type": "speaker_quote",
                      "visible_text_role": "speaker_quote",
                      "audio_role": "audio.speaker_source",
                      "duration_basis": "source_range",
                      "duration_status": "SOURCE_AUDIO_LOCKED",
                      "source_audio_range": {"start": "00:00", "end": "00:03"},
                      "quote_verification_status": "VERIFIED_STT",
                      "audio_policy": "source_on_tts_off",
                      "visual_strategy": "source_visual_action"
                    }
                  ]
                }
                """,
            )
            write_json(
                root / "20_script" / "timeline_design_gate.json",
                """
                {
                  "status": "PASS"
                }
                """,
            )
            write_json(
                root / "20_script" / "humanize_korean_gate.json",
                """
                {
                  "status": "PASS",
                  "structure_changed": false,
                  "protected_fields_changed": false
                }
                """,
            )
            write_json(
                root / "20_script" / "report1_handoff.json",
                """
                {
                  "gate_name": "REPORT1_HANDOFF_GATE",
                  "status": "PASS",
                  "owner_skill": "00-tikitaka",
                  "next_skill": "000short-production-agent",
                  "next_gate": "CAPCUT_OPENABLE_PROJECT",
                  "report1_approved": true,
                  "voice_audio_route_decided": true
                }
                """,
            )
            create_source_identity_and_linked_draft(root)
            reference_path = root / "capcut_refs" / "shrt white"
            reference_path.mkdir(parents=True)

            result = module.validate_capcut_openable_project_entry(
                {
                    "user_request": "capcut project",
                    "report1_approved": True,
                    "voice_audio_route_decided": True,
                    "template_profile": "shrt_white_base_v1",
                    "reference_project_name": "shrt white",
                    "reference_project_path": str(reference_path),
                    "derived_from_reference_project": True,
                },
                root,
            )

            self.assertEqual(result["status"], "CAPCUT_OPENABLE_PROJECT_ALLOWED")
            self.assertEqual(result["script_status"], "SCRIPT_LOCK_PACKAGE")
            self.assertEqual(result["next_gate"], "ASSET_PREP_GATE")


if __name__ == "__main__":
    unittest.main()

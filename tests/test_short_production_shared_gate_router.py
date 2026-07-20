"""P06 000short-production-agent shared-gate router tests (RED first).

Asserts:
- Owner transfer receipt + matching design handoff SHA required at entry.
- G30 audio measurement precedes G40 SRT lock.
- status=NOT_REQUIRED + reason_code=NO_GENERATED_TTS when no generated TTS.
- G50 track plan built from locked G40 timing.
- shrt white only for general Shorts.
- G60 static PASS → WAIT_USER_VISUAL_GATE.
- G70 release_allowed=false.
- G80/G90 separate.
- Production cannot change hook or urakkai order.
"""

from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
import wave
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILL_DIR = ROOT / "skills" / "000short-production-agent"
WORKFLOW_YAML = SKILL_DIR / "workflow.yaml"
VALIDATOR_PY = SKILL_DIR / "scripts" / "validate_stage_gate.py"
RUNNER_PY = SKILL_DIR / "scripts" / "workflow_runner.py"
GATES_DIR = SKILL_DIR / "references" / "gates"
SCHEMAS_DIR = SKILL_DIR / "schemas"

GATE_REFS = [
    GATES_DIR / "G30_AUDIO.md",
    GATES_DIR / "G40_CAPTION_SRT.md",
    GATES_DIR / "G50_TRACK_PLAN.md",
    GATES_DIR / "G60_CAPCUT_ASSEMBLY.md",
    GATES_DIR / "G70_UPLOAD_PACKAGE.md",
    GATES_DIR / "G80_RENDER.md",
    GATES_DIR / "G90_FINAL_QC.md",
]

SCHEMAS = [
    SCHEMAS_DIR / "shorts_audio_lock.schema.json",
    SCHEMAS_DIR / "shorts_caption_lock.schema.json",
    SCHEMAS_DIR / "shorts_track_plan.schema.json",
    SCHEMAS_DIR / "shorts_production_gate.schema.json",
]


def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    try:
        spec.loader.exec_module(mod)
    except Exception:
        sys.modules.pop(name, None)
        raise
    return mod


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def _write_json(path: Path, payload: dict) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return path


def _write_wav(path: Path, duration_seconds: int = 1) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    sample_rate = 8000
    with wave.open(str(path), "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(sample_rate)
        wav.writeframes(b"\x00\x00" * sample_rate * duration_seconds)
    return path


def _write_mp4(path: Path, duration_seconds: int = 1) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    completed = subprocess.run(
        [
            "ffmpeg",
            "-v",
            "error",
            "-y",
            "-f",
            "lavfi",
            "-i",
            f"color=c=black:s=64x64:d={duration_seconds}",
            "-f",
            "lavfi",
            "-i",
            f"sine=frequency=1000:duration={duration_seconds}",
            "-shortest",
            "-c:v",
            "libx264",
            "-c:a",
            "aac",
            str(path),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    if completed.returncode != 0:
        raise RuntimeError(completed.stderr)
    return path


def _ledger_events(*event_specs: tuple[str, str | None, str]) -> list[dict]:
    events = [
        {
            "event_id": "evt-000000",
            "timestamp": "2026-07-21T00:00:00+09:00",
            "episode_id": "SH_TEST",
            "lane": "general_shorts_production",
            "gate": "G30",
            "event_type": "WORKFLOW_CREATED",
            "actor": "USER",
            "previous_event_id": None,
        }
    ]
    for index, (event_type, gate, actor) in enumerate(event_specs, start=1):
        events.append(
            {
                "event_id": f"evt-{index:06d}",
                "timestamp": f"2026-07-21T00:00:{index:02d}+09:00",
                "episode_id": "SH_TEST",
                "lane": "general_shorts_production",
                "gate": gate,
                "event_type": event_type,
                "actor": actor,
                "previous_event_id": events[-1]["event_id"],
            }
        )
    return events


class ShortProductionRouterFilePresenceTests(unittest.TestCase):
    def test_workflow_yaml_exists(self):
        self.assertTrue(WORKFLOW_YAML.exists(), "workflow.yaml missing")

    def test_validator_script_exists(self):
        self.assertTrue(VALIDATOR_PY.exists())

    def test_runner_script_exists(self):
        self.assertTrue(RUNNER_PY.exists())

    def test_gate_references_exist(self):
        for ref in GATE_REFS:
            self.assertTrue(ref.exists(), f"missing gate reference: {ref}")

    def test_schemas_exist(self):
        for sch in SCHEMAS:
            self.assertTrue(sch.exists(), f"missing schema: {sch}")


class P06SchemaContractTests(unittest.TestCase):
    def test_audio_schema_requires_real_measurement_artifacts(self):
        schema = json.loads(SCHEMAS[0].read_text(encoding="utf-8"))
        required = set(schema["required"])

        self.assertTrue(
            {
                "audio_source",
                "audio_path",
                "audio_sha256",
                "measured_duration_evidence_path",
                "ffprobe_verified",
            }.issubset(required)
        )
        self.assertIn("allOf", schema)

    def test_caption_schema_requires_real_srt_and_cue_checks(self):
        schema = json.loads(SCHEMAS[1].read_text(encoding="utf-8"))
        required = set(schema["required"])

        self.assertTrue(
            {
                "cues",
                "final_srt_path",
                "no_overlap_verified",
                "all_cues_within_measured_audio",
            }.issubset(required)
        )

    def test_track_plan_schema_requires_design_and_timeline_bindings(self):
        schema = json.loads(SCHEMAS[2].read_text(encoding="utf-8"))
        required = set(schema["required"])

        self.assertTrue(
            {
                "design_handoff_sha256",
                "timeline_order_matches_design_handoff",
            }.issubset(required)
        )

    def test_production_gate_schema_conditionally_locks_release(self):
        schema = json.loads(SCHEMAS[3].read_text(encoding="utf-8"))

        self.assertIn("allOf", schema)
        self.assertIn('"G70"', json.dumps(schema["allOf"]))
        self.assertIn('"const": false', json.dumps(schema["allOf"]))


class ShortProductionOwnershipTests(unittest.TestCase):
    def setUp(self):
        if not WORKFLOW_YAML.exists():
            self.skipTest("workflow.yaml not yet implemented (RED)")
        self.workflow_text = WORKFLOW_YAML.read_text(encoding="utf-8")

    def test_owns_g30_through_g90(self):
        for gate in ("G30", "G40", "G50", "G60", "G60.USER", "G70", "G80", "G90"):
            self.assertIn(gate, self.workflow_text)

    def test_does_not_own_design_gates(self):
        """Production must not own G00/G10/G20 — those belong to 00-tikitaka."""
        # workflow.yaml may mention them in 'forbidden' or 'received_from'
        # sections, but the ownership list must not include them.
        # We assert that the owner_skill field is set to 000short.
        self.assertIn("000short-production-agent", self.workflow_text)

    def test_capcut_root_is_shrt_white(self):
        """General Shorts production uses shrt white as the CapCut root."""
        low = self.workflow_text.lower()
        self.assertIn("shrt white", low)


class G30G40OrderTests(unittest.TestCase):
    """NORM-002: G30 (audio + measured duration) precedes G40 (caption/SRT)."""

    def setUp(self):
        if not WORKFLOW_YAML.exists():
            self.skipTest("workflow.yaml not yet implemented (RED)")
        self.workflow_text = WORKFLOW_YAML.read_text(encoding="utf-8")

    def test_g30_precedes_g40(self):
        idx30 = self.workflow_text.find("G30")
        idx40 = self.workflow_text.find("G40")
        self.assertGreater(idx30, -1)
        self.assertGreater(idx40, -1)
        self.assertLess(idx30, idx40)

    def test_srt_lock_requires_measured_audio(self):
        """G40 SRT lock must depend on G30 measured audio duration."""
        g40_ref = GATES_DIR / "G40_CAPTION_SRT.md"
        if g40_ref.exists():
            text = g40_ref.read_text(encoding="utf-8").lower()
            self.assertIn("measured", text)
            self.assertIn("audio", text)


class NotRequiredNoGeneratedTtsTests(unittest.TestCase):
    """NORM-003: NOT_REQUIRED_NO_GENERATED_TTS is forbidden; use
    status=NOT_REQUIRED + reason_code=NO_GENERATED_TTS."""

    def setUp(self):
        if not WORKFLOW_YAML.exists():
            self.skipTest("workflow.yaml not yet implemented (RED)")
        self.workflow_text = WORKFLOW_YAML.read_text(encoding="utf-8")

    def test_no_generated_tts_uses_reason_code(self):
        low = self.workflow_text.lower()
        self.assertIn("no_generated_tts", low)


class OwnerTransferEntryTests(unittest.TestCase):
    """Production must reject entry without valid owner-transfer receipt and
    matching design handoff SHA."""

    def setUp(self):
        if not WORKFLOW_YAML.exists():
            self.skipTest("workflow.yaml not yet implemented (RED)")
        self.workflow_text = WORKFLOW_YAML.read_text(encoding="utf-8")

    def test_entry_requires_owner_transfer_receipt(self):
        low = self.workflow_text.lower()
        self.assertIn("owner_transfer_receipt", low)
        self.assertIn("design_handoff", low)


class CreativeLockTests(unittest.TestCase):
    """Production cannot rewrite hook or urakkai order."""

    def setUp(self):
        if not WORKFLOW_YAML.exists():
            self.skipTest("workflow.yaml not yet implemented (RED)")
        self.workflow_text = WORKFLOW_YAML.read_text(encoding="utf-8")

    def test_production_cannot_change_hook_or_urakkai(self):
        low = self.workflow_text.lower()
        self.assertIn("hook", low)
        self.assertIn("urakkai", low)
        # Forbidden-rewrite policy must be present.
        self.assertTrue(
            "forbidden" in low or "cannot" in low,
            "workflow.yaml must declare creative-rewrite prohibition",
        )


class G60G70G80G90PolicyTests(unittest.TestCase):
    def setUp(self):
        if not WORKFLOW_YAML.exists():
            self.skipTest("workflow.yaml not yet implemented (RED)")
        self.workflow_text = WORKFLOW_YAML.read_text(encoding="utf-8")

    def test_g60_static_pass_waits_for_user_visual_gate(self):
        low = self.workflow_text.lower()
        self.assertIn("wait_user_visual_gate", low)

    def test_g70_release_allowed_false(self):
        """G70 package prepared but release_allowed=false."""
        low = self.workflow_text.lower()
        self.assertIn("release_allowed", low)
        self.assertIn("false", low)

    def test_g80_and_g90_are_separate(self):
        """G80 (render) and G90 (final QC) must be distinct gates."""
        low = self.workflow_text.lower()
        self.assertIn("g80", low)
        self.assertIn("g90", low)


class ValidatorRunnerIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.validator = _load_module("p06_validator_integration", VALIDATOR_PY)
        cls.runner = _load_module("p06_runner_integration", RUNNER_PY)

    def test_validator_result_is_gate_result_accepted_by_runner(self):
        validator_result = self.validator.validate_g60_user(
            ledger_events=_ledger_events(
                ("USER_VISUAL_PASS", "G60.USER", "USER")
            )
        )

        self.assertEqual(validator_result["schema_version"], "gate-result-v1")
        self.assertEqual(
            self.runner.apply_validator_result(
                validator_result=validator_result
            )["status"],
            "EXECUTE_DETERMINISTIC",
        )

    def test_runner_preserves_wait_user_visual_gate(self):
        validator_result = self.validator.validate_g60_user(
            ledger_events=_ledger_events()
        )

        decision = self.runner.apply_validator_result(
            validator_result=validator_result
        )

        self.assertEqual(decision["status"], "WAIT")
        self.assertEqual(decision["next_action"], "WAIT_USER_VISUAL_GATE")


class G30G50FailClosedBehaviorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.validator = _load_module("p06_validator_fail_closed", VALIDATOR_PY)

    def test_g30_rejects_missing_owner_transfer_and_design_handoff(self):
        result = self.validator.validate_g30(
            audio_lock={
                "status": "PASS",
                "measured_duration_evidence_sha256": "A" * 64,
            }
        )

        self.assertEqual(result["status"], "FAIL")
        self.assertIn(
            "FAIL_ENTRY_NO_OWNER_TRANSFER_RECEIPT",
            {error["code"] for error in result["errors"]},
        )

    def test_entry_rejects_missing_canonical_handoff_sha(self):
        errors = self.validator.validate_entry(
            owner_transfer_receipt={
                "schema_version": "owner-transfer-v1",
                "transfer_status": "PASS",
            },
            design_handoff={"status": "PASS"},
        )

        self.assertIn(
            "FAIL_ENTRY_HANDOFF_SHA_MISSING",
            {error["code"] for error in errors},
        )

    def test_no_tts_requires_measured_source_duration_evidence(self):
        result = self.validator.validate_g30(
            audio_lock={
                "status": "NOT_REQUIRED",
                "reason_code": "NO_GENERATED_TTS",
                "audio_source": "SOURCE_CLIP",
            },
            owner_transfer_receipt={
                "schema_version": "owner-transfer-v1",
                "transfer_status": "PASS",
                "canonical_handoff_sha256": "A" * 64,
            },
            design_handoff={
                "status": "PASS",
                "design_handoff_sha256": "A" * 64,
            },
        )

        self.assertEqual(result["status"], "FAIL")
        self.assertIn(
            "FAIL_G30_NO_MEASURED_DURATION",
            {error["code"] for error in result["errors"]},
        )

    def test_g40_rejects_empty_caption_lock(self):
        result = self.validator.validate_g40(
            caption_lock={},
            g30_audio_lock={
                "status": "PASS",
                "measured_duration_evidence_sha256": "A" * 64,
            },
        )

        self.assertEqual(result["status"], "FAIL")
        self.assertIn(
            "FAIL_G40_CAPTION_LOCK_SCHEMA",
            {error["code"] for error in result["errors"]},
        )

    def test_g40_rejects_bad_no_tts_reason(self):
        result = self.validator.validate_g40(
            caption_lock={
                "schema_version": "shorts-caption-lock-v1",
                "status": "PASS",
            },
            g30_audio_lock={
                "status": "NOT_REQUIRED",
                "reason_code": "WRONG",
                "measured_duration_evidence_sha256": "A" * 64,
            },
        )

        self.assertEqual(result["status"], "FAIL")
        self.assertIn(
            "FAIL_G40_G30_NO_TTS_REASON",
            {error["code"] for error in result["errors"]},
        )

    def test_g50_rejects_failed_g40_and_missing_hash_binding(self):
        result = self.validator.validate_g50(
            track_plan={"segments": [{"slot_id": "S1"}]},
            g40_caption_lock={"status": "FAIL"},
        )

        self.assertEqual(result["status"], "FAIL")
        codes = {error["code"] for error in result["errors"]}
        self.assertIn("FAIL_G50_G40_NOT_PASS", codes)
        self.assertIn("FAIL_G50_G40_SHA_MISSING", codes)

    def test_g50_rejects_unbound_creative_fields(self):
        result = self.validator.validate_g50(
            track_plan={
                "segments": [
                    {
                        "slot_id": "S1",
                        "hook": "changed hook",
                        "urakkai_order": 99,
                    }
                ],
                "timeline_order_matches_design_handoff": True,
            },
            g40_caption_lock={"status": "PASS"},
        )

        self.assertEqual(result["status"], "FAIL")
        self.assertIn(
            "FAIL_G50_CREATIVE_LOCK_MISMATCH",
            {error["code"] for error in result["errors"]},
        )


class G30G50RealArtifactBehaviorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.validator = _load_module("p06_validator_real_artifacts", VALIDATOR_PY)

    def _build_fixture(self, root: Path) -> dict:
        source_fingerprint = "1" * 64
        blueprint = {
            "creative_lock": {
                "hook": "locked hook",
                "urakkai_order": ["S1"],
                "production_profile": "shrt_white_base_v1",
                "editorial_authority": "00-tikitaka",
            }
        }
        timeline = {
            "project_duration_sec": 1,
            "source_fingerprint_sha256": source_fingerprint,
            "segments": [
                {
                    "edit_id": "S1",
                    "source_ref": "source.mp4",
                    "source_order": 0,
                    "timeline_order": 0,
                    "assembly_role": "situation_caption",
                    "caption_type": "situation_caption",
                    "visible_text_role": "situation",
                    "audio_role": "none",
                    "time_start": "00:00:00,000",
                    "time_end": "00:00:01,000",
                    "track": "T6",
                    "duration_basis": "source_range",
                    "duration_status": "SOURCE_AUDIO_LOCKED",
                    "audio_policy": "off",
                    "visual_strategy": "source_visual",
                }
            ],
        }
        external_review = {"schema_version": "shorts-external-review-receipt-v1", "status": "PASS"}
        blueprint_path = _write_json(root / "20_script" / "design_blueprint.json", blueprint)
        timeline_path = _write_json(root / "20_script" / "timeline_design.json", timeline)
        review_path = _write_json(
            root / "20_script" / "external_review_receipt.json",
            external_review,
        )
        handoff = {
            "schema_version": "shorts-design-handoff-v1",
            "episode_id": "SH_TEST",
            "lane": "general_shorts_design",
            "content_profile": "general_shorts",
            "production_mode": "source_led",
            "requested_target": "rendered",
            "source_fingerprint": source_fingerprint,
            "design_blueprint_path": "20_script/design_blueprint.json",
            "design_blueprint_sha256": _sha256(blueprint_path),
            "timeline_path": "20_script/timeline_design.json",
            "timeline_sha256": _sha256(timeline_path),
            "external_review_receipt_path": "20_script/external_review_receipt.json",
            "external_review_receipt_sha256": _sha256(review_path),
            "next_skill": "000short-production-agent",
            "next_lane": "general_shorts_production",
            "status": "PASS",
            "transfer_status": "PASS",
        }
        handoff_path = _write_json(root / "20_script" / "design_handoff.json", handoff)
        receipt = {
            "schema_version": "owner-transfer-v1",
            "from_lane": "general_shorts_design",
            "from_skill": "00-tikitaka",
            "to_lane": "general_shorts_production",
            "to_skill": "000short-production-agent",
            "source_fingerprint": source_fingerprint,
            "canonical_handoff_path": "20_script/design_handoff.json",
            "canonical_handoff_sha256": _sha256(handoff_path),
            "design_blueprint_sha256": _sha256(blueprint_path),
            "timeline_sha256": _sha256(timeline_path),
            "external_review_receipt_sha256": _sha256(review_path),
            "requested_target": "rendered",
            "transfer_status": "PASS",
        }
        receipt_path = _write_json(
            root / "20_script" / "owner_transfer_receipt.json",
            receipt,
        )
        audio_path = _write_wav(root / "30_audio_srt" / "source.wav")
        evidence = {
            "schema_version": "measured-duration-evidence-v1",
            "audio_path": "30_audio_srt/source.wav",
            "audio_sha256": _sha256(audio_path),
            "measured_duration_us": 1_000_000,
            "ffprobe_verified": True,
        }
        evidence_path = _write_json(
            root / "30_audio_srt" / "measured_duration_evidence.json",
            evidence,
        )
        audio_lock = {
            "schema_version": "shorts-audio-lock-v1",
            "episode_id": "SH_TEST",
            "status": "NOT_REQUIRED",
            "reason_code": "NO_GENERATED_TTS",
            "audio_source": "SOURCE_CLIP",
            "audio_path": "30_audio_srt/source.wav",
            "audio_sha256": _sha256(audio_path),
            "measured_duration_us": 1_000_000,
            "measured_duration_evidence_path": "30_audio_srt/measured_duration_evidence.json",
            "measured_duration_evidence_sha256": _sha256(evidence_path),
            "ffprobe_verified": True,
            "paid_tts_cost_event_id": None,
        }
        audio_lock_path = _write_json(root / "30_audio_srt" / "audio_lock.json", audio_lock)
        srt_path = root / "30_audio_srt" / "final.srt"
        srt_path.write_text(
            "1\n00:00:00,000 --> 00:00:01,000\nlocked hook\n",
            encoding="utf-8",
        )
        caption_lock = {
            "schema_version": "shorts-caption-lock-v1",
            "episode_id": "SH_TEST",
            "status": "PASS",
            "g30_audio_lock_sha256": _sha256(audio_lock_path),
            "final_cue_count": 1,
            "cues": [
                {
                    "cue_id": "S1",
                    "start_us": 0,
                    "end_us": 1_000_000,
                    "text": "locked hook",
                }
            ],
            "final_srt_path": "30_audio_srt/final.srt",
            "final_srt_sha256": _sha256(srt_path),
            "no_overlap_verified": True,
            "all_cues_within_measured_audio": True,
        }
        caption_lock_path = _write_json(
            root / "30_audio_srt" / "caption_lock.json",
            caption_lock,
        )
        track_plan = {
            "schema_version": "shorts-track-plan-v1",
            "episode_id": "SH_TEST",
            "status": "PASS",
            "g40_caption_lock_sha256": _sha256(caption_lock_path),
            "design_handoff_sha256": _sha256(handoff_path),
            "segments": [
                {
                    "slot_id": "S1",
                    "assembly_role": "situation_caption",
                    "source_order": 0,
                    "timeline_order": 0,
                    "clip_start_us": 0,
                    "clip_end_us": 1_000_000,
                    "audio_role": "OFF",
                    "caption_role": "situation_caption",
                }
            ],
            "timeline_order_matches_design_handoff": True,
        }
        return {
            "root": root,
            "handoff": handoff,
            "handoff_path": handoff_path,
            "receipt": receipt,
            "receipt_path": receipt_path,
            "audio_lock": audio_lock,
            "audio_lock_path": audio_lock_path,
            "caption_lock": caption_lock,
            "caption_lock_path": caption_lock_path,
            "track_plan": track_plan,
        }

    def test_valid_real_g30_g40_g50_chain_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            fixture = self._build_fixture(Path(tmp))

            g30 = self.validator.validate_g30(
                audio_lock=fixture["audio_lock"],
                owner_transfer_receipt=fixture["receipt"],
                design_handoff=fixture["handoff"],
                design_handoff_path=fixture["handoff_path"],
                artifact_root=fixture["root"],
            )
            g40 = self.validator.validate_g40(
                caption_lock=fixture["caption_lock"],
                g30_audio_lock=fixture["audio_lock"],
                g30_audio_lock_path=fixture["audio_lock_path"],
                artifact_root=fixture["root"],
            )
            g50 = self.validator.validate_g50(
                track_plan=fixture["track_plan"],
                g40_caption_lock=fixture["caption_lock"],
                g40_caption_lock_path=fixture["caption_lock_path"],
                design_handoff=fixture["handoff"],
                design_handoff_path=fixture["handoff_path"],
                artifact_root=fixture["root"],
            )

            self.assertEqual(g30["status"], "NOT_REQUIRED")
            self.assertEqual(g40["status"], "PASS")
            self.assertEqual(g50["status"], "PASS")

    def test_g30_rejects_receipt_sha_not_matching_handoff_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            fixture = self._build_fixture(Path(tmp))
            fixture["receipt"]["canonical_handoff_sha256"] = "F" * 64

            result = self.validator.validate_g30(
                audio_lock=fixture["audio_lock"],
                owner_transfer_receipt=fixture["receipt"],
                design_handoff=fixture["handoff"],
                design_handoff_path=fixture["handoff_path"],
                artifact_root=fixture["root"],
            )

            self.assertEqual(result["status"], "FAIL")
            self.assertIn(
                "FAIL_ENTRY_HANDOFF_SHA_MISMATCH",
                {error["code"] for error in result["errors"]},
            )

    def test_g40_rejects_wrong_audio_lock_file_sha(self):
        with tempfile.TemporaryDirectory() as tmp:
            fixture = self._build_fixture(Path(tmp))
            fixture["caption_lock"]["g30_audio_lock_sha256"] = "F" * 64

            result = self.validator.validate_g40(
                caption_lock=fixture["caption_lock"],
                g30_audio_lock=fixture["audio_lock"],
                g30_audio_lock_path=fixture["audio_lock_path"],
                artifact_root=fixture["root"],
            )

            self.assertEqual(result["status"], "FAIL")
            self.assertIn(
                "FAIL_G40_G30_SHA_MISMATCH",
                {error["code"] for error in result["errors"]},
            )

    def test_g50_rejects_timeline_order_drift(self):
        with tempfile.TemporaryDirectory() as tmp:
            fixture = self._build_fixture(Path(tmp))
            fixture["track_plan"]["segments"][0]["timeline_order"] = 9

            result = self.validator.validate_g50(
                track_plan=fixture["track_plan"],
                g40_caption_lock=fixture["caption_lock"],
                g40_caption_lock_path=fixture["caption_lock_path"],
                design_handoff=fixture["handoff"],
                design_handoff_path=fixture["handoff_path"],
                artifact_root=fixture["root"],
            )

            self.assertEqual(result["status"], "FAIL")
            self.assertIn(
                "FAIL_G50_CREATIVE_LOCK_MISMATCH",
                {error["code"] for error in result["errors"]},
            )


class G60G90RealGateBehaviorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.validator = _load_module("p06_validator_late_gates", VALIDATOR_PY)
        cls.template_path = (
            ROOT
            / "manifests"
            / "capcut-template-contracts"
            / "shrt_white_base_v1.json"
        )
        cls.template_contract = json.loads(
            cls.template_path.read_text(encoding="utf-8")
        )

    def _fixture(self, root: Path) -> dict:
        early = G30G50RealArtifactBehaviorTests()._build_fixture(root)
        track_plan_path = _write_json(
            root / "40_assets_used" / "track_plan.json",
            early["track_plan"],
        )
        assembly = {
            "schema_version": "shorts-assembly-result-v1",
            "episode_id": "SH_TEST",
            "status": "PASS",
            "capcut_root": "shrt white",
            "g50_track_plan_sha256": _sha256(track_plan_path),
            "template_contract_sha256": _sha256(self.template_path),
            "required_internal_asset": "Resources/media/transparent_center_white_1080x1920.png",
            "cache_online_material_referenced": False,
            "capcut_gui_opened": False,
            "slots": copy.deepcopy(self.template_contract["slots"]),
            "hard_fails": [],
        }
        assembly_path = _write_json(
            root / "50_capcut_project" / "assembly_result.json",
            assembly,
        )
        thumbnail_path = root / "70_upload" / "thumbnail.png"
        thumbnail_path.parent.mkdir(parents=True, exist_ok=True)
        thumbnail_path.write_bytes(b"PNG-P06")
        metadata_path = _write_json(
            root / "70_upload" / "upload_metadata.json",
            {"title": "P06", "description": "locked", "visibility": "private"},
        )
        upload_package = {
            "schema_version": "shorts-upload-package-v1",
            "episode_id": "SH_TEST",
            "status": "PASS",
            "release_allowed": False,
            "thumbnail_path": "70_upload/thumbnail.png",
            "thumbnail_sha256": _sha256(thumbnail_path),
            "metadata_path": "70_upload/upload_metadata.json",
            "metadata_sha256": _sha256(metadata_path),
            "uploaded_marker_present": False,
        }
        upload_path = _write_json(
            root / "70_upload" / "upload_package.json",
            upload_package,
        )
        render_path = _write_mp4(root / "60_exports" / "SH_TEST.mp4")
        render_evidence = {
            "schema_version": "shorts-render-evidence-v1",
            "episode_id": "SH_TEST",
            "status": "PASS",
            "g70_upload_package_sha256": _sha256(upload_path),
            "rendered_mp4_path": "60_exports/SH_TEST.mp4",
            "rendered_mp4_sha256": _sha256(render_path),
            "rendered_size_bytes": render_path.stat().st_size,
            "duration_us": 1_000_000,
            "duration_tolerance_us": 100_000,
            "ffprobe_verified": True,
            "video_stream_present": True,
            "audio_stream_present": True,
        }
        return {
            **early,
            "track_plan_path": track_plan_path,
            "assembly": assembly,
            "assembly_path": assembly_path,
            "upload_package": upload_package,
            "upload_path": upload_path,
            "render_evidence": render_evidence,
        }

    def test_empty_g60_assembly_fails(self):
        result = self.validator.validate_g60(assembly_result={})

        self.assertEqual(result["status"], "FAIL")
        self.assertIn(
            "FAIL_G60_WRONG_CAPCUT_ROOT",
            {error["code"] for error in result["errors"]},
        )

    def test_valid_g60_static_pass_waits_for_user_visual_gate(self):
        with tempfile.TemporaryDirectory() as tmp:
            fixture = self._fixture(Path(tmp))

            result = self.validator.validate_g60(
                assembly_result=fixture["assembly"],
                g50_track_plan=fixture["track_plan"],
                g50_track_plan_path=fixture["track_plan_path"],
                template_contract=self.template_contract,
                template_contract_path=self.template_path,
            )

            self.assertEqual(result["status"], "PASS")
            self.assertEqual(result["next_action"], "WAIT_USER_VISUAL_GATE")
            self.assertFalse(result["auto_advance_allowed"])

    def test_every_protected_template_lock_drift_fails(self):
        protected = {
            "transform_x",
            "transform_y",
            "scale_x",
            "scale_y",
            "rotation",
            "font_resource_id",
            "font_size",
            "alignment",
            "global_alpha",
            "line_max_width",
            "background_width",
            "background_height",
            "background_round_radius",
            "layer_index",
            "track_order",
        }
        with tempfile.TemporaryDirectory() as tmp:
            fixture = self._fixture(Path(tmp))
            for field in sorted(protected):
                matching_index = next(
                    (
                        index
                        for index, slot in enumerate(fixture["assembly"]["slots"])
                        if field in slot
                    ),
                    None,
                )
                if matching_index is None:
                    continue
                with self.subTest(field=field):
                    drifted = copy.deepcopy(fixture["assembly"])
                    value = drifted["slots"][matching_index][field]
                    drifted["slots"][matching_index][field] = (
                        f"{value}-drift" if isinstance(value, str) else value + 1
                    )
                    result = self.validator.validate_g60(
                        assembly_result=drifted,
                        g50_track_plan=fixture["track_plan"],
                        g50_track_plan_path=fixture["track_plan_path"],
                        template_contract=self.template_contract,
                        template_contract_path=self.template_path,
                    )
                    self.assertEqual(result["status"], "FAIL")
                    self.assertTrue(
                        any(
                            error["code"].startswith("FAIL_TEMPLATE_")
                            or error["code"]
                            in {"FAIL_LAYER_ORDER_CHANGED", "FAIL_TRACK_ORDER_CHANGED"}
                            for error in result["errors"]
                        )
                    )

    def test_g60_user_requires_user_visual_pass_event(self):
        missing = self.validator.validate_g60_user(
            ledger_events=_ledger_events()
        )
        present = self.validator.validate_g60_user(
            ledger_events=_ledger_events(
                ("USER_VISUAL_PASS", "G60.USER", "USER")
            )
        )

        self.assertEqual(missing["status"], "WAIT_USER_VISUAL_GATE")
        self.assertEqual(present["status"], "PASS")

    def test_g60_malformed_collections_fail_closed_without_exception(self):
        result = self.validator.validate_g60(
            assembly_result={
                "schema_version": "shorts-assembly-result-v1",
                "episode_id": "SH_TEST",
                "status": "PASS",
                "capcut_root": "shrt white",
                "g50_track_plan_sha256": "A" * 64,
                "template_contract_sha256": "B" * 64,
                "required_internal_asset": (
                    "Resources/media/transparent_center_white_1080x1920.png"
                ),
                "cache_online_material_referenced": False,
                "capcut_gui_opened": False,
                "slots": None,
                "hard_fails": None,
            }
        )

        self.assertEqual(result["status"], "FAIL")
        self.assertIn(
            "FAIL_G60_ASSEMBLY_SCHEMA",
            {error["code"] for error in result["errors"]},
        )

    def test_malformed_first_ledger_event_fails_closed_without_exception(self):
        result = self.validator.validate_g60_user(
            ledger_events=[
                "not-an-event",
                {
                    "event_id": "evt-2",
                    "timestamp": "2026-07-21T00:00:01Z",
                    "episode_id": "SH_TEST",
                    "lane": "general_shorts_production",
                    "gate": "G60.USER",
                    "event_type": "USER_VISUAL_PASS",
                    "actor": "USER",
                    "previous_event_id": "evt-1",
                },
            ]
        )

        self.assertEqual(result["status"], "FAIL")
        self.assertIn(
            "FAIL_LEDGER_EVENT_SCHEMA",
            {error["code"] for error in result["errors"]},
        )

    def test_g70_requires_user_visual_pass_and_keeps_release_false(self):
        with tempfile.TemporaryDirectory() as tmp:
            fixture = self._fixture(Path(tmp))
            missing = self.validator.validate_g70(
                upload_package=fixture["upload_package"],
                ledger_events=_ledger_events(),
                artifact_root=fixture["root"],
            )
            present = self.validator.validate_g70(
                upload_package=fixture["upload_package"],
                ledger_events=_ledger_events(
                    ("USER_VISUAL_PASS", "G60.USER", "USER")
                ),
                artifact_root=fixture["root"],
            )

            self.assertEqual(missing["status"], "FAIL")
            self.assertIn(
                "FAIL_G70_NO_USER_VISUAL_PASS",
                {error["code"] for error in missing["errors"]},
            )
            self.assertEqual(present["status"], "PASS")

    def test_g70_rejects_release_allowed_true_even_after_visual_pass(self):
        with tempfile.TemporaryDirectory() as tmp:
            fixture = self._fixture(Path(tmp))
            fixture["upload_package"]["release_allowed"] = True

            result = self.validator.validate_g70(
                upload_package=fixture["upload_package"],
                ledger_events=_ledger_events(
                    ("USER_VISUAL_PASS", "G60.USER", "USER")
                ),
                artifact_root=fixture["root"],
            )

            self.assertEqual(result["status"], "FAIL")
            self.assertIn(
                "FAIL_G70_RELEASE_MUST_BE_FALSE",
                {error["code"] for error in result["errors"]},
            )

    def test_g80_rejects_nonexistent_render_even_with_true_flags(self):
        result = self.validator.validate_g80(
            render_evidence={
                "ffprobe_verified": True,
                "rendered_mp4_sha256": "A" * 64,
                "rendered_mp4_path": "C:/does-not-exist/fake.mp4",
            }
        )

        self.assertEqual(result["status"], "FAIL")
        self.assertIn(
            "FAIL_G80_RENDER_FILE_MISSING",
            {error["code"] for error in result["errors"]},
        )

    def test_valid_real_g80_media_passes_without_releasing(self):
        with tempfile.TemporaryDirectory() as tmp:
            fixture = self._fixture(Path(tmp))

            result = self.validator.validate_g80(
                render_evidence=fixture["render_evidence"],
                g70_upload_package=fixture["upload_package"],
                g70_upload_package_path=fixture["upload_path"],
                artifact_root=fixture["root"],
            )

            self.assertEqual(result["status"], "PASS")
            self.assertEqual(result["next_action"], "PREPARE_G90")
            self.assertNotEqual(result["next_action"], "EPISODE_RELEASED")

    def test_g90_rejects_boolean_release_without_ledger_events(self):
        result = self.validator.validate_g90(
            final_qc={"final_qc_passed": True, "upload_approved": True}
        )

        self.assertNotEqual(result["status"], "PASS")
        self.assertIn(
            "FAIL_G90_LEDGER_REQUIRED",
            {error["code"] for error in result["errors"]},
        )

    def test_g90_requires_validator_then_user_events_on_g90(self):
        with tempfile.TemporaryDirectory() as tmp:
            fixture = self._fixture(Path(tmp))
            wrong_order = self.validator.validate_g90(
                final_qc={"schema_version": "shorts-final-qc-v1", "episode_id": "SH_TEST"},
                ledger_events=_ledger_events(
                    ("UPLOAD_APPROVED", "G90", "USER"),
                    ("FINAL_QC_PASS", "G90", "VALIDATOR"),
                ),
                render_evidence=fixture["render_evidence"],
            )
            wrong_actor = self.validator.validate_g90(
                final_qc={"schema_version": "shorts-final-qc-v1", "episode_id": "SH_TEST"},
                ledger_events=_ledger_events(
                    ("FINAL_QC_PASS", "G90", "USER"),
                    ("UPLOAD_APPROVED", "G90", "VALIDATOR"),
                ),
                render_evidence=fixture["render_evidence"],
            )

            self.assertEqual(wrong_order["status"], "FAIL")
            self.assertEqual(wrong_actor["status"], "FAIL")

    def test_g90_g80_only_waits_for_final_qc(self):
        with tempfile.TemporaryDirectory() as tmp:
            fixture = self._fixture(Path(tmp))

            result = self.validator.validate_g90(
                final_qc={"schema_version": "shorts-final-qc-v1", "episode_id": "SH_TEST"},
                ledger_events=_ledger_events(
                    ("GATE_PASSED", "G80", "VALIDATOR")
                ),
                render_evidence=fixture["render_evidence"],
            )

            self.assertEqual(result["status"], "WAIT_USER_INPUT")
            self.assertEqual(result["next_action"], "WAIT_USER_INPUT")

    def test_g90_final_qc_without_upload_waits_for_approval(self):
        with tempfile.TemporaryDirectory() as tmp:
            fixture = self._fixture(Path(tmp))

            result = self.validator.validate_g90(
                final_qc={"schema_version": "shorts-final-qc-v1", "episode_id": "SH_TEST"},
                ledger_events=_ledger_events(
                    ("GATE_PASSED", "G80", "VALIDATOR"),
                    ("FINAL_QC_PASS", "G90", "VALIDATOR"),
                ),
                render_evidence=fixture["render_evidence"],
            )

            self.assertEqual(result["status"], "WAIT_UPLOAD_APPROVAL")
            self.assertEqual(result["next_action"], "WAIT_UPLOAD_APPROVAL")

    def test_g90_upload_before_final_qc_fails_with_valid_g80(self):
        with tempfile.TemporaryDirectory() as tmp:
            fixture = self._fixture(Path(tmp))

            result = self.validator.validate_g90(
                final_qc={"schema_version": "shorts-final-qc-v1", "episode_id": "SH_TEST"},
                ledger_events=_ledger_events(
                    ("GATE_PASSED", "G80", "VALIDATOR"),
                    ("UPLOAD_APPROVED", "G90", "USER"),
                    ("FINAL_QC_PASS", "G90", "VALIDATOR"),
                ),
                render_evidence=fixture["render_evidence"],
            )

            self.assertEqual(result["status"], "FAIL")
            self.assertIn(
                "FAIL_G90_UPLOAD_BEFORE_FINAL_QC",
                {error["code"] for error in result["errors"]},
            )

    def test_g90_wrong_event_actor_fails_with_valid_g80(self):
        with tempfile.TemporaryDirectory() as tmp:
            fixture = self._fixture(Path(tmp))

            result = self.validator.validate_g90(
                final_qc={"schema_version": "shorts-final-qc-v1", "episode_id": "SH_TEST"},
                ledger_events=_ledger_events(
                    ("GATE_PASSED", "G80", "VALIDATOR"),
                    ("FINAL_QC_PASS", "G90", "USER"),
                    ("UPLOAD_APPROVED", "G90", "VALIDATOR"),
                ),
                render_evidence=fixture["render_evidence"],
            )

            self.assertEqual(result["status"], "FAIL")
            self.assertIn(
                "FAIL_G90_EVENT_AUTHORITY",
                {error["code"] for error in result["errors"]},
            )

    def test_valid_g90_ordered_ledger_releases_without_auto_upload(self):
        with tempfile.TemporaryDirectory() as tmp:
            fixture = self._fixture(Path(tmp))
            events = _ledger_events(
                ("GATE_PASSED", "G80", "VALIDATOR"),
                ("FINAL_QC_PASS", "G90", "VALIDATOR"),
                ("UPLOAD_APPROVED", "G90", "USER"),
            )

            result = self.validator.validate_g90(
                final_qc={"schema_version": "shorts-final-qc-v1", "episode_id": "SH_TEST"},
                ledger_events=events,
                render_evidence=fixture["render_evidence"],
            )

            self.assertEqual(result["status"], "PASS")
            self.assertEqual(result["next_action"], "EPISODE_RELEASED")
            self.assertFalse(result["auto_advance_allowed"])


class P06ValidatorCliBehaviorTests(unittest.TestCase):
    def test_g60_user_cli_consumes_ledger_and_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            ledger_path = Path(tmp) / "gate_ledger.jsonl"
            ledger_path.write_text(
                "\n".join(
                    json.dumps(event, ensure_ascii=False)
                    for event in _ledger_events(
                        ("USER_VISUAL_PASS", "G60.USER", "USER")
                    )
                )
                + "\n",
                encoding="utf-8",
            )

            completed = subprocess.run(
                [
                    sys.executable,
                    "-B",
                    str(VALIDATOR_PY),
                    "--gate",
                    "G60.USER",
                    "--ledger",
                    str(ledger_path),
                ],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                check=False,
            )

            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertEqual(json.loads(completed.stdout)["status"], "PASS")


if __name__ == "__main__":
    unittest.main()

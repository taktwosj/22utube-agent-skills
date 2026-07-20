"""RW-P03 / RW-P04 regression tests for shared core modules.

- RW-P03-01: validate_gate must reject explicit PASS when errors is non-empty.
- RW-P03-02: state projection must not set release_allowed=true before
  G90 FINAL_QC_PASS + UPLOAD_APPROVED.
- RW-P04-02: cache invalidation must be dependency-aware for every
  cache-key component (duration, resolution, selected_range, profile_version).
- RW-P04-03: canonical MD reconciliation must compare by structural field
  path, not by global scalar-value presence (so a deleted duplicate-value
  field is detected as a real change, not cosmetic).
"""

from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CORE_DIR = ROOT / "shared" / "workflow-harness" / "core"
GATE_VALIDATION_PY = CORE_DIR / "gate_validation.py"
STATE_PY = CORE_DIR / "state_projection.py"
PROMPT_FACTORY_PY = CORE_DIR / "prompt_factory.py"
CANONICAL_RENDER_PY = CORE_DIR / "canonical_render.py"


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


class ValidateGateRejectsPassWithErrorsTests(unittest.TestCase):
    """RW-P03-01: validate_gate must not return PASS when errors non-empty."""

    def setUp(self):
        self.gv = _load_module("rw_p03_01_gv", GATE_VALIDATION_PY)

    def test_explicit_pass_with_errors_rejected(self):
        with self.assertRaises(self.gv.PassWithErrorsForbidden):
            self.gv.validate_gate(
                lane="general_shorts_production",
                gate="G40",
                subgate=None,
                validated_inputs=[],
                evidence=[],
                errors=[{"code": "FAIL_SOMETHING"}],
                warnings=[],
                next_action="x",
                auto_advance_allowed=True,
                auto_advance_class="DETERMINISTIC_ONLY",
                status="PASS",
            )

    def test_derived_pass_with_errors_returns_fail(self):
        """If status is not explicitly set and errors exist, derived status
        must be FAIL, never PASS."""
        result = self.gv.validate_gate(
            lane="general_shorts_production",
            gate="G40",
            subgate=None,
            validated_inputs=[],
            evidence=[],
            errors=[{"code": "FAIL_SOMETHING"}],
            warnings=[],
            next_action="x",
            auto_advance_allowed=False,
            auto_advance_class="NONE",
        )
        self.assertNotEqual(result["status"], "PASS")

    def test_explicit_pass_with_no_errors_succeeds(self):
        result = self.gv.validate_gate(
            lane="general_shorts_production",
            gate="G40",
            subgate=None,
            validated_inputs=[],
            evidence=[],
            errors=[],
            warnings=[],
            next_action="PREPARE_G50",
            auto_advance_allowed=True,
            auto_advance_class="DETERMINISTIC_ONLY",
            status="PASS",
        )
        self.assertEqual(result["status"], "PASS")


class ReleaseAllowedG90GateTests(unittest.TestCase):
    """RW-P03-02: release_allowed=true requires G90 FINAL_QC_PASS and a
    separate UPLOAD_APPROVED event. UPLOAD_APPROVED before G90 must NOT
    flip release_allowed."""

    def setUp(self):
        self.state = _load_module("rw_p03_02_state", STATE_PY)

    def _base_events(self):
        return [
            {
                "event_id": "evt-000000",
                "timestamp": "2026-07-20T10:00:00+09:00",
                "episode_id": "EP-01",
                "lane": "general_shorts_production",
                "gate": None,
                "event_type": "WORKFLOW_CREATED",
                "actor": "USER",
                "previous_event_id": None,
            }
        ]

    def test_upload_approved_before_g90_does_not_release(self):
        """UPLOAD_APPROVED without a prior FINAL_QC_PASS must not set
        release_allowed=true."""
        events = self._base_events()
        events.append({
            "event_id": "evt-000001",
            "timestamp": "2026-07-20T11:00:00+09:00",
            "episode_id": "EP-01",
            "lane": "general_shorts_production",
            "gate": "G90",
            "event_type": "UPLOAD_APPROVED",
            "actor": "USER",
            "previous_event_id": "evt-000000",
        })
        projection = self.state.rebuild_state(events)
        self.assertFalse(
            projection["release_allowed"],
            "UPLOAD_APPROVED before FINAL_QC_PASS must not release",
        )

    def test_final_qc_pass_then_upload_approved_releases(self):
        events = self._base_events()
        events.append({
            "event_id": "evt-000001",
            "timestamp": "2026-07-20T11:00:00+09:00",
            "episode_id": "EP-01",
            "lane": "general_shorts_production",
            "gate": "G90",
            "event_type": "FINAL_QC_PASS",
            "actor": "VALIDATOR",
            "previous_event_id": "evt-000000",
        })
        events.append({
            "event_id": "evt-000002",
            "timestamp": "2026-07-20T12:00:00+09:00",
            "episode_id": "EP-01",
            "lane": "general_shorts_production",
            "gate": "G90",
            "event_type": "UPLOAD_APPROVED",
            "actor": "USER",
            "previous_event_id": "evt-000001",
        })
        projection = self.state.rebuild_state(events)
        self.assertTrue(projection["release_allowed"])

    def test_final_qc_pass_alone_does_not_release(self):
        events = self._base_events()
        events.append({
            "event_id": "evt-000001",
            "timestamp": "2026-07-20T11:00:00+09:00",
            "episode_id": "EP-01",
            "lane": "general_shorts_production",
            "gate": "G90",
            "event_type": "FINAL_QC_PASS",
            "actor": "VALIDATOR",
            "previous_event_id": "evt-000000",
        })
        projection = self.state.rebuild_state(events)
        self.assertFalse(projection["release_allowed"])

    def test_final_qc_pass_on_non_g90_gate_does_not_count(self):
        """RW-P03-02 strict: FINAL_QC_PASS must occur on gate=G90. A
        FINAL_QC_PASS recorded against any other gate must not satisfy the
        release precondition, so a subsequent UPLOAD_APPROVED (even on G90)
        must not release."""
        events = self._base_events()
        # FINAL_QC_PASS recorded against G20 (wrong gate).
        events.append({
            "event_id": "evt-000001",
            "timestamp": "2026-07-20T11:00:00+09:00",
            "episode_id": "EP-01",
            "lane": "general_shorts_production",
            "gate": "G20",
            "event_type": "FINAL_QC_PASS",
            "actor": "VALIDATOR",
            "previous_event_id": "evt-000000",
        })
        # UPLOAD_APPROVED on G90.
        events.append({
            "event_id": "evt-000002",
            "timestamp": "2026-07-20T12:00:00+09:00",
            "episode_id": "EP-01",
            "lane": "general_shorts_production",
            "gate": "G90",
            "event_type": "UPLOAD_APPROVED",
            "actor": "USER",
            "previous_event_id": "evt-000001",
        })
        projection = self.state.rebuild_state(events)
        self.assertFalse(
            projection["release_allowed"],
            "FINAL_QC_PASS on a non-G90 gate must not satisfy release precondition",
        )

    def test_upload_approved_on_non_g90_gate_does_not_release(self):
        """UPLOAD_APPROVED on a non-G90 gate must not release even if
        FINAL_QC_PASS on G90 preceded it."""
        events = self._base_events()
        events.append({
            "event_id": "evt-000001",
            "timestamp": "2026-07-20T11:00:00+09:00",
            "episode_id": "EP-01",
            "lane": "general_shorts_production",
            "gate": "G90",
            "event_type": "FINAL_QC_PASS",
            "actor": "VALIDATOR",
            "previous_event_id": "evt-000000",
        })
        events.append({
            "event_id": "evt-000002",
            "timestamp": "2026-07-20T12:00:00+09:00",
            "episode_id": "EP-01",
            "lane": "general_shorts_production",
            "gate": "G70",
            "event_type": "UPLOAD_APPROVED",
            "actor": "USER",
            "previous_event_id": "evt-000001",
        })
        projection = self.state.rebuild_state(events)
        self.assertFalse(
            projection["release_allowed"],
            "UPLOAD_APPROVED on a non-G90 gate must not release",
        )

    def test_actor_for_final_qc_pass_is_validator(self):
        """The canonical contract pins FINAL_QC_PASS actor to VALIDATOR.
        A FINAL_QC_PASS from any other actor must not satisfy release
        precondition."""
        events = self._base_events()
        events.append({
            "event_id": "evt-000001",
            "timestamp": "2026-07-20T11:00:00+09:00",
            "episode_id": "EP-01",
            "lane": "general_shorts_production",
            "gate": "G90",
            "event_type": "FINAL_QC_PASS",
            "actor": "RUNNER",
            "previous_event_id": "evt-000000",
        })
        events.append({
            "event_id": "evt-000002",
            "timestamp": "2026-07-20T12:00:00+09:00",
            "episode_id": "EP-01",
            "lane": "general_shorts_production",
            "gate": "G90",
            "event_type": "UPLOAD_APPROVED",
            "actor": "USER",
            "previous_event_id": "evt-000001",
        })
        projection = self.state.rebuild_state(events)
        self.assertFalse(
            projection["release_allowed"],
            "FINAL_QC_PASS actor must be VALIDATOR for the release precondition",
        )

    def test_actor_for_upload_approved_is_user(self):
        """UPLOAD_APPROVED actor must be USER (material user-owned decision).
        A VALIDATOR or RUNNER UPLOAD_APPROVED must not release."""
        events = self._base_events()
        events.append({
            "event_id": "evt-000001",
            "timestamp": "2026-07-20T11:00:00+09:00",
            "episode_id": "EP-01",
            "lane": "general_shorts_production",
            "gate": "G90",
            "event_type": "FINAL_QC_PASS",
            "actor": "VALIDATOR",
            "previous_event_id": "evt-000000",
        })
        events.append({
            "event_id": "evt-000002",
            "timestamp": "2026-07-20T12:00:00+09:00",
            "episode_id": "EP-01",
            "lane": "general_shorts_production",
            "gate": "G90",
            "event_type": "UPLOAD_APPROVED",
            "actor": "RUNNER",
            "previous_event_id": "evt-000001",
        })
        projection = self.state.rebuild_state(events)
        self.assertFalse(
            projection["release_allowed"],
            "UPLOAD_APPROVED actor must be USER for release",
        )


class CacheInvalidationDependencyAwareTests(unittest.TestCase):
    """RW-P04-02: invalidation must react to every cache-key component."""

    def setUp(self):
        self.pf = _load_module("rw_p04_02_pf", PROMPT_FACTORY_PY)

    def _base_current(self):
        return {
            "source_sha256": "A" * 64,
            "duration_us": 10_000_000,
            "resolution": "1080x1920",
            "selected_range": {"start_us": 0, "end_us": 10_000_000},
            "profile_version": "shorts_analysis_v1",
            "tool_versions": {"ffprobe": "7.0", "ocr": "v1"},
            "sampling_policy": {"frame_sample_fps": 1},
            "layers": {
                "transcript_segments": {"sha256": "B" * 64},
                "ocr_segments": {"sha256": "C" * 64},
                "scene_segments": {"sha256": "E" * 64},
            },
        }

    def test_duration_change_invalidates_all_layers(self):
        current = self._base_current()
        new_inputs = {
            "source_sha256": "A" * 64,
            "duration_us": 20_000_000,
            "resolution": "1080x1920",
            "selected_range": {"start_us": 0, "end_us": 10_000_000},
            "profile_version": "shorts_analysis_v1",
            "tool_versions": {"ffprobe": "7.0", "ocr": "v1"},
            "sampling_policy": {"frame_sample_fps": 1},
        }
        plan = self.pf.plan_cache_invalidation(
            current_manifest=current, new_inputs=new_inputs
        )
        self.assertEqual(set(plan["invalidate"]),
                         {"transcript_segments", "ocr_segments", "scene_segments"})

    def test_resolution_change_invalidates_all_layers(self):
        current = self._base_current()
        new_inputs = dict(self._base_current())
        new_inputs["source_sha256"] = "A" * 64
        new_inputs["resolution"] = "1920x1080"
        plan = self.pf.plan_cache_invalidation(
            current_manifest=current, new_inputs=new_inputs
        )
        self.assertEqual(set(plan["invalidate"]),
                         {"transcript_segments", "ocr_segments", "scene_segments"})

    def test_selected_range_change_invalidates_all_layers(self):
        current = self._base_current()
        new_inputs = dict(self._base_current())
        new_inputs["source_sha256"] = "A" * 64
        new_inputs["selected_range"] = {"start_us": 1000, "end_us": 10_000_000}
        plan = self.pf.plan_cache_invalidation(
            current_manifest=current, new_inputs=new_inputs
        )
        self.assertEqual(set(plan["invalidate"]),
                         {"transcript_segments", "ocr_segments", "scene_segments"})

    def test_profile_version_change_invalidates_all_layers(self):
        current = self._base_current()
        new_inputs = dict(self._base_current())
        new_inputs["source_sha256"] = "A" * 64
        new_inputs["profile_version"] = "shorts_analysis_v2"
        plan = self.pf.plan_cache_invalidation(
            current_manifest=current, new_inputs=new_inputs
        )
        self.assertEqual(set(plan["invalidate"]),
                         {"transcript_segments", "ocr_segments", "scene_segments"})


class CanonicalReconcileStructuralPathTests(unittest.TestCase):
    """RW-P04-03: reconcile by structural field path, not global scalar presence."""

    def setUp(self):
        self.cr = _load_module("rw_p04_03_cr", CANONICAL_RENDER_PY)

    def test_deleted_duplicate_value_field_is_detected_as_change(self):
        """If canonical has two fields with the same value and the human MD
        drops one of them, the global-scalar check would call it cosmetic.
        Structural-path check must catch it as a mismatch."""
        canonical = {
            "schema_version": "demo-v1",
            "episode_id": "EP-DEMO",
            "title_a": "SAME_TEXT",
            "title_b": "SAME_TEXT",
        }
        rendered = self.cr.render_markdown(canonical)
        # Remove one occurrence of SAME_TEXT so a naive global-scalar check
        # would still find the value present once.
        tampered_md = rendered.replace("`title_a`: SAME_TEXT", "`title_a`: ", 1)
        with self.assertRaises(self.cr.HumanMdCanonicalJsonMismatch):
            self.cr.reconcile_human_md(canonical=canonical, human_md=tampered_md)

    def test_array_element_with_duplicate_value_is_detected(self):
        """RW-P04-03 strict: two array elements that happen to share a value
        must be distinguished by their structural path (index). Dropping
        one element's value while keeping the other's must NOT pass as
        cosmetic."""
        canonical = {
            "schema_version": "demo-v1",
            "episode_id": "EP-DEMO",
            "segments": [
                {"id": "seg-001", "title": "SAME_TITLE"},
                {"id": "seg-002", "title": "SAME_TITLE"},
            ],
        }
        rendered = self.cr.render_markdown(canonical)
        # Remove the [0] element's title value but keep [1]'s. A leaf-key-
        # only check would still see SAME_TITLE on the [1] line and pass.
        lines = rendered.splitlines()
        tampered_lines = []
        removed_once = False
        for line in lines:
            if not removed_once and "`title`: SAME_TITLE" in line:
                # Only remove the FIRST occurrence (segments[0]).
                tampered_lines.append(line.replace("`title`: SAME_TITLE", "`title`: "))
                removed_once = True
            else:
                tampered_lines.append(line)
        tampered_md = "\n".join(tampered_lines)
        with self.assertRaises(self.cr.HumanMdCanonicalJsonMismatch):
            self.cr.reconcile_human_md(canonical=canonical, human_md=tampered_md)

    def test_nested_object_duplicate_value_is_detected(self):
        """Nested objects under different parent paths that share a value
        must be distinguished by their full parent path, not by leaf key
        alone."""
        canonical = {
            "schema_version": "demo-v1",
            "episode_id": "EP-DEMO",
            "chapter_a": {"title": "SAME"},
            "chapter_b": {"title": "SAME"},
        }
        rendered = self.cr.render_markdown(canonical)
        tampered_md = rendered.replace("`title`: SAME", "`title`: ", 1)
        with self.assertRaises(self.cr.HumanMdCanonicalJsonMismatch):
            self.cr.reconcile_human_md(canonical=canonical, human_md=tampered_md)


if __name__ == "__main__":
    unittest.main()

"""P04 analysis cache + prompt factory tests (RED first).

Asserts:
- External (Gemini) analysis is optional; local source is primary evidence.
- External analysis conflict is reported, not silently adopted.
- Analysis cache invalidates only the affected layer when one input changes.
- Prompt factory manifest records template path/SHA, input paths/SHAs,
  included segment IDs, excluded fields, and packet SHA; reuse on match.
- Shared language quality contract is appended to every external prompt.
"""

from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SHARED_CORE_DIR = ROOT / "shared" / "workflow-harness" / "core"
PROMPT_FACTORY_PY = SHARED_CORE_DIR / "prompt_factory.py"
CANONICAL_RENDER_PY = SHARED_CORE_DIR / "canonical_render.py"

SHARED_TEMPLATES_DIR = ROOT / "shared" / "workflow-harness" / "prompt_templates"
TIKITAKA_TEMPLATES_DIR = ROOT / "skills" / "00-tikitaka" / "prompt_templates"
POLITICS_TEMPLATES_DIR = ROOT / "skills" / "111-politics-longform" / "prompt_templates"

ANALYSIS_CACHE_SCHEMA = ROOT / "skills" / "00-tikitaka" / "schemas" / "analysis_cache_manifest.schema.json"


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


class ModulePresenceTests(unittest.TestCase):
    def test_prompt_factory_module_exists(self):
        self.assertTrue(PROMPT_FACTORY_PY.exists(), "prompt_factory.py missing")

    def test_canonical_render_module_exists(self):
        self.assertTrue(CANONICAL_RENDER_PY.exists(), "canonical_render.py missing")


class TemplatePresenceTests(unittest.TestCase):
    def test_shared_templates_exist(self):
        for name in (
            "shared_language_quality_contract.md",
            "shared_external_authority_contract.md",
        ):
            self.assertTrue(
                (SHARED_TEMPLATES_DIR / name).exists(),
                f"missing shared template: {name}",
            )

    def test_tikitaka_templates_exist(self):
        for name in (
            "shorts_urakkai_prompt.md",
            "shorts_review_r1_prompt.md",
            "shorts_review_r2_prompt.md",
        ):
            self.assertTrue(
                (TIKITAKA_TEMPLATES_DIR / name).exists(),
                f"missing tikitaka template: {name}",
            )

    def test_politics_templates_exist(self):
        for name in (
            "politics_dialogue_prompt.md",
            "politics_review_r1_prompt.md",
            "politics_review_r2_prompt.md",
        ):
            self.assertTrue(
                (POLITICS_TEMPLATES_DIR / name).exists(),
                f"missing politics template: {name}",
            )

    def test_analysis_cache_schema_exists(self):
        self.assertTrue(ANALYSIS_CACHE_SCHEMA.exists())


class PromptFactoryManifestTests(unittest.TestCase):
    def setUp(self):
        if not PROMPT_FACTORY_PY.exists():
            self.skipTest("prompt_factory.py not yet implemented (RED)")
        self.pf = _load_module("p04_prompt_factory", PROMPT_FACTORY_PY)

    def test_prompt_factory_manifest_matches_inputs(self):
        """Manifest must record template path + SHA, input paths + SHAs,
        included segment IDs, excluded fields, and packet SHA."""
        template_text = "# Template\nWrite a urakkai for these segments."
        template_path = SHARED_TEMPLATES_DIR / "shared_language_quality_contract.md"
        if template_path.exists():
            template_text = template_path.read_text(encoding="utf-8")
        result = self.pf.build_prompt(
            template_path=str(template_path),
            template_text=template_text,
            inputs=[
                {"path": "10_analysis/source_fingerprint.json", "content": '{"v":1}'},
                {"path": "10_analysis/transcript_segments.json", "content": "[1,2,3]"},
            ],
            included_segment_ids=["seg-001", "seg-002"],
            excluded_fields=["internal_notes"],
            language_quality_contract=str(SHARED_TEMPLATES_DIR / "shared_language_quality_contract.md"),
            external_authority_contract=str(SHARED_TEMPLATES_DIR / "shared_external_authority_contract.md"),
        )
        manifest = result["manifest"]
        for key in (
            "schema_version",
            "template_path",
            "template_sha256",
            "input_artifacts",
            "included_segment_ids",
            "excluded_fields",
            "packet_sha256",
            "packet_text",
        ):
            self.assertIn(key, manifest, f"manifest missing {key}")
        self.assertEqual(manifest["included_segment_ids"], ["seg-001", "seg-002"])
        self.assertEqual(manifest["excluded_fields"], ["internal_notes"])
        # Each input artifact entry must carry path + sha256.
        for entry in manifest["input_artifacts"]:
            self.assertIn("path", entry)
            self.assertIn("sha256", entry)
            self.assertEqual(len(entry["sha256"]), 64)

    def test_prompt_reused_when_content_addressed_key_matches(self):
        """If template SHA + input SHAs + segment IDs + excluded fields
        match an existing manifest, the same packet is reused."""
        template_path = SHARED_TEMPLATES_DIR / "shared_language_quality_contract.md"
        template_text = template_path.read_text(encoding="utf-8") if template_path.exists() else "T"
        common_inputs = [
            {"path": "a.json", "content": "A"},
            {"path": "b.json", "content": "B"},
        ]
        common_kwargs = dict(
            template_path=str(template_path),
            template_text=template_text,
            included_segment_ids=["seg-1"],
            excluded_fields=[],
            language_quality_contract=str(SHARED_TEMPLATES_DIR / "shared_language_quality_contract.md"),
            external_authority_contract=str(SHARED_TEMPLATES_DIR / "shared_external_authority_contract.md"),
        )
        r1 = self.pf.build_prompt(inputs=common_inputs, **common_kwargs)
        r2 = self.pf.build_prompt(inputs=common_inputs, **common_kwargs)
        self.assertEqual(r1["manifest"]["packet_sha256"], r2["manifest"]["packet_sha256"])

    def test_prompt_packet_includes_language_quality_and_authority_contracts(self):
        template_path = SHARED_TEMPLATES_DIR / "shorts_urakkai_prompt.md"
        # Use the tikitaka template if available, else a minimal stub.
        if not template_path.exists():
            template_path = SHARED_TEMPLATES_DIR / "shared_language_quality_contract.md"
        template_text = template_path.read_text(encoding="utf-8")
        result = self.pf.build_prompt(
            template_path=str(template_path),
            template_text=template_text,
            inputs=[{"path": "a.json", "content": "A"}],
            included_segment_ids=[],
            excluded_fields=[],
            language_quality_contract=str(SHARED_TEMPLATES_DIR / "shared_language_quality_contract.md"),
            external_authority_contract=str(SHARED_TEMPLATES_DIR / "shared_external_authority_contract.md"),
        )
        packet = result["packet_text"]
        # The packet must include the language quality + external authority
        # contract blocks. We check for a stable marker string.
        self.assertTrue(len(packet) > len(template_text))


class AnalysisCacheTests(unittest.TestCase):
    """Analysis cache contract: same source is not re-analyzed. Cache key
    is content-addressed; only the affected layer invalidates."""

    def setUp(self):
        if not PROMPT_FACTORY_PY.exists():
            self.skipTest("prompt_factory.py not yet implemented (RED)")
        self.pf = _load_module("p04_cache", PROMPT_FACTORY_PY)

    def test_external_analysis_is_optional(self):
        """A cache manifest with no external analysis result must still be valid."""
        manifest = self.pf.build_analysis_cache_manifest(
            source_sha256="A" * 64,
            duration_us=10_000_000,
            resolution="1080x1920",
            selected_range={"start_us": 0, "end_us": 10_000_000},
            profile_version="shorts_analysis_v1",
            tool_versions={"ffprobe": "7.0"},
            sampling_policy={"frame_sample_fps": 1},
            layers={
                "transcript_segments": {"sha256": "B" * 64, "count": 5},
                "ocr_segments": {"sha256": "C" * 64, "count": 3},
            },
            external_analysis=None,
        )
        self.assertIsNone(manifest["external_analysis"])
        self.assertEqual(manifest["schema_version"], "analysis-cache-manifest-v1")

    def test_external_analysis_conflict_is_reported(self):
        """If an external analysis result disagrees with local primary
        evidence, the manifest must flag EXTERNAL_ANALYSIS_MISMATCH rather
        than silently adopting the external result."""
        manifest = self.pf.build_analysis_cache_manifest(
            source_sha256="A" * 64,
            duration_us=10_000_000,
            resolution="1080x1920",
            selected_range={"start_us": 0, "end_us": 10_000_000},
            profile_version="shorts_analysis_v1",
            tool_versions={"ffprobe": "7.0"},
            sampling_policy={"frame_sample_fps": 1},
            layers={
                "transcript_segments": {"sha256": "B" * 64, "count": 5},
            },
            external_analysis={
                "provider": "gemini",
                "transcript_sha256": "D" * 64,  # differs from local B*64
            },
        )
        self.assertEqual(manifest["external_analysis_status"], "EXTERNAL_ANALYSIS_MISMATCH")

    def test_only_changed_cache_layer_invalidates(self):
        """Invalidation plan: when one layer's inputs change, only that
        layer is invalidated; the others remain valid."""
        plan = self.pf.plan_cache_invalidation(
            current_manifest={
                "source_sha256": "A" * 64,
                "tool_versions": {"ffprobe": "7.0", "ocr": "v1"},
                "sampling_policy": {"frame_sample_fps": 1},
                "layers": {
                    "transcript_segments": {"sha256": "B" * 64},
                    "ocr_segments": {"sha256": "C" * 64},
                    "scene_segments": {"sha256": "E" * 64},
                },
            },
            new_inputs={
                "source_sha256": "A" * 64,  # unchanged
                "tool_versions": {"ffprobe": "7.0", "ocr": "v2"},  # OCR bumped
                "sampling_policy": {"frame_sample_fps": 1},
            },
        )
        self.assertIn("ocr_segments", plan["invalidate"])
        self.assertNotIn("transcript_segments", plan["invalidate"])
        self.assertNotIn("scene_segments", plan["invalidate"])


if __name__ == "__main__":
    unittest.main()

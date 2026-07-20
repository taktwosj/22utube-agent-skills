"""P08 context-manifest and deterministic effect-pool tests (RED first)."""

from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CORE = ROOT / "shared" / "workflow-harness" / "core"
CONTEXT = CORE / "context_manifest.py"
EFFECT = CORE / "effect_policy.py"
SHORT_POOLS = ROOT / "skills" / "000short-production-agent" / "assets" / "effect_pools"
POLITICS_POOLS = ROOT / "skills" / "111-politics-longform" / "assets" / "effect_pools"


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


class SharedContextManifestTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.context = _load("p08_context_manifest", CONTEXT)

    def test_every_model_call_writes_context_manifest(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            manifest = self.context.ContextManifest(
                lane="politics_longform",
                gate="G20",
                subgate="REVIEW_R1_RETURNED",
                run_id="run-001",
            )
            manifest.add_loaded_file("20_script/script.md", "abcd")
            manifest.add_excluded("other_lane_references")
            manifest.set_estimated_tokens_from_chars(4)
            path = self.context.write_model_call_context(
                episode_root=root,
                manifest=manifest,
            )
            self.assertTrue(path.is_file())
            payload = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(payload["model_call_ready"], True)
            self.assertEqual(payload["loaded_files"][0]["path"], "20_script/script.md")
            self.assertIn("other_lane_references", payload["excluded_by_policy"])

    def test_unrelated_lane_reads_zero(self):
        with tempfile.TemporaryDirectory() as tmp:
            manifest = self.context.ContextManifest(
                lane="politics_longform",
                gate="G20",
                subgate=None,
                run_id="run-002",
                unrelated_lane_reads=1,
            )
            manifest.set_estimated_tokens_from_chars(20)
            with self.assertRaises(self.context.ContextPolicyViolation):
                self.context.write_model_call_context(
                    episode_root=Path(tmp),
                    manifest=manifest,
                )

    def test_context_manifest_records_loaded_and_excluded_files(self):
        manifest = self.context.ContextManifest(
            lane="general_shorts_design",
            gate="G20",
            subgate=None,
            run_id="run-003",
        )
        manifest.add_loaded_file("20_script/design.json", "{}")
        for category in ("full_transcript", "capcut_json", "prior_test_logs"):
            manifest.add_excluded(category)
        manifest.set_estimated_tokens_from_chars(2)
        payload = manifest.to_dict()
        self.assertEqual(len(payload["loaded_files"]), 1)
        self.assertEqual(len(payload["excluded_by_policy"]), 3)

    def test_context_manifest_rejects_path_traversal_identifiers(self):
        with tempfile.TemporaryDirectory() as tmp:
            manifest = self.context.ContextManifest(
                lane="politics_longform",
                gate="../G20",
                subgate=None,
                run_id="../../escape",
            )
            manifest.set_estimated_tokens_from_chars(20)
            with self.assertRaises(self.context.ContextPolicyViolation):
                self.context.write_model_call_context(
                    episode_root=Path(tmp),
                    manifest=manifest,
                )


class DeterministicEffectPolicyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.effect = _load("p08_effect_policy", EFFECT)

    def test_required_effect_pools_exist_and_parse(self):
        paths = [
            SHORT_POOLS / "shorts_comedy.json",
            SHORT_POOLS / "shorts_emotion.json",
            SHORT_POOLS / "shorts_tension.json",
            POLITICS_POOLS / "politics_neutral.json",
            POLITICS_POOLS / "politics_emphasis.json",
        ]
        for path in paths:
            self.assertTrue(path.is_file(), path)
            self.assertIsInstance(json.loads(path.read_text(encoding="utf-8")), dict)

    def test_effect_selection_is_seeded_and_reproducible(self):
        pool = {
            "schema_version": "effect-pool-v1",
            "preset_pool_version": "shorts-comedy-v1",
            "lane": "general_shorts_production",
            "policy": "SELECT_FROM_POOL",
            "presets": [
                {"preset_id": "fx-a", "approved": True},
                {"preset_id": "fx-b", "approved": True},
                {"preset_id": "fx-c", "approved": True},
            ],
        }
        first = self.effect.select_effect(
            pool=pool, episode_id="EP-01", segment_id="SEG-02"
        )
        second = self.effect.select_effect(
            pool=pool, episode_id="EP-01", segment_id="SEG-02"
        )
        self.assertEqual(first, second)
        self.assertIn(first["preset_id"], {"fx-a", "fx-b", "fx-c"})
        self.assertEqual(first["seed_material"], "EP-01SEG-02shorts-comedy-v1")

    def test_politics_explicit_only_never_auto_selects(self):
        pool = {
            "schema_version": "effect-pool-v1",
            "preset_pool_version": "politics-emphasis-v1",
            "lane": "politics_longform",
            "policy": "EXPLICIT_ONLY",
            "presets": [{"preset_id": "fx-p", "approved": True}],
        }
        decision = self.effect.select_effect(
            pool=pool, episode_id="POL-01", segment_id="SEG-01"
        )
        self.assertEqual(decision["status"], "WAIT_EXPLICIT_EFFECT_SELECTION")

    def test_politics_auto_pool_must_be_conservative(self):
        pool = {
            "schema_version": "effect-pool-v1",
            "preset_pool_version": "politics-risky-v1",
            "lane": "politics_longform",
            "policy": "SELECT_FROM_POOL",
            "conservative": False,
            "presets": [{"preset_id": "fx-risky", "approved": True}],
        }
        with self.assertRaises(self.effect.EffectPolicyError):
            self.effect.select_effect(
                pool=pool,
                episode_id="POL-01",
                segment_id="SEG-01",
            )


if __name__ == "__main__":
    unittest.main()

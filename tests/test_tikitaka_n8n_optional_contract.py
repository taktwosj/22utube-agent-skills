import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
HARNESS_PATH = REPO_ROOT / "skills" / "00-tikitaka" / "scripts" / "tikitaka_harness_runner.py"
PRODUCTION_GATE_PATH = (
    REPO_ROOT
    / "skills"
    / "000short-production-agent"
    / "scripts"
    / "validate_production_gate.py"
)
TIKITAKA_SKILL_PATH = REPO_ROOT / "skills" / "00-tikitaka" / "SKILL.md"
PRODUCTION_SKILL_PATH = REPO_ROOT / "skills" / "000short-production-agent" / "SKILL.md"


def load_harness():
    module_name = "tikitaka_harness_runner_n8n_optional_contract"
    spec = importlib.util.spec_from_file_location(module_name, HARNESS_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"unable to load {HARNESS_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def load_production_gate():
    module_name = "validate_production_gate_n8n_optional_contract"
    spec = importlib.util.spec_from_file_location(module_name, PRODUCTION_GATE_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"unable to load {PRODUCTION_GATE_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


class TikitakaN8nOptionalContractTest(unittest.TestCase):
    def test_standard_tikitaka_run_marks_n8n_not_required(self):
        harness = load_harness()

        with tempfile.TemporaryDirectory() as tmp:
            status = harness.n8n_status(Path(tmp), {})

        self.assertEqual(status["status"], "NOT_REQUIRED")
        self.assertFalse(status["required"])
        self.assertIn("Codex", status["reason"])
        self.assertTrue(harness.upstream_satisfied(status))

    def test_stale_n8n_evidence_is_ignored_when_route_is_not_selected(self):
        harness = load_harness()

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "n8n_execution_id.txt").write_text(
                "stale-execution",
                encoding="utf-8",
            )
            status = harness.n8n_status(root, {})

        self.assertEqual(status["status"], "NOT_REQUIRED")
        self.assertFalse(status["required"])
        self.assertIsNone(status["evidence"])

    def test_explicit_n8n_route_still_fails_closed_without_evidence(self):
        harness = load_harness()

        with tempfile.TemporaryDirectory() as tmp:
            status = harness.n8n_status(Path(tmp), {"n8n_required": True})

        self.assertEqual(status["status"], "NOT_RUN")
        self.assertTrue(status["required"])
        self.assertEqual(status["blocker"], "WAIT_N8N_EXECUTION_EVIDENCE")
        self.assertFalse(harness.upstream_satisfied(status))

    def test_harness_honors_explicit_orchestration_route(self):
        harness = load_harness()

        with tempfile.TemporaryDirectory() as tmp:
            status = harness.n8n_status(
                Path(tmp),
                {"orchestration": {"route": "n8n"}},
            )

        self.assertEqual(status["status"], "NOT_RUN")
        self.assertTrue(status["required"])
        self.assertEqual(status["blocker"], "WAIT_N8N_EXECUTION_EVIDENCE")
        self.assertFalse(harness.upstream_satisfied(status))

    def test_skill_contracts_name_codex_as_stage_transition_owner(self):
        tikitaka = TIKITAKA_SKILL_PATH.read_text(encoding="utf-8")
        production = PRODUCTION_SKILL_PATH.read_text(encoding="utf-8")

        for text in (tikitaka, production):
            self.assertIn("n8n_stage_transition=NOT_USED", text)
            self.assertIn("stage_transition_owner=Codex", text)
            self.assertIn("n8n_default_status=NOT_REQUIRED", text)

    def test_production_final_gate_defaults_n8n_to_not_required(self):
        production = load_production_gate()

        with tempfile.TemporaryDirectory() as tmp:
            status = production.validate_n8n_requirement({}, Path(tmp))

        self.assertEqual(status["n8n_status"], "NOT_REQUIRED")
        self.assertFalse(status["n8n_required"])

    def test_production_final_gate_requires_evidence_only_when_n8n_selected(self):
        production = load_production_gate()

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            with self.assertRaisesRegex(
                production.GateFail,
                "WAIT_N8N_EXECUTION_EVIDENCE",
            ):
                production.validate_n8n_requirement(
                    {"n8n_required": True},
                    root,
                )

            evidence = root / "n8n_webhook_response.json"
            evidence.write_text('{"status":"passed"}', encoding="utf-8")
            status = production.validate_n8n_requirement(
                {
                    "n8n_required": True,
                    "n8n_evidence_path": evidence.name,
                },
                root,
            )

        self.assertEqual(status["n8n_status"], "DONE")
        self.assertTrue(status["n8n_required"])

    def test_production_final_gate_honors_explicit_orchestration_route(self):
        production = load_production_gate()

        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(
                production.GateFail,
                "WAIT_N8N_EXECUTION_EVIDENCE",
            ):
                production.validate_n8n_requirement(
                    {"orchestration": {"route": "n8n"}},
                    Path(tmp),
                )


if __name__ == "__main__":
    unittest.main()

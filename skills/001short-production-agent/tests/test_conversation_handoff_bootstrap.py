import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


SKILL = Path(__file__).resolve().parents[1]
VALIDATOR = SKILL / "scripts" / "validate_conversation_handoff.py"


def load_validator():
    if not VALIDATOR.is_file():
        return None
    spec = importlib.util.spec_from_file_location("validate_conversation_handoff", VALIDATOR)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class SessionHandoffBootstrapTest(unittest.TestCase):
    def valid_handoff(self):
        return {
            "schema_version": "001short-session-handoff-v1",
            "owner_skill": "001short-production-agent",
            "lane": "general_shorts_production",
            "resume_requested": False,
            "episode_id": None,
            "request_scope": "새 일반 쇼츠 제작",
            "next_action": "원본 입력 확인",
        }

    def test_skill_protocol_workflow_and_tools_declare_bootstrap(self):
        skill_text = (SKILL / "SKILL.md").read_text(encoding="utf-8")
        protocol = json.loads((SKILL / "protocol.json").read_text(encoding="utf-8"))
        workflow = json.loads((SKILL / "workflow.json").read_text(encoding="utf-8"))
        tools = json.loads((SKILL / "tools.json").read_text(encoding="utf-8"))

        self.assertIn("## New Session Handoff Bootstrap", skill_text)
        self.assertIn("$HOME/.hermes/.env", skill_text)
        self.assertIn("scripts/validate_conversation_handoff.py", skill_text)
        self.assertEqual(protocol["schemas"]["session_handoff"], "schemas/conversation_handoff.schema.json")
        self.assertTrue(protocol["invariants"]["session_handoff_secret_material_forbidden"])
        self.assertEqual(protocol["session_handoff"]["owner_skill"], "001short-production-agent")
        self.assertTrue(protocol["session_handoff"]["resume_requires_episode_id_and_explicit_request"])
        self.assertEqual(workflow["session_bootstrap"]["env_file"], "$HOME/.hermes/.env")
        self.assertEqual(workflow["session_bootstrap"]["validator"], "scripts/validate_conversation_handoff.py")
        self.assertEqual(tools["session_handoff"]["validator"], "scripts/validate_conversation_handoff.py")

    def test_validator_accepts_safe_new_episode_handoff(self):
        module = load_validator()
        self.assertIsNotNone(module)
        self.assertEqual(module.validate_handoff(self.valid_handoff()), [])

    def test_validator_requires_explicit_episode_resume(self):
        module = load_validator()
        self.assertIsNotNone(module)
        handoff = self.valid_handoff()
        handoff["resume_requested"] = True
        self.assertIn("HANDOFF_EPISODE_ID_REQUIRED", module.validate_handoff(handoff))

    def test_validator_rejects_wrong_owner_and_secret_material(self):
        module = load_validator()
        self.assertIsNotNone(module)
        handoff = self.valid_handoff()
        handoff["owner_skill"] = "top5isu-shorts"
        handoff["api_key"] = "must-not-be-stored"
        errors = module.validate_handoff(handoff)
        self.assertIn("HANDOFF_OWNER_SKILL_INVALID", errors)
        self.assertIn("HANDOFF_SECRET_MATERIAL_FORBIDDEN:api_key", errors)

    def test_cli_prints_only_safe_summary(self):
        module = load_validator()
        self.assertIsNotNone(module)
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "handoff.json"
            path.write_text(json.dumps(self.valid_handoff(), ensure_ascii=False), encoding="utf-8")
            summary = module.safe_summary(module.read_json(path), env_file_exists=True)
        self.assertEqual(summary["status"], "PASS")
        self.assertEqual(summary["owner_skill"], "001short-production-agent")
        self.assertNotIn("env", summary)
        self.assertNotIn("messages", summary)
        self.assertTrue(summary["env_file_exists"])


if __name__ == "__main__":
    unittest.main()

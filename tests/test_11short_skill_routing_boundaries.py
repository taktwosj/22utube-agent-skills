from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]
SKILLS = ROOT / "skills"


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def skill_text(name: str) -> str:
    return read(SKILLS / name / "SKILL.md")


def description(text: str) -> str:
    match = re.match(r"---\n(.*?)\n---", text, flags=re.S)
    if not match:
        raise AssertionError("missing YAML frontmatter")
    desc_match = re.search(r"^description:\s*(.+)$", match.group(1), flags=re.M)
    if not desc_match:
        raise AssertionError("missing description")
    return desc_match.group(1)


class SkillRoutingBoundaryTests(unittest.TestCase):
    def test_tikitaka_frontmatter_is_script_draft_only(self):
        desc = description(skill_text("00-tikitaka"))
        for token in [
            "Shorts source analysis",
            "remake scripting",
            "hook candidates",
            "상단/timed 중단",
            "Do not use for SRT",
            "CapCut",
            "production packages",
            "polishing-only",
        ]:
            with self.subTest(token=token):
                self.assertIn(token, desc)

    def test_script_writer_frontmatter_requires_existing_draft(self):
        desc = description(skill_text("00script-writer"))
        for token in [
            "already provides",
            "existing Korean script",
            "retention",
            "writer review",
            "Do not use for URL/source intake",
            "Tikitaka/urakkai initial drafting",
            "channel planning",
            "SRT",
            "CapCut",
        ]:
            with self.subTest(token=token):
                self.assertIn(token, desc)

    def test_script_writer_body_keeps_existing_draft_hook_work_in_writer_lane(self):
        text = skill_text("00script-writer")
        for token in [
            "existing draft's `상단`, timed `중단`, hook candidates",
            "stay inside `00script-writer`",
            "rewrite_status: REWRITE_DRAFT",
            "production_status: WAIT_EXPLICIT_000SHORT_REQUEST",
        ]:
            with self.subTest(token=token):
                self.assertIn(token, text)

    def test_script_writer_pass_terms_are_namespaced_not_production_pass(self):
        text = skill_text("00script-writer")
        persona_ref = read(SKILLS / "00script-writer" / "references" / "parallel-persona-gate.md")
        combined = text + "\n" + persona_ref

        for token in [
            "reader_comprehension_gate_status=PASS",
            "persona_rewrite_gate_status=PASS",
            "writer-owned PASS values never create SCRIPT_LOCK",
            "production_status=PASS",
            "upload_ready",
            "CapCut/SRT permission",
        ]:
            with self.subTest(token=token):
                self.assertIn(token, combined)

        for forbidden in [
            "Final PASS",
            "before calling the work final",
            "최종 판정: PASS / REWRITE_REQUIRED",
        ]:
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, persona_ref)

    def test_production_frontmatter_is_assets_only(self):
        desc = description(skill_text("000short-production-agent"))
        for token in [
            "production assets",
            "subtitles",
            "layout JSON",
            "CapCut",
            "upload packages",
            "Do not use for script creation",
            "urakkai decisions",
            "hook/channel planning",
            "draft-only polishing",
        ]:
            with self.subTest(token=token):
                self.assertIn(token, desc)

    def test_22utube_policy_then_tikitaka_then_000short_handoff_is_explicit(self):
        policy = skill_text("22utube-production-agent")
        tikitaka = skill_text("00-tikitaka")
        production = skill_text("000short-production-agent")

        for token in [
            "22utube-production-agent is the first policy/root gate",
            "Then route Shorts script/remake work to `00-tikitaka`",
            "After 보고서1 approval and voice/audio route decision, route to `000short-production-agent` for 보고서2",
        ]:
            with self.subTest(skill="22utube", token=token):
                self.assertIn(token, policy)

        for token in [
            "report1_handoff.json",
            "next_skill=000short-production-agent",
            "다음 스킬: 000short-production-agent",
            "00-tikitaka는 보고서2를 작성하지 않는다",
        ]:
            with self.subTest(skill="00-tikitaka", token=token):
                self.assertIn(token, tikitaka)

        for token in [
            "report1_handoff.json",
            "REPORT1_HANDOFF_GATE",
            "next_skill=000short-production-agent",
            "owner_skill=00-tikitaka",
        ]:
            with self.subTest(skill="000short", token=token):
                self.assertIn(token, production)

    def test_agent_prompts_do_not_reintroduce_broad_routing(self):
        tikitaka = read(SKILLS / "00-tikitaka" / "agents" / "openai.yaml")
        writer = read(SKILLS / "00script-writer" / "agents" / "openai.yaml")
        production = read(SKILLS / "000short-production-agent" / "agents" / "openai.yaml")

        self.assertIn("DRAFT_EYE_REVIEW", tikitaka)
        self.assertIn("do not create SRT", tikitaka)
        self.assertIn("Route polish-only existing drafts", tikitaka)
        self.assertNotIn("tikitaka_production_input", tikitaka)

        self.assertIn("only when an existing Korean script", writer)
        self.assertIn("Do not start URL/source intake", writer)
        self.assertIn("Tikitaka/urakkai initial drafting", writer)
        self.assertNotIn("before script lock, SRT, CapCut text", writer)

        self.assertIn("only when explicitly asked for production assets", production)
        self.assertIn("do not originate script/urakkai/hook/channel planning", production)
        self.assertNotIn("URL-only request is a full production request by default", production)

    def test_shorts_academy_references_are_owner_scoped(self):
        tikitaka_ref = read(SKILLS / "00-tikitaka" / "references" / "shorts-academy.md")
        writer_ref = read(SKILLS / "00script-writer" / "references" / "shorts-academy.md")
        production_ref = read(SKILLS / "000short-production-agent" / "references" / "shorts-academy.md")
        pipeline = read(SKILLS / "000short-production-agent" / "02_PIPELINE_RULES.md")

        self.assertIn("Tikitaka draft decisions", tikitaka_ref)
        self.assertIn("not standalone channel planning", tikitaka_ref)

        self.assertIn("existing script draft", writer_ref)
        self.assertIn("does not start channel planning", writer_ref)
        self.assertIn("Route new source-remake", writer_ref)
        self.assertNotIn("Use this reference for Korean Shorts channel planning, source-remake scripts", writer_ref)

        self.assertIn("read-only production check", production_ref)
        self.assertIn("does not authorize script creation", production_ref)

        self.assertIn("Broad Shorts Academy wording alone does not start production", pipeline)
        self.assertIn("explicit production request and script authority", pipeline)


if __name__ == "__main__":
    unittest.main()

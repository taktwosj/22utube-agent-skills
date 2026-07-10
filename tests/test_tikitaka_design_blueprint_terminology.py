from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TIKITAKA_SKILL = (ROOT / "skills" / "00-tikitaka" / "SKILL.md").read_text(encoding="utf-8")
TIKITAKA_HARNESS = (
    ROOT / "skills" / "00-tikitaka" / "scripts" / "tikitaka_harness_runner.py"
).read_text(encoding="utf-8")
PRODUCTION_SKILL = (
    ROOT / "skills" / "000short-production-agent" / "SKILL.md"
).read_text(encoding="utf-8")


def test_tikitaka_user_facing_stage_one_is_design_blueprint():
    assert "## 설계도 계약" in TIKITAKA_SKILL
    assert "# 설계도" in TIKITAKA_SKILL
    assert "## Report 1 Contract" not in TIKITAKA_SKILL
    assert "# 보고서1" not in TIKITAKA_SKILL


def test_tikitaka_harness_emits_design_blueprint_heading():
    assert '"report": "설계도"' in TIKITAKA_HARNESS
    assert 'header = "# 설계도"' in TIKITAKA_HARNESS
    assert 'header = "# 보고서1"' not in TIKITAKA_HARNESS


def test_tikitaka_harness_fail_closes_missing_integrated_blueprint():
    assert "def design_blueprint_status" in TIKITAKA_HARNESS
    assert '"design_blueprint": design_blueprint_status(work_dir)' in TIKITAKA_HARNESS


def test_stage_two_skill_asks_for_design_blueprint_approval():
    assert "설계도 승인" in PRODUCTION_SKILL
    assert "사용자가 보고서1" not in PRODUCTION_SKILL

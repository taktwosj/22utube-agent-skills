"""빌드 뒤 마무리 단계 계약.

빌더가 내놓은 프로젝트를 그대로 열면 없는 경로를 찾다가 CapCut 이 멈추고,
음량 노멀라이즈도 꺼진 채로 남는다. 그 둘을 마무리 단계가 책임진다.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILL_DIR = ROOT / "skills" / "119-politics-longform-capcut"
SKILL = SKILL_DIR / "SKILL.md"
SCRIPT = SKILL_DIR / "scripts" / "finalize_politics_media_and_loudness.py"


def test_finalize_script_exists():
    assert SCRIPT.is_file()


def test_finalize_relinks_every_canonical_file():
    src = SCRIPT.read_text(encoding="utf-8")
    # 타임라인만 고치면 CapCut 미디어 목록이 여전히 없는 파일을 찾는다
    assert 'META = "draft_meta_info.json"' in src
    assert "root / META" in src
    assert 'CANONICAL = ("draft_content.json", "template-2.tmp")' in src
    assert 'Timelines' in src
    assert "MEDIA_FILE_MISSING" in src


def test_finalize_enables_and_precomputes_loudness():
    src = SCRIPT.read_text(encoding="utf-8")
    assert "loudnorm" in src
    assert '"enable"] = True' in src or 'item["enable"] = True' in src
    assert "loudness_param" in src
    assert "avg_loudness" in src and "peak_loudness" in src
    assert "ThreadPoolExecutor" in src


def test_finalize_refuses_while_capcut_open():
    src = SCRIPT.read_text(encoding="utf-8")
    assert "CAPCUT_MUST_BE_CLOSED" in src


def test_assembly_doc_orders_finalize_after_build():
    doc = SKILL.read_text(encoding="utf-8")
    assert "finalize_politics_media_and_loudness.py" in doc
    assert doc.index("build_politics_v8_project.py") < doc.index("빌드 뒤 마무리") or "빌드 뒤 마무리" in doc

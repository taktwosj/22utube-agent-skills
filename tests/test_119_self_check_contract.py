# -*- coding: utf-8 -*-
"""119 두 스킬의 self-check 가 실제로 돌고, 깨지면 실제로 잡는지 본다.

배포 도구(skill_release.py verify --self-check)는 scripts/self-check.sh 를 찾아
실행한다. 파일만 있고 통과만 하면 의미가 없으므로, 계약값을 일부러 되돌려
FAIL 이 나오는지도 함께 확인한다.
"""
from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
SKILLS = ("spine-script-119", "119-politics-longform-capcut")
BASH = shutil.which("bash")


def run_self_check(skill_root: Path) -> subprocess.CompletedProcess:
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
    return subprocess.run(
        [BASH, str(skill_root / "scripts" / "self-check.sh")],
        cwd=skill_root, capture_output=True, text=True,
        encoding="utf-8", errors="replace", env=env)


@pytest.mark.parametrize("name", SKILLS)
def test_self_check_exists_and_is_bash(name: str) -> None:
    script = REPO / "skills" / name / "scripts" / "self-check.sh"
    assert script.is_file(), f"{name}: self-check.sh 가 없다"
    text = script.read_text(encoding="utf-8")
    assert text.splitlines()[0].startswith("#!"), f"{name}: shebang 이 없다"
    # 릴리스 폴더에 .pyc 가 생기면 다음 activate 가 막힌다.
    assert "PYTHONDONTWRITEBYTECODE" in text
    # 줄바꿈에 CR 이 섞이면 shebang 이 깨져 다른 환경에서 실행이 안 된다.
    assert chr(13) not in text, f"{name}: CRLF 줄바꿈"


@pytest.mark.skipif(BASH is None, reason="bash 없음")
@pytest.mark.parametrize("name", SKILLS)
def test_self_check_passes_on_clean_tree(name: str) -> None:
    done = run_self_check(REPO / "skills" / name)
    assert done.returncode == 0, done.stdout + done.stderr


@pytest.mark.skipif(BASH is None, reason="bash 없음")
def test_self_check_catches_reverted_short_speed(tmp_path: Path) -> None:
    copy = tmp_path / "spine-script-119"
    shutil.copytree(REPO / "skills" / "spine-script-119", copy)
    common = copy / "scripts" / "_common.py"
    common.write_text(
        common.read_text(encoding="utf-8").replace("SHORT_SPEED = 1.2", "SHORT_SPEED = 1.0"),
        encoding="utf-8")
    done = run_self_check(copy)
    assert done.returncode == 1
    assert "SHORT_SPEED" in done.stdout


@pytest.mark.skipif(BASH is None, reason="bash 없음")
def test_self_check_catches_missing_finalize_script(tmp_path: Path) -> None:
    copy = tmp_path / "119-politics-longform-capcut"
    shutil.copytree(REPO / "skills" / "119-politics-longform-capcut", copy)
    (copy / "scripts" / "finalize_politics_media_and_loudness.py").unlink()
    done = run_self_check(copy)
    assert done.returncode == 1
    assert "finalize_politics_media_and_loudness.py" in done.stdout


@pytest.mark.skipif(BASH is None, reason="bash 없음")
@pytest.mark.parametrize("name", SKILLS)
def test_self_check_writes_no_bytecode(tmp_path: Path, name: str) -> None:
    copy = tmp_path / name
    shutil.copytree(REPO / "skills" / name, copy)
    if name == "spine-script-119":
        # spine 의 hf_lib 는 이웃 스킬 hyperframes-politics-119/scripts/hf119 를 읽는다. 함께 배포된다.
        shutil.copytree(REPO / "skills" / "hyperframes-politics-119", tmp_path / "hyperframes-politics-119")
    assert run_self_check(copy).returncode == 0
    assert not list(copy.rglob("__pycache__")), "릴리스에 .pyc 가 생기면 activate 가 막힌다"
    assert not list(copy.rglob("*.pyc"))

#!/usr/bin/env bash
# 배포 뒤 이 스킬이 실제로 돌아가는 상태인지 5초 안에 확인한다.
# 파일을 읽기만 한다. CapCut·미디어·네트워크·디스크 쓰기 없음.
set -euo pipefail
export PYTHONDONTWRITEBYTECODE=1   # 릴리스 폴더에 .pyc 가 생기면 다음 activate 가 막힌다
# 쓸 수 있는 파이썬을 고른다. 윈도우의 python3 는 실행되지 않는 스토어 껍데기일 수 있다.
PY=""
for cand in python3 python py; do
  if command -v "$cand" >/dev/null 2>&1 && "$cand" -c "import sys" >/dev/null 2>&1; then
    PY="$cand"; break
  fi
done
[ -n "$PY" ] || { echo "SELF_CHECK FAIL: 쓸 수 있는 파이썬이 없다"; exit 1; }
cd "$(dirname "$0")/.."
"$PY" - <<'PY'
import ast, io, pathlib, sys

# 한국어를 찍는다. 콘솔 기본 코드페이지가 cp949 면 그대로 깨진다.
if hasattr(sys.stdout, "buffer"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

skill = pathlib.Path.cwd()
fail = []

# 1) 스크립트가 전부 문법상 열리나. compile 만 하고 실행·import 는 안 한다.
scripts = sorted((skill / "scripts").glob("*.py"))
if not scripts:
    fail.append("scripts/*.py 가 하나도 없다")
trees = {}
for path in scripts:
    try:
        trees[path.name] = ast.parse(path.read_text(encoding="utf-8"), path.name)
    except SyntaxError as exc:
        fail.append(f"{path.name}: 문법 오류 {exc.lineno}행 {exc.msg}")

def top_assign(name, target):
    """모듈 최상단 상수 값을 실행 없이 읽는다."""
    for node in trees.get(name, ast.Module(body=[], type_ignores=[])).body:
        if isinstance(node, ast.Assign):
            for t in node.targets:
                if isinstance(t, ast.Name) and t.id == target:
                    return ast.literal_eval(node.value)
    return None

def has_def(name, target):
    tree = trees.get(name)
    return bool(tree) and any(
        isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name == target
        for n in ast.walk(tree))

# 2) ASSEMBLY_ONLY 경로의 스크립트가 다 있나
for name in ("validate_pre119_handoff.py", "compile_pre119_episode_cards.py",
             "run_politics_assembly_preflight.py", "build_politics_v8_project.py",
             "capture_politics_relink_readback.py", "finalize_politics_media_and_loudness.py"):
    if name not in trees:
        fail.append(f"scripts/{name} 가 없다 (ASSEMBLY_ONLY 경로)")

# 3) 계약값이 살아 있나
PLACEHOLDER = "C:/__CAPCUT_RELINK_REQUIRED__"
if top_assign("build_politics_v8_project.py", "RELINK_PLACEHOLDER_ROOT") != PLACEHOLDER:
    fail.append("build_politics_v8_project.RELINK_PLACEHOLDER_ROOT 가 계약값과 다르다")
fin = "finalize_politics_media_and_loudness.py"
if top_assign(fin, "SENTINEL") != PLACEHOLDER:
    fail.append(f"{fin}.SENTINEL 이 빌더 자리표시자와 다르다")
if top_assign(fin, "META") != "draft_meta_info.json":
    fail.append(f"{fin}.META 가 draft_meta_info.json 이 아니다 (CapCut 미디어 목록)")
for func in ("require_capcut_closed", "relink", "audible_loudness"):
    if not has_def(fin, func):
        fail.append(f"{fin}.{func} 가 없다")

# 4) 계약 문서가 같이 왔나
skill_md = skill / "SKILL.md"
if not skill_md.is_file():
    fail.append("SKILL.md 가 없다")
else:
    text = skill_md.read_text(encoding="utf-8")
    for phrase in ("ASSEMBLY_ONLY", "finalize_politics_media_and_loudness"):
        if phrase not in text:
            fail.append(f"SKILL.md 에 '{phrase}' 계약 문구가 없다")

if fail:
    for line in fail:
        print("SELF_CHECK FAIL:", line)
    sys.exit(1)
print(f"검사 통과: 스크립트 {len(scripts)}개 · ASSEMBLY_ONLY 5단계 + 마무리 1단계")
PY

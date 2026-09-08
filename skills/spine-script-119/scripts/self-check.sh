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

# 2) 계약값이 살아 있나
speed = top_assign("_common.py", "SHORT_SPEED")
if speed != 1.2:
    fail.append(f"_common.SHORT_SPEED 가 1.2 가 아니다: {speed!r}")
if top_assign("build_assets.py", "CUE_EDGE") is None:
    fail.append("build_assets.CUE_EDGE 가 없다 (오프닝 문장 끊김 방지)")
for func in ("attach_loudness", "clean_meta"):
    if not has_def("build_short.py", func):
        fail.append(f"build_short.{func} 가 없다")

# 3) 계약 문서가 같이 왔나
skill_md = skill / "SKILL.md"
if not skill_md.is_file():
    fail.append("SKILL.md 가 없다")
else:
    text = skill_md.read_text(encoding="utf-8")
    for phrase in ("1.2배", "오프닝"):
        if phrase not in text:
            fail.append(f"SKILL.md 에 '{phrase}' 계약 문구가 없다")

if fail:
    for line in fail:
        print("SELF_CHECK FAIL:", line)
    sys.exit(1)
print(f"검사 통과: 스크립트 {len(scripts)}개 · 쇼츠 속도 {speed}배")
PY

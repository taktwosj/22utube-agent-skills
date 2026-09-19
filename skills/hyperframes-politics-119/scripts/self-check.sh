#!/usr/bin/env bash
set -euo pipefail
export PYTHONDONTWRITEBYTECODE=1
PY=""
for cand in python3 python py; do
  if command -v "$cand" >/dev/null 2>&1 && "$cand" -c "import sys" >/dev/null 2>&1; then
    PY="$cand"; break
  fi
done
[ -n "$PY" ] || { echo "SELF_CHECK FAIL: Python unavailable"; exit 1; }
cd "$(dirname "$0")/.."
"$PY" - <<'PY'
import ast, pathlib, sys
skill = pathlib.Path.cwd()
for path in (skill / 'scripts').rglob('*.py'):
    code = path.read_text(encoding='utf-8')
    compile(code, str(path), 'exec')
    if 'hf119' in path.parts:
        tree = ast.parse(code)
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                assert node.module not in ('_common', 'hf_lib', 'hf_icons'), path
            elif isinstance(node, ast.Import):
                assert not any(a.name in ('_common', 'hf_lib', 'hf_icons') for a in node.names), path
sys.path.insert(0, str(skill / 'scripts'))
import hf119
for name in ('configure', 'init', 'build', 'T', 'P', 'Q'):
    assert callable(getattr(hf119, name)), name
assert hf119.DIAGRAM_KINDS == ('timeline', 'flow', 'relation', 'move', 'doc')
assert not {'_common', 'hf_lib', 'hf_icons'} & sys.modules.keys()
assert (skill / 'references/scene-mode.md').is_file()
from hf119.motion.presets import FX_CHAPTER_ONCE, FX_SECONDS, PRESETS
assert len(PRESETS) == 11, PRESETS.keys()
for kind, spec in PRESETS.items():
    assert set(spec['fx']) <= set(FX_SECONDS), kind
assert FX_CHAPTER_ONCE == ('shake',)
for doc in ('index.md', 'scene-presets.md', 'limits.md'):
    assert (skill / 'references/motion' / doc).is_file(), doc
print('SELF_CHECK PASS: hf119 public API, motion presets, syntax, no spine dependency')
PY

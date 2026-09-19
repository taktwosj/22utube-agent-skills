# -*- coding: utf-8 -*-
"""나레이션 블록에 줄을 끼워 넣거나 뺀 뒤 NL 번호를 다시 매긴다. 이미 만든 wav·장면은 살린다.

순서
  1. 고치기 전에 work/narration_lines.json 을 work/_backup_before_insert/ 로 복사해 둔다.
     (이 스크립트는 그 사본을 옛 번호의 기준으로 읽는다. 없으면 멈춘다.)
  2. narration/<block>.txt 를 고친다.
  3. python renumber_narration.py --root <root> --dry   매핑만 본다
  4. python renumber_narration.py --root <root>         적용
  5. tts_lines.py 로 새 줄만 합성 → make_cards.py → render_scenes.py --missing

하는 일
  - 옛 NLxx.txt/wav 는 지우지 않고 narration/_old_numbering/ 으로 옮긴다.
  - 옛 줄 텍스트와 새 줄 텍스트를 difflib 로 맞춰 같은 줄이면 wav 를 새 이름으로 복사한다.
  - hyperframes/NL*.mp4 를 _old_numbering/ 으로 전부 옮긴 뒤 새 이름으로 복사한다.
    걸친 줄 중 하나라도 바뀌었으면 HF_NEEDS_RERENDER 로 찍고 복사하지 않는다.
  - work/scenes.py 안의 "NLxx" 이름을 같은 매핑으로 바꾼다. 없어진 줄은 "NLxx_OLD" 로 남긴다.
  - 결과 work/renumber_map.json {old: new}
"""
from __future__ import annotations

import difflib
import json
import re
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _common import load_cards_def_raw, resolve_root, root_parser  # noqa: E402


def main() -> int:
    p = root_parser("나레이션 줄 끼워 넣은 뒤 NL 번호 재정렬")
    p.add_argument("--dry", action="store_true", help="매핑만 출력하고 파일은 건드리지 않는다")
    args = p.parse_args()
    root = resolve_root(args)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    narr = root / "narration"
    hf = root / "hyperframes"
    backup = root / "work" / "_backup_before_insert" / "narration_lines.json"
    if not backup.is_file():
        raise SystemExit(f"RENUMBER_BASELINE_MISSING: {backup} — 원고를 고치기 전에 narration_lines.json 을 복사해 둔다")

    cd = load_cards_def_raw(root)
    old_rows = json.loads(backup.read_text(encoding="utf-8"))
    old = []
    for r in old_rows:
        src = narr / f"{r['name']}.txt"
        if not src.is_file():
            src = narr / "_old_numbering" / f"{r['name']}.txt"
        if not src.is_file():
            raise SystemExit(f"OLD_LINE_TEXT_MISSING: {r['name']}")
        old.append((r["name"], src.read_text(encoding="utf-8").strip()))

    new = []
    for block in dict.fromkeys(cd.NARRATION_ORDER):  # tts_lines.py 와 같은 순서·같은 중복 제거
        for line in (narr / f"{block}.txt").read_text(encoding="utf-8").splitlines():
            line = line.replace("\\n", " ").strip()
            if line:
                new.append(line)

    sm = difflib.SequenceMatcher(a=[t for _, t in old], b=new, autojunk=False)
    mapping, fresh = {}, []
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == "equal":
            for k in range(i2 - i1):
                mapping[old[i1 + k][0]] = f"NL{j1 + k + 1:02d}"
        else:
            if i2 > i1:
                print("OLD_DROPPED", [old[i][0] for i in range(i1, i2)])
            fresh += [f"NL{j + 1:02d}" for j in range(j1, j2)]

    print("매핑", len(mapping), "새 줄", len(fresh), fresh)
    print("번호 바뀜", sum(1 for a, b in mapping.items() if a != b))
    if args.dry:
        return 0

    stash = narr / "_old_numbering"
    stash.mkdir(exist_ok=True)
    for name, _ in old:
        for ext in (".txt", ".wav"):
            src = narr / f"{name}{ext}"
            if src.exists():
                shutil.move(str(src), str(stash / f"{name}{ext}"))
    for a, b in mapping.items():
        shutil.copy2(stash / f"{a}.wav", narr / f"{b}.wav")

    # 먼저 전부 옮긴 뒤 복사한다. 옮기면서 바로 복사하면 새 이름이 아직 옮기지 않은
    # 원래 파일 이름과 겹칠 때 원본을 덮어쓴다 (2026-09-14 NL118-NL120 등 3개 유실)
    rx = re.compile(r"NL\d+")
    if hf.is_dir():
        hstash = hf / "_old_numbering"
        hstash.mkdir(exist_ok=True)
        originals = sorted(hf.glob("NL*.mp4"))
        for mp4 in originals:
            shutil.move(str(mp4), str(hstash / mp4.name))
        for mp4 in originals:
            names = rx.findall(mp4.stem)
            if all(x in mapping for x in names):
                target = hf / (rx.sub(lambda m: mapping[m.group(0)], mp4.stem) + ".mp4")
                shutil.copy2(hstash / mp4.name, target)
            else:
                print("HF_NEEDS_RERENDER", mp4.name)

    sp = root / "work" / "scenes.py"
    if sp.is_file():
        s = sp.read_text(encoding="utf-8")
        s = re.sub(r'"(NL\d+)(?:-(NL\d+))?"',
                   lambda m: '"' + "-".join(mapping.get(x, x + "_OLD") for x in m.groups() if x) + '"', s)
        sp.write_text(s, encoding="utf-8")
    (root / "work" / "renumber_map.json").write_text(json.dumps(mapping, ensure_ascii=False, indent=1), encoding="utf-8")
    print("완료 — 새 줄은 tts_lines.py, 장면은 scenes.py 의 _OLD 를 고친 뒤 render_scenes.py --missing")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

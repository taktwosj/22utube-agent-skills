# -*- coding: utf-8 -*-
"""나레이션 원고를 줄 단위로 Typecast API 합성한다. 웹 에디터 경로(split_tts_lines.py)의 API 판이다.

narration/<block>.txt 를 NARRATION_ORDER 순서로 읽어 한 줄마다 NLxx.txt 를 쓰고,
NLxx.wav 가 없을 때만 make_typecast_tts.py 로 합성한다. 이미 있는 wav 는 다시 만들지 않는다.
끝나면 work/narration_lines.json [{name, block, duration}] 을 쓴다. make_cards·hf_lib 가 읽는다.

합성기 위치: 환경변수 또는 ZSkillSync paths.json 의 TYPECAST_TTS_TOOL.
없으면 현재 작업 폴더(22factory) 아래 00_asset_tools/tools/make_typecast_tts.py 를 본다.
집 사운드 고정값·템포 1.2 는 합성기가 잠근다. 여기서 voice·속도를 바꾸지 않는다.

check_narration.py 가 PASS 한 원고만 넣는다.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _common import load_cards_def_raw, resolve_root, root_parser  # noqa: E402
from runtime_paths import configured_path  # noqa: E402


def tts_tool() -> Path:
    tool = configured_path("TYPECAST_TTS_TOOL", Path.cwd() / "00_asset_tools" / "tools" / "make_typecast_tts.py")
    if not tool.is_file():
        raise SystemExit(f"TYPECAST_TTS_TOOL_MISSING: {tool} — TYPECAST_TTS_TOOL 을 주거나 22factory 폴더에서 실행한다")
    return tool


def duration(wav: Path) -> float:
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(wav)],
                         capture_output=True, text=True).stdout.strip()
    try:
        return float(out)
    except ValueError:
        raise SystemExit(f"FFPROBE_FAILED: {wav}")


def main() -> int:
    args = root_parser("나레이션 줄 단위 Typecast 합성").parse_args()
    root = resolve_root(args)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    cd = load_cards_def_raw(root)
    narr = root / "narration"
    narr.mkdir(exist_ok=True)
    tool = None
    rows, i = [], 0
    for block in dict.fromkeys(cd.NARRATION_ORDER):  # 앞뒤 CTA 처럼 같은 블록이 두 번 오면 한 번만 합성한다
        for line in (narr / f"{block}.txt").read_text(encoding="utf-8").splitlines():
            line = line.replace("\\n", " ").strip()
            if not line:
                continue
            i += 1
            name = f"NL{i:02d}"
            (narr / f"{name}.txt").write_text(line, encoding="utf-8")
            wav = narr / f"{name}.wav"
            if not wav.exists():
                tool = tool or tts_tool()
                r = subprocess.run([sys.executable, str(tool), "--text-file", str(narr / f"{name}.txt"), "--out", str(wav)],
                                   capture_output=True, text=True, encoding="utf-8", errors="replace")
                if r.returncode != 0:
                    print(f"TTS_FAILED {name}: {(r.stderr or r.stdout)[-300:]}", flush=True)
                    return 1
            d = duration(wav)
            rows.append({"name": name, "block": block, "duration": d})
            print(f"{name} {block:<8} {d:5.2f}s  {line[:34]}", flush=True)
    (root / "work" / "narration_lines.json").write_text(json.dumps(rows, ensure_ascii=False, indent=1), encoding="utf-8")
    tot = sum(r["duration"] for r in rows)
    print(f"\n완료 {len(rows)}줄  총 {tot:.1f}s = {tot / 60:.2f}분")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

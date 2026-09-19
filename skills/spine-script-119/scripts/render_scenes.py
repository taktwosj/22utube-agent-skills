# -*- coding: utf-8 -*-
"""하이퍼프레임 장면 전체를 만든다: 생성 → hyperframes check --strict → render high 30fps.

장면 정의는 회차 <root>/work/scenes.py 의 SPECS 다. 틀은 templates/scenes.template.py.
산출물  <root>/hyperframes/<file>.mp4
로그    <root>/hyperframes/_logs/<file>.check.log | render.log
요약    <root>/work/render_scenes.json  (file → duration, check_exit, render_exit, mp4, sec)

    python render_scenes.py --root <root>                 # 전부
    python render_scenes.py --root <root> NL02-NL05 NL12  # 이름 지정
    python render_scenes.py --root <root> --missing       # mp4 가 없는 것만
    python render_scenes.py --root <root> --check-only    # 전 장면 생성 + check 만. 렌더 전에 설정 오류를 한 번에 잡는다
    python render_scenes.py --root <root> --jobs 4        # check·render 를 동시에 4개. 기본 4

순서: 장면 프로젝트 생성은 전부 먼저(빠르다). 그 다음 check·render 를 --jobs 개씩 동시에 돈다.
check 가 실패한 장면은 렌더하지 않고 다음으로 넘어간다. 마지막에 실패 목록을 찍고 exit 2.
렌더 하나가 30~50초라 37장면을 한 줄로 돌리면 30분, 4개씩이면 8분 안팎이다.
"""
from __future__ import annotations

import importlib.util
import json
import os
import shutil
import subprocess
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import hf_lib  # noqa: E402
from _common import load_cards_def_raw, resolve_root, root_parser  # noqa: E402

DEFAULT_JOBS = 4


def load_specs(root: Path) -> list[dict]:
    path = root / "work" / "scenes.py"
    if not path.is_file():
        raise SystemExit(f"SCENES_MISSING: {path} — templates/scenes.template.py 를 복사해 채운다")
    spec = importlib.util.spec_from_file_location("scenes", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    specs = getattr(mod, "SPECS", None)
    if not specs:
        raise SystemExit("SCENES_SPECS_EMPTY: work/scenes.py 에 SPECS 가 없다")
    return specs


def npx() -> str:
    exe = "npx.cmd" if os.name == "nt" else "npx"
    if not shutil.which(exe):
        raise SystemExit(f"NPX_MISSING: {exe} — Node.js 설치는 사용자 터미널에서 한다")
    return exe


def run_logged(cmd: list[str], log: Path) -> int:
    res = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    log.write_text(res.stdout + res.stderr, encoding="utf-8")
    return res.returncode


def main() -> int:
    p = root_parser("하이퍼프레임 장면 생성·검사·렌더")
    p.add_argument("names", nargs="*", help="장면 file 이름. 없으면 전부")
    p.add_argument("--missing", action="store_true", help="mp4 가 없는 장면만")
    p.add_argument("--check-only", action="store_true", help="생성 + check --strict 만. 렌더 안 함")
    p.add_argument("--jobs", type=int, default=DEFAULT_JOBS, help=f"동시에 돌릴 check·render 수. 기본 {DEFAULT_JOBS}")
    args = p.parse_args()
    root = resolve_root(args)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    jobs = max(1, args.jobs)

    cd = load_cards_def_raw(root)
    hf = hf_lib.init(root, getattr(cd, "HF_BRAND", None))
    specs = load_specs(root)
    only = set(args.names)
    known = {s["file"] for s in specs}
    unknown = only - known
    if unknown:
        raise SystemExit("SCENE_NAME_UNKNOWN: " + ", ".join(sorted(unknown)))

    logs = hf / "_logs"
    logs.mkdir(parents=True, exist_ok=True)
    summary_path = root / "work" / "render_scenes.json"
    summary = json.loads(summary_path.read_text(encoding="utf-8")) if summary_path.is_file() else {}
    exe = npx()
    lock = threading.Lock()

    # 1) 대상 고르기 + 프로젝트 생성. build 는 파일 몇 개 쓰는 게 전부라 한 줄로 돈다.
    #    build 안의 검사(MOTION_CHAPTER_LIMIT 등 SystemExit)는 첫 장면에서 멈추지 않고 전부 모은다.
    #    챕터당 모션 1회 같은 규칙은 프로세스 안에서 세므로, 이름을 나눠 여러 프로세스로 돌리면 빠져나간다.
    #    그래서 렌더 전에 --check-only 를 전체 목록으로 한 번 돈다.
    todo: list[tuple[str, Path, Path, float]] = []
    build_failed: list[tuple[str, str]] = []
    for spec in specs:
        name = spec["file"]
        out = hf / f"{name}.mp4"
        if only and name not in only:
            continue
        if args.missing and out.is_file():
            continue
        try:
            proj, total = hf_lib.build(spec)
        except SystemExit as exc:
            build_failed.append((name, str(exc)))
            print(f"{name:14s} build=FAIL {exc}", flush=True)
            continue
        todo.append((name, proj, out, total))
    for name, msg in build_failed:
        with lock:
            summary[name] = {"duration": None, "check_exit": None, "render_exit": None, "mp4": (hf / f"{name}.mp4").is_file(),
                             "sec": 0, "build_error": msg}
    if build_failed:
        summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=1), encoding="utf-8")
    if not todo and not build_failed:
        print("DONE 0 / 0 (대상 장면 없음)")
        return 0

    # 2) check → render. 장면마다 독립이라 --jobs 개씩 동시에.
    def work(item: tuple[str, Path, Path, float]) -> tuple[str, dict]:
        name, proj, out, total = item
        t0 = time.time()
        chk = run_logged([exe, "--yes", "hyperframes", "check", str(proj), "--strict"], logs / f"{name}.check.log")
        ren_code = None
        if chk == 0 and not args.check_only:
            ren_code = run_logged([exe, "--yes", "hyperframes", "render", str(proj), "-q", "high", "-f", "30",
                                   "-o", str(out), "--quiet"], logs / f"{name}.render.log")
        entry = {"duration": total, "check_exit": chk, "render_exit": ren_code,
                 "mp4": out.is_file(), "sec": round(time.time() - t0, 1)}
        with lock:
            if args.check_only and name in summary:
                summary[name].update(check_exit=chk, duration=total)  # 렌더 결과는 지난 값을 남긴다
            else:
                summary[name] = entry
            summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=1), encoding="utf-8")
            print(f"{name:14s} check={chk} render={ren_code} {entry['sec']}s", flush=True)
        return name, entry

    results: list[tuple[str, dict]] = []
    if jobs == 1:
        results = [work(item) for item in todo]
    else:
        with ThreadPoolExecutor(max_workers=jobs) as pool:
            results = list(pool.map(work, todo))

    bad_build = [n for n, _m in build_failed]
    if args.check_only:
        bad = [n for n, e in results if e["check_exit"] != 0]
        total_n = len(results) + len(bad_build)
        print(f"CHECK_DONE {len(results) - len(bad)} / {total_n} 장면 통과")
        if bad_build:
            print("HYPERFRAME_BUILD_FAILED:", ", ".join(bad_build), "— 위 build=FAIL 줄의 코드를 scenes.py 에서 고친다")
        if bad:
            print("HYPERFRAME_CHECK_FAILED:", ", ".join(bad), "— hyperframes/_logs/<name>.check.log")
        return 2 if (bad or bad_build) else 0

    failed = bad_build + [n for n, e in results if e["check_exit"] != 0 or e["render_exit"] != 0]
    ok_run = len(results) + len(bad_build) - len(failed)
    ok_all = sum(1 for v in summary.values() if v.get("check_exit") == 0 and v.get("render_exit") == 0)
    print(f"DONE {ok_run} / {len(results) + len(bad_build)} 이번 실행  (누적 {ok_all} / {len(summary)})")
    if failed:
        print("HYPERFRAME_RENDER_FAILED:", ", ".join(failed))
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

# -*- coding: utf-8 -*-
"""척추 후보 스캔. 허용 목록 채널의 videos·streams 탭 최근 업로드를 나열한다.

척추는 채널이 아니라 구간이다. 진행자·고정 논객이 이어서 정치평론을 하는 구간이면 어느
허용 채널이든 척추가 된다. 그래서 group 으로 거르지 않고 전 채널을 본다(--groups 로 좁힐 수 있다).

유튜브 RSS 는 2026-09-17 기준 채널 대부분에서 404·500 을 내 yt-dlp 목록 추출로 바꿨다.
영상은 받지 않는다. 목록 추출은 업로드일을 주지 않으므로 --probe 를 주면 영상마다 날짜·길이·
channel_id 를 실측한다(느리다. 봇 확인에 막히면 그 사실을 표시).
"""
from __future__ import annotations

import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _common import BLOCKED_VIDEO_IDS, load_allowlist  # noqa: E402

TABS = ("videos", "streams")


def listing(cid: str, tab: str, limit: int) -> list[tuple[str, str, str]]:
    p = subprocess.run(["yt-dlp", "--encoding", "utf-8", "--no-warnings", "--flat-playlist",
                        "--extractor-args", "youtube:lang=ko", "-I", f"1:{limit}",
                        "--print", "%(duration)s|%(id)s|%(title)s",
                        f"https://www.youtube.com/channel/{cid}/{tab}"],
                       capture_output=True, timeout=300)
    out = p.stdout.decode("utf-8", "replace")
    if p.returncode != 0 and not out.strip():
        err = p.stderr.decode("utf-8", "replace").strip().splitlines()
        # streams 탭이 없는 채널은 정상이다
        if err and "does not have a" in err[-1]:
            return []
        raise RuntimeError(err[-1] if err else f"yt-dlp exit {p.returncode}")
    rows = []
    for line in out.splitlines():
        parts = line.split("|", 2)
        if len(parts) == 3:
            rows.append(tuple(parts))
    return rows


def probe(vid: str) -> str:
    p = subprocess.run(["yt-dlp", "--encoding", "utf-8", "--skip-download", "--no-warnings", "-q", "--print",
                        "%(upload_date)s|%(duration)s|%(channel_id)s", f"https://www.youtube.com/watch?v={vid}"],
                       capture_output=True, timeout=90)
    return p.stdout.decode("utf-8", "replace").strip() if p.returncode == 0 else "BOT_CHECK_OR_ERROR"


def minutes(raw: str) -> str:
    try:
        return f"{float(raw) / 60:6.1f}m"
    except ValueError:
        return "   ?   "   # 진행 중·예정 라이브


def main():
    import argparse
    ap = argparse.ArgumentParser(description="척추 후보 스캔")
    ap.add_argument("--limit", type=int, default=15, help="탭마다 최근 몇 편")
    ap.add_argument("--groups", default="", help="쉼표로 group 제한. 비우면 전 채널")
    ap.add_argument("--min-minutes", type=float, default=0.0, help="이보다 짧은 영상은 숨긴다")
    ap.add_argument("--probe", action="store_true", help="영상마다 업로드일·길이·channel_id 실측")
    a = ap.parse_args()
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    groups = {g for g in a.groups.split(",") if g}
    chans = [c for c in load_allowlist()["allowed_channels"] if not groups or c.get("group") in groups]
    jobs = [(c, tab) for c in chans for tab in TABS]

    def run(job):
        c, tab = job
        try:
            return job, listing(c["channel_id"], tab, a.limit), None
        except Exception as e:  # noqa: BLE001
            return job, [], e

    with ThreadPoolExecutor(6) as ex:
        results = list(ex.map(run, jobs))
    for (c, tab), rows, err in results:
        print(f"== {c['canonical_name']}  [{c.get('group')}/{c.get('format') or '-'}]  {c['channel_id']}  /{tab}")
        if err:
            print(f"   목록 실패: {err}")
            continue
        shown = 0
        for dur, vid, title in rows:
            if vid in BLOCKED_VIDEO_IDS:
                continue
            try:
                if float(dur) / 60 < a.min_minutes:
                    continue
            except ValueError:
                pass
            shown += 1
            extra = f"  {probe(vid)}" if a.probe else ""
            print(f"   {minutes(dur)} {vid} {title[:90]}{extra}")
        if shown == 0:
            print("   (해당 영상 없음)")


if __name__ == "__main__":
    main()

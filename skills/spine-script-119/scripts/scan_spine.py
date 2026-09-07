# -*- coding: utf-8 -*-
"""척추 후보 스캔. 허용 목록의 SOLO_ARGUMENT(+시사믹스) 채널 RSS 를 읽어 최근 업로드를 나열한다.

영상은 받지 않는다. 길이는 --probe 를 주면 yt-dlp 로 실측한다(봇 확인에 막히면 그 사실을 표시).
"""
from __future__ import annotations

import re
import subprocess
import sys
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _common import load_allowlist  # noqa: E402

KST = timezone(timedelta(hours=9))


def feed(cid: str) -> list[tuple[str, str, str]]:
    url = f"https://www.youtube.com/feeds/videos.xml?channel_id={cid}"
    with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"}), timeout=20) as r:
        h = r.read().decode("utf-8", "ignore")
    out = []
    for e in re.findall(r"<entry>(.*?)</entry>", h, re.S):
        t = re.search(r"<title>(.*?)</title>", e, re.S).group(1)
        v = re.search(r"<yt:videoId>(.*?)</yt:videoId>", e).group(1)
        d = re.search(r"<published>(.*?)</published>", e).group(1)
        out.append((d, v, re.sub(r"&quot;", '"', t)))
    return out


def probe(vid: str):
    p = subprocess.run(["yt-dlp", "--skip-download", "--no-warnings", "-q", "--print",
                        "%(duration)s|%(channel_id)s|%(upload_date)s", f"https://www.youtube.com/watch?v={vid}"],
                       capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=90)
    return p.stdout.strip() if p.returncode == 0 else "BOT_CHECK_OR_ERROR"


def main():
    import argparse
    ap = argparse.ArgumentParser(description="척추 후보 스캔")
    ap.add_argument("--hours", type=int, default=36)
    ap.add_argument("--groups", default="개인주장,시사믹스")
    ap.add_argument("--probe", action="store_true", help="yt-dlp 로 길이·channel_id 실측")
    a = ap.parse_args()
    groups = set(a.groups.split(","))
    since = datetime.now(KST) - timedelta(hours=a.hours)
    al = load_allowlist()
    chans = [c for c in al["allowed_channels"] if c.get("group") in groups]
    for c in sorted(chans, key=lambda c: (c.get("format") != "SOLO_ARGUMENT", c["canonical_name"])):
        tag = "척추" if c.get("format") == "SOLO_ARGUMENT" else c.get("format") or c["group"]
        print(f"== {c['canonical_name']}  [{tag}]  {c['channel_id']}")
        try:
            rows = feed(c["channel_id"])
        except Exception as e:  # noqa: BLE001
            print(f"   RSS 실패: {e}"); continue
        n = 0
        for d, v, t in rows:
            if datetime.fromisoformat(d) < since:
                continue
            n += 1
            extra = f"  {probe(v)}" if a.probe else ""
            print(f"   {d[:16]} {v} {t[:70]}{extra}")
        if n == 0:
            print(f"   (최근 {a.hours}시간 업로드 없음)")


if __name__ == "__main__":
    main()

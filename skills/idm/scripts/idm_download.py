#!/usr/bin/env python3
r"""idm-download — yt-dlp 로 서명된 직접 URL 을 뽑아 IDM 으로 받고 병합·검증한다.

IDM 은 유튜브 페이지 URL 을 그대로 받으면 GUI 가 떠서 멈춘다.
반드시 yt-dlp 로 직접 스트림 URL 을 먼저 뽑는다. 그 URL 에는 PO Token 이
서명돼 있어 일반 HTTP 클라이언트로 받을 수 있다.

IDM_DOWNLOAD_NAMING_POLICY
  JOB_ID   = <video_id>_<yyyyMMdd_HHmmss_fff>_<uuid8>
  작업폴더  = E:\IDM_JOBS\<JOB_ID>\
  임시파일  = video_<uuid8>.<ext> / audio_<uuid8>.<ext> / merged.mp4
  ffprobe PASS 이후에만 최종 폴더로 옮긴다.
  최종 파일명에는 반드시 video_id 를 포함한다.
  JOB 폴더는 절대 공유하지 않는다. IDM 자동 번호 기능에 의존하지 않는다.

IDM_FILENAME_POLICY
  ext 는 단일 소문자 토큰으로 정규화한다. [ ] " ' 공백 . 이 섞이면 IDM 을
  호출하지 않고 즉시 오류로 끝낸다. 확장자가 깨지면 IDM 이 "서버 형식과
  다르다"는 예/아니오 팝업을 띄우고 /n 으로도 막히지 않는다.
  팝업을 자동 클릭하지 말고 이름을 고친다.

SAVE_PATH_POLICY
  최종 저장 폴더는 고정하지 않는다. 호출할 때 작업 목적에 맞는 폴더를 넘긴다.
  바탕화면과 C 드라이브에는 저장하지 않는다. 작업 산출물은 E 드라이브에 둔다.
    119 정치롱폼   E:\정치롱폼\<YYMMDD HH시>\영상\<video_id>    정치·일반 쇼츠  E:\쇼츠\<YYMMDD HH시>    그 외 작업      E: 드라이브 아래 해당 작업 폴더
  JOB 임시폴더만 IDM_JOBS_ROOT(기본 E:\IDM_JOBS)를 쓰고 완료 후 지운다.

사용:
    python idm_download.py <youtube_url> <최종폴더> [--height 1080]
                           [--min-height 720] [--slug 제목축약] [--keep-job]
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import time
import uuid
from datetime import datetime
from pathlib import Path

IDMAN = Path(r"C:\Program Files (x86)\Internet Download Manager\IDMan.exe")
JOBS_ROOT = Path(os.environ.get("IDM_JOBS_ROOT", r"E:\IDM_JOBS"))
ALLOWED_EXT = {"mp4", "m4a", "webm", "weba", "opus", "mkv", "aac", "mp3", "3gp"}

# 편집 호환성 우선: h264 + m4a 를 먼저 시도한다.
# av1/opus 조합은 CapCut 에서 문제가 될 수 있고, m4a 는 MIME 이 audio/mp4 라
# IDM 의 확장자 확인 모달도 뜨지 않는다.
FMT_CHAIN = (
    "bv*[height<={h}][vcodec^=avc1]+ba[ext=m4a]/"
    "bv*[height<={h}]+ba[ext=m4a]/"
    "bv*[height<={h}]+ba/"
    "b[height<={h}]/b"
)
EXT_RE = re.compile(r"^[a-z0-9]{2,5}$")
NAME_RE = re.compile(r"^[A-Za-z0-9_.-]+$")
STABLE_SEC = 4
POLL_SEC = 2


def run(cmd, timeout=600):
    return subprocess.run(cmd, capture_output=True, text=True,
                          encoding="utf-8", errors="replace", timeout=timeout)


def video_id(url: str) -> str:
    m = re.search(r"(?:v=|youtu\.be/|shorts/)([A-Za-z0-9_-]{11})", url)
    return m.group(1) if m else "unknown"


def norm_ext(raw) -> str:
    """확장자를 단일 소문자 토큰으로 정규화하고 검증한다."""
    e = str(raw or "").strip()
    e = e.strip("[]\"' ")
    e = e.lstrip(".").lower()
    if not EXT_RE.match(e) or e not in ALLOWED_EXT:
        raise ValueError(f"확장자 비정상: {raw!r} -> {e!r}")
    return e


def idm_ext_for(fmt: dict) -> str:
    """IDM 에 넘길 확장자. ext 만 보지 말고 vcodec/acodec 를 함께 본다.

    audio-only WebM 은 서버가 Content-Type: audio/webm 을 보내고 IDM 은 그 MIME 의
    정식 확장자인 .weba 로 바꾸겠냐고 모달을 띄운다. 팝업을 억제하지 말고
    처음부터 .weba 로 준다.
    """
    ext = norm_ext(fmt.get("ext"))
    vcodec = str(fmt.get("vcodec") or "none").lower()
    acodec = str(fmt.get("acodec") or "none").lower()
    audio_only = vcodec in ("none", "") and acodec not in ("none", "")
    if ext == "webm" and audio_only:
        return "weba"
    return ext


def direct_streams(url: str, height: int) -> list:
    """[(직접URL, ext, 종류)] — JSON 으로 정확히 뽑는다. --print 문자열 파싱은 쓰지 않는다."""
    fmt = FMT_CHAIN.format(h=height)
    r = run([sys.executable, "-m", "yt_dlp", "--no-warnings", "-f", fmt,
             "-J", "--skip-download", url], timeout=300)
    if r.returncode != 0:
        raise RuntimeError(f"yt-dlp 실패: {(r.stderr or '').strip()[-300:]}")
    info = json.loads(r.stdout)
    picked = info.get("requested_formats") or [info]
    out = []
    for f in picked:
        vcodec = str(f.get("vcodec") or "none").lower()
        kind = "audio" if vcodec in ("none", "") else "video"
        out.append((f["url"], idm_ext_for(f), kind))
    return out


def idm_fetch(url: str, folder: Path, name: str, timeout=3600) -> Path:
    if not NAME_RE.match(name) or name.count(".") != 1:
        raise ValueError(f"파일명 비정상, IDM 호출 중단: {name!r}")
    dest = folder / name
    subprocess.Popen([str(IDMAN), "/n", "/d", url, "/p", str(folder), "/f", name])
    start = time.time()
    last = -1
    stable = 0.0
    while time.time() - start < timeout:
        time.sleep(POLL_SEC)
        size = dest.stat().st_size if dest.exists() else -1
        if size > 0 and size == last:
            stable += POLL_SEC
            if stable >= STABLE_SEC:
                return dest
        else:
            stable = 0.0
        last = size
    raise TimeoutError(f"IDM 시간 초과: {name}")


def probe(p: Path):
    r = run(["ffprobe", "-v", "error", "-show_entries",
             "stream=codec_type,codec_name,width,height:format=duration,size",
             "-of", "json", str(p)], timeout=120)
    if r.returncode != 0:
        return False, {}
    info = json.loads(r.stdout)
    st = info.get("streams", [])
    v = next((s for s in st if s.get("codec_type") == "video"), None)
    a = next((s for s in st if s.get("codec_type") == "audio"), None)
    dur = float(info.get("format", {}).get("duration", 0) or 0)
    return bool(v and a and dur > 0), {"v": v or {}, "a": a or {}, "dur": dur}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("url")
    ap.add_argument("dest_folder")
    ap.add_argument("--height", type=int, default=1080)
    ap.add_argument("--min-height", type=int, default=0,
                    help="이 높이보다 낮게 받히면 실패로 끝낸다. 119 롱폼은 720 을 준다.")
    ap.add_argument("--slug", default="")
    ap.add_argument("--keep-job", action="store_true")
    a = ap.parse_args()

    vid = video_id(a.url)
    now = datetime.now()
    short = uuid.uuid4().hex[:8]
    job = f"{vid}_{now:%Y%m%d_%H%M%S}_{now.microsecond // 1000:03d}_{short}"
    jobdir = JOBS_ROOT / job
    jobdir.mkdir(parents=True, exist_ok=True)
    dest_folder = Path(a.dest_folder)
    dest_folder.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    print(f"JOB_ID   {job}")
    print(f"작업폴더  {jobdir}")

    merged = jobdir / "merged.mp4"
    how = "IDM"
    try:
        if not IDMAN.is_file():
            raise RuntimeError("IDM 미설치")
        streams = direct_streams(a.url, a.height)
        print(f"직접 URL  {len(streams)}개  " +
              "  ".join(f"{k}:{e}" for _, e, k in streams))
        parts = []
        for i, (u, ext, kind) in enumerate(streams):
            nm = f"{kind}_{short}.{ext}"
            print(f"  IDM {i + 1}/{len(streams)} -> {nm}  ({kind})", flush=True)
            p = idm_fetch(u, jobdir, nm)
            print(f"    {p.stat().st_size:,} bytes", flush=True)
            parts.append(p)
        if len(parts) == 1:
            shutil.move(str(parts[0]), merged)
        else:
            cmd = ["ffmpeg", "-v", "error", "-y"]
            for p in parts:
                cmd += ["-i", str(p)]
            cmd += ["-c", "copy", "-movflags", "+faststart", str(merged)]
            r = run(cmd, timeout=1800)
            if r.returncode != 0:
                raise RuntimeError(f"merge 실패: {(r.stderr or '')[-300:]}")
    except Exception as exc:
        print(f"IDM 경로 실패({exc}) -> yt-dlp 폴백", flush=True)
        how = "yt-dlp"
        fmt = f"bv*[height<={a.height}]+ba/b[height<={a.height}]/b"
        r = run([sys.executable, "-m", "yt_dlp", "--no-playlist", "--no-progress",
                 "-f", fmt, "--merge-output-format", "mp4", "-o", str(merged), a.url],
                timeout=5400)
        if r.returncode != 0:
            print((r.stderr or "")[-400:])
            return 1

    ok, info = probe(merged)
    if not ok:
        print("ffprobe FAIL — 최종 폴더로 옮기지 않는다")
        return 1

    h = info["v"].get("height", "?")
    if a.min_height and isinstance(h, int) and h < a.min_height:
        print(f"해상도 미달 {h}p < {a.min_height}p — 최종 폴더로 옮기지 않는다")
        print("PO Token 공급자가 없으면 DASH 가 403 이 나고 360p 로 떨어진다. 먼저 그것을 고친다.")
        return 1
    slug = re.sub(r"[^A-Za-z0-9-]+", "-", a.slug).strip("-").lower()
    final = dest_folder / (f"{vid}_{slug}_{h}p.mp4" if slug else f"{vid}_{h}p.mp4")
    if final.exists():
        ok2, info2 = probe(final)
        same = (ok2 and abs(info2["dur"] - info["dur"]) < 1.0
                and final.stat().st_size == merged.stat().st_size)
        if same:
            print(f"동일 파일 존재 -> 재사용 {final}")
            if not a.keep_job:
                shutil.rmtree(jobdir, ignore_errors=True)
            return 0
        final = dest_folder / f"{final.stem}_{short}.mp4"
    shutil.move(str(merged), final)
    if not a.keep_job:
        shutil.rmtree(jobdir, ignore_errors=True)

    print(f"\n최종  {final}")
    print(f"방식  {how}")
    print(f"크기  {final.stat().st_size:,} bytes")
    print(f"영상  {info['v'].get('codec_name', '-')} {info['v'].get('width', '?')}x{h}")
    print(f"음성  {info['a'].get('codec_name', '-')}")
    print(f"길이  {info['dur']:.1f}s")
    print(f"경과  {time.time() - t0:.1f}s")
    print("검증  PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
r"""idm-download — yt-dlp 로 서명된 직접 URL 을 뽑아 IDM 으로 받고 병합·검증한다.

라우팅
  YouTube 등 추출기가 있는 페이지 URL  -> yt-dlp 가 받는다. IDM 은 쓰지 않는다.
  일반 파일 직접 URL(mp4, zip, 파일서버) -> IDM 이 받는다.

googlevideo 서명 URL 은 Range 헤더 없는 전체 요청을 403 으로 거부한다.
측정값: Range 없음 403, bytes=0- 403, bytes=0-1048575 206, bytes=0-10485759 206,
bytes=0-<전체크기> 403. IDM 은 전체 요청을 보내므로 이 URL 을 받지 못한다.
그래서 YouTube 는 IDM 으로 우회하지 않고 yt-dlp 로 받는다.

YouTube 403 과 360p 추락의 진짜 원인은 player_client 다. 기본 android_vr 의
GVS URL 은 bgutil 이 발급하지 못하는 PO Token 을 요구해서 403 이 나고, 폴백이
format 18(640x360)을 잡아 성공으로 보고된다. mweb 또는 web_embedded 로 고르면
같은 영상이 720p~1080p h264 로 받아진다.

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
    python idm_download.py <url> <최종폴더> [--height 1080]
                           [--min-height 720] [--slug 제목축약]
                           [--client mweb,web_embedded] [--try-idm] [--keep-job]
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
PAGE_RE = re.compile(r"(?:youtube\.com|youtu\.be|youtube-nocookie\.com)", re.I)
DEFAULT_CLIENT = "mweb,web_embedded"
DIRECT_FILE_RE = re.compile(r"\.(mp4|m4a|mkv|webm|mov|mp3|aac|zip|7z|rar|iso|pdf)(?:$|[?#])", re.I)
NAME_RE = re.compile(r"^[A-Za-z0-9_.-]+$")
STABLE_SEC = 4
POLL_SEC = 2
START_SEC = 90


class RouteToYtdlp(Exception):
    """실패가 아니라 경로 선택. 이 URL 은 IDM 이 아니라 yt-dlp 가 받는다."""


def run(cmd, timeout=600):
    return subprocess.run(cmd, capture_output=True, text=True,
                          encoding="utf-8", errors="replace", timeout=timeout)


def ytdlp_cmd() -> list:
    """yt-dlp 실행 방법을 런타임에서 찾는다.

    호출한 인터프리터(sys.executable)에 yt_dlp 모듈이 있다는 보장이 없다.
    Hermes venv 처럼 모듈이 없는 런타임에서도 PATH 의 yt-dlp 실행파일을 쓴다.
    """
    exe = shutil.which("yt-dlp") or shutil.which("yt-dlp.exe")
    if exe:
        return [exe]
    probe = subprocess.run([sys.executable, "-m", "yt_dlp", "--version"],
                           capture_output=True, text=True)
    if probe.returncode == 0:
        return [sys.executable, "-m", "yt_dlp"]
    raise RuntimeError("yt-dlp 를 찾지 못했다. PATH 의 실행파일이나 python -m yt_dlp 중 하나가 필요하다.")


def extractor_args(url: str, client: str) -> list:
    """YouTube 일 때만 player_client 를 고정한다.

    기본 android_vr 은 bgutil 이 만들지 못하는 PO Token 을 요구해 403 이 난다.
    mweb 과 web_embedded 는 발급된 토큰과 클라이언트가 일치해 정상 수신된다.
    """
    if not PAGE_RE.search(url) or not client:
        return []
    return ["--extractor-args", f"youtube:player_client={client};fetch_pot=always"]


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


def direct_streams(url: str, height: int, client: str) -> list:
    """[(직접URL, ext, 종류)] — JSON 으로 정확히 뽑는다. --print 문자열 파싱은 쓰지 않는다."""
    fmt = FMT_CHAIN.format(h=height)
    r = run([*ytdlp_cmd(), "--no-warnings", *extractor_args(url, client), "-f", fmt,
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
    """IDM 으로 한 스트림을 받는다.

    IDM 은 완료된 파일만 /p 폴더에 쓰고 부분 데이터는 자기 temp 에 둔다. 그래서
    폴더가 비어 있는 것만으로는 실패를 알 수 없다. 서버가 403 을 주면 IDM 은
    모달 오류창을 띄우고 무한 대기하므로, START_SEC 안에 아무 바이트도 나타나지
    않으면 실패로 보고 폴백으로 넘긴다.
    """
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
        if size <= 0 and time.time() - start > START_SEC:
            raise TimeoutError(
                f"IDM 이 {START_SEC}초 안에 한 바이트도 쓰지 못했다: {name}. "
                "서명 URL 이 403 이거나 오류창이 떠 있을 수 있다.")
        if size > 0 and size == last:
            stable += POLL_SEC
            if stable >= STABLE_SEC:
                return dest
        else:
            stable = 0.0
        last = size
    raise TimeoutError(f"IDM 시간 초과: {name}")


def probe(p: Path, need_audio: bool = True):
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
    ok = bool(v) and dur > 0 and (bool(a) or not need_audio)
    return ok, {"v": v or {}, "a": a or {}, "dur": dur}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("url")
    ap.add_argument("dest_folder")
    ap.add_argument("--height", type=int, default=1080)
    ap.add_argument("--min-height", type=int, default=0,
                    help="이 높이보다 낮게 받히면 실패로 끝낸다. 119 롱폼은 720 을 준다.")
    ap.add_argument("--slug", default="")
    ap.add_argument("--client", default=DEFAULT_CLIENT,
                    help="YouTube player_client. 빈 문자열이면 yt-dlp 기본값을 쓴다.")
    ap.add_argument("--try-idm", action="store_true",
                    help="추출기 페이지 URL 에도 IDM 을 시도한다. googlevideo 에서는 403 이 난다.")
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
    # 추출기 페이지 URL 은 영상+음성이 나와야 정상이다. 임의의 직접 파일은
    # 음성이 없을 수 있으므로 영상 스트림과 길이만 요구한다.
    need_audio = bool(PAGE_RE.search(a.url)) or not DIRECT_FILE_RE.search(a.url)
    try:
        if not IDMAN.is_file():
            raise RuntimeError("IDM 미설치")
        if PAGE_RE.search(a.url) and not a.try_idm:
            raise RouteToYtdlp(
                "추출기 페이지 URL. googlevideo 서명 URL 은 Range 없는 전체 요청을 "
                "403 으로 막아 IDM 이 받지 못한다")
        if DIRECT_FILE_RE.search(a.url):
            # 이미 직접 파일 URL 이다. yt-dlp 해석을 거치지 않고 IDM 에 그대로 준다.
            ext = norm_ext(DIRECT_FILE_RE.search(a.url).group(1))
            streams = [(a.url, ext, "video")]
        else:
            streams = direct_streams(a.url, a.height, a.client)
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
    except RouteToYtdlp as exc:
        print(f"경로  yt-dlp — {exc}", flush=True)
        how = "yt-dlp"
    except Exception as exc:
        print(f"IDM 경로 실패({exc}) -> yt-dlp 폴백", flush=True)
        how = "yt-dlp"

    if how == "yt-dlp":
        fmt = FMT_CHAIN.format(h=a.height)  # 폴백도 h264+m4a 를 먼저 고른다
        r = run([*ytdlp_cmd(), "--no-playlist", "--no-progress",
                 *extractor_args(a.url, a.client),
                 "-f", fmt, "--merge-output-format", "mp4", "-o", str(merged), a.url],
                timeout=5400)
        if r.returncode != 0:
            print((r.stderr or "")[-400:])
            return 1

    ok, info = probe(merged, need_audio)
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
        ok2, info2 = probe(final, need_audio)
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

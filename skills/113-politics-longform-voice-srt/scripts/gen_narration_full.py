#!/usr/bin/env python3
"""P02b full narration generation — candidate A locked (sona_speech_2).

권위 대본 문구 무수정. 26 세그먼트 개별 WAV + ffprobe 실측 + manifest.
실패 시 추정 길이로 대체하지 않는다.
"""
import hashlib
import json
import subprocess
import sys
import time
import wave
import winreg
from pathlib import Path

# --- 에피소드 파라미터 (환경변수 필수) ---------------------------------------
# PL_EPISODE_DIR   : 로컬 미디어 정본 (OneDrive 에피소드 폴더, Git 미추적)
# PL_REPO_EPISODE  : Git 추적 산출물 (clean checkout 내 docs/.../episodes/<ID>)
# PL_VIDEO_DIR     : 원본 mp4 폴더 (S01.mp4~)
# PL_SCRIPT_SHA256 : 권위 대본 SHA-256 (staleness 탐지용)
import os


def _req(name):
    v = os.environ.get(name)
    if not v:
        raise SystemExit(f"FAIL: 환경변수 {name} 미설정. 에피소드 경로를 명시해야 한다.")
    return v


EPISODE = Path(_req("PL_EPISODE_DIR"))
REPO_EPISODE = Path(_req("PL_REPO_EPISODE"))
# ---------------------------------------------------------------------------

SEGMENTS_JSON = REPO_EPISODE / "30_audio_srt" / "narration_segments.json"
OUT = EPISODE / "30_audio_srt" / "narration"
MANIFEST = EPISODE / "30_audio_srt" / "voice_manifest.json"

VOICE_ID = "otFXhy6zBa2LQ8AYSWUeDB"
MODEL = "sona_speech_2"
VOICE_SETTINGS = {"pitch_shift": 0, "pitch_variance": 1, "speed": 1}
MAX_RETRY = 3


def user_env(name):
    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment") as key:
        return winreg.QueryValueEx(key, name)[0]


def probe(path):
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries",
         "format=duration:stream=codec_name,sample_rate,channels,bits_per_sample",
         "-of", "json", str(path)],
        capture_output=True, text=True, check=True,
    )
    return json.loads(out.stdout)


def main():
    from supertone import Supertone

    data = json.loads(SEGMENTS_JSON.read_text(encoding="utf-8-sig"))
    segments = data["segments"]
    script_sha = data["authoritative_script_sha256"].lower()
    OUT.mkdir(parents=True, exist_ok=True)
    client = Supertone(api_key=user_env("SUPERTONE_API_KEY"))

    results = []
    cursor = 0.0
    failed = 0

    for i, seg in enumerate(segments, 1):
        sid = seg["segment_id"]
        dest = OUT / f"{sid}.wav"
        entry = {
            "segment_id": sid,
            "source_block_id": seg["source_block_id"],
            "part": seg["part"],
            "character_count": seg["character_count"],
            "path": str(dest),
        }
        for attempt in range(1, MAX_RETRY + 1):
            try:
                res = client.text_to_speech.create_speech(
                    voice_id=VOICE_ID, text=seg["text"], language="ko",
                    model=MODEL, output_format="wav",
                    voice_settings=VOICE_SETTINGS,
                )
                r = res.result
                audio = r.read() if hasattr(r, "read") else r.content
                if not isinstance(audio, bytes) or not audio.startswith(b"RIFF"):
                    raise ValueError("response is not RIFF WAV")
                dest.write_bytes(audio)
                with wave.open(str(dest), "rb") as w:
                    dur = w.getnframes() / w.getframerate()
                entry.update({
                    "status": "OK",
                    "bytes": len(audio),
                    "sha256": hashlib.sha256(audio).hexdigest(),
                    "duration_sec": round(dur, 6),
                    "offset_start_sec": round(cursor, 6),
                    "offset_end_sec": round(cursor + dur, 6),
                    "attempts": attempt,
                    "ffprobe": probe(dest),
                })
                cursor += dur
                print(f"[{i:2d}/26] OK  {sid} {dur:6.2f}s  {len(audio):>9,}B", flush=True)
                break
            except Exception as e:
                if attempt == MAX_RETRY:
                    entry.update({"status": "FAIL", "attempts": attempt,
                                  "error_type": type(e).__name__,
                                  "error": str(e)[:300]})
                    failed += 1
                    print(f"[{i:2d}/26] FAIL {sid} {type(e).__name__}: "
                          f"{str(e)[:150]}", flush=True)
                else:
                    time.sleep(2 * attempt)
        results.append(entry)

    ok = [r for r in results if r.get("status") == "OK"]
    manifest = {
        "schema_version": "yusimin-p02b-voice-manifest-v1",
        "status": "PASS" if failed == 0 else ("PARTIAL" if ok else "FAIL"),
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "authoritative_script_sha256": script_sha,
        "script_content_audit": {
            "report": "90_reports/script_content_audit_v1.json",
            "ruling": "PENDING_PROJECT_GPT",
            "note": "대본 수정 확정 시 해당 세그먼트만 재생성. "
                    "authoritative_script_sha256 변경으로 stale 탐지.",
        },
        "voice_id": VOICE_ID,
        "model": MODEL,
        "voice_settings": VOICE_SETTINGS,
        "language": "ko",
        "output_format": "wav",
        "generator": "supertone SDK 0.2.3 text_to_speech.create_speech",
        "segment_count": len(segments),
        "segment_ok": len(ok),
        "segment_failed": failed,
        "narration_total_duration_sec": round(cursor, 6),
        "narration_total_chars": sum(s["character_count"] for s in segments),
        "media_root": str(OUT),
        "git_tracked": False,
        "segments": results,
    }
    MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
                        encoding="utf-8")
    print(f"\nstatus={manifest['status']} ok={len(ok)}/{len(segments)} "
          f"total={cursor:.2f}s ({cursor/60:.2f}min)")
    print(f"manifest -> {MANIFEST}")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())

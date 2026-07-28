#!/usr/bin/env python3
"""P02b 발음검사 + P03 정렬용 word timestamp 추출.

faster-whisper로 나레이션 26 세그먼트 ASR. 산출은 두 가지:
  1) word-level timestamp  -> P03 SRT 정렬 입력
  2) ASR 전사 텍스트        -> 발음 검사 (권위 대본 어휘 대조)

주의: 자막 문자열은 ASR 출력이 아니라 권위 대본 원문을 쓴다.
여기서는 타이밍과 발음 확인만 얻는다.
"""
import json
import sys
import time
from pathlib import Path

# --- 에피소드 파라미터 (환경변수 필수) ---------------------------------------
# PL_EPISODE_DIR   : 로컬 정본 (OneDrive 에피소드 폴더)
# PL_VIDEO_DIR     : 원본 mp4 폴더 (S01.mp4~)
# PL_SCRIPT_SHA256 : 권위 대본 SHA-256 (staleness 탐지용)
import os


def _req(name):
    v = os.environ.get(name)
    if not v:
        raise SystemExit(f"FAIL: 환경변수 {name} 미설정. 에피소드 경로를 명시해야 한다.")
    return v


EPISODE = Path(_req("PL_EPISODE_DIR"))
# ---------------------------------------------------------------------------

NAR = EPISODE / "30_audio_srt" / "narration"
VOICE_MANIFEST = EPISODE / "30_audio_srt" / "voice_manifest.json"
OUT = EPISODE / "30_audio_srt" / "alignment_raw_v1.json"
PRON = EPISODE / "90_reports" / "pronunciation_check_v1.json"

# 권위 대본 lexicon 중 오발음 위험 어휘
TARGETS = [
    "유시민", "이재명", "박원석", "박은정", "김용민", "홍익표", "김재현",
    "보완수사권", "재수사권", "직접수사권", "수사권", "기소권",
    "공소청", "중수청", "국가수사본부", "고위공직자범죄수사처",
    "형사소송법", "더불어민주당", "민주당", "검찰개혁",
]

MODEL_SIZE = "medium"


def main():
    from faster_whisper import WhisperModel

    vm = json.loads(VOICE_MANIFEST.read_text(encoding="utf-8-sig"))
    segs = [s for s in vm["segments"] if s.get("status") == "OK"]
    print(f"segments={len(segs)} model={MODEL_SIZE}", flush=True)

    t0 = time.time()
    model = WhisperModel(MODEL_SIZE, device="cpu", compute_type="int8")
    print(f"model loaded in {time.time()-t0:.1f}s", flush=True)

    out = {
        "schema_version": "yusimin-p03-alignment-raw-v1",
        "status": "PENDING",
        "asr_engine": f"faster-whisper {MODEL_SIZE} int8 cpu",
        "authoritative_script_sha256": vm["authoritative_script_sha256"],
        "note": "타이밍/발음 확인 전용. 자막 문자열은 권위 대본 원문을 사용한다.",
        "segments": [],
    }

    for i, s in enumerate(segs, 1):
        wav = Path(s["path"])
        t1 = time.time()
        it, info = model.transcribe(
            str(wav), language="ko", word_timestamps=True,
            vad_filter=False, beam_size=5,
        )
        words, texts = [], []
        for seg in it:
            texts.append(seg.text)
            for w in (seg.words or []):
                words.append({
                    "word": w.word,
                    "start": round(w.start, 3),
                    "end": round(w.end, 3),
                    "prob": round(w.probability, 4),
                })
        asr_text = "".join(texts).strip()
        out["segments"].append({
            "segment_id": s["segment_id"],
            "source_block_id": s["source_block_id"],
            "wav": str(wav),
            "wav_duration_sec": s["duration_sec"],
            "offset_start_sec": s["offset_start_sec"],
            "asr_text": asr_text,
            "word_count": len(words),
            "words": words,
        })
        print(f"[{i:2d}/{len(segs)}] {s['segment_id']} words={len(words):3d} "
              f"{time.time()-t1:5.1f}s", flush=True)

    out["status"] = "PASS"
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n",
                   encoding="utf-8")

    # 발음 검사: 권위 대본에 해당 어휘가 있는 세그먼트에서 ASR이 같은 어휘를 냈는지
    src = {s["segment_id"]: s for s in vm["segments"]}
    seg_json = json.loads(
        (EPISODE / "30_audio_srt" / "narration_segments.json")
        .read_text(encoding="utf-8-sig"))
    text_by_id = {x["segment_id"]: x["text"] for x in seg_json["segments"]}

    findings, checked = [], 0
    for a in out["segments"]:
        sid = a["segment_id"]
        script_text = text_by_id.get(sid, "")
        for term in TARGETS:
            if term in script_text:
                checked += 1
                if term not in a["asr_text"]:
                    findings.append({
                        "segment_id": sid,
                        "term": term,
                        "script_occurrences": script_text.count(term),
                        "found_in_asr": False,
                        "asr_text": a["asr_text"][:400],
                        "severity": "REVIEW",
                        "note": "ASR이 해당 어휘를 그대로 내지 않음. "
                                "오발음 또는 ASR 한계일 수 있어 청취 확인 필요.",
                    })
    pron = {
        "schema_version": "yusimin-p02b-pronunciation-check-v1",
        "status": "PASS" if not findings else "REVIEW_REQUIRED",
        "asr_engine": f"faster-whisper {MODEL_SIZE} int8 cpu",
        "authoritative_script_sha256": vm["authoritative_script_sha256"],
        "voice_id": vm["voice_id"],
        "model": vm["model"],
        "terms_checked": checked,
        "mismatch_count": len(findings),
        "method": "권위 대본 세그먼트에 존재하는 어휘가 ASR 전사에도 나타나는지 대조. "
                  "불일치는 오발음 확정이 아니라 청취 확인 대상.",
        "findings": findings,
    }
    PRON.write_text(json.dumps(pron, ensure_ascii=False, indent=2) + "\n",
                    encoding="utf-8")
    print(f"\nalignment -> {OUT}")
    print(f"pronunciation status={pron['status']} "
          f"checked={checked} mismatch={len(findings)} -> {PRON}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

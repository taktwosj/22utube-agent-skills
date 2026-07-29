#!/usr/bin/env python3
"""잠금 프리플라이트 — 하류 스크립트가 게이트를 우회하지 못하게 한다.

게이트를 만들어 둬도 **스크립트를 직접 실행하면 그만이다.** 지난 에피소드에서
감사 게이트가 SKILL.md 안의 문장이었고 그대로 무시된 것과 같은 구조다.
그래서 실행 스크립트가 스스로 게이트를 호출하게 만든다.

사용 (스크립트 최상단):

    from lock_preflight import require_gate, locked_tts_params
    LOCK = require_gate(EPISODE, "tts")          # 실패하면 여기서 exit 1
    TTS = locked_tts_params(LOCK, EPISODE)       # 111 TTS 잠금만 사용

이 파일을 직접 실행하면 self-check 를 돌고 인자가 없으면 비정상 종료한다.
표준 라이브러리만 사용한다.
"""
import json
import subprocess
import sys
from pathlib import Path

GATE = Path(__file__).resolve().parent / "gate_lock.py"
LOCK_RELPATH = Path("20_script") / "script_lock.json"
TTS_LOCK_RELPATH = Path("30_audio_srt") / "tts_params_lock_v1.json"

REQUIRED_TTS_KEYS = ("provider", "voice_id", "model",
                     "speed", "pitch_shift", "pitch_variance")
TTS_LOCK_FIELDS = {"schema", "status", "authority", "script_sha256",
                   "tts_params"}


class LockGateError(SystemExit):
    """게이트 실패. 호출자는 잡지 말고 그대로 종료시킨다."""


def require_gate(episode, stage):
    """게이트를 실행하고 통과하면 잠금 dict 를 돌려준다. 실패하면 종료한다."""
    episode = Path(episode)
    if not GATE.is_file():
        raise LockGateError(f"WAIT_SCRIPT_LOCK_GATE: 게이트가 없다 {GATE}")

    proc = subprocess.run(
        [sys.executable, str(GATE), "--episode", str(episode),
         "--stage", stage, "--json"],
        capture_output=True, text=True, encoding="utf-8", errors="replace")

    try:
        report = json.loads(proc.stdout)
    except Exception:
        raise LockGateError(
            "WAIT_SCRIPT_LOCK_GATE: 게이트 출력을 읽을 수 없다\n"
            + (proc.stdout or "") + (proc.stderr or ""))

    if proc.returncode != 0 or not report.get("passed"):
        lines = [f"WAIT_SCRIPT_LOCK_GATE: stage={stage} 잠금 게이트 실패"]
        for f in report.get("failures", []):
            lines.append(f"  {f['code']}\n        {f['detail']}")
        lines.append("  대본 잠금이 유효해야 이 단계를 실행할 수 있다.")
        raise LockGateError("\n".join(lines))

    lock_path = episode / LOCK_RELPATH
    return json.loads(lock_path.read_text(encoding="utf-8"))


def locked_tts_params(lock, episode):
    """111이 별도로 잠근 TTS 설정을 돌려준다.

    같은 대본이라도 speed 1.0 -> 1.2 면 음성 길이가 달라지고, 그러면
    정렬·SRT·시간축이 전부 바뀐다. 110의 불변 대본 잠금에 TTS 결정을
    끼워 넣지 않고, 프로젝트 GPT 음색 승인 뒤 만든 111 잠금을 사용한다.
    """
    path = Path(episode) / TTS_LOCK_RELPATH
    if not path.is_file():
        raise LockGateError(f"WAIT_TTS_PARAMS_LOCK: {path} 없음")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise LockGateError(f"TTS_PARAMS_INTEGRITY_FAIL: {path}: {exc}")
    if not isinstance(payload, dict) or set(payload) != TTS_LOCK_FIELDS:
        raise LockGateError("TTS_PARAMS_INTEGRITY_FAIL: top-level fields mismatch")
    if payload.get("schema") != "politics-longform-tts-params-lock.v1":
        raise LockGateError("TTS_PARAMS_INTEGRITY_FAIL: schema 불일치")
    if payload.get("status") != "TTS_PARAMS_LOCKED":
        raise LockGateError("TTS_PARAMS_INTEGRITY_FAIL: status 불일치")
    if payload.get("authority") != "PROJECT_GPT":
        raise LockGateError("TTS_PARAMS_INTEGRITY_FAIL: authority 불일치")
    if payload.get("script_sha256") != (lock or {}).get("script_sha256"):
        raise LockGateError("TTS_PARAMS_INTEGRITY_FAIL: script_sha256 불일치")
    params = payload.get("tts_params") or {}
    if not isinstance(params, dict):
        raise LockGateError(
            "TTS_PARAMS_INTEGRITY_FAIL: tts_params must be object")
    missing = sorted(set(REQUIRED_TTS_KEYS) - set(params))
    if missing:
        raise LockGateError(
            f"TTS_PARAMS_INTEGRITY_FAIL: tts_params 키 누락 {missing}")
    if set(params) != set(REQUIRED_TTS_KEYS):
        raise LockGateError(
            "TTS_PARAMS_INTEGRITY_FAIL: tts_params fields mismatch")
    for key in ("provider", "voice_id", "model"):
        if not isinstance(params[key], str) or not params[key].strip():
            raise LockGateError(
                f"TTS_PARAMS_INTEGRITY_FAIL: {key} must be non-empty string")
    for key in ("speed", "pitch_shift", "pitch_variance"):
        value = params[key]
        if not isinstance(value, (int, float)) or isinstance(value, bool):
            raise LockGateError(
                f"TTS_PARAMS_INTEGRITY_FAIL: {key} must be numeric")
    if params["speed"] <= 0:
        raise LockGateError("TTS_PARAMS_INTEGRITY_FAIL: speed must be > 0")
    if params["pitch_variance"] <= 0:
        raise LockGateError(
            "TTS_PARAMS_INTEGRITY_FAIL: pitch_variance must be > 0")
    return params


def assert_runtime_matches(params, runtime):
    """런타임이 잠금과 다른 설정을 쓰려 하면 막는다."""
    diff = {k: (params.get(k), runtime[k])
            for k in runtime if k in params and params.get(k) != runtime[k]}
    if diff:
        lines = ["TTS_PARAMS_INTEGRITY_FAIL: 런타임 설정이 잠금과 다르다"]
        for k, (locked, got) in diff.items():
            lines.append(f"  {k}: 잠금 {locked!r} != 런타임 {got!r}")
        lines.append("  잠긴 값으로만 생성한다. override 하려면 다시 잠가라.")
        raise LockGateError("\n".join(lines))


def tts_params_fingerprint(params):
    """voice_manifest 에 남길 지문. 사후에 어떤 설정이었는지 대조 가능하게 한다."""
    import hashlib
    canon = json.dumps({k: params[k] for k in sorted(params)},
                       ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(canon.encode("utf-8")).hexdigest()


def _self_check():
    if len(sys.argv) < 2:
        print("FAIL: 이 파일은 모듈이다. 사용법:\n"
              "  from lock_preflight import require_gate, locked_tts_params\n"
              "  self-check 를 돌리려면 에피소드 경로를 인자로 준다. "
              "환경변수 PL_EPISODE_DIR 도 사용된다.", file=sys.stderr)
        return 2
    lock = require_gate(sys.argv[1], "tts")
    params = locked_tts_params(lock, sys.argv[1])
    print("PASS: 게이트 통과 · tts_params 지문 "
          f"{tts_params_fingerprint(params)[:16]}")
    return 0


if __name__ == "__main__":
    sys.exit(_self_check())

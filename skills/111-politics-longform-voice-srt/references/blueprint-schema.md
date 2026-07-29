# 정치롱폼 단계별 잠금

## 잠금 소유권

```text
110 script_lock.json             대본과 승인 증거
111 tts_params_lock_v1.json      프로젝트 GPT가 승인한 음색 설정
111 subtitle/timeline locks      최종 자막과 오디오 시간축
112 production input gate        위 잠금과 실제 미디어를 결합
```

앞 단계 잠금을 수정해 다음 단계 결정을 끼워 넣지 않는다. 다음 단계는 새 잠금을
쌓고 앞 단계 SHA를 참조한다.

## script_lock.json

110이 생성하고 111이 소비한다. 기계 계약은 110과 111의
`references/script_lock.schema.json`이며 두 파일은 byte-identical해야 한다.

```json
{
  "schema": "politics-longform-script-lock.v1",
  "episode_id": "PL_YYYYMMDD_slug",
  "status": "SCRIPT_LOCKED",
  "lock_version": 1,
  "locked_at": "ISO-8601",
  "produced_by": "110-politics-longform-script",
  "script_sha256": "...",
  "locked_script": "20_script/master_script_locked.md",
  "evidence": {
    "approved_script": {"path": "...", "sha256": "..."},
    "source_packet": {"path": "...", "sha256": "..."},
    "verification_report": {"path": "...", "sha256": "..."},
    "independent_review": {"path": "...", "sha256": "..."},
    "user_approval": {"path": "...", "sha256": "..."}
  },
  "events": {
    "review_event_id": "...",
    "claude_review_event_id": "...",
    "user_approval_event_id": "..."
  },
  "authority": {
    "drafter": "PROJECT_GPT",
    "reviewer": "CLAUDE",
    "final_lock": "USER"
  },
  "next_stage": "111-politics-longform-voice-srt"
}
```

111은 대본 내용을 재감사하지 않는다. 다음 결합만 다시 확인한다.

- 잠긴 대본과 승인 대본의 byte identity 및 SHA-256
- 증거 5종의 episode 상대경로, 실제 파일 SHA-256
- 검증 보고서의 대본 SHA, source packet SHA, 위반 0건
- 독립 검수서의 verdict, 대본 SHA, 검수 사건 ID
- 사용자 승인서의 경로, 파일 SHA, 검수·승인 사건 ID

## tts_params_lock_v1.json

Supertone TTS API 음색은 111의 샘플 검토 뒤 확정되므로 110 대본 잠금에 넣지 않는다.

```json
{
  "schema": "politics-longform-tts-params-lock.v1",
  "status": "TTS_PARAMS_LOCKED",
  "authority": "PROJECT_GPT",
  "script_sha256": "...",
  "tts_params": {
    "provider": "supertone",
    "voice_id": "...",
    "model": "sona_speech_2",
    "speed": 1,
    "pitch_shift": 0,
    "pitch_variance": 1
  }
}
```

`gen_narration_full.py`는 대본 잠금과 이 파일을 모두 확인한다. TTS 잠금의
`script_sha256`이 현재 대본 잠금과 다르면 생성하지 않는다.

## 공통 무결성 규칙

- 경로는 episode 상대경로만 사용한다. 절대경로와 `..`는 금지한다.
- SHA는 소문자 64자리 SHA-256만 허용한다.
- 잠금 뒤 파일 내용이 바뀌면 하류 게이트를 통과하지 못한다.
- 미실행 증거는 `PASS`가 아니라 `WAIT` 또는 `NOT RUN`이다.

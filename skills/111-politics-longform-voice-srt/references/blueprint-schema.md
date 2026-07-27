# 제작 잠금 스키마 v1

대본 잠금 = **설계도 확정**이다. 문장만 얼리는 게 아니라 하류 전체가 의존하는
결정을 동결한다.

## 잠금은 하나가 아니라 네 개다

v1 초안은 `script_lock.json` 하나에 `assembly_allowed` 플래그를 넣었다.
**모순이다.** 잠금은 불변인데 그 플래그는 자막 QC 이후 `false -> true`로
바뀌어야 한다. 바꾸면 잠금이 깨지고, 안 바꾸면 조립이 영원히 막힌다.

단계마다 별도 잠금을 쌓는다.

```text
script_lock.json           대본 · 출처 · 편집판정 · Supertone TTS 설정
  -> 나레이션 합성 허용

subtitle_lock.json         최종 SRT · 자막 QC 판정
  -> 자막 확정

timeline_lock.json         오디오 시간축 · 세그먼트 오프셋
  -> 시간축 확정

production_ready_lock.json 위 셋 + 템플릿 lock 의 SHA를 묶는다
  -> 조립·렌더 허용
```

각 잠금은 만들어진 뒤 **절대 수정되지 않는다.** 다음 단계는 새 파일을 쌓는다.

```text
gate_lock.py --stage tts       script_lock 검사
gate_assembly.py               production_ready_lock 검사
                               = 4개 잠금의 SHA 사슬을 전부 확인
```

---

## script_lock.json

```json
{
  "schema_version": "politics-longform-script-lock.v1",
  "episode_id": "PL_YYYYMMDD_slug",
  "status": "SCRIPT_LOCKED",
  "lock_version": 1,
  "locked_at": "ISO-8601",

  "authority": {
    "script_authority": "PROJECT_GPT",
    "audit_authority": "CLAUDE",
    "executor_editorial_authority": "NONE"
  },

  "locked_inputs": {
    "script":            {"path": "20_script/master_script.md",        "sha256": "..."},
    "source_map":        {"path": "20_script/source_map.json",          "sha256": "..."},
    "clip_manifest":     {"path": "10_analysis/clip_manifest.json",     "sha256": "..."},
    "intake_manifest":   {"path": "10_analysis/intake_manifest.json",   "sha256": "..."},
    "episode_lexicon":   {"path": "10_analysis/episode_lexicon.json",   "sha256": "..."},
    "machine_audit":     {"path": "90_reports/script_audit.json",       "sha256": "..."},
    "project_gpt_ruling":{"path": "20_script/project_gpt_ruling.json",  "sha256": "..."}
  },

  "ruling_summary": {
    "total_findings": 0,
    "approved_fix": 0,
    "rejected_no_change": 0,
    "deferred": 0,
    "unresolved": 0,
    "unresolved_high": 0,
    "unresolved_quote_mismatch": 0,
    "deferred_items": [
      {"id": "SCA-014", "reason": "...", "blocks": [],
       "approved_by": "PROJECT_GPT", "resolution_plan": "..."}
    ]
  },

  "editorial_decisions": {
    "chapter_order_approved": true,
    "source_media_verified": true,
    "clip_timecodes_verified": true,
    "hook_selection_approved": true,
    "lexicon_review_approved": true,
    "quote_accuracy_approved": true,
    "lexicon_conflicts": 0
  },

  "structure": {
    "chapter_count": 0,
    "narration_block_count": 0,
    "source_clip_count": 0,
    "logical_segment_count": 0,
    "chapters": [
      {"no": 1, "title": "...", "script_line_range": [0, 0],
       "segment_indices": []}
    ],
    "segments": [
      {"index": 1, "segment_id": "SEG001", "kind": "NARRATION",
       "chapter_no": 1, "script_line_range": [0, 0],
       "source_id": null, "source_timecode": null},
      {"index": 2, "segment_id": "SEG002", "kind": "SOURCE_VIDEO",
       "chapter_no": 1, "script_line_range": [0, 0],
       "source_id": "S05", "source_timecode": "00:08:50.279~00:09:09.560"}
    ]
  },

  "hooks": {
    "5": {"text": "대본 원문 그대로", "underline": "핵심어", "script_line": 0}
  },

  "labels": {
    "_rule": "세그먼트 인덱스별 화이트리스트. 해당 세그먼트 line 범위 안에 있어야 한다",
    "5": ["내각 성과"]
  },

  "tts_params": {
    "provider": "supertone", "voice_id": "...", "model": "sona_speech_2",
    "speed": 1, "pitch_shift": 0, "pitch_variance": 1
  },

  "render_target": {"canvas": "1920x1080", "fps": 30}
}
```

`gates_passed`는 없다. script_lock 이 존재하고 유효하면 그 자체가 나레이션 합성
허가다. 별도 플래그를 두지 않는다.

## 강제 규칙

### 필수 locked_inputs — 하나라도 없으면 exit 1

```text
script · source_map · clip_manifest · intake_manifest
episode_lexicon · machine_audit · project_gpt_ruling
```

대본 SHA만 맞고 clip_manifest 가 빠지면 **맞는 대본에 틀린 클립**으로 제작된다.

### 경로 — episode 상대경로만

```text
절대경로 금지
.. 구성요소 금지
resolve 결과가 episode root 밖이면 exit 1
```

`ep / "../../다른에피소드/x.md"` 는 실제로 `C:\다른에피소드\x.md` 로 탈출한다.

### segments — 순서가 계약이다

개수만 맞고 순서가 틀리면 **해설 전에 반론 영상이 먼저 나온다.** 정치 콘텐츠에서
인용과 해설의 순서가 뒤집히면 논지가 반대로 전달된다.

```text
index 는 1..N 연속. 결번 금지
segment_id 중복 0
len(segments) == logical_segment_count
kind == NARRATION 개수 == narration_block_count
kind == SOURCE_VIDEO 개수 == source_clip_count
chapters[].segment_indices 의 합집합 == segments 의 index 집합
SOURCE_VIDEO 는 source_id 와 source_timecode 필수
NARRATION 은 둘 다 null
```

### hooks · labels — 세그먼트 범위 안에서만

대본 전체에 존재하는지가 아니라 **그 세그먼트의 `script_line_range` 안에**
존재하는지 본다.

```text
seg5 주제      당 지배와 검찰개혁
잘못된 라벨     "국민 통합"   (챕터 4에 실재)
전역 검사      통과한다  ← 취약
범위 검사      차단한다
```

존재하지 않는 세그먼트 키도 차단한다.

### editorial_decisions — 필수 키 집합

```text
chapter_order_approved · source_media_verified · clip_timecodes_verified
hook_selection_approved · lexicon_review_approved · quote_accuracy_approved
lexicon_conflicts (0이어야 함)
```

키 누락·오타·false 전부 차단. `source_media_verifed` 같은 오타가 있으면
그 항목은 검사되지 않은 채 통과한다.

### deferred — 무엇을 막는지 명시해야 한다

```text
{"id": "SCA-014", "reason": "...", "blocks": ["TTS"],
 "approved_by": "PROJECT_GPT", "resolution_plan": "..."}
---
blocks 에 TTS 있음        script_lock 생성 금지
blocks 에 ASSEMBLY 있음   production_ready_lock 생성 금지
blocks 필드 자체가 없음    차단 (미기입으로 우회 방지)
```

`unresolved = 0` 만 보면 중대한 오류를 `DEFERRED`로 돌려 잠금을 통과시킬 수 있다.

### tts_params — 잠긴 값으로만 실행

```text
gen_narration 은 voice_id · model · speed · pitch_shift · pitch_variance 를
script_lock 에서 직접 읽는다. 환경변수 override 기본 금지.
runtime 값이 lock 과 다르면 음성을 생성하지 않는다.
```

같은 대본이라도 `speed 1.0 -> 1.2` 면 길이가 달라져 정렬·SRT·시간축이 전부 바뀐다.

---

## 게이트를 호출하지 않는 우회를 막는다

게이트가 있어도 **Supertone TTS 스크립트를 직접 실행하면 그만이다.** 지난 회차에서
감사 게이트가 산문이라 무시된 것과 같은 구조다.

```text
gen_narration.py 는 시작 시 gate_lock.py --stage tts 를 스스로 호출한다
실패하면 exit 1. 음성을 만들지 않는다
단독 실행으로 우회할 수 없다
실패 상태: WAIT_SCRIPT_LOCK_GATE
```

생성된 `voice_manifest.json` 에 lock 의 `tts_params` SHA 를 기록해
사후에도 어떤 설정으로 만들었는지 대조 가능하게 한다.

---

## 왜 필요한가

지난 에피소드는 오디오 시간축만 잠갔다. 후킹 문장·노드 라벨·비트 배치·
챕터별 화면 유형은 잠기지 않은 채 화면 단계로 넘어갔다.

그 결과 화면 단계가 **실행이 아니라 발명**이 됐다.

```text
CHAPTER 1   v7 -> v8 -> v11
ENDING      v9 -> v10 -> v11
```

그리고 감사 게이트가 문장이라 무시돼, 미판정 지적 11건이 합성 음성에 박혔다.
```

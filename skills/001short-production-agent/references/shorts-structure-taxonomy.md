# 쇼츠 원본 구조·우라까이 분류

Stage 02~05에서만 사용한다. CapCut track·근본·render 규격을 이 문서에 섞지 않는다.

## 1. 원본 관찰: 반드시 분리할 4축

| 축 | 기록값 | 판단 기준 |
|---|---|---|
| 소재 | `subject_category` | 실제 다루는 사람·사건·동물·스포츠·정보 등 |
| 화면 템플릿 | `presentation_template` | 일반 영상, 인스타/댓글 카드, 랭킹, 다큐 몽타주 등. `baked_order_semantics`도 함께 기록 |
| 전달 방식 | `delivery_mode` | 아래 DM 5종 중 하나 |
| 원본 서사 구조 | `source_structure_pattern` | 아래 SP 11종 중 하나 |

`subject_category`와 `presentation_template`은 서사 순서를 정하지 않는다. 화자발언·TTS·화면 글자는 원본의 `delivery_mode`이고, 최종 제작의 음성 선택은 별도 `execution_strategy`다.

### 전달 방식 DM 5종

| 값 | 뜻 | 기본 우라까이 처리 |
|---|---|---|
| `DM_SCREEN_TEXT_VISUAL` | 장면·화면 글자가 전달 | 강한 결과/증거를 앞에 두고, 나머지는 상황 자막으로 재배열. TTS는 필요한 한 문장만 |
| `DM_TTS_NARRATION` | 기존 나레이션이 흐름 주도 | 결론/증거를 선공개하고 정보 순서를 재작성 |
| `DM_ORIGINAL_SPEAKER` | 실제 화자 발언·리액션이 핵심 | 질문·답·반응을 대화 묶음으로 이동. 대사 말맛을 TTS로 덮지 않음 |
| `DM_MIXED` | TTS·원본 발언·자막이 역할 분담 | TTS는 연결, 원본 발언은 증거/감정, 자막은 즉시 이해 역할로 분리 |
| `DM_ACTION_RESULT_VISUAL` | 행동 과정과 결과가 핵심 | 결과 일부를 훅으로, 원인·실패·재시도를 본문으로 재진입 |

### 원본 서사 구조 SP 11종

| 값 | 원본 흐름 | 우라까이 우선안 |
|---|---|---|
| `SP_CAUSAL_PROGRESSION_TO_PAYOFF` | 원인→진행→결과 | `DST_PAYOFF_FIRST_CAUSAL_BACKFILL` |
| `SP_CLAIM_OR_QUESTION_TO_EVIDENCE_CHAIN` | 주장/질문→증거 | `DST_PROOF_FIRST_EVIDENCE_RECONSTRUCTION` |
| `SP_INTERACTION_ESCALATION_TO_REVERSAL` | 대화·반응→반전 | `DST_REVERSAL_FIRST_INTERACTION_RECOMPOSITION` |
| `SP_STATE_DEPENDENT_PROCESS_TO_RESULT` | 상태→시도→결과 | `DST_RESULT_FIRST_PROCESS_REENTRY` |
| `SP_RANKED_MODULAR_ESCALATION` | TOP-N/순위 상승 | `DST_DERANKED_PEAK_FIRST_MODULAR_ANTHOLOGY` |
| `SP_VISUAL_CONTRAST_TO_PROOF` | 대비→검증 | `DST_PAYOFF_FIRST_CONTRAST_RECOMPOSITION` |
| `SP_INCIDENT_EVIDENCE_TO_CONSEQUENCE` | 사건→증거→결과 | `DST_OUTCOME_FIRST_INCIDENT_BACKFILL` |
| `SP_DUAL_PAYOFF_SYNTHESIS` | 두 결과가 합쳐짐 | `DST_PAYOFF_FIRST_DUAL_SYNTHESIS` |
| `SP_CONFLICT_ESCALATION_TO_CONSEQUENCE` | 충돌→파국/결과 | `DST_CONSEQUENCE_FIRST_REVERSE_EXPLANATION` |
| `SP_JUDGMENT_MOTIVE_REFRAME` | 판단→동기 재해석 | `DST_PROOF_FIRST_ASSUMPTION_AUDIT` |
| `SP_SELF_INCRIMINATING_DENIAL_TO_PROOF` | 부정→자기모순 증거 | `DST_EXTERNAL_PROOF_FIRST_IRONIC_EPILOGUE` |

## 2. 제작 실행 방식: 원본 전달 방식과 별도 선택

| `execution_strategy` | 선택 조건 |
|---|---|
| `caption_only` | 행동·결과가 화면만으로 이해되고 새 해설이 불필요 |
| `full_tts` | 원본 대사를 쓰기 어렵고 새 설명이 서사를 끌어야 함 |
| `narration_plus_speaker` | TTS가 맥락을 연결하고 검증된 원본 발언이 감정/증거를 담당 |
| `original_audio_caption` | 실제 발언 자체가 후킹·감정·정보의 핵심 |
| `tts_intro_original_body` | 시작 맥락만 부족하고 이후 원본 발언/현장음이 강함 |

인스타·댓글·카드형은 `presentation_template=INSTAGRAM_CARD` 같은 화면 템플릿이다. TTS 여부를 뜻하지 않는다. 001에서는 원본 배경음 성분을 제거하고 CapCut A12를 비운다.

## 3. 우라까이 승인 규칙

각 구조 구간은 `source_beat_id`, 원본 시간, 사건, 발언, 화면 글자, 서사 기능, 의존 묶음, 훅 후보를 가진다. 최종 구조에는 아래를 모두 기록한다.

```text
source_order_signature: B1>B2>B3>B4
target_order_signature: B4a>B2>B1>B3>B4b
remake_structure_pattern: DST_...
resolution_type: TRANSFORM_CANDIDATE | TRANSFORM_APPROVED |
                 SAFE_UNCHANGED_FALLBACK | BLOCKED_REFERENCE
```

- `TRANSFORM_APPROVED`: 실제 VIDEO beat의 순서가 달라지고, 훅 뒤 본문도 비선형으로 재구성된 경우만 가능하다.
- `SAFE_UNCHANGED_FALLBACK`: 원본 순서 유지가 더 안전한 경우다. 우라까이 성공으로 세지 않는다.
- `BLOCKED_REFERENCE`: baked-in 랭킹/순번/카드가 전체 순서를 고정해 재배열하면 거짓 정보나 화면 충돌이 생기는 경우다. 제작으로 넘기지 않는다.
- `baked_order_semantics`: `NONE`, `LOCAL_REAUTHORABLE`, `GLOBAL_REMOVABLE`, `GLOBAL_IMMUTABLE`, `UNVERIFIED` 중 하나다. `GLOBAL_IMMUTABLE`은 재배열 금지다.
- 대화 의존성은 `NONE`, `CONTEXTUAL`, `EVIDENTIARY`, `INDIVISIBLE_DIALOGUE_BUNDLE`, `UNVERIFIED` 중 하나다. 질문→답, 주장→증거, 행동→결과, 지시어→대상은 묶음이 깨지면 실패다.
- 훅만 복사하고 본문을 원본 순서로 재생하거나 훅 beat를 다시 전부 반복하면 `URAKKAI_STRUCTURE_UNCHANGED`로 취급한다.

## 4. 몰입도·가단야·와우포인트

### 와우포인트 선정

첫 0~3초는 실제 결과, 증거, 반전, 강한 반응 중 하나여야 한다. 훅은 다음 네 질문에 모두 `yes`일 때만 쓴다.

1. 화면만 보아도 무엇이 달라졌는가.
2. 뒤에 “왜/어떻게”를 풀 여지가 남는가.
3. 질문·답·원인 같은 필수 의존 묶음을 함께 옮겼는가.
4. 본문에서 같은 장면을 통째로 반복하지 않는가.

### 가단야 적용

가단야는 **제작 공정**의 세 단계다(이야기 구조가 아니다 — 이야기 구조는 `narrative_arc`로 따로 부른다).

| 단계 | 뜻 | 확정할 것 | 금지 |
|---|---|---|---|
| 가(가이드라인) | 무엇을 남길지 정한다 | 시청자가 끝에 이해할 한 문장, 타깃 감정, 금지선, 훅의 미해결 질문 | 원본 요약을 목표로 삼기 |
| 단(단어변경) | 말을 바꾼다 | 제목·상황 자막·대사의 핵심 단어를 새 정보 순서에 맞춰 재맥락화 | 원본 자막의 단순 동의어 치환 |
| 야(야부리) | **와우포인트로 순서를 바꾼다** | 가장 강한 와우포인트를 0~3초로 끌어올리고 나머지 구간을 그에 맞춰 재배열한다. 그 재배열을 성립시키는 데 필요한 연결 TTS(훅, 인과 브리지, 대사 진입, 회수)를 함께 확정한다 | 원본 순서를 그대로 두고 TTS만 덮기. 모든 장면에 TTS를 덮어 원본 행동/대사를 지우기 |

야부리 결과는 `source_order_signature`와 `target_order_signature`의 차이로 증명된다. 두 signature가 같으면 야부리가 수행되지 않은 것이며 `URAKKAI_STRUCTURE_UNCHANGED`에 해당한다.

각 구간의 문장은 하나의 역할만 갖는다: `source_speech`, `situation_caption`, `tts_interpretation`, `graphic_text`. 실제 발화와 화면 글자와 해석을 서로 바꾸어 쓰지 않는다.

### 몰입 곡선

`와우포인트 → 미해결 질문 → 원인/증거의 선별 공개 → 긴장·대화·과정 → 결과 회수 → 짧은 여운`

TTS는 이 곡선의 빈 연결만 메운다. 자막형에는 TTS를 강제하지 않고, 화자발언형에서는 발언의 감정·정보를 원본 음성으로 남긴다.

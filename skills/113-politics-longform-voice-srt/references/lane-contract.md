# Lane 계약 — 113이 무엇을 111에서 가져오고 무엇을 버리는가

`handoff_version 2.0 / CLAUDE_ORCHESTRATOR_HYPERFRAMES_LANE_CORRECTION` 채택본.

```text
111-politics-longform   = 기존 lane. KEEP_UNCHANGED. 현재 파이프라인에서 NOT_USED.
113-politics-longform-voice-srt = HyperFrames 중립 음성·자막 데이터 생성
112-politics-longform-hyperframes = locked 템플릿 조립 및 렌더
capcut_dependency = 0
capcut_fallback   = FORBIDDEN
```

111에서 가져오는 것은 **구현 중립적 의미 규칙뿐**이다.

## 용어 계약

| 개념 | 113 정식 명칭 |
|---|---|
| Supertone 합성음성 | `narration_audio` |
| 합성음성 자막 | `narration_caption` |
| 원본 영상 발화 자막 | `source_speech_caption` |
| 우상단 평론 라벨 | `comment_label` |
| 챕터 제목 | `chapter_title` |
| 챕터 번호 | `chapter_number` |
| 출처 라벨 · 날짜 | `source_label` · `source_date` |

`TTS`를 단독 명칭으로 쓰지 않는다. 외부 도구를 가리킬 때만 `Supertone TTS API`로
한정한다.

이유: 111의 `role: tts`는 합성음성이 아니라 **원본 발화 자막 lane**을 뜻한다
(111 SKILL.md — "TTS는 합성음성이 아니라 편집 가능한 원본 발화 자막 lane이다").
113의 Supertone 합성과 정면 충돌하므로 단독 사용을 금지한다.

## 상속 / 폐기

**상속 (의미 규칙)**
- 원문 축약·요약·의역 금지
- 인명·기관명·법률용어 보존
- 가운데점 `·` 보존 (`수사·기소`)
- 자막 cue 순서 보존
- source caption 정규화 연결 일치 (승인 교정 반영 기준선. [source-caption-exceptions.md](source-caption-exceptions.md))
- 음성 경계 기준 cue 분할
- 확정 교정본의 상위 권위
- 오디오·영상 길이 허용오차 검증
- 실제 파일 기반 검증

**폐기:** CapCut 구현은 하나도 상속하지 않는다.

## 화면 레이아웃 권위

**113은 자막의 의미와 데이터만 만든다. 배치는 112 템플릿이 정한다.**

repo 정본 `politics-longform-hyperframes/template/style_tokens.json` 실측값:

```json
captionBand { "x": 0, "y": 842, "width": 1920, "height": 238 }
captionText { "x": 190, "y": 866, "width": 1540, "fontSize": 60,
              "lineHeight": 1.16, "maxLines": 2, "fontFamily": "ChosunGs, serif" }
comment     { "x": 1420, "y": 154, "width": 450, "size": 31 }
```

```text
자막 밴드 = 1개. maxLines = 2.
111의 "1줄 / 공백 제외 20자"는 이 템플릿에 적용되지 않는다.
cue 길이 상한은 113이 임의 숫자로 정하지 않는다.
초과 여부는 112의 `hyperframes check --strict --snapshots` layout 검사가 판정한다.
overflow가 나면 문구를 줄이지 말고 speech boundary에서 cue를 더 쪼갠다.
```

`comment_label`은 우상단 450px 폭의 **라벨**이며 111의 하단 2줄 평론
트랙과 동일한 역할로 취급하지 않는다. 112 템플릿이 실제로 요구할 때만 생성한다.

### 트랙 - visual_role 매핑

| 113 트랙 | 텍스트 권위 | 112 visual_role |
|---|---|---|
| `narration_caption` | 프로젝트 GPT 권위 대본 | `caption-text` |
| `source_speech_caption` | 선택 원본 SRT + 실제 음성 | `caption-text` |
| `chapter_title` | 권위 대본 chapter heading | `chapter-title` |
| `chapter_number` | 대본 챕터 순번 | `chapter-number` |
| `source_label` · `source_date` | 원본 출처 메타 | `source-label` · `source-date` |
| `comment_label` | 프로젝트 GPT 승인 문구 | `comment-label` |

`narration_caption`의 타이밍 권위는 forced alignment 결과다. 문구 재작성 금지.

## 컴포지션 매핑

| 113 세그먼트 종류 | 112 composition |
|---|---|
| 나레이션 | `narration-explainer` |
| 원본 클립 | `source-video` |
| 챕터 전환 | `chapter-transition` |

`data-hf-role` 실측: `caption-text` `chapter-title` `chapter-number`
`source-label` `source-date` `comment-label` `focus-lines`
`top-frame` `bottom-frame` `lower-caption-band` `subscribe-label`.

## 자막 권위 순서

```text
1. PROJECT_GPT_CORRECTED_SRT_LOCK  (subtitle_corrections.json 또는 확정 교정 SRT)
2. 사용자가 명시적으로 확정한 수정사항
3. 프로젝트 GPT 권위 대본
4. 실제 narration_audio 정렬 결과
5. 원본 영상 선택 구간 SRT
6. 자동 생성 SRT
7. ASR 초벌 결과
```

`USER_CORRECTED_SRT_LOCK`은 111의 레거시 명칭이며 alias로만 남긴다.
사용자는 중개자이고 **최종 자막 오류 판정은 프로젝트 GPT가 한다.**

lock 요건: 교정본 SHA-256 / cue 수 / 문구 diff / 시간축 검증 /
인명·법률용어 검증 / 가운데점·문장부호 보존 / 교정표 밖 문구 임의 수정 금지.
위반 시 `FAIL_PROJECT_GPT_CORRECTED_SRT_FIDELITY`.

## 산출물

```text
audio     narration_audio 파일들, voice_manifest.json, voice_duration_report.json
alignment alignment_raw_v1.json, pronunciation_check_v1.json
subtitle  narration_caption_v1, source_speech_caption_v1,
          subtitle_qc_package_v1.json, final_srt_draft_v1.srt
timeline  review_audio_timeline_v1.json, production_input_v1.json
report    113_validation_report_v1.json, production_status.json
```

`production_input_v1.json`이 112로 넘기는 단일 입력이다. 최소 의미 필드:
narration_audio 경로와 SHA-256 / 나레이션 길이 / narration caption cue /
원본 영상 경로 / 원본 클립 in·out 타임코드 / source speech caption cue /
chapter_title / segment type / segment start·end /
project GPT corrected subtitle lock / template lock manifest.

필드명 최종 확정 전에 112 SKILL.md와 template schema를 **실제로 읽는다.**

## 금지 산출물

CapCut draft / project / profile / material / text track / timeline / backup / ZIP.
하나라도 생성되면 `FAIL_CAPCUT_DEPENDENCY_DETECTED`.

## 실패 상태

```text
FAIL_CAPCUT_DEPENDENCY_DETECTED
FAIL_AUDIO_FILE_NOT_CREATED
FAIL_ALIGNMENT_FILE_NOT_CREATED
FAIL_AUDIO_DURATION_MISMATCH
FAIL_SOURCE_SPEECH_CAPTION_FIDELITY
FAIL_PROJECT_GPT_CORRECTED_SRT_FIDELITY
WAIT_SCRIPT_INTEGRITY
WAIT_SOURCE_FILE_MISSING
WAIT_PRONUNCIATION_REQUIRES_SCRIPT_REVISION
WAIT_ROOT_CAUSE
```

## 필수 테스트

```text
111 구현 관련 문자열·import 0건 (금지 선언문 제외)
111 실행 호출 0건
PL_EPISODE_DIR / PL_REPO_EPISODE / PL_VIDEO_DIR / PL_SCRIPT_SHA256 누락 시 BLOCKED
환경변수 경로가 허용 루트 밖이면 거부 (path traversal 차단)
권위 대본 SHA 불일치 시 WAIT_SCRIPT_INTEGRITY
원본 MP4 무수정
실패 시 부분 산출물 정리
WAV·JSON atomic write
API key·token 로그 출력 0건
가운데점 · 보존
PROJECT_GPT_CORRECTED_SRT_LOCK 이후 문구 변경 금지
112 production input schema 검증
```

## 템플릿 정본

```text
SOURCE_OF_TRUTH = C:\Users\arajun\repos\politics-longform-hyperframes\template
FORBIDDEN       = ...\22factory_*\02_politics_longform\templates\politics-longform-template-v1
```

OneDrive 사본은 `compositions/source-video.html` 해시가 lock과 불일치한다
(`369bd8c5…` vs lock `1ba0c0df…`). 부분 패치하거나 제작 입력으로 쓰지 않는다.
112 SKILL.md의 `template_default`는 repo 정본(`${PL_HYPERFRAMES_REPO}\template`)을
가리키도록 **이미 교정됐다.** drift 사본으로 되돌리지 않는다.

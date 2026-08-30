# 정치롱폼 Clean Assembly Harness

## 목적

`CLEAN_ASSEMBLY_HARNESS`는 프로젝트가 단순히 열리는지를 검사하는 기능이 아니다.
사용자가 승인한 전체 조립 계약과 실제 CapCut JSON이 정확히 일치하는지를 검사한다.
대화 기억이나 직전 오류에 의존하지 않고 파일에 잠긴 계약을 매 조립·검증 전에
다시 읽는다.

## Source of Truth

조립 전에 `50_capcut_project/assembly_contract.json`을 만든다. 이 파일은 다음
항목의 유일한 기준이다.

- `root_template`: `V8_MANUAL_OVERLAY_65`, 역할 `TEMPLATE_ONLY`
- `production_inputs`: 실제 사용할 영상·이미지·오디오·자막, 역할 `PRODUCTION`
- `reference_inputs`: 배치·구조 참고용 자료, 역할 `REFERENCE_ONLY`
- `expected_timeline_order`: 사용자 승인 순서
- `forbidden_project_inputs`: 실패·폐기·오염된 이전 프로젝트와 파생 계보
- `allowed_visible_text`: 화면에 나타날 수 있는 모든 텍스트
- 각 요소의 track role, 시작·종료, 위치, 크기, source/date/chapter 관계
- 입력 파일의 절대경로 또는 휴대 가능한 경로와 SHA-256

## V8 수동 레이아웃 근본

V8 근본은 파일명이나 테스트 미디어 이름으로 판별하지 않는다. 아래 12개 레이어의
역할·geometry·문구 슬롯을 함께 고정한다. 번호는 CapCut 화면에서 위에서 아래로
쌓이는 순서다.

| 레이어 | JSON track | 역할 | 실제 기준 |
|---:|---:|---|---|
| 1 | 10 | CHAPTER | `__CHAPTER__`, 중심 `(960,90)`, font 7, fixed width `504.2707`, 한 줄 |
| 2 | 9 | SOURCE | `출처 __SOURCE__`, 중심 `(960,165)`, font 5, fixed width `334.8208`, 한 줄 |
| 3 | 8 | TTS | `TTS`, 중심 `(960,990)`, font 8, fixed width `679.2648`, 노랑+검정 stroke `0.08`, 한 줄 |
| 4 | 7 | SRT | `SRT`, 중심 `(960,990)`, font 8, fixed width `679.2648`, 노랑+검정 stroke `0.08`, 한 줄 |
| 5 | 6 | CTA | `구독은 큰 힘이 됩니다.` + `댓글로 의견 부탁드려요!`, 중심 약 `(1688,839)`, scale `0.9`, 고정 2줄 |
| 6 | 5 | FOCUS FRONT | 투명 1920×1080, 중심 `(960,540)`, scale `1.0` |
| 7 | 4 | CARD IMAGE | 입력 1920×1080, 중심 `(960,540)`, scale `0.65`, 화면 `x=336,y=189,1248×702` |
| 8 | 3 | BOTTOM RAIL | `785.8748×70.1742`, 중심 약 `(960,986)`, alpha `0.5`, border `4 #CCCCCC` |
| 9 | 2 | TOP RAIL | `785.8748×71.7401`, 중심 약 `(929,96)`, alpha `0.5`, border `4 #CCCCCC` |
| 10 | 1 | FOCUS BACK | 투명 1920×1080, 중심 `(960,540)`, scale `1.0` |
| 11 | 0 | SOURCE VIDEO | 1920×1080, 중심 `(960,540)`, scale `1.0`, 원본 소리 포함 |
| 12 | 11 | NARRATION AUDIO | 나레이션 WAV, volume `1.0`, 화면 레이어 없음 |

CHAPTER와 SOURCE는 한 줄 슬롯이며 근본 JSON에는 글자 수 제한이 없다. TTS와 SRT는
각각 한 줄 슬롯이며 실제 cue는 공백 제외 15자 이하로 제한한다. 긴 자막과 승인된
논평 2문장은 같은 트랙에서 시간상 연속 cue로 나눈다.

- 1·2·3·5는 `STATIC_OVERLAY`이며 프로젝트 전체 길이로 자동 연장된다.
- 0·4·11의 기존 media는 geometry·audio 설정을 읽기 위한 `TEMPLATE_ONLY`다.
  새 프로젝트의 active material이나 timeline에는 남지 않는다.
- root의 외부 path는 clone 안 `Resources`로 포터블화한다. output JSON에는 root·cache·
  테스트 빌드 절대경로가 남으면 fail이다.
- `.bak`는 CapCut을 연 뒤 생성될 수 있다. build 직전 clone에는 포함하지 않으며,
  CapCut을 열기 전 output 검사에서 발견되면 fail이다.

```powershell
python -B scripts/build_politics_v8_project.py `
  --cards <episode_cards.json> `
  --root-project <validated V8_MANUAL_OVERLAY_65 root> `
  --capcut-root <CapCut draft root> `
  --media-dir <new portable media dir> `
  --report <build report>
```

## 신규 이미지카드 문구

신규 `CHAPTER_CARD`·`NARRATION_IMAGE`의 카드 제작 입력은 아래 두 필드로 고정한다.

```text
hook_terms: 정확히 3개
body_lines: 화면 문장 정확히 3줄
```

후킹 단어와 본문은 서로 다른 정보층이다. 후킹 단어를 문장처럼 늘리거나,
본문을 두 줄 또는 네 줄로 늘리지 않는다. 이 규칙은 새 카드 제작 입력에만 적용하며,
이미 승인·렌더된 기존 회차 자산을 소급 수정하지 않는다.

역할의 의미는 다음과 같다.

- `PRODUCTION`: 승인된 실제 콘텐츠다. 매니페스트와 타임라인에 들어갈 수 있다.
- `REFERENCE_ONLY`: 구조·배치 판단에만 사용한다. materials와 timeline에는 0개다.
- `TEMPLATE_ONLY`: 트랙 구조, 좌표, 크기, 효과, 레이어 설정만 복제할 수 있다.
  기존 영상·이미지·오디오·텍스트·`material_id`·`online_id`·`request_id`는
  새 프로젝트로 승계하지 않는다.

## Acceptance Criteria

다음 조건을 모두 만족해야 정적 조립 검사를 통과한다.

1. 실제 타임라인 순서가 `expected_timeline_order`와 완전히 같다.
2. 모든 `PRODUCTION` 입력의 경로와 SHA-256이 계약과 같다.
3. CL별 실제 파일과 `material_id`가 서로 다르며 중복되지 않는다.
4. `REFERENCE_ONLY` 자료가 draft materials와 timeline에 하나도 없다.
5. 외부·참고 프로젝트에서 복제된 `online_id`와 `request_id`가 없다.
6. 화면 텍스트는 `allowed_visible_text`에 승인된 것만 존재한다.
7. root `draft_content.json`과 `template-2/Timelines/*` 미러가 같다.
8. source, date, chapter, caption, lower, media의 위치·시간·역할이 계약과 같다.
9. `forbidden_project_inputs`의 프로젝트나 material 계보가 입력에 없다.
10. 승인되지 않은 추가 영상·이미지·오디오·텍스트·자막이 없다.

## Validation

아래 하나라도 발생하면 HARD FAIL이다.

```text
REFERENCE_ONLY_IN_MATERIALS
REFERENCE_ONLY_IN_TIMELINE
TIMELINE_ORDER_MISMATCH
SOURCE_HASH_MISMATCH
DUPLICATE_SOURCE_MATERIAL_ID
ONLINE_ID_PRESENT
REQUEST_ID_PRESENT
UNAPPROVED_VISIBLE_TEXT
JSON_MIRROR_MISMATCH
FORBIDDEN_PROJECT_INPUT_PRESENT
UNAPPROVED_MEDIA_PRESENT
ROLE_TIMING_GEOMETRY_MISMATCH
```

검증기는 파일 존재만 보지 않는다. `expected_timeline_order`, 각 입력 SHA-256,
material 참조, 화면 텍스트 집합, JSON 미러, 역할별 시간과 geometry를 모두
대조한다. 빌드 시작 직전, 검증 직전, 컨텍스트 압축 또는 작업 재개 직후에는
반드시 계약 파일을 다시 읽는다.

구조 오염이 확인되면 상태는
`STRUCTURAL_CONTAMINATION_REQUIRES_CLEAN_REBUILD`다. 실패한 대상 빌드를
부분 패치하지 않는다. 그 빌드만 폐기하고 고정 근본
검증된 `V8_MANUAL_OVERLAY_65` 근본에서 새 대상 프로젝트를 다시 만든다. 근본
아카이브와 로컬 근본 자체는 삭제하거나 수정하지 않는다.

## Evidence

정적 검증 결과에는 최소 다음 증거를 남긴다.

- `assembly_contract_sha256`
- 근본 archive/manifest SHA-256
- 모든 `PRODUCTION` 입력의 경로·SHA-256·역할
- materials와 timeline에서 발견된 실제 순서
- CL별 source file과 고유 `material_id`
- `REFERENCE_ONLY` 출현 건수
- `online_id`·`request_id` 출현 건수
- 실제 visible text와 `allowed_visible_text` 비교 결과
- root와 timeline mirror 해시
- 각 hard-fail 검사 결과

정적 검사가 통과해도 CapCut 화면 검증을 자동 통과시키지 않는다.
CapCut을 자동으로 열지 않는다. 사용자가 제공한 사용자 화면 또는 사용자가 알린 문제를
근거로 시각 검증하며, 그 전 상태는 `WAIT_USER_VISUAL_GATE`다. 정적 증거와
사용자 화면이 모두 계약과 일치할 때만 시각 게이트를 `PASS`로 바꾼다.

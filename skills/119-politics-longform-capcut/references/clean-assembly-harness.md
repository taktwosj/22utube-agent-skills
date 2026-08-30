# 정치롱폼 Clean Assembly Harness

## 목적

`CLEAN_ASSEMBLY_HARNESS`는 프로젝트가 단순히 열리는지를 검사하는 기능이 아니다.
사용자가 승인한 전체 조립 계약과 실제 CapCut JSON이 정확히 일치하는지를 검사한다.
대화 기억이나 직전 오류에 의존하지 않고 파일에 잠긴 계약을 매 조립·검증 전에
다시 읽는다.

## Source of Truth

조립 전에 `50_capcut_project/assembly_contract.json`을 만든다. 이 파일은 다음
항목의 유일한 기준이다.

- `root_template`: `jungchilong_base_v4_hook10_lower2`, 역할 `TEMPLATE_ONLY`
- `production_inputs`: 실제 사용할 영상·이미지·오디오·자막, 역할 `PRODUCTION`
- `reference_inputs`: 배치·구조 참고용 자료, 역할 `REFERENCE_ONLY`
- `expected_timeline_order`: 사용자 승인 순서
- `forbidden_project_inputs`: 실패·폐기·오염된 이전 프로젝트와 파생 계보
- `allowed_visible_text`: 화면에 나타날 수 있는 모든 텍스트
- 각 요소의 track role, 시작·종료, 위치, 크기, source/date/chapter 관계
- 입력 파일의 절대경로 또는 휴대 가능한 경로와 SHA-256

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
`jungchilong_base_v4_hook10_lower2`에서 새 대상 프로젝트를 다시 만든다. 근본
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

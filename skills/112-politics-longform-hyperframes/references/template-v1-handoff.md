# 정치롱폼 HyperFrames 공용 템플릿 v1 핸드오프

```text
STATUS=TEMPLATE_V1_LOCKED
HANDOFF_STATUS=READY
TEMPLATE_ID=politics-longform-template-v1
VERSION=v1
OWNER=112-politics-longform-hyperframes
NEXT=오세훈 전체 챕터에 공용 템플릿 적용 준비
```

## 1. Source of Truth

```text
TEMPLATE_PATH=C:\Users\arajun\OneDrive\22utube\22factory_20260628\02_politics_longform\templates\politics-longform-template-v1
SKILL_AUTHORITY=C:\Users\arajun\agent-skills\skills\112-politics-longform-hyperframes
MANIFEST=template_manifest.json
LOCK=template_lock.json
VALIDATION=validation_report.json
APPROVED_SNAPSHOT=evidence/template-v1-approved.png
```

## 2. 사용자 승인

```text
APPROVAL_TYPE=USER_VISUAL_APPROVAL
APPROVED_AT=2026-07-25T15:12:32.3329401+09:00
APPROVAL_EVIDENCE=사용자 명령 "잠그고. 핸드오프 내용써"
```

## 3. 잠긴 디자인 계약

```text
CANVAS=1920x1080
FPS=30
ASPECT_RATIO=16:9
FONT_FAMILY=ChosunGs
FONT_SCOPE=ALL_TEXT_ELEMENTS
FONT_ASSET=assets/fonts/ChosunGs.TTF
CAPTION_MAX_LINES=2
CAPTION_CONTAINER=lower-caption-band
STUDIO_TOKEN_EDITING=TOKEN_FILE_ONLY
```

잠긴 composition:

- `narration-explainer`
- `source-video`
- `chapter-transition`

잠긴 공용 요소:

- `top-frame`
- `bottom-frame`
- `focus-lines`
- `chapter-number`
- `chapter-title`
- `source-label`
- `source-date`
- `comment-label`
- `subscribe-label`
- `lower-caption-band`
- `caption-text`

## 4. 핵심 SHA-256

```text
STYLE_TOKENS_SHA256=122625c360c732c75f7f985cdd4565eca47486117fb5e6938acb40f053a18fbd
TEMPLATE_MANIFEST_SHA256=97268847bde2d1dda01e542cde4829e1a791f3e5058ee70ee700ea18baeb8f40
TEMPLATE_LOCK_SHA256=3846aa7d7e2a59221b4777eabc1f231205a942a147035cd0a616d04baca4d639
APPROVED_SNAPSHOT_SHA256=2656cef96fcbeece7904c0e49b142cf6f2694a5e0c743cd49dc43a00fb12a6f8
FONT_SHA256=4e191bc30d23ce34797dcaf7a0965dedd67a2d85cc5dd87325ee96626cba7bea
```

전체 잠금 파일 SHA는 `template_lock.json`의 `files` 객체가 권위본이다.

## 5. 검증 상태

```text
CONTRACT_VALIDATOR=PASS
UNIT_TESTS=PASS_8_OF_8
HYPERFRAMES_LINT=PASS_0_ERRORS_0_WARNINGS
HYPERFRAMES_STRICT_CHECK=PASS
RUNTIME_ERRORS=0
LAYOUT_ISSUES=0
MOTION_ERRORS=0
CONTRAST=43_OF_43_PASS
PREVIEW_SERVER=RUNNING
PREVIEW_URL=http://localhost:3018/#project/politics-longform-template-v1
```

## 6. 다음 채팅 재개 절차

1. 이 파일을 읽는다.
2. `template_lock.json`을 JSON으로 파싱한다.
3. `template_lock.json.files`의 모든 상대경로에 대해 SHA-256을 다시 계산한다.
4. 불일치가 하나라도 있으면 `BLOCKED_TEMPLATE_HASH_MISMATCH`로 중단한다.
5. 일치하면 승인된 공용 템플릿을 별도 오세훈 episode production project에 적용한다.
6. 승인 대본, 원본 영상 구간, WAV, SRT, 챕터 순서는 변경하지 않는다.
7. episode preview 승인 전 최종 MP4를 렌더하지 않는다.

## 7. 금지 및 경계

```text
EXISTING_OSEHUN_HF_PROJECT_MODIFIED=false
CAPCUT_USED=false
FINAL_MP4_RENDERED=false
GIT_COMMIT=NOT_RUN
GIT_PUSH=NOT_RUN
RUNTIME_DEPLOY=NOT_RUN
CAPCUT_FALLBACK=FORBIDDEN
```

기존 오세훈 프로젝트는 이번 템플릿 잠금에서 수정하지 않았다.

```text
C:\Users\arajun\OneDrive\22utube\22factory_20260628\02_politics_longform\episodes\PL_20260722_osehun_dangseon_bulgeum\60_hyperframes\project
```

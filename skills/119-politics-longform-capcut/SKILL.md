---
name: 119-politics-longform-capcut
description: Use only when a political-longform request explicitly contains CapCut, 캡컷, 119, or 119정치롱폼. Assemble an approved politics-longform episode as a clean, editable local CapCut project from portable OneDrive root assets and episode cards.
---

# 119 정치롱폼 CapCut 카드 조립

## 역할과 경계

사용자가 CapCut을 직접 말했을 때만 119를 사용한다.
110·111·112 요청을 119로 자동 우회하지 않는다.
FORBIDDEN: 사용자가 명시하지 않은 CapCut 조립으로의 자동 전환.
119는 잠긴 제작 입력을 **기계적으로 CapCut 프로젝트로 조립·검증**하는 단계다.
정치적 사실판단, 대본 작성, 음성 생성, SRT 교정은 각각 110·111의 책임이다.

```text
110  주제·대본·출처·직접 인용·사용자 확인
111  잠긴 나레이션 음성·최종 SRT·시간축
119  episode_cards.json → 로컬 CapCut 프로젝트 → 재연결·검증
112  HyperFrames를 사용한다고 명시한 경우만 별도 진행
```

Stage 1 초벌, 후보 타임코드, 미확정 ASR, 잠기지 않은 대본으로 CapCut을 만들지
않는다. 누락은 추정으로 메우지 않고 `WAIT_STAGE2_INPUTS`로 멈춘다.

## 저장소와 소유권

한 회차에는 active writer 한 명만 허용한다. CapCut 또는 그 백그라운드 프로세스가
열려 있으면 draft를 만들거나 고치지 않는다.

```text
WORKSPACE_ROOT
├─ 00_asset_tools/templates/capcut/jungchilong/   OneDrive 공유 근본 ZIP·manifest·contract
├─ 02_politics_longform/episodes/{episode_id}/    회차 JSON·보고서·텍스트 증빙
└─ (로컬 전용) %LOCALAPPDATA%/CapCut/...           실제 CapCut draft

로컬 전용: 원본 MP4, relink Media 폴더, CapCut draft, cache, 계정 정보
OneDrive: 근본 ZIP, manifest, contract, cards, 검증 보고서, 해시, handoff
```

다른 PC에서는 OneDrive가 동기화된 뒤 각 PC의 `WORKSPACE_ROOT`만 다르게 잡는다.
contract와 episode JSON에 사용자 프로필 절대경로, `%LOCALAPPDATA%`, CapCut cache 경로를
기록하지 않는다.

## 공용 근본 계약

현재 새 회차에 쓸 근본은 active pointer가 선택한 검증 완료 bundle 하나다.

```text
active pointer
00_asset_tools/templates/capcut/jungchilong/capcut_active_root_v1.json

active pointer -> PASS_ROOT_CONTRACT resolver -> builder --workspace-root
```

근본을 직접 열어 이름만 바꾸거나, 과거 회차·실패본·`.bak`를 다음 회차의 근본으로
사용하지 않는다. 새 화면을 근본으로 승격해야 할 때만 CapCut을 닫고
`scripts/promote_capcut_root.py prepare`를 staging 사본에 실행한다. active v5는 수정·덮어쓰기
금지이며 새 화면 근본은 v6부터 시작한다.

```text
staging copy
-> prepare candidate bundle
-> PASS_ROOT_PROMOTION_STATIC + visual WAIT + post-open WAIT
-> user visual approval and CapCut open/save/close evidence
-> activate candidate
-> atomic active pointer update
-> immutable active version
```

prepare는 `root_version + root_profile` 두 값 모두와 active parent에서 모든 산출물 이름을 파생하고
`CANDIDATE_ROOT_BUNDLE_PREPARED`만 반환한다. 이때 static PASS여도 active가 아니며
`capcut_active_root_v1.json`을 바꾸지 않는다. visual과 post-open이 각각
`PASS_USER_VISUAL_GATE`, `PASS_CAPCUT_OPEN_CLOSE`가 된 뒤에만 `activate`를 실행한다.
activate는 전체 bundle과 parent lineage를 다시 검증하고 마지막 파일 작업으로 active
pointer를 원자 교체한다. 실패하면 기존 pointer bytes를 그대로 보존한다. 활성 근본과 근본
화면 증거는 회차 `VISUAL_GATE`를 부여하지 않는다. 활성화된 root ZIP과 version bundle은
불변이다.

각 PC에서 다음으로 상대경로·manifest·ZIP 해시를 먼저 확인한다.

```powershell
$workspaceRoot = (Resolve-Path $env:WORKSPACE_ROOT)
python scripts/resolve_politics_capcut_root.py `
  --workspace-root $workspaceRoot
```

`PASS_ROOT_CONTRACT`가 아니면 builder를 실행하지 않는다.
handoff data, 과거 contract 경로, 직접 입력한 archive 경로·SHA는 근본을 선택할 수 없다.
builder의 `--root-archive`와 `--root-sha256`은 허용하지 않는다.

## 사전 입력 게이트

다음을 만족한 경우에만 Stage 2 조립을 시작한다.

```text
episode_id / active_writer_machine / lock_owner
20_script/design_blueprint_approved.json
20_script/design_blueprint_approved.md
10_analysis/timeline_design_approved.json
90_reports/external_review_gate.json
10_analysis/speech_boundary_lock.json
10_analysis/roughcut_edl_locked.json
10_analysis/source_labels_locked.json
20_locked_clips/locked_clips_manifest.json
```

```powershell
python scripts/validate_politics_capcut_inputs.py `
  --episode-dir <episode_dir> `
  --report <episode_dir>\90_reports\capcut_stage2_preflight_v1.json `
  --active-writer-machine <home_windows|office_windows|macmini> `
  --lock-owner <owner>
```

결과가 `PASS`가 아니면 `WAIT_STAGE2_INPUTS`다. 이 preflight는 읽기 전용이며,
CapCut 프로젝트·미디어·잠긴 원본을 바꾸지 않는다.

## episode_cards.json

대시보드 전체 JSON을 builder에 직접 넘기지 않는다. 승인된 장면만 추출해 다음 경로에
쓴다.

```text
{episode_dir}/50_capcut_project/episode_cards.json
```

전체 schema와 필수 필드는 `references/episode-card-contract.md`를 따른다.
카드는 시작 시각 순서대로 이어지고, 빈 시간 또는 추정 padding을 만들지 않는다.

```text
INTRO
CHAPTER_CARD
SOURCE_VIDEO
NARRATION_IMAGE
NARRATION_VIDEO
TEXT_EXPLAINER
ENDING
```

필수 시간 규칙:

```text
INTRO                  첫 카드, 0~5.000초
CHAPTER_CARD           나레이션이 없으면 정확히 3.000초
SOURCE_VIDEO           source_duration_us == target_duration_us
모든 카드              target_start_us == 직전 카드 끝
project duration       마지막 카드 끝과 정확히 같음
```

원본 영상은 계단식 다중 video track으로 쌓지 않는다. 모든 실제 영상·챕터 이미지·인트로
카드는 선언된 순서대로 하나의 연속 primary video lane에 놓는다. 그래야 CapCut이 빈
구간을 압축해 다음 클립을 앞당기지 않는다.

## 화면 규칙

### 인트로와 챕터

```text
인트로: 5초, 오늘 볼 쟁점을 소개하는 편집 가능한 2줄 텍스트만
챕터 카드: 눈길을 끄는 16:9 이미지 + 편집 가능한 chapter label / chapter hook
챕터 카드 하단 30%: 핵심 피사체·이미지 안의 문구를 두지 않는 안전 영역
무음 챕터 카드: 3초
```

챕터 카드 중에는 하단 슬롯을 `NONE`으로 둔다. 챕터 제목은 카드가 끝난 뒤에도 해당
챕터의 원본 영상 구간 동안 상단에 유지한다.

### 고정 HUD

해당 source-video 구간에는 다음을 승인 timeline의 시간 그대로 유지한다.

```text
상단: 챕터 번호와 챕터 문장
좌측: 출처 채널명과 실제 게시일
우측: CTA
```

채널·날짜는 2줄의 별도 editable 텍스트로 유지하여 CapCut의 자동 줄바꿈에 의존하지
않는다. 근본의 rail, frame, 불투명도는 바꾸지 않고 보존한다.

### 하단 공용 2줄 슬롯

하단에는 논리적으로 하나의 2줄 슬롯만 있다. 같은 시간대의 mode는 정확히 하나다.

```text
SOURCE_TTS           실제 원본 발화 자막
NARRATION_TTS        111에서 잠긴 나레이션 SRT 자막
VIDEO100_EXPLAINER   원본 영상만으로 구성한 짧은 논점·논거 설명
NONE                 하단 표시 없음
```

- 평론·원본 자막·나레이션 자막을 다른 트랙에 동시에 쌓지 않는다.
- 원본 방송에 이미 있는 자막과 겹치면 `NONE` 또는 원본 자막을 피하는 위치로
  조정하고, 해결되지 않으면 `NEEDS_VISUAL_REVIEW`다.
- `SOURCE_TTS`는 잠긴 원본 SRT를 축약·의역하지 않는다.
- `NARRATION_TTS`는 잠긴 111 SRT만 사용한다.
- `VIDEO100_EXPLAINER`는 출처가 뒷받침하는 짧은 설명만 넣으며, 문장 사이에 `·`를
  쓰지 않는다. 쉼표나 줄바꿈을 사용한다.
- 줄 수는 최대 2줄이고, 기본 한 줄은 공백 제외 20자 이하다.

## 미디어 재연결

각 회차는 고유한 이름의 로컬 `Media` 폴더를 쓴다. builder는 source video와 narration
video를 의도적으로 offline path로 써서, CapCut의 Media Relink에서 그 회차 폴더를
명시적으로 선택하게 한다. chapter image는 프로젝트 `Resources`에 내장한다.

```text
PROJECT_CREATED_WAIT_MEDIA_RELINK
→ 사용자가 회차 Media 폴더 선택
→ CapCut 저장·종료
→ post-open readback
→ MEDIA_RELINKED | FAIL_MEDIA_RELINK_PERSISTENCE
```

파일명만 같다는 이유로 과거 로컬 미디어가 연결됐다고 간주하지 않는다. relink 뒤 저장된
CapCut JSON path와 Media SHA-256이 일치해야 한다.
최종 draft 전체에서 `onlineMaterial`, `__CAPCUT_RELINK_REQUIRED__`, 비어 있지 않은
`online_id`·`request_id`가 하나라도 발견되면 `MEDIA_RESOLUTION=FAIL`이다.

## 조립 실행

CapCut을 완전히 종료한 뒤 실행한다. 아래 `<...>`만 현재 회차 값으로 치환한다.

```powershell
$workspaceRoot = (Resolve-Path $env:WORKSPACE_ROOT)

python scripts/build_politics_card_project.py `
  --cards <episode_dir>\50_capcut_project\episode_cards.json `
  --workspace-root $workspaceRoot `
  --capcut-root "$env:LOCALAPPDATA\CapCut\User Data\Projects\com.lveditor.draft" `
  --media-dir "$env:USERPROFILE\Videos\22utube_capcut_media\<project_name>\Media" `
  --report <episode_dir>\90_reports\capcut_build_v1.json
```

`PROJECT_CREATED_WAIT_MEDIA_RELINK`은 조립 정적 검사 통과일 뿐, 재연결·화면검수·MP4
렌더가 완료됐다는 뜻이 아니다.
OneDrive에 동기화하는 `capcut_build_v1.json`에는 workspace 상대경로나
`LOCAL_CAPCUT_DRAFT`, `LOCAL_MEDIA_FOLDER`, `LOCAL_PATH` 같은 이식 가능한 참조만 쓴다.
실제 로컬 project/media/source 절대경로는 조립 실행과 CLI 안내에만 사용하고 report에
직렬화하지 않는다.
build report의 `root_bundle.root_visual_gate`는 근본 승격 당시의 역사적 증거다.
회차의 top-level `VISUAL_GATE`와 별개이며 회차 화면 승인을 상속하거나 대체하지 않는다.

## 검증과 정리

CapCut을 열어 relink folder를 선택하고 저장한 뒤 닫는다. 닫힌 상태에서 readback을
실행한다.

```powershell
python scripts/capture_politics_relink_readback.py `
  --project "$env:LOCALAPPDATA\CapCut\User Data\Projects\com.lveditor.draft\<project_name>" `
  --build-report <episode_dir>\90_reports\capcut_build_v1.json `
  --media-dir "$env:USERPROFILE\Videos\22utube_capcut_media\<project_name>\Media" `
  --report <episode_dir>\90_reports\capcut_relink_readback_v1.json
```

`--media-dir`는 portable build report의 `LOCAL_MEDIA_FOLDER/...` 참조를 현재 PC의 실제
Media 폴더에 연결하는 private readback 입력이다. 이 절대경로는 report에 직렬화하지 않는다.
portable report에 이 입력이 없으면 `WAIT_PRIVATE_MEDIA_DIR_REQUIRED`로 멈춘다. 과거의
절대경로 기반 v1 build report는 `--media-dir` 없이도 읽는다.

실패 복구는 `첫 실패 지점 재현 → 최소 수정 → 동일 검증 재실행` 순서로 한다.
실패한 명령과 gate를 기록하고, 그 gate의 원인만 수정한 뒤 같은 명령을 다시 실행한다.
동일 검증이 PASS가 아니면 다음 gate나 완료 상태로 진행하지 않는다.

필수 결과:

```text
ROOT_CONTRACT=PASS
STAGE2_PREFLIGHT=PASS
CARDS_CONTIGUOUS=PASS
SOURCE_DURATION_EXACT=PASS
PROJECT_DURATION_EXACT=PASS
LOWER_TWO_LINE_SLOT_ACTIVE_COUNT=1
CAPCUT_MIRRORS=PASS
PROJECT_BUILD=PASS
STATIC_STRUCTURE=PASS
MEDIA_RELINK=PASS
MEDIA_RESOLUTION=PASS
FINAL_DRAFT_PLACEHOLDER_SCAN=PASS
HUD_TRACK_GEOMETRY=PASS
LOWER_SLOT_TRACK_GEOMETRY=PASS
NO_JUNK_FILES=PASS
VISUAL_GATE=WAIT_USER_VISUAL_GATE|PASS
MP4=NOT_RUN|PASS
UPLOAD=NOT_RUN|PASS
```

builder는 source/date HUD, CTA, 하단 슬롯의 track id·type·index와 clip geometry를
build report에 고정한다. post-open readback은 저장된 실제 draft에서 같은 필드를 다시
읽어 text·시간·개수와 함께 비교한다. FAIL report도 파일로 남기되 CLI는 nonzero로
종료한다. 이 비교는 좌표·트랙 드리프트를 잡는 정적 검사이며 실제 화면의 가독성, 가림,
크롭, 재생 상태를 승인하지 않는다. 그 판단은 계속 `VISUAL_GATE`가 소유한다.

`STATIC_STRUCTURE`와 `MEDIA_RESOLUTION`은 공식 `PROJECT_BUILD`와 `MEDIA_RELINK`의
세부 증거다. 세부 PASS를 `VISUAL_GATE`, `MP4`, `UPLOAD` PASS로 승격하지 않는다.
`PROJECT_BUILD`는 이 builder의 독립 기계 gate다. `ROOT_CONTRACT`와
`STAGE2_PREFLIGHT` 증거가 없으면 그 둘은 별도 `WAIT`이며 자동으로 PASS가 되지 않는다.

`.bak`, `before_*`, `_backup_*`, `helper_*`는 active draft에 남기지 않는다. 필요한
백업은 draft 밖의 명시적 archive에만 두며, 다른 회차를 고치는 방식으로 재사용하지
않는다.

## 완료 보고

```text
ROOT_CONTRACT: PASS|FAIL|WAIT
STAGE2_PREFLIGHT: PASS|FAIL|WAIT
PROJECT_BUILD: PASS|FAIL|WAIT
STATIC_STRUCTURE: PASS|FAIL|WAIT
MEDIA_RELINK: PASS|FAIL|WAIT
MEDIA_RESOLUTION: PASS|FAIL|WAIT
VISUAL_GATE: PASS|WAIT
MP4: PASS|NOT RUN
UPLOAD: PASS|NOT RUN
PROJECT_NAME:
LOCAL_CAPCUT_PATH:
ONEDRIVE_CARDS_PATH:
REPORTS:
BLOCKER:
NEXT:
```

`MEDIA_RELINK=PASS` AND `VISUAL_GATE=PASS`가 둘 다 있어야 최종·완료의
필요조건이 된다. 둘 중 하나라도 없으면 최종·완료·upload-ready라고 표현하지
않는다. `MP4`와 `UPLOAD`은 각각 별도 상태다. `MP4=PASS`와 원격 업로드 준비
증거가 없으면 upload-ready라고 표현하지 않고, `UPLOAD=PASS` 없이 업로드
완료라고 표현하지 않는다.

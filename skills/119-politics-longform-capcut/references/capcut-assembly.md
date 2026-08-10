# CapCut 조립과 검증

직접 경로의 D 준비, A–D join, caption layout, 사용자 조립표, build, relink,
readback, media resolution, visual에만 이 문서를 읽는다.

## 준비와 근본

CapCut과 백그라운드 프로세스가 닫혔는지 로컬 process 검사로 확인한다.
active pointer를 공식 resolver로 읽고 `PASS_ROOT_CONTRACT`를 확인한다.
정상 resolver PASS를 다시 Codex에게 검토시키지 않는다.

## Join과 cards

join owner 한 명만 A source, B narration, C Resources, D root 결과를 실제 파일로 확인한 뒤:

```text
{episode_dir}/50_capcut_project/episode_cards.json
```

을 쓴다. ASSEMBLY_ONLY에서는 seed의 카드 순서·대사·논평·CTA·시각 문구를 재작성하지 않는다.
실제 파일·SHA·duration·검증된 source range만 결합한다.

## 빌드 전 전체 자막 검사

모든 source SRT, narration SRT, cards lower text는 다음을 만족해야 한다.

```text
평균 15자/줄
최대 2줄
두 줄 전체 30자 목표
한 줄 hard max 18자
```

cards 검사:

```powershell
python scripts/validate_politics_caption_layout.py `
  --cards <episode_dir>\50_capcut_project\episode_cards.json `
  --report <episode_dir>\90_reports\caption_layout_v1.json
```

A/B의 각 SRT도 같은 script의 `--srt`로 검사한다.

3줄, 평균 길이 초과, commentary 1줄·3줄, 작업 메모가 있으면 build하지 않는다.
긴 원본·나레이션 SRT는 텍스트를 바꾸지 말고 cue를 분할한다.
논평은 상위 PRE-119 문구를 짧게 고친 뒤 cards를 재생성한다.

## 사용자 최종 조립표

caption layout PASS 뒤 다음을 로컬로 생성한다.

```powershell
python scripts/generate_user_final_assembly_grid.py `
  --cards <episode_dir>\50_capcut_project\episode_cards.json `
  --output <episode_dir>\50_capcut_project\USER_FINAL_ASSEMBLY_GRID.md
```

GRID는 READ-ONLY다. GRID를 수정해 cards로 역반영하지 않는다.

## Build

```powershell
$workspaceRoot = (Resolve-Path $env:WORKSPACE_ROOT)
python scripts/build_politics_card_project.py `
  --cards <episode_dir>\50_capcut_project\episode_cards.json `
  --workspace-root $workspaceRoot `
  --capcut-root "$env:LOCALAPPDATA\CapCut\User Data\Projects\com.lveditor.draft" `
  --media-dir "$env:USERPROFILE\Videos\22utube_capcut_media\<project_name>\Media" `
  --report <episode_dir>\90_reports\capcut_build_v1.json
```

`PROJECT_CREATED_WAIT_MEDIA_RELINK`은 정적 검사 통과일 뿐 완성이 아니다.

## Build 이후 수정 금지

BUILD 뒤 active draft에서 CTA·chapter·source label·lower text·card media·template·
attachment·history metadata를 직접 수술하지 않는다.

구조 불일치:

```text
상위 입력 또는 episode_cards 수정
→ caption validator
→ GRID 재생성
→ clean rebuild 1회
```

ASSEMBLY_ONLY에서 builder 기능개선·TDD·새 adapter로 자동 확장하지 않는다.
현재 builder가 승인 정책을 지원하지 않으면 `ASSEMBLY_BLOCKED:<원인>`으로 멈춘다.

## Relink와 readback

회차 고유 Media 폴더를 선택하고 저장·종료한 뒤 readback한다.

```powershell
python scripts/capture_politics_relink_readback.py `
  --project "$env:LOCALAPPDATA\CapCut\User Data\Projects\com.lveditor.draft\<project_name>" `
  --build-report <episode_dir>\90_reports\capcut_build_v1.json `
  --media-dir "$env:USERPROFILE\Videos\22utube_capcut_media\<project_name>\Media" `
  --report <episode_dir>\90_reports\capcut_relink_readback_v1.json
```

실제 path와 Media SHA가 일치해야 한다.
offline placeholder와 online material ID가 남으면 `MEDIA_RESOLUTION=FAIL`이다.

## Visual gate

실제 화면에서 다음을 확인한다.

```text
모든 하단 자막 최대 2줄
평균 15자/줄 기준
자동 줄바꿈으로 3줄 없음
글자 과도 축소 없음
얼굴·핵심 정보 가림 없음
HTML 카드 하단 30% 안전
SRT와 논평 동시 표시 없음
작업 메모 노출 없음
```

GRID와 정적 좌표는 실제 화면 PASS를 대체하지 않는다.

## 완료 보고

```text
DIRECT_SCRIPT_READY 또는 ASSEMBLY_ONLY_READY
ROOT_CONTRACT
CAPTION_LAYOUT
EPISODE_CARDS
USER_FINAL_ASSEMBLY_GRID
PROJECT_BUILD
MEDIA_RELINK
MEDIA_RESOLUTION
VISUAL_GATE
```

`MEDIA_RELINK=PASS`, `MEDIA_RESOLUTION=PASS`, `VISUAL_GATE=PASS`가 모두 있어야 완료다.

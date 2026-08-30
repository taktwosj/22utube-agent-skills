# CapCut 조립과 검증

직접 경로의 D 준비, A–D join, assembly preflight, build, relink, readback, media resolution, visual에만 이 문서를 읽는다.

## 준비와 근본

CapCut과 백그라운드 프로세스가 닫혔는지 확인한다. active pointer를 공식 resolver로 읽고 `PASS_ROOT_CONTRACT`를 확인한다.

## Join과 cards

join owner 한 명만 A source, B narration, C Resources, D root 결과를 실제 파일로 확인한 뒤:

```text
{episode_dir}/50_capcut_project/episode_cards.json
```

을 쓴다. ASSEMBLY_ONLY에서는 seed의 카드 순서·대사·논평·CTA·시각 문구를 재작성하지 않는다.

## Build 전 ASSEMBLY_PREFLIGHT

```powershell
python scripts/run_politics_assembly_preflight.py `
  --cards <episode_dir>\50_capcut_project\episode_cards.json `
  --report <episode_dir>\90_reports\assembly_preflight_v1.json `
  --grid <episode_dir>\50_capcut_project\USER_FINAL_ASSEMBLY_GRID.md
```

이 한 번의 로컬 실행이 다음을 묶어 검증한다.

```text
CAPTION_LAYOUT
SRT_TEXT_FIDELITY
CARDS_SHA
SRT/RAW_INPUT_SHA
USER_FINAL_ASSEMBLY_GRID
```

FAIL이면 build하지 않는다. 정상 PASS 결과를 다시 Codex에게 읽혀 같은 검사를 반복시키지 않는다.

## Build

```powershell
$workspaceRoot = (Resolve-Path $env:WORKSPACE_ROOT)
python scripts/build_politics_card_project.py `
  --cards <episode_dir>\50_capcut_project\episode_cards.json `
  --assembly-preflight-report <episode_dir>\90_reports\assembly_preflight_v1.json `
  --workspace-root $workspaceRoot `
  --capcut-root "$env:LOCALAPPDATA\CapCut\User Data\Projects\com.lveditor.draft" `
  --media-dir "$env:USERPROFILE\Videos\22utube_capcut_media\<project_name>\Media" `
  --report <episode_dir>\90_reports\capcut_build_v1.json
```

ASSEMBLY_ONLY cards는 preflight report가 없거나 cards/SRT/GRID SHA가 바뀌면 build 전에 차단된다.

CTA OFF는 build 전에 root CTA segment를 제거한다. 카드별 CTA가 섞이면 `CTA_POLICY_MIXED_UNSUPPORTED`다.

`PROJECT_CREATED_WAIT_MEDIA_RELINK`은 정적 검사 통과일 뿐 완성이 아니다.

## 사용자 전달 경계

정적 build가 PASS하면 에이전트는 CapCut을 열지 않는다. 다음 세 경로를 실제 build report에서 읽어 사용자에게 보고하고 `WAIT_USER_CAPCUT_CHECK`로 멈춘다.

```text
프로젝트 파일명
프로젝트 전체 경로
미디어 폴더 전체 경로
```

이 전달 시점에는 다음과 같이 보고한다.

```text
MEDIA_RELINK=NOT RUN — USER MANUAL
MEDIA_RESOLUTION=NOT RUN — USER MANUAL
VISUAL_GATE=NOT RUN — USER MANUAL
MP4=NOT RUN
UPLOAD=NOT RUN
```

사용자가 직접 CapCut을 열고 확인한다. 정적 build를 전체 CapCut 제작 완료로 승격하지 않는다.

## 승인 후 MCP export

정상 조립은 위 경계에서 끝난다. 이후 사용자가 `USER_CAPCUT_CHECK_PASS`와 `APPROVE_CAPCUT_EXPORT`를 각각 명시한 `2pow 22factory MCP` export job만 다음을 수행할 수 있다.

1. build/readback과 일치하는 정확한 기존 프로젝트 하나를 연다. 이름만 비슷하거나 evidence가 없는 프로젝트는 거부한다.
2. 프로젝트 내용을 수정하지 않고 입력 응답과 visual/readback 상태를 재확인한다. 비밀번호·결제·로그인·macOS 권한창·프로젝트 불일치·offline media가 보이면 중단한다.
3. 회차의 새 `60_export/<episode_id>_<timestamp>.mp4`로 내보낸다. 기존 파일을 덮어쓰지 않는다.
4. 완료 표시와 size/mtime 안정화를 확인한 뒤 ffprobe로 MP4 container, video stream, positive duration, width, height를 검증한다.
5. `PROJECT_BUILD`, `USER_CAPCUT_CHECK`, `EXPORT`, `MP4_CREATED`, `MP4_VALIDATED`, `MCP_ARTIFACT_AVAILABLE`, `REMOTE_FILE_RETRIEVAL`, `UPLOAD`을 별도 상태로 기록한다.
6. MCP의 `factory_artifact`가 episode-local 파일의 metadata와 `resource_link`를 반환하고, 원격 client가 같은 SHA의 실제 bytes를 읽어 다시 검사하기 전에는 파일 전달 완료라고 하지 않는다.

이 export 승인은 draft 수정·삭제·업로드·게시 승인이 아니다. MCP/tunnel이 로컬 경로 문자열만 돌려준 상태는 `MCP_ARTIFACT_AVAILABLE=FAIL`이다.

## Build 이후 수정 금지

BUILD 뒤 active draft에서 CTA·chapter·source label·lower text·card media·template·attachment·history metadata를 직접 수술하지 않는다.

구조 불일치:

```text
상위 입력 또는 episode_cards 수정
→ ASSEMBLY_PREFLIGHT 재실행
→ clean rebuild 1회
```

## Relink와 readback

회차 고유 Media 폴더를 선택하고 저장·종료한 뒤 readback한다.

```powershell
python scripts/capture_politics_relink_readback.py `
  --project "$env:LOCALAPPDATA\CapCut\User Data\Projects\com.lveditor.draft\<project_name>" `
  --build-report <episode_dir>\90_reports\capcut_build_v1.json `
  --media-dir "$env:USERPROFILE\Videos\22utube_capcut_media\<project_name>\Media" `
  --report <episode_dir>\90_reports\capcut_relink_readback_v1.json
```

실제 path와 Media SHA가 일치해야 한다. offline placeholder와 online material ID가 남으면 `MEDIA_RESOLUTION=FAIL`이다. CTA OFF 회차는 readback presentation contract에서도 CTA segment가 없어야 PASS다.

## Visual gate

실제 화면에서 다음을 확인한다.

```text
모든 하단 자막 한 번에 한 줄
공백 제외 15자/줄 이하
자동 줄바꿈 2줄 이상 없음
글자 과도 축소 없음
얼굴·핵심 정보 가림 없음
V8 카드 이미지 화면 `x=336,y=189,1248×702`
SRT와 논평 동시 표시 없음
CTA 승인값 일치
작업 메모 노출 없음
```

GRID와 정적 좌표는 실제 화면 PASS를 대체하지 않는다.

## 완료 보고

```text
PRE119_VALIDATION 또는 DIRECT_SCRIPT_READY
ASSEMBLY_ONLY_READY
ROOT_CONTRACT
EPISODE_CARDS
ASSEMBLY_PREFLIGHT
CAPTION_LAYOUT
SRT_TEXT_FIDELITY
USER_FINAL_ASSEMBLY_GRID
PROJECT_BUILD
MEDIA_RELINK
MEDIA_RESOLUTION
VISUAL_GATE
```

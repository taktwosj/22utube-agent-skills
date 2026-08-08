# CapCut 조립과 검증

직접 경로의 D 준비, A–D join, build, relink, readback, visual에만 이 문서를 읽는다.

## 준비와 근본

CapCut과 백그라운드 프로세스가 닫혔는지 확인한다. active pointer
`00_asset_tools/templates/capcut/jungchilong/capcut_active_root_v1.json`을 공식 resolver로
읽고 `PASS_ROOT_CONTRACT`를 확인한다. builder에 `--root-archive`나 `--root-sha256`을 직접
주지 않는다. 근본 승격을 별도로 요청받았을 때만 [root-bundle-contract.md](root-bundle-contract.md)를
읽는다.

## Join과 cards

join owner 한 명만 A source, B narration, C Resources, D root/target 결과를 실제 파일로
확인한 뒤 `{episode_dir}/50_capcut_project/episode_cards.json`을 쓴다. schema가 필요할 때만
[episode-card-contract.md](episode-card-contract.md)를 읽는다. 카드는 한 primary video lane에서
빈 구간 없이 이어진다. SOURCE_VIDEO의 source/target duration은 1x 재생일 때만 같다.

HUD 시간은 `episode_cards.json`의 실제 카드 시간에서 파생한다. source 구간에는 상단
챕터, 좌측 출처 채널·실제 게시일, 우측 CTA를 둔다. 채널·날짜는 별도 editable text다.
하단에는 같은 시간대에 `SOURCE_TTS`, `NARRATION_TTS`, `VIDEO100_EXPLAINER`, `NONE` 중
하나만 둔다. 직접 경로의 `NARRATION_TTS`는 119 생성·정렬 SRT를 받는다.

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

`PROJECT_CREATED_WAIT_MEDIA_RELINK`은 정적 검사 통과일 뿐 완성이 아니다. portable report에는
상대경로나 `LOCAL_*` 참조만 쓰고 실제 로컬 절대경로를 직렬화하지 않는다. root의 과거
visual evidence를 회차 `VISUAL_GATE`로 승격하지 않는다.

## Relink와 readback

회차 고유 `Media` 폴더를 CapCut에서 선택하고 저장·종료한 뒤 실행한다.

```powershell
python scripts/capture_politics_relink_readback.py `
  --project "$env:LOCALAPPDATA\CapCut\User Data\Projects\com.lveditor.draft\<project_name>" `
  --build-report <episode_dir>\90_reports\capcut_build_v1.json `
  --media-dir "$env:USERPROFILE\Videos\22utube_capcut_media\<project_name>\Media" `
  --report <episode_dir>\90_reports\capcut_relink_readback_v1.json
```

readback의 실제 path와 Media SHA-256이 일치해야 한다. `onlineMaterial`,
`__CAPCUT_RELINK_REQUIRED__`, 비어 있지 않은 `online_id`·`request_id`가 남으면
`MEDIA_RESOLUTION=FAIL`이다. 정적 좌표·트랙 비교는 실제 화면의 가독성·가림·크롭·재생을
승인하지 않으며 `VISUAL_GATE`가 별도로 소유한다.

## 완료 보고

직접 경로는 `DIRECT_SCRIPT_READY`, `ROOT_CONTRACT`, `PROJECT_BUILD`, `STATIC_STRUCTURE`,
`MEDIA_RELINK`, `MEDIA_RESOLUTION`, `VISUAL_GATE`와 blocker/next를 보고한다.
`STAGE2_PREFLIGHT`는 보고하지 않는다. 레거시 경로만 이를 추가한다.

`MEDIA_RELINK=PASS`와 `VISUAL_GATE=PASS`가 모두 있어야 CapCut 제작 완료다. MP4와 업로드는
별도 요청이 없으면 각각 `NOT RUN`이다. `.bak`, `before_*`, `_backup_*`, `helper_*`는 active
draft에 남기지 않는다.

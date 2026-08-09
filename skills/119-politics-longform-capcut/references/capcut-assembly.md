# CapCut 조립과 검증

직접 경로의 D 준비, A/D와 활성 선택 작업의 join, build, relink, readback, visual에만 이 문서를 읽는다.

## 준비와 근본

CapCut과 백그라운드 프로세스가 닫혔는지 확인한다. active pointer
`00_asset_tools/templates/capcut/jungchilong/capcut_active_root_v1.json`을 공식 resolver로
읽고 `PASS_ROOT_CONTRACT`를 확인한다. builder에 `--root-archive`나 `--root-sha256`을 직접
주지 않는다. 근본 승격을 별도로 요청받았을 때만 [root-bundle-contract.md](root-bundle-contract.md)를
읽는다.

## Join과 cards

join owner 한 명만 A source와 D root/target을 항상 확인하고, 명시 요청으로 활성화된 경우에만
B narration과 C Resources를 확인한 뒤 `{episode_dir}/50_capcut_project/episode_cards.json`을 쓴다.
요청되지 않은 B/C는 `NOT_REQUESTED` 또는 `NOT_APPLICABLE`이며 join이 기다리지 않는다. schema가 필요할 때만
[episode-card-contract.md](episode-card-contract.md)를 읽는다. 카드는 한 primary video lane에서
빈 구간 없이 이어진다. SOURCE_VIDEO의 source/target duration은 1x 재생일 때만 같다.

PRE-119 경로에서는 handoff validator가 cards를 쓰지 않는다. A/D와 활성 B/C가 완료된 뒤
join owner가 실제 자산 증거를 다음 CLI에 전달한다.

```powershell
python scripts/compile_pre119_episode_cards.py `
  --validation-report <episode_dir>\90_reports\pre119_handoff_validation.json `
  --asset-evidence <episode_dir>\90_reports\pre119_abcd_assets.json `
  --output <episode_dir>\50_capcut_project\episode_cards.json
```

A/D PASS, 요청된 B/C PASS, 실제 경로·SHA-256·양의 duration, SOURCE_TTS의 RAW/DISPLAY
provenance 중 하나라도 없으면 output을 만들지 않는다.

기본 카드는 source footage와 embedded source audio를 유지하고 editable text overlay를
사용한다. 나레이션을 요청하지 않았으면 narration media/SRT와 narration card를 요구하지
않는다. 이미지를 요청하지 않았으면 episode image와 image card를 요구하지 않는다. 별도
요청이 없으면 `SOURCE_VIDEO` 챕터 1→2→3→4를 t=0부터 빈 구간 없이 배치한다. intro는
명시 요청된 경우에만 앞에 둔다. 이때 공식 resolver의 layout contract에서 검증된
`content_start_us`를 duration으로 사용하며 5초를 임의로 고정하지 않는다. 카드 요청값이
근본 경계와 다르면 `INTRO_DURATION_CONTRADICTS_ROOT`로 중단한다.

지원 목표 조합은 `SOURCE_VIDEO=VIDEO+SOURCE`, `NARRATION_VIDEO=VIDEO+NARRATION`,
`CHAPTER_CARD=IMAGE+SILENT`, `NARRATION_IMAGE=IMAGE+NARRATION`이다. `VIDEO+SILENT`와
`IMAGE+SOURCE`는 별도 구현·검증 전에는 지원 조합이 아니다. lower의 사용자 선택은
`SRT|COMMENTARY_2LINE|NONE`이며 [episode-card-contract.md](episode-card-contract.md)의
기존 mode에 매핑한다. 이 이름을 새 JSON field로 만들지 않는다.

HUD 시간은 `episode_cards.json`의 실제 카드 시간에서 파생한다. source 구간에는 상단
챕터, 좌측 출처 채널·실제 게시일, 우측 CTA를 둔다. 채널·날짜는 별도 editable text다.
하단 `SRT`는 active audio가 SOURCE면 `SOURCE_TTS`/source SRT, NARRATION이면
`NARRATION_TTS`/narration SRT로 매핑한다. SILENT+SRT는 무효다. `COMMENTARY_2LINE`은
`VIDEO100_EXPLAINER`, `NONE`은 `NONE`에 매핑한다.

v5 root의 `__CHAPTER__`는 장식용 placeholder가 아니라 필수 상단 슬롯이다. build 뒤 relink 전에
각 `SOURCE_VIDEO` 챕터마다 root의 챕터 스타일·위치로 된 non-placeholder 상단 텍스트 1개가 있는지
정적으로 확인한다. 누락 시 lower/출처 텍스트를 재사용하지 말고, CapCut을 닫은 뒤 root 챕터 track을
복원해 실제 카드 시간에 맞춰 넣고 duration·source track 불변을 검증한다. 이 검사가 없으면
`VISUAL_GATE=PASS`가 될 수 없다.

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
draft에 남기지 않는다. B/C 결과는 요청받았을 때만 보고한다. 요청되지 않은 narration이나
image의 부재는 `MEDIA_RELINK` 또는 `VISUAL_GATE`의 실패 사유가 아니다. 나중에 B/C가
명시 요청되면 성공한 A/D를 재실행하지 않고 cards에 해당 작업 결과만 추가한다.
나레이션 target mode는 builder 구현과 해당 검증 증거가 확인되기 전에는 `PASS`로 보고하지
않는다. 이는 base video-only build를 막지 않는다.

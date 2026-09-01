# 승인 후 CapCut 내보내기와 파일 전달

CapCut 편집 프로젝트를 로컬 MP4로 내보내고 MCP 또는 Telegram으로 전달할 때 사용한다. 정상 제작 router가 아니라 사용자의 화면 확인과 별도 export 승인이 모두 있는 후속 단계다.

## 범위

- 로컬 MP4 내보내기만 요청되면 YouTube 게시·예약·공개를 실행하지 않는다.
- `2pow 22factory MCP`에서는 `USER_CAPCUT_CHECK_PASS`와 `APPROVE_CAPCUT_EXPORT`가 모두 있어야 시작한다.
- 사용자가 내보내기와 파일 전달을 함께 요청하면 실제 bytes/file 회수까지 완료가 아니다.
- CapCut 프로젝트 생성·클라우드 업로드 완료를 MP4 렌더 완료로 해석하지 않는다.
- 프로젝트 내용 수정·기존 MP4 덮어쓰기·업로드·게시·삭제는 이 승인에 포함되지 않는다.

## 1. 내보내기 전 확인

1. 최종 프로젝트를 이름만이 아니라 draft/project/timeline ID 또는 build receipt로 확인한다.
2. active draft의 duration, VIDEO segment 수·순서, T1/T2, A9/A10, live media 경로를 readback한다.
3. 출력은 외장 2pow 회차 폴더의 정확한 `60_export/` episode-local 경로를 사용한다.
4. 같은 파일이 이미 있으면 덮어쓰지 않고 timestamp 또는 새 version이 붙은 새 경로를 사용한다.
5. 목표 출력 경로를 workflow receipt에 기록한다.

## 2. CapCut UI 내보내기

1. Home의 정확한 로컬 프로젝트 행을 열고 프로젝트명·길이·시작 화면을 확인한다.
2. `내보내기` 버튼 또는 CapCut의 정상 내보내기 단축키를 사용한다.
3. 클릭이 한 번 무시되면 같은 좌표를 반복하지 말고 먼저 **입력 응답 probe**를 한다.
   - 타임라인의 알려진 시점(예: 중간 구조 전환)을 한 번 클릭한다.
   - 재생헤드·timecode·프리뷰 프레임이 실제로 바뀌는지 새 캡처로 확인한다.
   - 프로세스 CPU나 `frontmost=true`만으로 편집기 응답을 PASS하지 않는다.
4. 타임라인 probe도 실패하면 창 단위 캡처뿐 아니라 **전체 화면 캡처**를 확인한다. 창 캡처에 안 잡히는 macOS native permission dialog, notification overlay, stale helper가 입력을 막을 수 있다.
5. 비밀번호·결제·macOS 권한창은 에이전트가 대신 누르지 않는다. 예를 들어 `CapCut이 로컬 네트워크의 기기를 찾도록 허용` 창이 나타나면 중단하고 사용자가 직접 `허용` 또는 `허용 안 함`을 선택하게 한다. 로컬 파일 내보내기만 필요할 때는 네트워크 권한이 필수라고 단정하지 않는다.
6. 사용자가 권한창을 처리했다고 하면 전체 화면에서 사라졌는지 확인한 뒤 probe를 다시 수행한다. 사용자가 `눌러도 반응 없다`고 보고하면 같은 수동 클릭을 다시 요구하지 않는다.
7. 편집기가 교착된 것으로 보이면 먼저 정상 종료를 요청한다. 정상 종료가 제한 시간 안에 끝나지 않고, 종료 전 draft JSON·duration·segment count 등 정적 무결성 readback이 PASS했다면 앱 프로세스만 종료 후 새 세션으로 연다. 프로젝트 파일을 수정하거나 삭제하지 않는다.
8. 로컬본 편집기만 무응답이고 이미 **업로드 후 reopen 검증을 통과한 동일 클라우드본**이 있으면 독립 복구 경로로 사용할 수 있다.
   - 목적지는 반드시 `User3160027826975의 공간/MAC` breadcrumb로 확인한다. `자동 업로드`의 동명 행을 MAC 정본으로 오인하지 않는다.
   - cloud row의 이름·크기·길이·최근 편집 시각을 읽고 검증된 정본과 일치시키고, 다시 연 뒤 타임라인 probe로 입력 응답을 확인한다.
   - 클라우드본 사용은 구조·미디어·화면 reopen 검증이 선행된 경우에만 허용한다. 단지 이름이 같다는 이유로 대체하지 않는다.
9. 타임라인 probe는 PASS하지만 상단 `내보내기`만 반응하지 않으면 좌표·단축키 조합을 계속 추측하지 않는다. 한 번의 전체 화면 확인, 정확한 버튼 hitbox 확인, 정상 재시작까지로 범위를 제한하고 CapCut UI blocker로 보고한다. MP4가 실제 생성되지 않은 상태를 완료라고 말하지 않는다.
10. 설정창이 열리면 파일명·저장 위치·해상도·프레임레이트·코덱·포맷·오디오 포함 여부를 읽어 기록한다. 프로젝트 승인 규격과 다르면 실행하지 않는다.
11. 일반 세로 쇼츠는 승인 설계가 달리 지정하지 않는 한 1080×1920, MP4/H.264, 원본 또는 승인 FPS, 오디오 포함을 우선하되 실제 UI 값을 검증한다.

### 응답 판정표

| 관찰 | 해석 | 다음 행동 |
|---|---|---|
| 타임라인·timecode·프리뷰 모두 변경 | 편집기 입력 정상 | 내보내기 버튼 1회 시도 |
| 타임라인 probe 실패, native 권한창 보임 | 권한창이 입력 차단 | 사용자가 직접 처리 후 재검증 |
| probe 실패, 정상 종료도 시간 초과 | 편집기 세션 교착 가능성 | 정적 무결성 확인 후 앱만 재시작 |
| 로컬 probe 실패, 검증된 MAC cloud본 probe PASS | 로컬 세션 한정 문제 | MAC cloud 정본으로 내보내기 계속 |
| probe PASS, 내보내기만 반복 무응답 | 상단 UI/export blocker | 반복 클릭 중단, 미완료로 정확히 보고 |

## 3. 완료 판정

- 진행창이 닫혔다는 사실만으로 완료 판정하지 않는다.
- 출력 파일이 생성되고 size/mtime이 안정화되며 CapCut 완료 표시가 확인돼야 한다.
- 내보내기 실패·취소·부분 파일은 최종 산출물로 전달하지 않는다.

## 4. 출력 검증

최종 MP4에 대해 다음을 새로 검사한다.

- `ffprobe` decode/parse 성공
- video stream 존재
- audio stream 존재
- 해상도와 display aspect ratio
- codec, pixel format, FPS
- 실제 duration이 승인 timeline과 허용 오차 내 일치
- 파일 byte size와 SHA-256
- 오디오가 무음이 아님
- 첫 장면, 핵심 구조 전환, 중간, 끝 프레임 시각 QA
- T1/T2/TTS 자막 잘림, 검은 화면, offline media, 마지막 프레임 이상 여부

검증 결과와 파일 경로를 `90_reports/export_report.json` 또는 동등한 회차 보고서에 기록한다.

## 5. MCP·Telegram 전달

### MCP

1. `factory_artifact`는 등록 workflow의 해당 `episode_id/60_export` 안에 있는 검증 PASS MP4만 선택한다.
2. 결과에는 workflow, episode_id, export/validation 상태, 절대경로, 파일명, bytes, duration, resolution, created_at, SHA-256과 MCP `resource_link`를 함께 둔다.
3. 로컬 `/Volumes/...` 문자열만 반환하면 `MCP_ARTIFACT_AVAILABLE=FAIL`이다.
4. MCP client가 `resources/read`로 같은 SHA의 MP4 blob을 받아 실제 bytes를 재구성하고 다시 ffprobe하기 전에는 `REMOTE_FILE_RETRIEVAL=PASS`가 아니다.
5. tunnel은 MCP JSON-RPC 전달 경로일 뿐 일반 파일 URL로 오인하지 않는다. 큰 파일 응답이 client 또는 tunnel 한계를 넘으면 `WAIT_ARTIFACT_TRANSPORT_LIMIT`로 멈춘다.

### Telegram

1. 검증 PASS MP4만 첨부한다.
2. Telegram 답변에 `MEDIA:/absolute/path/to/video.mp4`를 넣는다.
3. 파일명, 해상도, 길이, 크기, 검증 상태를 짧게 함께 보고한다.
4. Telegram 첨부 성공과 YouTube 게시를 혼동하지 않는다.

## 상태 예시

```text
WAIT_EXPORT_APPROVAL
EXPORT_IN_PROGRESS
EXPORT_COMPLETED
EXPORT_VALIDATED
MCP_ARTIFACT_AVAILABLE
REMOTE_FILE_RETRIEVAL_COMPLETED
TELEGRAM_HANDOFF_COMPLETED
```

`REMOTE_FILE_RETRIEVAL_COMPLETED`와 `TELEGRAM_HANDOFF_COMPLETED`는 각각 MP4 검증 PASS 후 해당 client가 실제 bytes/file을 받은 경우에만 사용한다.

# TOP5 제작목록·OneDrive 경량 동기화

TOP5·군림보 CapCut 프로젝트 파일이 정적 검증을 통과한 뒤 적용한다. raw CapCut draft, Cache, 앱 DB, 대형 이미지·오디오를 OneDrive에 복제하지 않는다.

## 승인 범위

사용자가 `TOP5 만들자`, `만들자`, `진행`, `끝까지`라고 했고 제목·각도를 선택했다면 기본 stop point인 **편집 가능한 CapCut 프로젝트 파일과 검증 보고서까지** 계속 진행한다. 같은 범위의 대본·TTS·이미지·조립 단계마다 승인 버튼을 반복하지 않는다.

다시 질문하는 경우는 다음뿐이다.

- 인물·순위·핵심 사실을 공식 자료로 확정할 수 없음
- 사용자가 선택해야 결과가 실질적으로 달라지는 창작 방향
- 결제·게시·공개·예약·삭제·업로드
- 개인정보·권리·정책상 새 blocker

Clarify UI가 시간초과돼도 앞서 사용자가 명시한 제작 승인과 제목 선택을 무효화하지 않는다.

## production_id와 버전 이력

- `production_id`는 episode_id로 고정한다.
- 최신 CapCut 프로젝트명, 로컬 경로, template profile, current draft SHA-256, 상태를 기록한다.
- `capcut_project_history`에는 version, project_name, machine, recorded_at, last_seen_at, draft hash, 이미지 수·규격·high-impact indices를 누적한다.
- 같은 프로젝트를 다시 읽었으면 기존 version의 `last_seen_at`과 hash를 갱신한다. 새 프로젝트명이면 다음 version을 추가한다.

## OneDrive 경량 episode

기본 경로:

```text
${ONEDRIVE_22UTUBE_ROOT}/22factory_20260628/01_shorts_factory/episodes/{episode_id}
```

`ONEDRIVE_22UTUBE_ROOT`는 현재 머신의 동기화된 `22utube` 루트를 탐색해
결정하며, 특정 사용자명이나 볼륨 경로를 계약에 고정하지 않는다.

저장 대상:

```text
50_capcut_project/project_pointer.json
90_reports/assembly_report.md
90_reports/local_paths.md
90_reports/production_summary.json
90_reports/upload_info.md
90_reports/trend_hunter_production_metadata_pending.json
episode_state.json
```

저장 후 실제 OneDrive realpath, 파일 수·크기, 로컬 원본과 SHA-256 일치, JSON parse를 검증한다.

## Trend Hunter 상태

서버 source·API·전송 스크립트와 `video_id`가 모두 확인된 경우에만 서버 카드에 전송한다. 없으면 프로젝트 완료를 막지 말고 다음처럼 기록한다.

```text
status=WAIT_TREND_HUNTER_VIDEO_ID
production_enabled=false
server_send_attempted=false
```

이 상태에서도 로컬 metadata와 OneDrive 경량 episode 업데이트는 PASS다. 서버에 실제 전송하지 않았으면 `Trend Hunter 서버 업데이트 완료`라고 말하지 않는다. 보고는 반드시 아래처럼 분리한다.

```text
OneDrive 제작목록 metadata=UPDATED
Trend Hunter server card=WAIT_TREND_HUNTER_VIDEO_ID
render=NOT_PERFORMED
upload=NOT_PERFORMED
```

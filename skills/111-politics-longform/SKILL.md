---
name: 111-politics-longform
description: Use when the user says 111정치롱폼, 정치롱폼, 정치미드폼, 민주진영 유튜브, 매불쇼 롱폼, 유시민 롱폼, or asks to design, review, assemble, validate, or package a Korean political longform video, lower two-line commentary, jungchilong CapCut project, upload copy, API upload, or thumbnail hooks.
---

# 111 Politics Longform

## Core Rule

정치 롱폼은 다음 두 단계로 운영한다.

```text
Stage 1: 실제 소스·전체 자막·후보 구간·하단 2줄 초벌 평론을 포함한 1차 설계도
외부 검토: 한 파일에 시간순으로 정리한 평론 패킷 송신·회수
Stage 2: 원본·초벌안·외부안을 검토해 설계 확정 → speech lock → locked clips → CapCut 조립·검증
```

Stage 1 초벌을 그대로 조립하지 않는다. Stage 2는 발언·맥락·논리·가독성을
검토하고 최종 반영안을 확정한다. 조립에는 `timeline_design_approved.json`만
사용하고 `timeline_design_draft.json`을 조립에 사용하지 않는다.

## 근본 CapCut 프로젝트

단일 근본은 로컬의 과거 에피소드가 아니라 검증된 OneDrive 아카이브다.

```text
target_profile: jungchilong_base_v3_intro15
promotion_state: READY
target_archive: ${env:WORKSPACE_ROOT}\22factory_20260628\00_asset_tools\templates\capcut\jungchilong\jungchilong_v3_intro15_CAPCUT_20260715.zip
target_manifest: ${env:WORKSPACE_ROOT}\22factory_20260628\00_asset_tools\templates\capcut\jungchilong\template_manifest_v3_intro15.json
archive_sha256: B461A07FF18E1491E837E56A0681A35CCB0A25CBF9D7BFA2B6004C6D32CC878A
packaged_file_count: 39
intro_sha256: E899A65CC6C089FF116CBB6175B6A43B8580A69C523720B093FBE259F05717B9
restore_target: %LOCALAPPDATA%\CapCut\User Data\Projects\com.lveditor.draft\jungchilong
gui_gate: 90_reports\jungchilong_gui_restore_gate.json
canvas: 1920x1080
content_start_sec=15.083333
intro_asset: jungchilong/Resources/media/123123.mp4
```

위 값이 현재 운영 계약이다. 새 작업은 v3 승격 대기나 v2 fallback으로 돌리지
않는다. 실행 때마다 ZIP·manifest·파일 수·인트로 해시를 다시 검증하며, 상수와
실파일이 다르면 `FAIL_ARCHIVE_INTEGRITY`로 중단한다. v2 아카이브는 이력 확인용
read-only 자료일 뿐 새 에피소드의 근본이 아니다.

권한 순서는 `ZIP + template_manifest.json` → 검증된 로컬 복구본
`jungchilong` → 에피소드 복제본이다. ZIP과 로컬 복구본을 직접 수정하지 않는다.
Stage 2는 로컬 복구본 전체를 새 에피소드 프로젝트명으로 복제한 뒤 복제본만
수정한다.

YP007, YP005, YM007 are legacy visual references only. 이 프로젝트들을 근본,
fallback 근본, 새 에피소드의 복제 원본으로 사용하지 않는다. 과거 하단 평론의
밀도나 레이아웃을 참고할 때만 읽는다.

아카이브 무결성 PASS와 현재 머신의 CapCut GUI 열림 PASS는 별도 게이트다.
매니페스트의 `gui_restore_test_on_second_machine=WAIT_USER_RESTORE`는
`LOCAL_GUI_RESTORE=PASS`가 아니다.
새 근본 승격은 CapCut을 완전히 종료한 뒤 별도 staging 사본에서만 수행한다.
`.bak`, 임시 파일, orphan media, 외부 사용자 경로를 제거하고 인트로를
`Resources/media`에 내장한 다음 root·`template-2.tmp`·`Timelines/*` 미러를
일치시킨다. `INTRO_MEDIA_FFPROBE=PASS`, `INTRO_MEDIA_SHA256=PASS`,
`INTRO_TEXT_COVERAGE=PASS`, `OVERLAY_OFFSET=PASS`,
`NO_FOREIGN_ABSOLUTE_PATHS=PASS`, 복구 validator PASS가 모두 확인된 새 ZIP과
매니페스트 및 `V3_LOCAL_GUI_RESTORE=PASS`(`gui_opened=true`,
`timeline_visible=true`)가 모두 확인되어야 `jungchilong_base_v3_intro15`로
승격한다. 구조 validator만으로는 승격하지 않는다. 파일 수·ZIP SHA는 승격
결과를 매니페스트와 코드에 함께 pin하며 이전 37개 값을 재사용하지 않는다.
승격 증거는 `v3_local_gui_restore_gate.json`에 기록하고 template profile,
archive 이름·SHA-256, manifest 이름·SHA-256과 결합한다. archive verifier는
이 증거 파일과 `status=PASS`, `gui_opened=true`, `timeline_visible=true`를 직접
검사해야 하며 `promotion_state=READY` 상수만으로 통과시키지 않는다.

## 정치 롱폼 공통 제작 계약

### 작업 루트와 소유권

```text
active_root: ${env:WORKSPACE_ROOT}\22factory_20260628
politics_lane: 02_politics_longform\episodes\{episode_id}
legacy_root: ${env:UTUBE_ROOT} (legacy read-only fallback)
active_writer_machine: home_windows|office_windows|macmini|unknown
lock_owner: required
capcut_mode: local_only
onedrive_role: archive_and_handoff
raw_capcut_sync: false
```

작업 전에 active root의 `AGENTS.md`와
`docs\YOUTUBE_PRODUCTION_WORK_ORDER.md`를 읽는다. 실제 factory root를 찾지
못하면 `WAIT_FACTORY_ROOT_NOT_RESOLVED`로 중단한다. 한 에피소드에는 active
writer machine 하나만 허용한다. 다른 머신으로 넘길 때는 CapCut을 완전히
종료하고 소유권 매니페스트를 갱신한다.

원본 영상, locked clips, raw CapCut draft, 캐시와 렌더는 active writer machine의
로컬 디스크에 둔다. 전체 SRT/TXT는 외부 검토와 기기간 인계에 필요한 작은 텍스트
증거이므로 episode의 `10_analysis/transcripts`에 둘 수 있다. OneDrive에는 이
텍스트 증거와 상대경로 매니페스트, 해시, 설계도, 외부 검토 문서, 스냅샷, 복구
안내와 보고서만 둔다.

### 시작 브리프

생산 작업 전 다음을 작성한다.

```text
정치 롱폼 시작 브리프
- 사용자 의도:
- 에피소드 ID:
- 실제 출처/채널/업로드일:
- Stage: Stage 1 / external review / Stage 2
- 근본 템플릿: jungchilong_base_v3_intro15
- active_writer_machine / lock_owner:
- 음성 정책: source audio embedded / explicit exception
- 현재 게이트:
- blocker:
- next:
```

### 진행판

실행 증거만 반영한다. 실행하지 않은 항목은 `NOT RUN`, 로컬 실행으로 n8n을
쓰지 않았으면 `NOT RUN - local run`이다.

```text
[정치 롱폼 진행판]
A. 설계·검토
01 소스 확보·ffprobe           WAIT/RUNNING/PASS
02 전체 자막·후보 구간         WAIT/RUNNING/PASS
03 Stage 1 초벌 설계도         WAIT/RUNNING/PASS
04 외부 평론 패킷              WAIT/SENT/RECEIVED/PASS
05 평론 논리·맥락 검토         WAIT/RUNNING/PASS
06 승인 설계도                 WAIT/RUNNING/PASS

B. 조립
01 speech boundary lock        NOT RUN/PASS/FAIL
02 locked clips + ffprobe      NOT RUN/PASS/FAIL
03 jungchilong 로컬 GUI 복구    NOT RUN/PASS/FAIL
04 에피소드 복제본 조립         NOT RUN/PASS/FAIL
05 CapCut JSON 미러            NOT RUN/PASS/FAIL
06 오디오·간격 검증             NOT RUN/PASS/FAIL
07 frame QA                    NOT RUN/PASS/FAIL
08 프로젝트 정리               NOT RUN/PASS/FAIL
09 최종 설계도 강제출력         NOT RUN/PASS/FAIL
10 최종 조립도 강제출력         NOT RUN/PASS/FAIL
11 썸네일·업로드 문안 강제출력   NOT RUN/PASS/FAIL
12 캣컷 프로젝트 복사 푸터       NOT RUN/PASS/FAIL
13 final-output harness        BLOCKED/PASS/FAIL
14 all/final harness           BLOCKED/PASS/FAIL

C. 외부
n8n: NOT RUN - local run / PASS / FAIL
rights/fair-use: WAIT/PASS
upload_ready: false/true
```

## Stage 1 — 초벌 설계도

Stage 1은 형식을 빠짐없이 채우되 내용은 `STAGE1_DRAFT`, `CANDIDATE`,
`NEEDS_REVIEW` 상태로 둔다. CapCut draft, speech lock, locked clips, export,
`FINAL_DESIGN`, `upload_ready`를 만들거나 주장하지 않는다.

### 소스 증거

YouTube 소스는 FHD/1080-first로 확보하되 원본 입력 해상도는 1080p와 720p를
모두 정상 허용한다.

```text
preferred_source_resolution=1920x1080
required_accepted_source_resolutions=1920x1080|1280x720
source_resolution_gate=SOURCE_RESOLUTION_ACCEPTED
source_dimensions_preserved_from_ffprobe=true
final_canvas_resolution=1920x1080
thumbnail_resolution_contract=1280x720
```

`1920x1080` 원본을 우선 확보하지만, `1280x720` 원본도 해상도만으로 실패시키지
않는다. 720p 원본은 실제 ffprobe 폭·높이를 매니페스트에 보존하고 16:9 비율을
유지한 채 최종 `1920x1080` CapCut 캔버스에 맞춘다. 입력 소스 해상도, 최종
CapCut 캔버스, `1280x720` 썸네일 규격은 서로 다른 계약이다. 위 두 원본 규격은
최소 보장 입력이며, 1440p·4K 등 다른 정상 원본도 ffprobe와 소스 검증을 통과하면
허용한다.

`source_manifest.json`의 모든 소스는 다음 필드를 가진다.

```text
source_id, channel, upload_date, url, video_id
local_path (local media root-relative), transcript_path (episode-relative)
bytes, sha256, download_status=PASS
ffprobe.status=PASS, width, height, video_duration_sec, audio_duration_sec
```

원본과 locked clip의 로컬 기준은 `--media-root` 또는
`POLITICS_LONGFORM_MEDIA_ROOT`로 명시한다. 이 루트는 OneDrive episode 밖이어야
하고 factory root 안에도 둘 수 없다. 매니페스트에는 절대경로가 아니라 이 루트
기준 상대경로만 기록한다. 검증기는 저장된 `ffprobe` 필드를 신뢰하지 않고 실제
파일에 `ffprobe`를 다시 실행해 video/audio stream, 크기와 길이를 대조한다.

전체 SRT/TXT는 디스크에 저장한다. 모델 컨텍스트에는 전체 자막을 반복 적재하지
말고 후보 구간의 자막만 읽는다. 후보 영상 구간은 보통 1~5분이며 원본
`source_in`과 `source_out`을 반드시 기록한다.

### Stage 1 산출물

```text
00_source/source_manifest.json
10_analysis/roughcut_edl.json
10_analysis/source_labels.json
10_analysis/topic_flow.json
10_analysis/design_blueprint_draft.json
10_analysis/design_blueprint_draft.md
10_analysis/timeline_design_draft.json
10_analysis/transcripts/S01_full.srt
10_analysis/transcripts/S01_full.txt
20_script/commentary_review_packet_sent.md
20_script/commentary_review_packet_manifest.json
90_reports/stage1_gate.json
```

`design_blueprint_draft.md`는 jungchilong의 실제 화면 역할을 기준으로 출처,
날짜, 우측 상단 주제, 원본 범위, 최종 타임라인과 하단 평론을 보여준다.
후보 EDL·라벨·topic flow·timeline은 상태 문자열만 있는 빈 PASS/CANDIDATE 파일일
수 없다. clip/source id, 순서, 원본 범위, 타임라인 연속성, 길이와 초벌 평론이
서로 일치해야 Stage 1 PASS다.

`topic_flow.json`과 timeline의 `flow_straps`는 단순 문자열 배열이 아니다. 각
항목은 다음 필드를 가진 시간 객체이며, `content_start_sec`부터 프로젝트 끝까지
gap·overlap 없이 연속으로 덮는다.

```json
{
  "flow_id": "F001",
  "timeline_start_sec": 15.083333,
  "timeline_end_sec": 120.0,
  "text": "[비판 동기] > 정계개편 비약 > 인사 개입 > 검찰개혁 지연 > 당 해체 경고"
}
```

데이터의 `text`에는 전체 목차와 정확히 하나의 활성 주제를 대괄호로 표시한다.
화면 렌더러는 대괄호를 제거하고 해당 주제 전체만 노란색, 나머지는 흰색으로
표시한다. 각 flow 구간의 시작·종료와 활성 주제는 승인 timeline과 같아야 한다.

### 친근한 감상 포인트 인트로

모든 새 정치롱폼은 근본에 내장된 15.083333초 인트로를 그대로 사용한다. 별도
외부 영상을 앞에 다시 붙이거나 Desktop 경로를 참조하지 않는다.

```text
profile: jungchilong_base_v3_intro15
media: Resources/media/123123.mp4
timeline role: intro video + intro_text
content_start_sec=15.083333
```

Stage 1은 오늘 다룰 쟁점과 감상·검증 포인트를 친근하게 설명하는 초벌 문안을
만든다. Stage 2는 사실성·논리·가독성을 다시 검토해 `final_intro_text`를 확정한다.
최종 인트로는 정확히 2개 cue이며 각 cue는 실제 2줄이다. cue 1은 오늘 다룰
쟁점, cue 2는 시청자가 볼 감상·검증 포인트를 설명한다. 전체 문안은 공백 포함
약 70~90자를 기준으로 하되 15초 화면 가독성을 우선한다.
승인 timeline에서 cue 1은 `role=issue`, cue 2는 `role=viewing_point`로 고정한다.

두 cue는 `[0,content_start_sec)`를 gap·overlap 없이 정확히 덮고 두 번째 cue는
15.083333초에 끝난다. source, date, flow, source_caption, lower commentary,
subscribe와 첫 locked clip은 모두 `content_start_sec`에서 시작한다.
인트로 구간에는 source, date, flow, source_caption, lower_commentary, subscribe를 표시하지 않는다.

### 하단 2줄 초벌 평론

- `segment_id`는 `C001`, `C002`처럼 고정하고 시간 변경과 분리한다.
- 인트로가 없으면 첫 구간은 `00:00`부터, 인트로가 있으면 첫 구간은
  `content_start_sec`부터 시작한다.
- 구간은 반개구간 `[start,end)`로 연속이어야 한다. 예:
  `00:00-00:20`, `00:20-00:43`, `00:43-01:00`.
- 약 20초를 목표로 하되 발언 단락과 출처 전환에 따라 10~35초를 허용한다.
- 1줄은 실제 발언·사실 요약, 2줄은 논리적으로 이어지는 해석·평론이다.
- 원본에 없는 사실, 결론 비약, 추상적 구호, 인접 중복을 피한다.

### TTS 원본자막 텍스트 트랙

Stage 1 설계도와 timeline에는 하단 평론과 분리된 `source_caption`/`TTS` 정책을
기록한다. `source_caption`은 `track_type=text`, `editability=editable`인 CapCut
텍스트 역할이며, 원본 영상에 다시 구워 넣은 자막이 아니다.

```text
role: tts
placement: lower commentary 바로 위의 비충돌 영역
font size: 8.0 (`TTS font size: 8.0`)
style: 흰색 글자
max lines: 1줄
TTS non-space characters: max 20
timing: speech boundary lock 후 실제 발화 문장별 cue
gap: 무음·비발화 구간의 자연스러운 자막 공백 허용
```

Stage 1에서는 `status=CANDIDATE`와 화면 정책만 고정한다. 실제 cue별 문자열과
시작·종료 시간은 Stage 2에서 전체 SRT/TXT와 원음을 대조하고 speech boundary
lock 후 승인 timeline에 기록한다. 원본 영상에 박힌 자막이 있으면 크롭 또는
마스킹한 뒤 `source_caption`을 표시한다. 이중 노출을 없앨 수 없으면
`NEEDS_VISUAL_REVIEW`로 두고 조립 PASS를 주장하지 않는다.

TTS는 합성음성이 아니라 편집 가능한 원본 발화 자막 lane이다. 20자 제한을
맞추기 위해 원문을 축약·요약·의역하지 않는다. 긴 발화는 자연스러운 speech
boundary에서 여러 cue로 나누고 각 cue만 공백 제외 최대 20자로 만든다. 표시 cue의
정규화 연결 문자열은 선택 원본 자막의 정규화 연결 문자열과 100% 같아야 한다.
누락·치환·요약이 있으면 `FAIL_SOURCE_CAPTION_FIDELITY`다.

`source_caption_track.original_transcript`의 계약 표기는
`original_transcript: episode-relative SRT/TXT path`다. 이 필드는 자막 본문이
아니라 episode 기준 SRT/TXT 상대경로이며 절대경로나 본문 문자열을 넣지 않는다.
fidelity 검증은 표시 cue 텍스트를 시간순으로 정규화해 연결한 값과, 연속 중복을
제거한 unique consecutive `(source_id, source_cue_index)`가 가리키는 선택 원본
`source_text`를 시간순으로 정규화해 연결한 값을 비교한다. 경로 문자열 자체를
화면 자막과 비교하지 않는다.

### CapCut 화면 텍스트 입력 규칙

- 화면 텍스트에는 가운데점 `·`을 사용하지 않는다. CapCut에서 글자가 잘릴 수
  있으므로 의미를 유지한 채 공백 없는 쉼표 `,`로 바꾼다.
- 예: `재건축·재개발이`는 쓰지 않고 `재건축,재개발이`로 입력한다.
- 이 치환은 TTS, 하단 평론, 우측 상단 주제 등 최종 화면 텍스트에 적용한다.
  원본 자막·출처 기록용 원문은 그대로 보존한다.

### 한 파일 외부 검토 패킷

외부 검토 지침은 파일 맨 위에 한 번만 쓴다. 그 아래에 최종 타임라인 순서대로
모든 평론 구간을 반복한다.

파일 최상단에는 다음 명령 프롬프트를 정확히 한 번 넣는다.

```text
너는 민주진영 관점의 정치 평론가다. 이재명, 민주당, 유시민 등 민주진영의 문제의식에 우호적인 시각으로 논평하되, 원본 자막과 확인된 사실을 벗어난 주장, 가짜 인용, 인신공격, 확인되지 않은 범죄 단정은 추가하지 않는다.
```

```text
# 정치롱폼 외부 평론 검토
## 검토 지침
...

<!-- SEGMENT_ID:C001 -->
### C001 | 00:00-00:20
출처: {channel}
게시일: {YYYY.MM.DD}
연결 영상: {source_id}
원본 구간: {source_in}-{source_out}
우측 상단 주제: {topic}

[원본 자막]
{해당 구간 전체 자막}

[Stage 1 초벌 평론]
1줄: {stage1_line1}
2줄: {stage1_line2}

[외부 제안 평론]
외부 1줄:
외부 2줄:
수정 이유:
<!-- END_SEGMENT:C001 -->
```

송신본은 `commentary_review_packet_sent.md`, 회신본은
`commentary_review_packet_returned.md`로 분리한다. `external_review_gate.json`에
두 파일의 SHA-256, segment id 목록, immutable payload digest를 기록한다.
외부 검토 검증은 현재 송신본과 회신본만 서로 비교하지 않는다. Stage 1에서 만든
`commentary_review_packet_manifest.json`의 원본 송신 SHA-256, segment 순서,
immutable payload digest를 권위 기준으로 다시 대조한다. 세 파일을 함께 변조해도
PASS가 나와서는 안 된다.
외부 회신을 받으면 별도 `commentary_review_receipt.json`에
`review_origin=user_return|external_model`, 모델명, timezone 포함 ISO-8601 시각,
`recorded_by=user|external_adapter`, 발송 매니페스트 SHA-256, 회신 SHA-256,
raw response SHA-256을 기록한다. Stage 1의 발송 매니페스트에 이 값을 덧씌우지
않는다. 회신 수신기는 사용자 메시지 이벤트면 `authority_event_id=user_message:*`,
외부 모델 호출이면 `authority_event_id=adapter_call:*`을 기록하고, 수신기 전용
Ed25519 private key로 영수증 canonical JSON을 서명한다. 검증기는
`POLITICS_EXTERNAL_REVIEW_PUBLIC_KEY`의 공개키를 사용하되, 그 파일 SHA-256이
writer가 바꿀 수 없는 pipeline 상수 `EXTERNAL_REVIEW_PUBLIC_KEY_SHA256`에 pin된
지문과 정확히 일치할 때만 `authority_signature`를 확인한다. 운영 지문이 아직
설정되지 않았으면 `WAIT_EXTERNAL_REVIEW_AUTHORITY_KEY_PIN`으로 차단한다. 수신기
서명자는 전달받은 값을 그대로 서명하지 않고 append-only 사용자 메시지 또는
adapter 호출 저장소에서 `authority_event_id`를 다시 찾고 실제 raw response의
SHA-256을 독립 계산한 뒤 서명한다.
서명이 없거나 불일치하면 FAIL이며 writer 에이전트는 private key를 소유하지
않는다. `recorded_by=agent_self`는 항상 FAIL이다. 빈 외부 슬롯은 검토 PASS가
아니며, 에이전트가 직접 만든 문장을 `user_return`으로 표시하지 않는다. 화면 반영 문장은 각 줄
공백 제외 최대 15자이고 가운데점 `·`을 쓰지 않는다.

## Stage 2 — 편집 검토와 승인 설계

Stage 2는 원본 자막, Stage 1 초벌 평론, 외부 제안 평론을 비교한다. 각 구간에
다음 중 하나를 기록한다.

```text
decision: keep_stage1|accept_external|merge|rewrite
decision_reason: required
final_line1: required
final_line2: required
```

검토 기준:

1. 실제 발언과 일치하는가.
2. 앞뒤 맥락을 왜곡하지 않는가.
3. 1줄에서 2줄로 논리가 이어지는가.
4. 주어·쟁점·결과가 분명한가.
5. 근거 없는 단정, 반복, 모순, 상투어가 없는가.
6. 노출 시간 안에 읽을 수 있는가.

### 승인 무효화

외부 검토 후 source range, source id, transcript, timeline order/start/end,
topic이 바뀌면 기존 검토를 재사용하지 않는다. 즉시 다음으로 되돌린다.

```text
SOURCE_TRANSCRIPT_VERIFIED=WAIT
EXTERNAL_REVIEW_REFLECTED=WAIT
DESIGN_APPROVED=WAIT
```

새 송신본을 만들고 외부 검토를 다시 받아야 한다. 단순 맞춤법 수정만 immutable
payload를 바꾸지 않는다.

### 승인 산출물

```text
20_script/commentary_review_packet_returned.md
20_script/commentary_review_receipt.json
20_script/commentary_decisions.json
20_script/design_blueprint_approved.json
20_script/design_blueprint_approved.md
10_analysis/timeline_design_approved.json
90_reports/external_review_gate.json
```

조립 진입 조건:

```text
SOURCE_TRANSCRIPT_VERIFIED=PASS
EXTERNAL_REVIEW_REFLECTED=PASS
DESIGN_APPROVED=PASS
```

preassembly 검증은 모든 조립 호출에 강제되며 공개 우회 옵션이 없다. 승인 설계,
외부 검토 게이트, speech lock, locked EDL·라벨·클립 중 하나라도 실패하면 조립을
시작하지 않는다.

### 골 기능 실행 모드

사용자가 `골 기능으로`, `너무 세밀하다`, `언제 끝나`처럼 범위를 줄이면 선택적
패키징을 붙잡지 말고 실제 산출물 완성 경로로 즉시 전환한다.

1. 우선순위는 `native CapCut 폴더 생성 → root registry 등록 → 콘텐츠 무간격 →
   오디오 0 → JSON 미러 동일 → 미디어 존재`다.
2. 렌더·업로드가 범위 밖이면 썸네일, 설명, 해시태그, YouTube API 프로필 같은
   후속 메타데이터 누락으로 이미 통과한 CapCut 조립을 롤백하지 않는다.
3. 이때 조립은 `PASS_CORE_ASSEMBLY`, 후속 산출물은
   `DEFERRED_CORE_ASSEMBLY_ONLY`, `final_gate: BLOCKED`,
   `upload_ready: false`로 분리한다. 렌더·업로드 완료로 확대해석하지 않는다.
4. 보고는 결론과 프로젝트명부터 짧게 쓴다. 폴더 생성, registry 등록, GUI
   열림/미리보기, 렌더, 업로드는 서로 다른 상태로 한 줄씩만 명시한다.
5. false-positive 검사를 고치느라 승인 원문을 바꾸지 않는다. 승인 문구가 정상
   시청자 문장이라면 검사 범위를 내부 표식으로 좁힌다.

Windows Stage 2 조립의 경로 길이, 마이크로초 정규화, 핵심 검증 패턴은
`references/stage2-core-assembly.md`를 참고한다.

### 잠금된 Stage 1의 Stage 2 이행

Stage 1 잠금본이 현행 preassembly 계약에 실패하면 승인 원본을 직접 고치지 않는다.

1. `validate-stage1`, `validate-external`, `validate-preassembly`를 분리 실행하고
   실행 전후 `design_lock_manifest.json.required_files` 해시를 대조한다.
2. 검증 CLI가 보고서 JSON을 다시 쓸 수 있으면 원본이 아니라 임시 복사본에서
   실행한다.
3. 서명된 외부검토 메타데이터, 결정 필드, portable media path 같은 호환 차이는
   동기화 트리 밖의 disposable Stage 2 runtime copy에서만 정규화한다.
4. 각 locked clip은 기존 SHA-256과 실제 ffprobe를 다시 검증한다.
5. runtime 호환본을 원래 Stage 1 잠금 위로 복사하지 않는다.
6. 결과 보고에는 `source_stage1_mutated: false`, preassembly 결과, native project
   생성·등록, GUI·렌더·업로드 상태를 각각 남긴다.

상세 절차는 `references/locked-stage1-to-stage2-migration.md`를 참고한다.

## Stage 2 — speech lock과 locked clips

CapCut보다 먼저 다음을 만든다.

```text
10_analysis/speech_boundary_lock.json
10_analysis/roughcut_edl_locked.json
10_analysis/source_labels_locked.json
20_locked_clips/locked_clips_manifest.json
```

모든 파일의 `status=PASS`가 필요하다. 각 locked clip은 파일 존재, SHA-256,
ffprobe PASS, video/audio duration을 기록한다. 오디오는
`audio_duration_sec >= video_duration_sec - 0.25`여야 한다. 하나라도 실패하면
`WAIT_LOCKED_CLIPS` 또는 `FAIL_LOCKED_CLIPS`로 중단한다.
실제 `video_duration_sec`와 locked EDL의 `duration_sec` 차이도 `0.25`초
이하여야 한다.

`speech_boundary_lock.json`은 빈 PASS 파일이 아니다. 모든 locked clip의
`clip_id`, `source_id`, `source_in_sec`, `source_out_sec`를 순서대로 포함하고
`roughcut_edl_locked.json`의 SHA-256을 `roughcut_edl_sha256`으로 고정한다.

## Stage 2 — jungchilong 조립

1. archive와 manifest 경로를 해결한다.
2. archive SHA-256, 고정 루트 `jungchilong/`, 승격된 매니페스트에 pin된 파일 수,
   manifest `PASS_ARCHIVE_INTEGRITY`, 복원본 전 파일의 archive 대비 SHA-256
   일치를 확인한다. 현재 v3는 `promotion_state=READY`지만 실검증이 실패하면
   이 단계는 BLOCKED다.
3. `POLITICS_WRITER_MACHINE`과 승인 설계 소유권이 일치하는지 확인하고,
   active writer machine의 GUI 게이트를 검증한다. 게이트에는 `status=PASS`,
   `project=jungchilong`, `active_writer_machine`, `lock_owner`, archive SHA-256,
   template profile, `verified_by`, ISO-8601 `verified_at`, `capcut_version`,
   `gui_opened=true`, `timeline_visible=true`가 모두 필요하다.
   단, 사용자가 CapCut 눈검수를 직접 맡겠다고 명시하면 GUI 게이트는
   `status=DEFERRED_TO_USER`, `gui_opened=false`, `timeline_visible=false`,
   `user_review_pending=true`로 사실대로 기록할 수 있다. 이 경우 JSON 조립은
   진행할 수 있지만 사람의 시각 검증과 `upload_ready`는 계속 BLOCKED다.
4. CapCut이 완전히 종료됐는지 확인한다.
5. 로컬 `jungchilong`을 새 에피소드 프로젝트명으로 전체 복제한다.
6. 복제본의 root와 `Timelines/*` JSON 미러를 함께 패치한다.
7. `timeline_design_approved.json`과 locked clips만 화면 타임라인에 적용한다.
   `design_blueprint_approved.json`, `commentary_decisions.json`, 승인 timeline의
   구간·최종 문장·결정·flow가 정확히 같아야 한다.
8. 조립은 트랜잭션으로 처리한다. 레지스트리를 먼저 읽고 검증하며, 프로젝트
   rename 뒤 어떤 단계라도 실패하면 새 프로젝트 폴더를 제거하고
   `root_meta_info.json`을 원래 바이트로 원복한다.

### 화면 역할

역할을 track index가 아니라 텍스트·geometry·track type으로 찾는다.

```text
main video: intro video at 0, then locked clips in approved order
intro_text: 인트로 구간의 친근한 감상 포인트 2줄
source: 출처 {실제 채널명}
date: YYYY.MM.DD
flow/topic: `topic1 > topic2 > topic3`, 현재 항목만 노란색
source_caption/TTS: 실제 발화 cue에 맞춘 수정 가능한 한 줄 원본자막 (`TTS font size: 8.0`, 공백 제외 최대 20자)
lower line 1: `__LOWER_T1_A__`에 final_line1 (`lower commentary font size: 8.0`)
lower line 2: `__LOWER_T1_B__`에 final_line2 (`lower commentary font size: 8.0`)
lower commentary non-space characters: max 15 per line, 즉 공백 제외 최대 15자
subscribe: 구독은 큰 힘이 됩니다. (우측 상단)
fixed overlays/effects: jungchilong 근본의 배치와 리소스 보존
```

출처와 날짜는 소스 전환마다 나누고 해당 소스 구간 전체에 정확히 맞춘다.
내부 id, `roughcut`, `edl`, mojibake와 U+FFFD는 화면에 노출하지 않는다.
`진입` 같은 일반 한국어 단어를 전역 금칙어로 두지 않는다. 승인된 시청자 문구
`마지막 쟁점 진입`은 허용하고, 명백한 내부 workflow marker일 때만 차단한다.

### 오디오 계약

사용자가 나레이션·BGM·TTS·분리 오디오 수리를 명시하지 않은 기본값:

```text
source speech: embedded in video
audio_normalization_target: -14 LUFS
audio_track_count == 0
materials.audios == []
every main video segment volume == 1.0
every locked clip audio_duration_sec >= video_duration_sec - 0.25
```

별도 오디오를 만들지 않는다. 원본 음성과 별도 추출 음성을 동시에 사용해
중복 음성을 만들지 않는다. 기본값으로 locked clip의 임베디드 오디오를 통합
`-14 LUFS` 목표로 노멀라이즈한다. 최종 조립본의 전체 프로그램 loudness를 다시
측정하고 목표 오차가 검증기 허용범위 안일 때만
`AUDIO_LOUDNESS_NORMALIZATION=PASS`다. 단순히 CapCut 볼륨을 `1.0`으로 둔 것은
노멀라이즈 PASS 증거가 아니다.

### CapCut 검증

- canvas는 `1920x1080`이다. 썸네일 `1280x720` 규격과 혼동하지 않는다.
- main video first start는 0이며, 인트로 뒤 첫 locked clip은
  `content_start_sec`에서 시작하고 last end는 project duration과 일치한다.
- main video는 전체 구간에서 gap이 0이다. lower commentary는
  `content_start_sec`부터 project duration까지 gap이 0이다.
- `intro_text`는 0부터 `content_start_sec`까지 연속이며 그 뒤에는 남지 않는다.
- 각 평론 구간에는 `__LOWER_T1_A__`와 `__LOWER_T1_B__`에 대응하는 세그먼트가
  정확히 하나씩 있어야 하며 같은 시작·종료를 사용한다.
  `LOWER_COMMENTARY_ACTIVE_PAIR_COUNT=1`을 요구한다. 단일 합친 2줄 객체, 초벌안과
  최종안의 동시 노출, 추가 lower-like 트랙은 `FAIL_DUPLICATE_LOWER_COMMENTARY`다.
  Stage 1·외부안·폐기안은 보고서에만 남기고 CapCut에는 final_line1/2만 넣는다.
- `source_caption`/`TTS`는 승인 timeline의 cue별 문자열·시작·종료와 정확히 같고,
  하단 평론과 겹치지 않으며 글자 크기 `8.0`, 한 줄, 공백 제외 최대 20자여야 한다.
- 우측 상단 목차는 `topic1 > topic2 > topic3`처럼 ASCII ` > `를 표시하고
  대괄호를 화면에 노출하지 않는다. 숫자 접두사를 붙이지 않는다. 사용자가
  명시한 경우에만 예외다. 현재 주제의 전체 문자열은 노란색, 나머지는 흰색이다.
- 하단 평론 A/B는 글자 크기 `8.0`을 유지하고 각 줄은 공백 제외 최대 15자다.
- 최종 화면 텍스트 전체에서 가운데점 `·`이 0개인지 확인하고, 필요한 병렬
  표기는 `재건축,재개발이`처럼 공백 없는 쉼표로 입력한다.
- 동일 cue의 활성 `source_caption` 세그먼트는 한 번만 존재한다. 박힌 자막과
  이중 노출이 없어야 하며, frame QA에는 원본자막과 하단 평론이 함께 보이는
  프레임을 포함한다.
- `draft_content.json`, `template-2.tmp`, `Timelines/*` 미러는 논리적으로 동일하다.
- source/date/topic/lower text 수는 설계 데이터에 따라 가변이며 고정 6·38을
  요구하지 않는다.
- source/date/topic/lower/subscribe의 최종 문자열과 시작·종료 시간은 승인
  timeline과 정확히 같아야 한다. 개수와 간격만 맞는 다른 문장은 FAIL이다.
- ffprobe, 오디오·간격, 최소 3개 프레임과 contact sheet의 frame QA를 실행한다.
- 구조 검증 결과에 `LOWER_COMMENTARY_LAYOUT=PASS`가 있어야 한다.
- TTS cue 연결 원문 일치 결과는 `SOURCE_CAPTION_FIDELITY=PASS`여야 한다.
- 인트로 ffprobe·SHA·2 cue·무간격·본편 offset 결과는 모두 PASS여야 한다.
- 프로젝트 내부의 `*.bak`, `.before_*`, `before_*`, `*_backup_*`, helper 파일을
  정리한다. 백업은 outside the active CapCut draft tree에 둔다.
- 정리 실패는 `WAIT_PROJECT_CLEANUP` 또는 `FAIL_PROJECT_CLEANUP`이다.

### 조립 산출물

```text
50_capcut_project/assembly_blueprint.md
50_capcut_project/capcut_project_name.txt
50_capcut_project/local_capcut_path.txt
50_capcut_project/capcut_draft_manifest.json
50_capcut_project/draft_content_snapshot.json
50_capcut_project/draft_meta_info_snapshot.json
50_capcut_project/restore_notes.md
50_capcut_project/capcut_project_copy.md
90_reports/final_design_blueprint.md
20_script/upload_package_final.json
70_upload/upload_package.md
90_reports/final_output_gate.json
90_reports/final_gate.json
```

`final_design_blueprint.md`는 초벌안·외부안·최종 반영안, 실제 CapCut 배치,
설계 대비 변경, ffprobe·미러·오디오·frame QA·cleanup 결과를 함께 기록한다.

### 최종 3종 강제출력 계약

Stage 2 완료 보고 직전에는 다음 세 문서를 모두 새로 렌더하고 전문을 stdout에
순서대로 출력한 다음, 맨 끝에 CapCut 프로젝트 복사 푸터를 출력한다. 파일 경로만
보고하거나 하나라도 출력하지 않으면 완료가 아니다.

```text
설계도 경로: 90_reports/final_design_blueprint.md
조립도 경로: 50_capcut_project/assembly_blueprint.md
업로드 패키지 경로: 70_upload/upload_package.md
캣컷 복사 안내: 50_capcut_project/capcut_project_copy.md
```

설계도에는 승인 소스·게시일·우측 상단 주제·원본 구간·타임라인 구간·전체 원본
자막·Stage 1 초벌 평론·외부 제안·최종 2줄 평론을 포함한다. 조립도에는 실제
CapCut 프로젝트·트랙·영상 배치·출처·날짜·주제·전체 최종 평론·전체 원본 자막·
미러 해시·오디오·검증 상태를 포함한다. 업로드 패키지에는 썸네일 내용안내,
업로드 제목·설명·타임스탬프·출처 URL·해시태그·고정 댓글·작업 메모를 포함한다.
설계도와 조립도에는 인트로 2개 cue의 시간과 `final_intro_text` 전문도 포함한다.

다음 명령으로 세 문서를 렌더·검증하고 전문을 강제 출력한다.

```text
py -3 {TOOLS_ROOT}/politics_longform_final_output_harness.py --episode {episode_dir}
```

`90_reports/final_output_gate.json`에 다음 값이 모두 있어야 한다.

```text
FINAL_DESIGN_BLUEPRINT_OUTPUT=PASS
FINAL_ASSEMBLY_BLUEPRINT_OUTPUT=PASS
FINAL_UPLOAD_PACKAGE_OUTPUT=PASS
THUMBNAIL_COPY_OUTPUT=PASS
UPLOAD_COPY_OUTPUT=PASS
CAPCUT_PROJECT_COPY_OUTPUT=PASS
FINAL_OUTPUT_HARNESS=PASS
LOWER_COMMENTARY_VISUAL_SIZE=PASS
SOURCE_CAPTION_VISUAL_SIZE=PASS
TTS_CHAR_LIMIT=PASS
LOWER_COMMENTARY_CHAR_LIMIT=PASS
FLOW_TOPIC_HIGHLIGHT=PASS
INTRO_TEXT_OUTPUT=PASS
INTRO_MEDIA_FFPROBE=PASS
INTRO_MEDIA_SHA256=PASS
INTRO_TEXT_COVERAGE=PASS
OVERLAY_OFFSET=PASS
SOURCE_CAPTION_FIDELITY=PASS
AUDIO_LOUDNESS_NORMALIZATION=PASS
NO_FOREIGN_ABSOLUTE_PATHS=PASS
force_full_stdout=true
```

기본 `thumbnail.delivery=TEXT_GUIDE_ONLY` 모드에서
`THUMBNAIL_COPY_OUTPUT=PASS는 완전한 텍스트 설계안`이 존재하고 아래 형식 검증을
통과했다는 뜻이다. 이 모드에서는 실제 PNG 파일을 요구하지 않는다. 이미지 생성
또는 썸네일 적용 완료를 뜻하지도 않는다.

문서 누락, 빈 문서, 필수 clip/commentary/source-caption ID 누락, 업로드 필수
항목·출처 URL 누락, 해시 불일치,
CapCut 프로젝트명·휴대 가능한 로컬 경로 누락, 또는 전문 미출력은
`FAIL_FINAL_OUTPUT`이다. 이 상태에서는 완료라고 보고하지
않는다. 최종 사용자 보고에도 위의 `설계도 경로:`, `조립도 경로:`,
`업로드 패키지 경로:`를 반드시 각각 한 번 이상 표시한다.

## 업로드·썸네일 패키지

업로드 제목에는 Shorts `#shorts` 규칙을 적용하지 않는다. 내용에 실제 채널,
영상명, URL, 업로드일과 논리적인 타임스탬프 설명을 포함한다. 썸네일은
`1280x720`이며 실제 인물·쟁점을 사용하고 왜곡된 얼굴, 가짜 스캔들 이미지,
근거 없는 단정은 금지한다.

Stage 2의 기본 전달 방식은 `thumbnail.delivery=TEXT_GUIDE_ONLY`다. 사용자가
그대로 제작할 수 있는 썸네일 문구·인물·프레임·배치 지침을 텍스트로 제공하며
final-output harness는 실제 PNG 파일을 요구하지 않는다. 사용자가 YouTube Data
API 업로드를 명시한 경우에만 검증된 썸네일 파일을 별도 필수 입력으로 전환한다.

기본 채널 프로필 요청에는 다음을 사용할 수 있다.

```text
채널 이름: 민주 디코더
핸들: @minju_decoder_kr
설명 첫 줄: 정치 뉴스 뒤에 숨은 흐름을 민주진영의 시선으로 정리하는 채널입니다.
```

`20_script/upload_package_final.json`은 최종 문안 데이터이고,
`70_upload/upload_package.md`는 사용자가 그대로 읽고 복사하는 출력본이다.
출력본은 다음 슬롯을 순서대로 모두 채운다.

```text
[썸네일 내용안내]
- 1280x720 규격
- 상단 인물 3명 추천과 각 인물의 실제 프레임 출처
- 각 인물 하단 약 6글자 상황 표현
- 빨간 줄 후킹 1: 메인 쟁점 한 줄
- 하단 2줄 후킹 2: 검증할 정보와 맥락
- 글자색·외곽선·배경 처리
- 왜곡 인물, 가짜 표정·인용, 미확인 범죄 단정 금지

[업로드 내용]
- 최종 제목
- 설명문 전문
- 00:00부터 시작하는 타임스탬프
- 실제 채널·게시일·영상명·URL 출처
- 해시태그 (#shorts 제외)
- 고정 댓글
- 업로드 작업 메모
```

최종 사용자 보고에는 업로드 패키지 경로만 적지 말고
`[썸네일 내용안내]`와 `[업로드 내용]` 전문을 다시 출력한다. 사용자는 이 본문을
보고 썸네일 제작과 YouTube 업로드 입력을 수행한다. 문안 패키지 PASS는 실제
업로드 완료나 `upload_ready=true`를 뜻하지 않는다.

### YouTube Data API 비공개 업로드

현재 작업에서 사용자가 API 업로드를 명시한 경우에만 실행한다. API key만으로는
업로드하지 않으며 현재 PC의 OAuth 채널 프로필을 사용한다. 기본 프로필은
`minju_decoder`, 예상 채널은 `민주 디코더`다. 자격증명과 token은
`%LOCALAPPDATA%\CodexYouTube` 아래에만 두고 스킬·OneDrive에 저장하지 않는다.
PC마다 최초 1회 OAuth 인증이 필요하며 token을 PC 간 동기화하지 않는다.

업로드 기본값은 `privacyStatus=private`, `selfDeclaredMadeForKids=false`,
`containsSyntheticMedia=true`다. 최종 제목·설명·검증된 썸네일 파일을 사용한다.
썸네일 파일이 없으면 업로드를 시작하지 않는다. `channels.list(mine=true)`의
채널 ID/이름이 기대값과 다르면 중단하고 다른 token으로 fallback하지 않는다.
공개 전환은 별도 사용자 지시 없이는 금지한다.

API 실행기는 활성 작업공간의 `tools/youtube_profile_upload.py`를 우선 사용한다.
정치롱폼 호출에는 `--thumbnail {verified_thumbnail_path} --require-thumbnail`을
함께 전달한다. 범용 호출에서 썸네일을 생략할 수 있어도 정치롱폼 계약에서는
생략할 수 없다.
매 실행 시작 시 상태 파일을 `PREFLIGHT`와 전 게이트 `NOT RUN`으로 원자 초기화해
이전 업로드의 PASS를 승계하지 않는다. 입력·metadata·썸네일 사전검사 실패는
`preflight_status=FAIL`로 기록하고 원격 검증 실패로 오분류하지 않는다. 채널 확인
직후 insert 요청 전에 `API_UPLOADING`을 먼저 기록하며, insert 생성 또는 첫 chunk
실패는 반드시 `API_UPLOAD=FAIL`로 매핑한다.
도구가 없거나 OAuth 프로필이 확인되지 않으면 `API_UPLOAD=NOT RUN`으로 남기고
업로드를 흉내 내지 않는다. 쓰기 요청의 아동용 필드는
`status.selfDeclaredMadeForKids=false`이며 `madeForKids`를 쓰기 필드로 보내지 않는다.

```text
OAUTH_PROFILE_RESOLVED=NOT RUN|PASS|FAIL
EXPECTED_CHANNEL_MATCH=NOT RUN|PASS|FAIL
API_UPLOAD=NOT RUN|PASS|FAIL
THUMBNAIL_SET=NOT RUN|PASS|FAIL
REMOTE_METADATA_VERIFY=NOT RUN|PASS|FAIL
api_upload_status=NOT_RUN|UPLOADED_PRIVATE|FAIL
```

업로드 뒤 privacy, `selfDeclaredMadeForKids=false`, AI 사용 표시(공식 API가
노출하는 범위), 제목, 설명을 원격 재조회하고 썸네일 set 응답의 items를 확인한
뒤 video ID와 URL을 보고한다. 제목·설명·아동용 아님·썸네일 중 하나라도 확인되지
않으면 `REMOTE_METADATA_VERIFY=FAIL`이다. `upload_ready`와
실제 `api_upload_status`는 별개다. API 실행 시 `[API 업로드 결과]` 전문을 출력한
뒤에만 절대 마지막 CapCut 프로젝트 복사 푸터를 출력한다.

그 뒤, 최종 응답의 절대 마지막에는 다음 블록을 출력한다. 이 블록 뒤에는 상태,
설명, 인사말을 포함해 어떤 텍스트도 추가하지 않는다. 실제 프로젝트 폴더를 다른
위치로 복제하는 명령이 아니라, 사용자가 복사 버튼으로 가져갈 프로젝트명과
휴대 가능한 로컬 경로를 제공한다.

````text
## 캣컷 프로젝트 파일 복사하기

프로젝트 파일명:

```text
{project_name}
```

프로젝트 폴더:

```text
%LOCALAPPDATA%\CapCut\User Data\Projects\com.lveditor.draft\{project_name}
```
````

## 최종 게이트

다음 상태를 분리한다.

```text
STAGE1_DRAFT=PASS
EXTERNAL_REVIEW=PASS
DESIGN_APPROVED=PASS
LOCKED_CLIPS=PASS
CAPCUT_ASSEMBLY=PASS
LOWER_COMMENTARY_LAYOUT=PASS
LOWER_COMMENTARY_VISUAL_SIZE=PASS
SOURCE_CAPTION_VISUAL_SIZE=PASS
TTS_CHAR_LIMIT=PASS
LOWER_COMMENTARY_CHAR_LIMIT=PASS
FLOW_TOPIC_HIGHLIGHT=PASS
INTRO_TEXT_OUTPUT=PASS
INTRO_MEDIA_FFPROBE=PASS
INTRO_MEDIA_SHA256=PASS
INTRO_TEXT_COVERAGE=PASS
OVERLAY_OFFSET=PASS
SOURCE_CAPTION_FIDELITY=PASS
AUDIO_LOUDNESS_NORMALIZATION=PASS
NO_FOREIGN_ABSOLUTE_PATHS=PASS
CAPCUT_META_DURATION=PASS
FINAL_DESIGN=PASS
FINAL_DESIGN_BLUEPRINT_OUTPUT=PASS
FINAL_ASSEMBLY_BLUEPRINT_OUTPUT=PASS
FINAL_UPLOAD_PACKAGE_OUTPUT=PASS
THUMBNAIL_COPY_OUTPUT=PASS
UPLOAD_COPY_OUTPUT=PASS
CAPCUT_PROJECT_COPY_OUTPUT=PASS
FINAL_OUTPUT_HARNESS=PASS
force_full_stdout=true
upload_ready=false|true
OAUTH_PROFILE_RESOLVED=NOT RUN|PASS|FAIL
EXPECTED_CHANNEL_MATCH=NOT RUN|PASS|FAIL
API_UPLOAD=NOT RUN|PASS|FAIL
THUMBNAIL_SET=NOT RUN|PASS|FAIL
REMOTE_METADATA_VERIFY=NOT RUN|PASS|FAIL
```

하나의 PASS가 다음 PASS를 자동으로 뜻하지 않는다. source reuse 권리 또는
fair-use 판단, GUI 확인, 렌더와 업로드 패키지가 남아 있으면
`upload_ready=false`다. harness나 n8n을 실행하지 않았으면 `NOT RUN`으로
보고한다.

## Policy

민주진영 정치 평론은 허용되지만 실제 출처와 발언 맥락을 보존한다. 하단 2줄
평론은 사실과 의견을 구분하고 원본 자막으로 뒷받침한다. 검증하지 않은 주장,
가짜 인용, 명예훼손성 단정, 확인되지 않은 범죄 사실을 추가하지 않는다.

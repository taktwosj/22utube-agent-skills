---
name: 111-politics-longform
description: Use when the user says 111정치롱폼, 정치롱폼, 정치미드폼, 민주진영 유튜브, 매불쇼 롱폼, 유시민 롱폼, or asks to design, review, assemble, validate, or package a Korean political longform video, lower two-line commentary, 1-3 derived political Shorts, 45-70 second source candidates, jungchilong CapCut project, upload copy, API upload, or thumbnail hooks.
---

# 111 Politics Longform

## Shared Gate Router

`workflow.yaml`이 정치롱폼과 파생 정치 쇼츠의 G00~G90 단일 라우터다.
현재 gate의 계약만 `references/gates/`에서 읽고
`scripts/validate_stage_gate.py`로 검증한다. 자동 진행 판단은
`scripts/workflow_runner.py`가 결정론적 로컬 단계에 한해서만 수행한다.

```text
owner: 111-politics-longform
gates: G00 G10 G20 G30 G40 G50 G60 G60.USER G70 G80 G90
content_profile: politics_longform | politics_derived_short
production_mode: source_led | narrated
main_root: jungchilong_base_v3_intro15
derived_short_root: SHRTJUNGCHI
cross_lane_handoff: FORBIDDEN
auto_external_llm_calls: 0
max_auto_retries: 0
```

기존의 동일 대화 2회 검수, 사용자 교정 SRT, clean assembly hard-fail,
근본 프로젝트 계약은 새 라우터에서도 그대로 적용된다. 정적 G60 PASS는
`WAIT_USER_VISUAL_GATE`이며 사용자 시각 승인으로 간주하지 않는다.

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

CapCut GUI 열림, 타임라인 표시, CapCut 프로세스 종료 여부는 자동 확인하지
않는다. 사용자가 프로젝트 문제를 알린 경우에만 해당 문제를 진단한다.
새 근본 승격은 별도 staging 사본에서 수행한다. `.bak`, 임시 파일, orphan
media, 외부 사용자 경로를 제거하고 인트로를
`Resources/media`에 내장한 다음 root·`template-2.tmp`·`Timelines/*` 미러를
일치시킨다. `INTRO_MEDIA_FFPROBE=PASS`, `INTRO_MEDIA_SHA256=PASS`,
`INTRO_TEXT_COVERAGE=PASS`, `OVERLAY_OFFSET=PASS`,
`NO_FOREIGN_ABSOLUTE_PATHS=PASS`, 복구 validator PASS가 모두 확인된 새 ZIP과
매니페스트가 확인되어야 `jungchilong_base_v3_intro15`로 승격한다. 파일 수·ZIP
SHA는 승격 결과를 매니페스트와 코드에 함께 pin하며 이전 37개 값을 재사용하지
않는다.

## 파생 정치 쇼츠 계약

정치 롱폼 파생 쇼츠의 CapCut 근본은 `SHRTJUNGCHI`다.
`jungchilong_base_v3_intro15`는 롱폼 근본이며 쇼츠 근본이 아니다.
일반 `shrt white`를 정치 롱폼 파생 쇼츠의 근본으로 사용하지 않는다.

```text
root_project: SHRTJUNGCHI
restore_target: %LOCALAPPDATA%\CapCut\User Data\Projects\com.lveditor.draft\SHRTJUNGCHI
canvas: 1080x1920
default_duration: 60~100초
target_shorts_count=3
valid_shorts_count=0~3
editorial_arc: 갈등 → 분석 → 결론
purpose: longform_entry_point
```

Stage 1에서 롱폼과 같은 원본·맥락을 유지한 채 최대 3개를 함께 설계한다.
약한 후보를 숫자 맞추기로 승인하지 않는다. 0개면
`SKIPPED_NO_VALID_CANDIDATE`를 명시적으로 승인한다. 승인된 후보마다 다음 파일을
만들고, 최종 권위인 `design_lock_manifest.json`에 해시로 고정한다.

```text
20_script/shorts/SHxx/edit_plan_approved.json
20_script/design_lock_manifest.json
approved_short_ids
longform_entry_point
```

`edit_plan_approved.json`은 원본 범위와 경계, 편집 순서, 훅, T1/T2, 화자 색상,
자막 줄바꿈, 제목·설명과 롱폼 진입 지점을 확정한다. Stage 2는 SHRTJUNGCHI를 승인된 쇼츠마다 복제해
조립하고, `approved_short_ids`에 없는 후보는 만들지 않는다. Stage 2에서 구간 재선정, 순서 변경, 훅·자막 축약,
제목·설명 재작성 또는 새 쇼츠 추가를 하지 않는다.

현재 active writer machine에서 실제 `SHRTJUNGCHI` 폴더와 레지스트리 연결을
다시 확인한다. 오래된 `root_meta_info.json` 기록만으로 존재를 주장하지 않는다.
근본 무결성, CapCut 화면, 하네스는 서로 다른 게이트이며 실행하지 않은 항목은
`NOT RUN`이다. 근본 폴더가 없거나 무결성을 검증할 수 없으면
`WAIT_SHRTJUNGCHI_ROOT_REQUIRED`로 중단한다. 이때 `shrt white`, jungchilong,
과거 파생 프로젝트 또는 JSON 스냅샷으로 대체 조립하지 않는다.

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
03 jungchilong 로컬 근본 검증    NOT RUN/PASS/FAIL
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

### 미드롱폼 채널 게이트

트렌드헌터 미드롱폼 탭이나 자동 탐색으로 원본 후보를 고를 때는 먼저
`references/midlongform-channel-policy.md`를 읽고 고정된 허용 채널 24개와
블랙리스트 1개를 적용한다. 채널 이름이 아니라 YouTube 채널 ID를 우선 대조한다.
블랙리스트가 허용 목록보다 우선하며 `MBC 라디오 시사`는 자동 후보와 원본
소스에서 제외한다.

허용 목록에 없는 채널은 자동 채택하지 않고 `WAIT_CHANNEL_NOT_ALLOWLISTED`로
보고한다. 사용자가 특정 URL을 직접 원본으로 지정한 경우에만 명시적 예외로
검토할 수 있으며, 이때도 출처·맥락·권리 게이트를 그대로 적용한다. 채널 허용은
`rights/fair-use=PASS`, 사실 검증 PASS 또는 제작 승인을 뜻하지 않는다.

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
- 하단 두 줄은 화면 배치를 위한 형식일 뿐, 1줄과 2줄에 고정된 의미 역할을
  부여하지 않는다. 두 줄 전체가 하나의 자연스러운 생각으로 읽히게 나누며,
  같은 뜻을 두 번 반복하지 않는다.
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

### 사용자 최종 교정 SRT 잠금

사용자가 직접 교정한 SRT 또는 구체적인 교정 목록을 주고 최종 반영을 지시하면
`references/final-corrected-subtitle-lock.md`를 읽는다. 이때 사용자 교정본은
이전 자동자막, 생성 자막, 초벌 SRT보다 우선하는 최종 권위다.

교정본을 `30_audio_srt`에 복사하고 SHA-256으로 고정한 뒤 다음 검증기를 실행한다.

```text
py -3 scripts/validate_final_corrected_srt.py ^
  --srt {final_corrected_srt} ^
  --corrections-json {corrections_json} ^
  --expected-cue-count {cue_count}
```

`USER_CORRECTED_SRT_LOCK=PASS` 전에는 CapCut 최종 자막을 만들지 않는다. 검증 후
본문·줄바꿈·문장부호·cue 순서를 다시 자동 교정하거나 축약하지 않는다.
`[콧방귀]`, `[웃음]`, `>>`처럼 사용자가 제거한 표기와 결론부
`정리하겠습니다` 연속 반복이 되살아나면 FAIL이다. 두 줄 자막은 편집 가능한
두 텍스트 트랙에 같은 시작·종료로 배치하고, cue별로 다시 합친 결과가 교정 SRT와
정확히 같아야 `FINAL_CORRECTED_CAPTION_FIDELITY=PASS`다.
사용자 교정본이 없는 에피소드에서는 이 전용 게이트들을 `NOT_APPLICABLE`로
기록하고 기존 `SOURCE_CAPTION_FIDELITY` 계약을 적용한다.

### CapCut 화면 텍스트 입력 규칙

- 사용자 교정본과 원본 발화 자막의 가운데점 `·`, 띄어쓰기, 고유명사와 문장부호는
  그대로 보존한다. 예: `수사·기소`, `재건축·재개발`.
- 가운데점 때문에 실제 렌더에서 글자가 잘리는 것이 확인된 경우에만 사용자에게
  알리고 해당 비자막 템플릿 문구를 수정한다. 사용자 교정 자막을 쉼표로 되돌리지
  않는다.

## ChatGPT 마스터 원고 2회 검수

정치평론가 마스터 원고를 만들거나 `commentary_master_script_draft.md`가 입력에
있으면 다음 두 계약을 먼저 읽는다.

```text
references/chatgpt_project_router_instruction.md
references/chatgpt_politics_longform_review_contract.md
```

마스터 원고와 하단 2줄 외부 검토는 별도 게이트다.

```text
MASTER_COMMENTARY_REVIEW_GATE: 마스터 원고의 ChatGPT 2회 검수
EXTERNAL_LOWER_COMMENTARY_GATE: 시간순 하단 2줄 외부 검토
```

`MASTER_COMMENTARY_REVIEW_GATE`는
`20_script/master_commentary_review/` 아래의 독립 파일만 사용한다. 기본 계약은
사람이 읽는 세 문서와 Codex 결정표를 하나의 내부 해시 매니페스트로 묶는 방식이다.

```text
round1_returned.md
round1_codex_decisions.json
round2_returned.md
round2_repair_returned.md  # 필요한 경우만
review_manifest.json       # 자동화 계층 전용
master_commentary_review_gate.json
```

과거 9파일 packet/manifest/receipt 체계는 기존 에피소드 검증용으로만 호환한다.
새 작업에서는 검수자에게 packet ID, SHA-256, manifest, receipt를 작성시키지 않는다.

Round 1은 `INDEPENDENT_REVIEW`와 `REVISION_PROPOSAL`을 수행한다. 외부 응답은
JSON이나 YAML이 아니라 사람이 읽는 마크다운으로 받는다. 기본 입력은 마스터
원고, fact map, 조사 자료이며 직접 인용·날짜·숫자·법원·수사·범죄 관련 검증에
필요한 원문과 출처만 조건부로 추가한다. Round 1은 총평, 중심 명제, 블록별 진단,
강한 문장·약한 문장 최대 5개, 정치적 균형, 근거 부족 목록, 번호가 붙은
문장·블록 단위 수정안을 포함한다. 원고 전문을 다시 쓰지 않는다.

Codex는 각 외부 제안을 내부 `suggestion_id`로 연결하고 `ADOPTED`,
`PARTIALLY_ADOPTED`, `REJECTED`, `PENDING_EVIDENCE` 중 exactly one 결정과
이유를 기록한다. 제안을 반영한 뒤 Round 2를 반드시 Round 1과 같은 ChatGPT
conversation에서 이어서 수행한다. packet ID, 해시, manifest, receipt와
conversation ID는 자동화 계층에서만 관리하고 ChatGPT에 반환하도록 요구하지
않는다.
근거 검증은 품질 검수를 대체하지 않으며, 차분하지만 단호한 구어체·구체적인
인물과 행동·자연스러운 문장 리듬을 함께 검수한다.

Round 2에는 Round 1 검수 결과, 제안별 결정표, 수정 원고, 수정 fact map, 변경
요약과 짧은 핵심 질문·블록 순서를 보낸다. timeline JSON 전문이나 내부 HTML
앵커를 ChatGPT 프롬프트에 노출하지 않는다. Round 2는 `EVIDENCE_AUDIT`와
`FLOW_CONTINUITY_AUDIT`를 분리해 수행하고 오탈자·띄어쓰기·고유명사·분리 자모·
U+FFFD·`<<`·`<d>` 같은 편집 잔여 기호를 `문자 품질 감사`로 검사한다. 이 검사는
시청자에게 보이거나 들리는 문장에 적용하며 URL·JSON·해시·내부 ID는 제외한다.
Round 2는 수정된 원고를 전면 재작성하지 않고 남은 문제와 위치만 반환한다.

외부 반환 상태는 두 회차 모두 `PENDING_CODEX_REVIEW`다.
`PASS_RECOMMENDED`는 외부 권고일 뿐 사용자 승인이나 최종 승인 파일이 아니다.
`REVISE_REQUIRED`, `EVIDENCE_REQUIRED`, 흐름 FAIL, 남은 blocker,
`PENDING_EVIDENCE`가 있으면 `WAIT_CHATGPT_REVIEW_REPAIR`로 중단한다.

검증 명령:

```powershell
python scripts/validate_chatgpt_two_pass_review.py --review-dir "{episode}\20_script\master_commentary_review"
```

`MASTER_COMMENTARY_REVIEW_GATE=PASS`와 사용자의 명시적 원고 승인이 모두 있기
전에는 `commentary_master_script_approved.md`를 만들지 않는다. 하단 2줄용
`commentary_review_packet_sent.md`와 관련 manifest, receipt, gate 파일은
`EXTERNAL_LOWER_COMMENTARY_GATE` 전용이며 마스터 원고 검수에 재사용하지 않는다.

## 정치 롱폼 파생 숏폼 후보

승인된 정치 롱폼에서 파생 숏폼을 요청하면 다음 계약을 읽는다.

```text
references/chatgpt_project_router_instruction.md
references/chatgpt_politics_shortform_review_contract.md
```

`111-politics-longform`이 먼저 약 45~70초의 연속 원본 구간을 1~3개 선별한다.
후보는 하나의 `source_id`와 연속 `segment_id`만 사용한다. 원문 타임코드,
첫 3초 원본 발화, 핵심 인용, 앞뒤 맥락, fact map 근거를 함께 기록한다.
유효 후보가 적으면 3개를 강제로 채우지 않는다.

후보 산출물:

```text
20_script/politics_shortform/politics_shortform_candidates.md
```

후보 선별 단계에서는 상단, timed 중단, TTS 문안, 우라까이, 원본 순서 변경,
여러 구간 재조립을 만들지 않는다. Codex와 사용자가 후보 범위를 선택한 뒤에만
`00-tikitaka`가 쇼츠 설계를 시작한다. Tikitaka가 원본 범위를 바꿔야 하면
`DESIGN_REOPEN_REQUIRED`로 이 단계에 반환한다.

기존 `20_script/shorts/SH01~SH03`이 있어도 최신 승인 원고보다 오래됐거나
제목·훅·평론이 최신 fact map과 충돌하면 승인 상태를 재사용하지 않는다.
후보·쇼츠 문구를 바꾸면 Stage 1 승인과 해시를 다시 만든다.

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
않는다. 기본 스키마는 `politics-external-review-hash-receipt-v1`이며 개인키나
공개키를 요구하지 않는다. 검증기는 Stage 1 발송 매니페스트, 현재 회신 파일,
영수증에 기록된 SHA-256을 서로 대조한다. `authority_event_id`는 사용자 메시지면
`user_message:*`, 외부 모델 호출이면 `adapter_call:*`을 기록한다. 기존 Ed25519
영수증은 과거 에피소드 호환용으로만 검증한다.
`recorded_by=agent_self`는 항상 FAIL이다. 빈 외부 슬롯은 검토 PASS가
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
3. 두 줄 전체가 하나의 자연스러운 생각으로 이어지는가.
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
4. 보고는 결론과 프로젝트명부터 짧게 쓴다. 폴더 생성, registry 등록, 렌더,
   업로드는 서로 다른 상태로 한 줄씩만 명시한다.
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
   생성·등록, 렌더·업로드 상태를 각각 남긴다.

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

### CLEAN_ASSEMBLY_HARNESS

조립을 시작하기 전에 `50_capcut_project/assembly_contract.json`을 만든다.
이 파일에는 Source of Truth, Acceptance Criteria, Validation, Evidence와 함께
모든 입력의 `PRODUCTION`·`REFERENCE_ONLY`·`TEMPLATE_ONLY` 역할,
`expected_timeline_order`, `forbidden_project_inputs`, `allowed_visible_text`,
경로·SHA-256·시간·위치·화면 역할을 고정한다. 빌드·검증 직전과 컨텍스트 압축
또는 작업 재개 직후에는 이 계약 파일을 다시 읽는다.

`REFERENCE_ONLY` 콘텐츠 유입, 폐기된 프로젝트 계보 사용, 순서·해시 불일치,
중복 material ID, 외부 online/request ID, 승인되지 않은 화면 텍스트는
`STRUCTURAL_CONTAMINATION_REQUIRES_CLEAN_REBUILD`다. 오염된 파생 프로젝트를
부분 패치하지 않고 실패한 대상 빌드만 폐기한 뒤 고정 근본
`jungchilong_base_v3_intro15`에서 다시 조립한다.

정적 JSON 하네스가 통과해도 CapCut을 자동으로 열거나 화면 PASS를 주장하지
않는다. 사용자가 제공한 화면 또는 사용자가 알린 문제로 검증하기 전에는
`WAIT_USER_VISUAL_GATE`다. 전체 계약과 hard-fail 목록은
`references/clean-assembly-harness.md`를 따른다.

1. archive와 manifest 경로를 해결한다.
2. archive SHA-256, 고정 루트 `jungchilong/`, 승격된 매니페스트에 pin된 파일 수,
   manifest `PASS_ARCHIVE_INTEGRITY`, 복원본 전 파일의 archive 대비 SHA-256
   일치를 확인한다. 현재 v3는 `promotion_state=READY`지만 실검증이 실패하면
   이 단계는 BLOCKED다.
3. `POLITICS_WRITER_MACHINE`과 승인 설계 소유권이 일치하는지 확인한다.
4. 로컬 `jungchilong`을 새 에피소드 프로젝트명으로 전체 복제한다.
5. 복제본의 root와 `Timelines/*` JSON 미러를 함께 패치한다.
6. `timeline_design_approved.json`과 locked clips만 화면 타임라인에 적용한다.
   `design_blueprint_approved.json`, `commentary_decisions.json`, 승인 timeline의
   구간·최종 문장·결정·flow가 정확히 같아야 한다.
7. 사용자 교정 SRT가 있으면 `USER_CORRECTED_SRT_LOCK=PASS`와 해당 SHA-256을
   확인하고, 교정본만 편집 가능한 최종 자막으로 배치한다.
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
- 사용자 최종 교정 SRT의 가운데점 `·`과 문장부호가 CapCut 자막에서도 그대로
  유지되는지 확인한다. 전역 치환으로 `수사·기소`를 `수사,기소`로 되돌리지 않는다.
- 동일 cue의 활성 `source_caption` 세그먼트는 한 번만 존재한다. 박힌 자막과
  이중 노출이 없어야 하며, frame QA에는 원본자막과 하단 평론이 함께 보이는
  프레임을 포함한다.
- 사용자 교정 SRT가 있으면 두 자막 트랙을 시간순으로 재구성해 cue 수·줄바꿈·
  본문·시작·종료를 대조하고 `FINAL_CORRECTED_CAPTION_FIDELITY=PASS`를 요구한다.
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
USER_CORRECTED_SRT_LOCK=NOT_APPLICABLE|PASS
USER_CORRECTED_SRT_SHA256=NOT_APPLICABLE|PASS
USER_CORRECTION_RULES=NOT_APPLICABLE|PASS
FINAL_CORRECTED_CAPTION_FIDELITY=NOT_APPLICABLE|PASS
CLEAN_ASSEMBLY_HARNESS=PASS
VISUAL_GATE=WAIT_USER_VISUAL_GATE|PASS
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
USER_CORRECTED_SRT_LOCK=NOT_APPLICABLE|PASS
USER_CORRECTED_SRT_SHA256=NOT_APPLICABLE|PASS
USER_CORRECTION_RULES=NOT_APPLICABLE|PASS
FINAL_CORRECTED_CAPTION_FIDELITY=NOT_APPLICABLE|PASS
CLEAN_ASSEMBLY_HARNESS=PASS
VISUAL_GATE=WAIT_USER_VISUAL_GATE|PASS
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
fair-use 판단, 렌더와 업로드 패키지가 남아 있으면
`upload_ready=false`다. harness나 n8n을 실행하지 않았으면 `NOT RUN`으로
보고한다.

## Policy

민주진영 정치 평론은 허용되지만 실제 출처와 발언 맥락을 보존한다. 하단 2줄
평론은 사실과 의견을 구분하고 원본 자막으로 뒷받침한다. 검증하지 않은 주장,
가짜 인용, 명예훼손성 단정, 확인되지 않은 범죄 사실을 추가하지 않는다.

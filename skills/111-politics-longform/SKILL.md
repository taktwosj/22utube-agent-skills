---
name: 111-politics-longform
description: Use when the user says 111정치롱폼, 정치롱폼, 민주진영 유튜브, 매불쇼 롱폼, 유시민 롱폼, or asks to make/update a Korean political longform CapCut draft, T1 chapter text, YouTube upload package, channel profile, keywords, or thumbnail hooks for a 민주진영 political commentary channel.
---

# 111 Politics Longform

## Core Rule

Use the user's locked political longform root:

```text
Default CapCut base: jungchilong
Automatic fallback: forbidden
Route: keep the setup, replace only the source video/media unless the user says otherwise.
Source label: derive from the actual source channel/date, not from the template name.
```

Never modify `jungchilong` in place. Validate it, copy the whole project to a
new episode draft, and patch only the copy. Do not automatically fall back to
YP007, YP005, YM007, YSM, or a generated derivative. Use another base only when
the user explicitly names it in the current request.

Do not rebuild the style from scratch. Preserve the `jungchilong` template feel:
top source label, top subscribe line, lower T1 explanation lane, 1280x720
political commentary layout, and source-audio longform flow.

For YouTube sources, download or secure the production source as FHD/1080-first
when available. Use `width<=1920 AND height<=1920` so both `1920x1080`
landscape and `1080x1920` vertical source clips are accepted. Lower-resolution
media is allowed only for preview/proxy fallback, blocked downloads, or explicit
user requests; do not treat a proxy as the authoritative production source.

`jungchilong` is the clean visual skeleton and the only default Stage 2 base.
Older YP007, YP005, YM007, and YSM projects are reference-only unless the user
explicitly names one for the current job; their presence never changes the
default base.
Use `출처 매불쇼` only when the actual source channel is Maebulshow. For every
other source, use the real source channel and date from `source_manifest.json`,
`source_labels.json`, or the source metadata. If the user explicitly names a
different base template or promotes another political longform draft, use that
base and preserve the same source-label rules.

## 정치 롱폼 공통 제작 계약

기존 공통 운영 스킬을 호출하거나 설치하지 않는다. 정치 롱폼에 필요한
공통 장편 운영 규칙은 이 스킬이 직접 소유한다. 별도 브레인스토밍 스킬도
필수 의존하지 않고, 아래 시작 브리프를 이 스킬 안에서 작성한다.

### 작업 루트와 소유권

```text
active_root: ${env:WORKSPACE_ROOT}\22factory_20260628
politics_lane: 02_politics_longform\episodes\{episode_id}
legacy_root: ${env:UTUBE_ROOT} (reference-only)
canvas: 1280x720
capcut_mode: local_only
onedrive_role: lightweight archive and handoff metadata
raw_capcut_sync: false
```

작업 시작 전에 active root의 `AGENTS.md`와
`docs\YOUTUBE_PRODUCTION_WORK_ORDER.md`를 읽는다. OneDrive에는 원본 CapCut
프로젝트 폴더·캐시·대형 렌더를 복사하지 않고, 매니페스트·스냅샷·검증보고서와
업로드 메타데이터만 보관한다. 한 에피소드에는 active writer machine 하나만
허용한다.

`${env:WORKSPACE_ROOT}`와 `${env:UTUBE_ROOT}`는 portable placeholders다.
현재 프로세스에 값이 있다는 가정으로 명령을 실행하지 않는다. 열린 workspace
또는 OneDrive 위치에서 active factory root를 찾고 `AGENTS.md`와
`docs\YOUTUBE_PRODUCTION_WORK_ORDER.md`가 모두 존재하는지 확인한다. 해결할 수
없으면 `WAIT_FACTORY_ROOT_NOT_RESOLVED`로 중단한다.

### 시작 브리프와 진행판

생산 명령을 받으면 파일을 수정하기 전에 다음 브리프를 먼저 만든다. 이
브리프는 별도 `000brainstorm` 스킬을 호출하지 않고 이 스킬이 직접 관리한다.

```text
정치 롱폼 시작 브리프
- 사용자 의도:
- 실제 출처/채널/업로드일:
- 에피소드 경로:
- 선택 템플릿: jungchilong / 사용자 명시 예외
- Stage 1 또는 Stage 2:
- 결과물: 소스 패키지 / CapCut / 업로드 패키지
- 음성·자막·T1 정책:
- 현재 막힌 게이트:
- 다음 액션:
```

진행판은 실제 실행 증거만 반영한다. n8n을 쓰지 않은 로컬 작업은 `WAIT -
local run; n8n not invoked`로 기록하고, 실행하지 않은 하네스는 `NOT RUN`으로
기록한다.

```text
[정치 롱폼 진행판]
A. 실행
01 소스 확보             WAIT/RUNNING/PASS
02 소스·출처 검증        WAIT/RUNNING/PASS
03 speech boundary lock  WAIT/RUNNING/PASS
04 locked clips          WAIT/RUNNING/PASS
05 jungchilong CapCut 조립 WAIT/RUNNING/PASS
06 업로드·썸네일 패키지   WAIT/RUNNING/PASS

B. 검증
01 ffprobe                NOT RUN/PASS/FAIL
02 CapCut JSON 미러       NOT RUN/PASS/FAIL
03 오디오·간격 검증       NOT RUN/PASS/FAIL
04 프레임·시각 검증(frame QA) NOT RUN/PASS/FAIL
05 프로젝트 정리         NOT RUN/PASS/FAIL
06 최종 게이트           BLOCKED until all required evidence exists
```

### Stage 경계

Stage 1은 소스 조사·확보 단계로 끝낸다. Stage 1에서는 소스 매니페스트,
후보 `roughcut_edl.json`, 후보 `source_labels.json`, 후보 `topic_flow.json`,
ffprobe 보고서와 핸드오프 상태만 만든다. Stage 1에서는 CapCut draft, locked
clips, `speech_boundary_lock.json`, `roughcut_edl_locked.json`,
`source_labels_locked.json`, export 또는 `upload_ready`를 만들거나 주장하지
않는다.

Stage 2는 Stage 1의 source video가 로컬에 실제 존재할 때만 시작한다. Stage 2가
소스 재검증, speech-boundary lock, locked clips, `jungchilong` 검증·복사,
CapCut 조립, JSON 미러 패치, 오디오·간격·프레임 검증, 업로드 문구와 썸네일
훅을 소유한다.

### 장편 CapCut·검증 기본값

- 캔버스는 1280x720이다.
- 원본 발언 오디오는 메인 영상에 내장된 상태를 유지한다.
- 사용자가 별도 나레이션·BGM·TTS·오디오 수리를 요청하지 않으면 별도 오디오
  트랙을 만들지 않는다.
- root `draft_content.json`과 `template-2.tmp`, `Timelines/*` 미러를 함께
  패치하고, 세그먼트 수·첫 시작·마지막 종료·gap_count를 확인한다.
- CapCut이 열려 있거나 백그라운드 프로세스가 남아 있으면 기존 draft를
  덮어쓰지 않고 완전 종료 후 새 프로젝트 또는 재개 절차를 사용한다.
- `ffprobe`, JSON 미러 확인, 오디오/간격 확인, 최소 3개 프레임과 contact
  sheet 확인, 프로젝트 임시파일 정리가 끝나기 전에는 `PASS`, `FINAL`,
  `upload_ready`를 쓰지 않는다.
- 필요한 백업은 outside the active CapCut draft tree에 저장한다. 최종 응답 전
  활성 draft 내부의 `*.bak`, `.before_*`, `before_*`, `*_backup_*`와 임시
  helper 파일을 확인하고 제거한다. 정리할 수 없으면
  `WAIT_PROJECT_CLEANUP` 또는 `FAIL_PROJECT_CLEANUP`으로 중단한다.
- 출처 재사용 권리 또는 fair-use 판단이 확인되지 않으면 업로드 준비 완료를
  주장하지 않는다.

### 공유 도구의 대체 규칙

n8n은 선택적 상태판이며 파일 편집의 전제조건이 아니다. 로컬로 실행할 때는
n8n 상태를 `WAIT`로 남긴다. 하네스가 없거나 실행하지 않았으면 결과를
`NOT RUN`으로 보고한다. 이 계약의 실제 정치 롱폼 내용과 템플릿 규칙은 아래
`Core Rule`, `Workflow`, `Upload Package`, `Thumbnail Package`가 단일 권한이다.

## Entry Modes

Recognize two entry modes, but keep the finishing process identical:

```text
1. Codex-build mode: Codex starts from topic/source URLs and builds the source
   package, roughcut, T1, CapCut draft, harness evidence, and upload package.
2. External-rough finishing mode: Claude, GLM, or another agent provides a
   rough package, handoff, roughcut, source labels, T1 draft, or topic flow.
   Treat that package as input to verify and finish, not as already-final work.
```

In Codex-build mode, Codex owns source discovery from approved reference
channels, transcript/range verification, source downloading, clip ordering,
roughcut creation, CapCut draft creation, T1, source labels, thumbnail prompt,
and upload package.

In external-rough finishing mode, Claude/GLM may do the first pass: issue scan,
candidate videos, timestamp ranges, rough chapter flow, and first-cut notes.
Codex still owns final verification and production: re-check sources, use only
approved reference channels when the user says so, rebuild or normalize clips,
set the final order, patch the CapCut JSON mirrors, verify audio/video, and
produce the final upload package.

In both modes, final work means the same checklist: read the source package,
verify source identity, split visible source labels by transition, insert or
repair lower T1, preserve the topic-flow strap, patch root and `Timelines/*`
CapCut JSON mirrors, run the harness gates, and prepare the upload package.

## Default CapCut Base Contract

Treat this CapCut draft as the only default/root project for political longform
Stage 2:

```text
%LOCALAPPDATA%\CapCut\User Data\Projects\com.lveditor.draft\jungchilong
```

Never modify `jungchilong` in place. Before every Stage 2 copy, run the bundled
read-only validator from the skill directory:

```powershell
python scripts/validate_clean_base.py --base "$env:LOCALAPPDATA/CapCut/User Data/Projects/com.lveditor.draft/jungchilong"
```

If the folder is missing, stop with `WAIT_JUNGCHILONG_BASE_MISSING`. If the
validator detects old episode media, real source labels, backup files,
`onlineMaterial` contamination, or Korean mojibake, stop with
`FAIL_JUNGCHILONG_DIRTY_BASE`. Do not repair the locked root while building an
episode. Do not automatically fall back to YP007, YP005, YM007, YSM, or a
generated derivative.

After validation passes, copy the whole `jungchilong` project to a new episode
draft name and patch only that copy.

Required project JSON/files to read, copy, and patch:

```text
{base}\draft_content.json
{base}\template-2.tmp
{base}\draft_meta_info.json
{base}\Timelines\*\draft_content.json
{base}\Timelines\*\template-2.tmp
```

Support files that should usually be preserved from the base unless the user asks to redesign the template:

```text
{base}\draft_settings
{base}\timeline_layout.json
{base}\attachment_pc_common.json
{base}\attachment_editing.json
{base}\draft_virtual_store.json
{base}\Resources\...
{base}\common_attachment\...
```

Detect `jungchilong` tracks and materials by role, not by a historical hard-coded
track index:

```text
main video: replace with the current locked clips in the locked EDL order
visual/effect/sticker tracks: preserve geometry, render order, timing pattern, and valid base assets
t5: fixed subscribe line, full duration
t4: lower T1 explanatory chapter lane
t3: viewer-facing topic-flow strap
t2: source upload date only, `YYYY.MM.DD`
t1: source channel only, `출처 {채널명}`
```

Preserve every valid non-source visual, banner, sticker, transition, and effect
already present in the clean `jungchilong` base. Do not fabricate YP007-only
filter tracks or fixed overlays when `jungchilong` does not contain those roles.
Patch a visual asset path only when the copied base or the current episode
manifest actually references that asset, and fail on unknown old media paths.

Keep source audio embedded in each main video segment. Preserve loudness
normalization, `QualityEnhance`, and clip-level edit effects when those roles
exist in the clean base. Do not invent missing effects merely to imitate an
older template.

For source attribution, keep t1 and t2 as separate visible lanes. Never merge
the date into t1, and never show a template channel such as `출처 매불쇼` unless
the actual source channel is Maebulshow.

When creating a new political longform draft, copy the whole `jungchilong`
project folder to a new project name first, then patch all root and
`Timelines/*` JSON mirrors. When finishing a Claude/GLM rough package, use a
provided draft only if the handoff explicitly names it; otherwise start from a
fresh validated `jungchilong` copy. Keep `draft_content.json` and
`template-2.tmp` byte-logically equivalent for timeline content after edits.
If CapCut is open, expect stale UI until CapCut is fully restarted.

## Workflow

1. Resolve the episode and CapCut draft.
   - CapCut root usually lives under `%LOCALAPPDATA%\CapCut\User Data\Projects\com.lveditor.draft`.
   - For new source evidence, prefer `22factory_20260628\02_politics_longform\episodes\{episode_id}`.
   - Use `22utube\11utube\yellow\episodes\...` only as a legacy read-only fallback or explicit repair source.
   - For external-rough finishing mode, first read `handoff_to_codex.md`, `source_manifest.json`, `source_labels.json`, `edit\roughcut_edl.json`, `text\lower_t1_draft.json`, `decisions\topic_flow.json`, `upload_description_draft.md`, and `report.md` when present.
   - Also read `edit\segment_markers_hq.srt`, `source\M1\source.ko.srt`, `analysis\srt_items.json`, `upload_description.md`, and existing CapCut draft metadata when present.

2. Keep CapCut visible text roles separate.
   - t1 source channel: actual source channel only, `출처 {채널명}`.
   - t2 upload date: actual source upload date only, `YYYY.MM.DD`.
   - t3 flow strap: viewer-facing video composition/chapter sequence.
   - t4 lower T1: chapter-by-chapter explanatory commentary.
   - t5 subscribe line: keep exactly `구독과 좋아요는 큰힘이 됩니다. 감사합니다.` unless asked.
   - If the source is actually Maebulshow, use `출처 매불쇼` in t1. Never apply `출처 매불쇼` globally because a legacy reference project contained that label.
   - Never show internal ids such as `M1-1`, `M1-2`, `roughcut`, `edl`, or `진입`.
   - Source channel/date labels must be long enough to read at the front of
     each source section. Do not leave one global source label; split t1 and t2
     at every source-video transition and stretch each label exactly across its
     source segment.
   - Keep the upper/lower banner colors and geometry from `jungchilong`: dark blue banner backing,
     white source/T1 text, black stroke, and yellow highlight only on the
     current flow topic.

3. Keep source audio embedded unless explicitly requested otherwise.
   - If source videos already contain speech, do not extract audio and do not
     add a separate audio track; this creates doubled voices.
   - Expected final project state: `audio_track_count == 0`,
     `materials.audios == []`, and main video segment `volume` stays audible
     (`1.0` unless the user asks for a change).
   - A separate audio track is allowed only when the user explicitly asks for
     narration, BGM, TTS, or detached audio repair.

### Mixed Source Standard

For mixed-source political longform drafts, do not use one continuous label such as
`출처 JTV뉴스 외`. Split the top source track at every source-video transition and
show t1/t2 separately:

```text
t1: 출처 {채널명}
t2: YYYY.MM.DD
```

Use the video's `release_timestamp` when available, otherwise use `timestamp`, and
render only the calendar date in KST. Do not render hour/minute in the visible
source date. Keep detailed URLs and timestamps in the upload description and
final report.

For the current Jung Chung-rae source-mix layout, preserve the visible flow strap:

```text
사퇴 요구와 책임론 배경 -> 정청래 직접 사퇴 발언 ->
연임 도전 해설 -> 이재명 정부 성공 프레임 ->
다음 당권 조건
```

The flow strap may show the full sequence, but only the topic that applies to the
current source-video segment should be yellow. Non-current topics should be
white or otherwise visually de-emphasized. Do not make the whole strap yellow for
every segment.

When the user asks for the current corrected visual standard, split the main video
by source transitions and preserve the finishing roles actually present in the
validated `jungchilong` copy:

```text
source video material: current locked clip for the exact EDL range
audio: embedded source speech, one audible stream, no duplicate audio track
base visual roles: preserve every valid banner, sticker, transition, and effect
source/date roles: split t1/t2 at every source transition
flow role: keep the full sequence and highlight only the active topic
unknown or old media paths: zero
```

Do this per source video/range unit or per chapter block, not as one blind global
adjustment over the whole project. Do not create an effect or overlay that is not
present in the clean base or current episode manifest.

4. Write lower T1 from the actual speech.
   - Start at `00:00`; do not leave the opening empty.
   - Maintain continuous flow through the full roughcut unless the user asks for sparse notes.
   - For a 15:00 cut, target about 35-40 lower T1 segments; a validated 15-minute reference uses 38.
   - For a 20:30 cut, target about 40-50 lower T1 segments, not 8-18.
   - Use `챕터1_`, `챕터2_`, `챕터3_` labels that match viewer-facing topic sections.
   - Each item should be 1-2 lines: first line summarizes what the speaker is saying, second line adds concise interpretation/opinion.
   - Be concrete: name the actor, claim, issue, or consequence. Avoid abstract filler such as `민심을 챙겨야 합니다`, `정치가 중요합니다`, or generic advice.
   - Positive opinion is allowed, but keep it tied to the exact claim: `이 분석은 구조를 보게 만든다`, `이 지점은 민주당이 아프게 들어야 한다`.

5. Chapter mapping examples.
   - `00:00` chapter 1: 유시민 등장, 사전투표, 선거 토론의 판 세팅.
   - `02:20` chapter 2: 선거 의미, 내란 청산, 이재명 정부 동력, 보수/극우 제도화 분석.
   - `07:46` chapter 3: 민주당, 조국혁신당, 범민주 진보 진영, 포용력과 대선 후보군.
   - `14:16` chapter 4: 내부 경쟁의 폭력성, 당원 압박, 투표 전략과 민주당 지도부 책임.

For the Jung Chung-rae 30m flow example, use this kind of 5-part political flow
when the issue naturally supports it:

```text
사퇴·연임 -> 당심·여론 -> 정통성 행보 -> 당내 리스크 -> 당권 선택
```

Only the active part should be yellow in the flow strap. The other parts stay
white/de-emphasized.

6. CapCut JSON update rules.
   - Back up `draft_content.json` and `template-2.tmp` before edits, outside the active CapCut draft tree.
   - Patch both project root files and matching `Timelines/*/draft_content.json`, `Timelines/*/template-2.tmp` cache files.
   - Use UTF-8 Python IO. Avoid PowerShell inline Korean strings for JSON writes; store Korean text in UTF-8 JSON or patch via `apply_patch`.
   - After writing, verify segment count, first start time, last end time, gap count, and forbidden terms.
   - Before the final response, verify the active draft contains no `*.bak`, `.before_*`, `before_*`, `*_backup_*`, or temporary helper files. Use `WAIT_PROJECT_CLEANUP` or `FAIL_PROJECT_CLEANUP` when cleanup cannot be completed.

Verification pattern:

```text
lower T1 segment count: 40-50 for 20m
lower T1 segment count: 35-40 for 15m
t1 source channel segments: split by source-video transition, no date text
t2 upload date segments: split by source-video transition, `YYYY.MM.DD`
t3 flow strap segments: split by chapter/flow transition
t4 lower T1 segments: continuous chapter commentary
t5 subscribe segments: fixed subscribe line, full duration
base visual roles: every valid `jungchilong` banner/sticker/effect role is preserved
fabricated YP-style tracks: zero
unknown or previous-episode media paths: zero
source video materials: only current locked clips and approved episode assets
audio: exactly one audible embedded source stream per main segment
first_start: 0.00
last_end: roughcut end
gap_count: 0 unless intentionally sparse
forbidden visible terms: M1-, roughcut, edl, 진입
mojibake scan: use the project's Korean Encoding Constitution patterns, including common CP949 mojibake and Unicode replacement character U+FFFD
```

If CapCut is open or background processes remain, tell the user to fully close CapCut before reopening the draft.

## Upload Package

For longform upload text, do not apply Shorts `#shorts` title rules.

Use this structure:

```text
제목
{person/source issue hook}｜{viewer reason to click}

내용
출처 {실제 채널명} YYYY.MM.DD

{one-paragraph summary of what this edit explains}

00:00 {topic line with a logical one-sentence explanation}
02:20 {topic line with a logical one-sentence explanation}
07:46 {topic line with a logical one-sentence explanation}
14:16 {topic line with a logical one-sentence explanation}

출처
- 원본 채널:
- 원본 영상:
- 원본 URL:
- 원본 업로드일:

{3-5 hashtags}
```

Timestamp lines must not be bare labels. Write what the section argues and why it matters.

## Text Background Defaults

For `jungchilong` political longform text boxes, preserve the clean black backing
and geometry from the validated base instead of leaving text floating directly
on video.

CapCut text background defaults:

```text
background: on
background color: black
opacity: 100%
rounded rectangle: 30%
height: 14%
width: 14%
```

Use this on short visible reaction, subscribe, or source-support text when
readability matters over busy footage. Keep the box tight around the text; do
not create a large full-screen panel or cover the subject's face. If a source
label already sits on the fixed top blue banner or lower T1 already sits on the
fixed lower blue banner, do not add a second black backing unless the footage
makes the text unreadable.

## Channel Setup

If the user asks to convert a channel to 민주진영 political YouTube, use this baseline:

```text
채널 이름: 민주 디코더
핸들: @minju_decoder_kr
설명 첫 줄: 정치 뉴스 뒤에 숨은 흐름을 민주진영의 시선으로 정리하는 채널입니다.
```

Keyword baseline:

```text
민주당, 이재명, 유시민, 매불쇼, 민주진영, 정치해설, 시사해설, 검찰개혁, 언론개혁, 내란청산, 국민의힘, 조국혁신당, 범민주, 진보진영, 정치뉴스, 한국정치, 선거분석, 여론분석, 국회, 대통령, 윤석열, 김어준, 뉴스공장, 정치비평, 진보유튜브, 민주당유튜브, 정치유튜브, 시사유튜브
```

## Thumbnail Package

When asked for a thumbnail prompt, provide:

```text
강한훅 1줄
{urgent political hook}

다음훅 2줄
{specific person or issue}
{specific conflict or warning}

이미지 프롬프트
1280x720 YouTube political commentary thumbnail...
```

Rules:
- Hook must be concrete, not generic.
- Use the actual person/issue: `유시민`, `이재명`, `민주당`, `내란 청산`, `폭력적 방식`, `적신호`.
- Avoid fake claims, caricature, flames, or distorted faces.
- If source is a real show frame, keep the thumbnail as political commentary, not impersonation.

Default political longform thumbnail layout:

```text
1280x720 Korean political YouTube thumbnail, bold 3-person split-screen layout.

Top image area:
- Place three political/broadcast figures in three vertical panels: left, center, right.
- Use realistic broadcast screenshot style from the actual video whenever possible.
- Add one short reaction caption near each person's face.
- Reaction captions: bold white Korean text, thick black outline.

Middle red emphasis bar:
- Full-width bright red horizontal banner.
- Large bold white Korean text with thick black outline.
- Use the strongest factual conflict phrase from the video.

Bottom black hook area:
- Black background.
- Line 1: huge neon green Korean hook text, with one critical emphasis word in red when useful.
- Line 2: huge white Korean explanatory hook.
- The bottom two lines must explain why the viewer should click, not merely repeat a title.

Negative:
no distorted faces, no caricature, no flames, no fake scandal imagery,
no unreadable Korean text, no random English, no extra people, no blurry text.
```

Example for a Kim Sang-wook / Ulsan tram issue:

```text
Left caption: 할말이 없네요...
Center caption: "협박으로 들린다"
Right caption: 왜 다 민영입니까?

Red bar: '트램 재검토' 업무보고서 터진 정면충돌
Bottom line 1: "그게 상식입니까?" 김상욱 회의장 폭발
Bottom line 2: 예타·민영화·공론화 두고 공무원 보고에 반박
```

## Policy

Political content is allowed as commentary, but keep source attribution visible and description-level EDSA context clear. Do not claim upload-ready/final if source reuse rights or fair-use judgment has not been checked.

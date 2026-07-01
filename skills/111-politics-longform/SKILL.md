---
name: 111-politics-longform
description: Use when the user says 111정치롱폼, 정치롱폼, 정치롱폼1단계, 정치롱폼2단계, 정치롱폼 대화형, Claude 초벌, 캣컵전단계, 민주진영 유튜브, 매불쇼 롱폼, 유시민 롱폼, or asks to make/update a Korean political longform source-download package, CapCut draft, T1 chapter text, YouTube upload package, channel profile, keywords, or thumbnail hooks for a 민주진영 political commentary channel.
---

# 111 Politics Longform

## 22factory Active Root Override - 2026-06-29

For new political longform work, read:

```text
${env:WORKSPACE_ROOT}\22factory_20260628\AGENTS.md
```

New political longform episode outputs and source-evidence files must be created
under:

```text
22factory_20260628\02_politics_longform\episodes\PL_YYYYMMDD_slug
```

Legacy `22utube\11utube\yellow\episodes` folders are read-only reference or
explicit repair targets unless the user asks for legacy work. Shared yellow
assets may still be read from `$env:UTUBE_ROOT\yellow\assets\...`. The editable
CapCut draft remains under the local `com.lveditor.draft` directory; OneDrive
stores metadata, manifests, snapshots, reports, exports, and upload packages.

Skill sync surfaces: runtime `$HOME\.codex\skills\111-politics-longform`;
shared source `${env:WORKSPACE_ROOT}\codex_skills_source\111-politics-longform`.
Ignore old `11utube\codex_skills_source` or `skills_sync` paths unless present.

## Core Rule

Use the user's political longform setup by priority:

```text
Default CapCut base priority 1: YP007_jungchungrae_30m_flow_rcut
Fallback production base: YP005_sajeontupyu_issues_15m_final_rcut
Legacy style ancestor/fallback: YM007_maebulshow_yusimin_20m_rcut
Route: keep the setup, replace only the source video/media unless the user says otherwise.
Source label: derive from the actual source channel/date, not from the template name.
```

Do not rebuild the style from scratch. Preserve the template feel: top source label, top subscribe line, lower T1 explanation lane, 1280x720 political commentary layout, and source-audio longform flow.

For YouTube sources, download or secure the production source as FHD/1080-first
when available. Use `width<=1920 AND height<=1920` so both `1920x1080`
landscape and `1080x1920` vertical source clips are accepted. Lower-resolution
media is allowed only for preview/proxy fallback, blocked downloads, or explicit
user requests; do not treat a proxy as the authoritative production source.

YP007 is the current preferred political longform visual template. YP005 is the
fallback production base. YM007 is a legacy style/template ancestor and
emergency fallback, not a source identity rule.
Use `출처 매불쇼` only when the actual source channel is Maebulshow. For every
other source, use the real source channel and date from `source_manifest.json`,
`source_labels.json`, or the source metadata. If the user explicitly names a
different base template or promotes another political longform draft, use that
base and preserve the same source-label rules.

## Execution Stages

Use the same factory episode folder for both stages:
`22factory_20260628\02_politics_longform\episodes\PL_YYYYMMDD_slug`.

`정치롱폼1단계` / `politics-longform-stage1` means source intake through video download only. It may find topics, source URLs, candidate ranges, and rough flow, but it must stop before speech-boundary lock, locked clips, CapCut, export, or upload-ready claims.

Stage 1 required outputs: `episode_manifest.json`,
`00_source\source_manifest.json`, `00_source\{video_id}\source_full.mp4`,
candidate `10_analysis\roughcut_edl.json`, candidate
`10_analysis\source_labels.json`, `10_analysis\topic_flow.json` using
`A > B > C`, optional `20_script\lower_t1_draft.json`,
`90_reports\stage1_handoff_to_codex.md`, and `90_reports\stage1_status.json`
with `PASS_SOURCE_DOWNLOADED` or `WAIT_DOWNLOAD`.

If download is blocked, Stage 1 must output exact source URLs, desired formats,
and `WAIT_DOWNLOAD`; do not fabricate local media.

`정치롱폼2단계` / `politics-longform-stage2` means Codex finalization. It reads
Stage 1, verifies source identity, creates `speech_boundary_lock.json`,
`roughcut_edl_locked.json`, `source_labels_locked.json`, cuts `*_locked.mp4`,
copies YP007, patches root and `Timelines/*` CapCut JSON mirrors, validates,
then prepares upload text and thumbnail hooks.

Stage 2 input gate: if `source_full.mp4` is missing for any used source, return to Stage 1. Never build final CapCut from Stage 1 rough media or candidate EDL.

Claude/GLM/other agents may produce Stage 1. Codex owns Stage 2 unless the user
explicitly says otherwise.

## Interactive Stage 2 Handoff Mode

Use this mode when the user says `대화형`, `Claude 초벌`, `캣컵전단계`,
`인수`, `올려`, or asks what to tell Claude/Codex after another agent made the
rough package.

Do not jump from a Claude rough package straight to a final CapCut claim.
Treat the rough package as untrusted input and run a short conversation loop:

```text
1. INTAKE_SUMMARY:
   - episode folder
   - roughcut/video path
   - sources found or missing
   - available files
   - missing files that block Stage 2

2. ONE_BLOCKING_QUESTION:
   Ask at most one question when the answer is required before file edits.
   If the missing fact can be inferred from local files, inspect files instead
   of asking.

3. USER_CONFIRM:
   When the user says "진행", "올려", "가자", "그걸로", or equivalent,
   proceed with Stage 2 only if source_full media and lock inputs are present.

4. STAGE2_ACTION:
   Verify source identity, lock speech boundaries, create locked clips, copy
   YP007, patch CapCut root plus Timelines mirrors, validate, then report.
```

If the user only wants a prompt for Claude, output a copyable instruction that
forces Claude to produce Stage 1 handoff files only. Claude must not report
CapCut final, upload-ready, or production PASS unless the user explicitly made
Claude the Stage 2 owner.

Claude Stage 1 handoff must include:

```text
90_reports/stage1_handoff_to_codex.md
90_reports/stage1_status.json
00_source/source_manifest.json
10_analysis/roughcut_edl.json
10_analysis/source_labels.json
10_analysis/topic_flow.json
20_script/lower_t1_draft.json when available
roughcut video path or candidate cut paths
missing/blocker list
```

Codex Stage 2 must not use candidate `roughcut_edl.json` as final. It must
create or verify `speech_boundary_lock.json`, `roughcut_edl_locked.json`,
`source_labels_locked.json`, and locked media before creating the final CapCut
draft.

## Hard Gates Before CapCut

Speech boundary lock: treat `roughcut_edl.json`, `source_labels.json`, and
downloaded `SEG*.mp4` files as candidate-only. Do not create or patch a final
CapCut draft if `cut_fix: pending`, `speech_boundary_adjust`, download notes,
missing `speech_boundary_lock.json`, missing `roughcut_edl_locked.json`, missing
`source_labels_locked.json`, missing locked clips, or missing ffprobe PASS
evidence remains. Required order: verify transcript/SRT -> write
`10_analysis\speech_boundary_lock.json` with rough/locked start/end and reason
-> cut locked clips -> build CapCut only from locked EDL/media. If only rough
clips exist, report `WAIT`.

YP007 flow strap style lock: `flow_strap` is not controlled by font size alone.
Locate it by role (`track.name == "flow_strap"` or reference text), not hard-coded
index. Clone the YP007 text clip/material style, transform, scale, size, font,
stroke/background, render order, and full text-box geometry; change only visible
text, per-segment range, and active-topic color. Verify active topic is yellow
and inactive topics are de-emphasized for every segment.

Open CapCut safety: if CapCut is open or background processes remain, do not
overwrite an existing target draft folder. Build a clean new project name or
wait for full close/restart, then patch root and `Timelines/*` mirrors.

## Default CapCut Base Priority

Treat this CapCut draft as the canonical default/first-choice base for the
political longform style:

```text
%LOCALAPPDATA%\CapCut\User Data\Projects\com.lveditor.draft\YP007_jungchungrae_30m_flow_rcut
```

In CapCut this base may appear as `정치롱폼기본` through
`draft_meta_info.json`. Treat the folder name `YP007_jungchungrae_30m_flow_rcut`
and the visible name `정치롱폼기본` as the same canonical base.

Use YP005 only if YP007 is unavailable, broken, or the user explicitly asks for
the older 사전투표 baseline. Do not fall back to `YM007_*`, `YM008_*`, or newly
generated derivatives unless YP007 and YP005 are unavailable or the user
explicitly promotes/names another base. `YP007_jungchungrae_30m_flow_rcut` is a
visual/style template, not a mandatory source/channel label.

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

Known YP007 track/material roles:

```text
tracks[0] video: main source video cut track. Split by source/range unit; replace media path/duration with the new roughcut or rebuilt cut sequence.
tracks[1] filter: the three saved YP007 filter/effect materials (`크림`, `배경 터치업`, `보정`). Randomly/distributively place these by source-video or clip segment; do not collapse to one global filter. Clone or patch filter material values to 30-55 (`0.30`-`0.55` in JSON); 100 is too strong for this format.
tracks[2] video/photo: image1, full-frame transparent emphasis overlay `focus_lines_transparent_1920x1080.png`. Preserve and stretch to project duration.
tracks[3] video/photo: image2, lower blue banner `politics_lower_blue_banner_1312x92.png`. Preserve and stretch to project duration.
tracks[4] video/photo: image3, top blue banner `politics_top_blue_banner_1314x68.png`. Preserve and stretch to project duration.
tracks[5] text: t5 fixed subscribe line, exactly `구독과 좋아요는 큰힘이 됩니다. 감사합니다.` unless the user explicitly changes it.
tracks[6] text: t4 lower T1 explanatory chapter lane. Replace with new `챕터N_` commentary and stretch continuously.
tracks[7] text: t3 video composition/topic-flow strap. Preserve the sequence structure and update/highlight per current source segment.
tracks[8] text: t2 source upload date only, formatted `YYYY.MM.DD`.
tracks[9] text: t1 source channel name only, formatted `출처 {채널명}`. Do not include the upload date here.
materials.texts[t5 range]: subscribe line material.
materials.texts[t4 range]: lower T1 materials.
materials.texts[t3 range]: topic-flow strap materials.
materials.texts[t2 range]: source upload-date materials.
materials.texts[t1 range]: visible source-channel materials.
```

YP007 has one filter track and three fixed image/video overlay tracks. Do not
drop or overwrite these when replacing the main video. Prefer role detection
over hard-coded track indexes if a future template changes the order.

For YP007, source attribution is split across two visible lanes: t1 is channel
name, t2 is upload date. Never merge the date into t1, and never show a
template channel such as `출처 매불쇼` unless the actual source channel is
Maebulshow.

Every main video segment must keep the YP007 finishing stack: source audio
embedded in the video, loudness normalization enabled, quality enhancement HD
preserved through the source video material's `QualityEnhance` algorithm, and
the clip-level `smart_color_adjust`, `sharpen`, `clear`, and `particle` edit
effects. For each source video/clip, randomize the visible strength values in
the 30-50 range (`0.30`-`0.50` in JSON) so repeated segments are not identical.
The filter-track materials (`크림`, `배경 터치업`, `보정`) must also be kept in the
30-55 range (`0.30`-`0.55` in JSON), not the template default `1.0`/100.

Shared OneDrive visual assets for YP007-style political longform:

```text
$env:UTUBE_ROOT\yellow\assets\politics_longform_template\focus_lines_transparent_1920x1080.png
$env:UTUBE_ROOT\yellow\assets\politics_longform_template\politics_lower_blue_banner_1312x92.png
$env:UTUBE_ROOT\yellow\assets\politics_longform_template\politics_top_blue_banner_1314x68.png
$env:UTUBE_ROOT\yellow\assets\politics_longform_template\asset_manifest.json
```

When a copied CapCut draft still points to `D:\Downloads\...` for these PNGs,
patch the media material paths to the OneDrive shared paths above. Keep the
transparent focus-line overlay as a full-frame emphasis layer, and keep the
upper/lower blue banner PNGs behind the corresponding text lanes.

When creating a new political longform draft, copy the whole YP007 project
folder to a new project name first, then patch all root and `Timelines/*` JSON
mirrors. When finishing a Claude/GLM rough package, use the provided draft only
if the handoff explicitly names it; otherwise copy YP007 and apply the rough
package into that copy. Keep `draft_content.json` and `template-2.tmp`
byte-logically equivalent for timeline content after edits. If CapCut is open,
expect stale UI until CapCut is fully restarted.

For lower T1 reference text only, YP005/YM007 may contain these operator files:

```text
{base}\bottom_topic_comments_v4.json
{base}\t1_topic_texts.json
```

Use them as examples of density and format, not as content for a new video.

## Workflow

1. Resolve the episode and CapCut draft.
   - CapCut root usually lives under `%LOCALAPPDATA%\CapCut\User Data\Projects\com.lveditor.draft`.
   - For new source evidence, prefer the factory episode folder under `22factory_20260628\02_politics_longform\episodes\PL_YYYYMMDD_slug`.
   - Use `22utube\11utube\yellow\episodes\...` only as legacy reference or explicit repair target.
   - For external-rough finishing mode, first read `handoff_to_codex.md`, `source_manifest.json`, `source_labels.json`, `edit\roughcut_edl.json`, `text\lower_t1_draft.json`, `decisions\topic_flow.json`, `upload_description_draft.md`, and `report.md` when present.
   - Also read `edit\segment_markers_hq.srt`, `source\M1\source.ko.srt`, `analysis\srt_items.json`, `upload_description.md`, and existing CapCut draft metadata when present.

2. Keep CapCut visible text roles separate.
   - t1 source channel: actual source channel only, `출처 {채널명}`.
   - t2 upload date: actual source upload date only, `YYYY.MM.DD`.
   - t3 flow strap: viewer-facing video composition/chapter sequence.
   - t4 lower T1: chapter-by-chapter explanatory commentary.
   - t5 subscribe line: keep exactly `구독과 좋아요는 큰힘이 됩니다. 감사합니다.` unless asked.
   - If the source is actually Maebulshow, use `출처 매불쇼` in t1. Never apply `출처 매불쇼` globally just because the YP005/YM007 template was used.
   - Never show internal ids such as `M1-1`, `M1-2`, `roughcut`, `edl`, or `진입`.
   - Source channel/date labels must be long enough to read at the front of
     each source section. Do not leave one global source label; split t1 and t2
     at every source-video transition and stretch each label exactly across its
     source segment.
   - Keep the upper/lower banner colors from YP007: dark blue banner backing,
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

### Supertone TTS / Narration Exception

Political longform normally preserves source speech, not generated narration.
If the user explicitly asks for TTS, narration audio, voice generation, or a
separate voice track, use the shared Supertone route:

```powershell
py -3.14 "${env:WORKSPACE_ROOT}\22factory_20260628\00_asset_tools\tools\make_supertone_tts.py" "<대본 텍스트>" "<출력파일.wav>"
```

Rules:

- Read only `SUPERTONE_API_KEY`, `SUPERTONE_VOICE_ID`, `SUPERTONE_PITCH`,
  `SUPERTONE_SPEED`, and `SUPERTONE_MODEL`; never paste, print, store, or
  serialize the API key.
- On `home_windows`, User-scope Supertone variables may exist even if the
  current Codex process environment is stale. The shared script reads Windows
  User environment as a fallback.
- Use `py -3.14`; do not assume bare `python` has the Supertone SDK.
- Current home_windows default is the Chunsik Supertone setup through
  `SUPERTONE_VOICE_ID` and `sona_speech_1`.
- If Supertone env or SDK is unavailable, stop at
  `WAIT_SUPERTONE_ENV_OR_SDK_MISSING`; do not switch to Edge TTS, ElevenLabs,
  browser TTS, Kokoro, or another provider without explicit user approval.
- Keep generated voice as a separate, clearly named audio asset and update
  CapCut root plus `Timelines/*` mirrors if it is inserted.

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
by source transitions and keep the full YP007 finishing stack:

```text
source video material: QualityEnhance / HD fixed
audio: loudness normalize enabled on every main source segment
filter track: randomly distribute the three saved YP007 filter materials
filter strength: cloned/patched filter materials randomized 30-55 per source video/clip
adjustment: smart/auto adjust randomized 30-50 per source video/clip
edit effects: sharpen, clear, and particle randomized 30-50 per source video/clip
fixed overlays: image1, image2, image3 stretched full duration
```

Do this per source video/range unit or per chapter block, not as one blind global
adjustment over the whole project. Random values should be deterministic enough
to reproduce from the project package, but clips in the same video should not all
share the exact same value.

4. Write lower T1 from the actual speech.
   - Start at `00:00`; do not leave the opening empty.
   - Maintain continuous flow through the full roughcut unless the user asks for sparse notes.
   - For a 15:00 cut, target about 35-40 lower T1 segments. The saved YP005 사전투표 baseline uses 38.
   - For a 20:30 cut, target about 40-50 lower T1 segments, not 8-18.
   - Use `챕터1_`, `챕터2_`, `챕터3_` labels that match viewer-facing topic sections.
   - Each item should be 1-2 lines: first line summarizes what the speaker is saying, second line adds concise interpretation/opinion.
   - Be concrete: name the actor, claim, issue, or consequence. Avoid abstract filler such as `민심을 챙겨야 합니다`, `정치가 중요합니다`, or generic advice.
   - Positive opinion is allowed, but keep it tied to the exact claim: `이 분석은 구조를 보게 만든다`, `이 지점은 민주당이 아프게 들어야 한다`.
   - Run the `00script-writer` reader comprehension gate on every lower T1 item before patching CapCut. A lower T1 item is `REWRITE_REQUIRED` if a first-time reader cannot explain the two lines in one plain sentence.
   - Use the writer-mode `구멍/앵커/보상/회수` check for T1: each chapter block must open a concrete question, keep one concrete actor/object/number/action anchor, reward attention with the next detail, and recover that anchor later. Abstract words such as `핵심`, `본질`, `역설`, `의혹`, and `프레임` cannot replace the anchor.
   - If agent mode is available and the T1 text feels even slightly ambiguous, ask an isolated reader agent to judge `PASS/FAIL`, state what the line means, name the confusing word or subject, and propose a clearer 2-line caption. Do not defend confusing T1 with extra context; rewrite it.
   - Fail example: `챕터5_ 내란에 기여한 사람이 왜 내란 연루자가 됐어야 했나 / 이 역설적 질문이 특검 전체의 핵심 의혹이다`.
   - Pass example: `챕터5_ 내란에 기여했다면 왜 수사 대상에서 빠졌나 / 2차 종합특검의 핵심은 바로 이 질문이다`.

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
   - Back up `draft_content.json` and `template-2.tmp` before edits.
   - Patch both project root files and matching `Timelines/*/draft_content.json`, `Timelines/*/template-2.tmp` cache files.
   - Use UTF-8 Python IO. Avoid PowerShell inline Korean strings for JSON writes; store Korean text in UTF-8 JSON or patch via `apply_patch`.
   - After writing, verify segment count, first start time, last end time, gap count, and forbidden terms.

Verification pattern:

```text
lower T1 segment count: 40-50 for 20m
lower T1 segment count: 35-40 for 15m
t1 source channel segments: split by source-video transition, no date text
t2 upload date segments: split by source-video transition, `YYYY.MM.DD`
t3 flow strap segments: split by chapter/flow transition
t4 lower T1 segments: continuous chapter commentary
t5 subscribe segments: fixed subscribe line, full duration
fixed image tracks: image1/image2/image3 each full duration and media path exists
filter track: uses the three saved YP007 filter/effect materials across the source segments
filter values: `크림`, `배경 터치업`, and `보정` are each 0.30-0.55, never 1.0/100
quality enhancement: every main video material preserves `QualityEnhance`
auto/edit effects: smart_color_adjust, sharpen, clear, and particle values are 0.30-0.50 per clip
loudness normalize: every main video segment references an enabled loudness material
speech boundary lock: `speech_boundary_lock.json`, `roughcut_edl_locked.json`, and `source_labels_locked.json` exist and every final segment uses locked media
flow strap style: t3/flow_strap clones YP007 text-box geometry, transform, scale, font, stroke/background, and render order; not just font size
open CapCut safety: existing target draft was not overwritten while CapCut was open
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

For YP007-style political longform text boxes, preserve the clean black backing
seen in the current operator reference instead of leaving text floating directly
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

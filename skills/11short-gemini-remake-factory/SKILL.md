---
name: 11short-gemini-remake-factory
description: Portable 11utube/11short YouTube Shorts remake workflow from Brainstorm and Gemini/Google AI Studio source analysis through normalized analysis.json, Korean captions, optional generated voice only when explicitly requested, CapCut draft creation, and shorts_remake_harness analysis/assets/capcut/all gates. Use when the user gives a YouTube Shorts URL and asks for Gemini analysis, 쇼츠 리메이크, 11short production, CapCut draft, OCR overlays, Korean captions, or wants the same production process on another PC from OneDrive.
---

# 11short Gemini Remake Factory

Use this skill to produce a complete 11short remake package from a YouTube Shorts URL. The required done state is a visible local CapCut draft plus PASS reports for `analysis`, `assets`, `capcut`, and final `all`.

This skill is portable. Resolve paths from OneDrive and environment variables; do not hardcode a Windows user name.

## 11short Voice Policy

- Do not use Supertone, TTS, or generated narration unless the user explicitly requests voice generation.
- Default audio mode is original source audio + captions/OCR + BGM.
- If the user says `보이스`, `TTS`, `슈퍼톤`, `Supertone`, `나레이션`, or explicitly asks for generated voice, then use the Supertone workflow.
- If generated voice is not explicitly requested, set `voice_generation_mode=user_supplied` and `supertone_generation_enabled=false` in `status.json`.
- Do not check Supertone balance, read Supertone API key docs, or run Supertone scripts unless generated voice was explicitly requested.
- With generated voice disabled, omit `--intro-audio`, `--voiceover-audio`, and `--voiceover-srt` from CapCut generation.

## Required Order

1. Run the Brainstorm gate first.
2. Create the work folder under `${UTUBE_ROOT}\11short\000short-production-agent\episodes\{yyMMdd-videoid-or-profile}`.
3. Download the source with `yt-dlp`, including metadata and comments when possible.
4. Probe the source with `ffprobe` and create contact sheets before trusting any AI analysis.
5. Run the installed `watch`/`claude-video` skill against `source.mp4` with `py -3` on Windows; save `watch_report.md` and extracted frames under `watch\`. Use `--no-whisper` when no Whisper API key is configured.
6. Build `gemini_request.md` from `references/gemini-capcut-remake-system-prompt.md` plus the source URL, then ask Gemini/Google AI Studio to analyze the source. Use one source URL per Gemini chat and enable URL context. If URL context is weak, upload `source.mp4`.
7. Save Gemini artifacts, then normalize them. Gemini output is raw observation, not production truth.
8. Cross-check Gemini against `ffprobe`, contact sheets, and `watch` frames/transcript in `analysis_crosscheck.md`; repair timeline, OCR, hook, and speech claims before writing final `analysis.json`.
9. Extract every meaningful original screen text/subtitle/OCR/dialogue cue into a source text inventory, then convert it into our Korean visible text package.
10. Run the 00script-writer retention pass to choose the source-derived hook, place the strongest hook in the first 3 seconds, and record its fields in `analysis.json`.
11. Run real random 5-persona review when available. PASS requires at least 3 of 5 personas to understand the clip from our Korean visible text only, with original audio and original source text ignored, and at least 3 of 5 personas to say they would watch 30 seconds or more. If fewer than 3 of 5 approve, rewrite from the feedback and run the remaining 5 personas as the second pass; final PASS still requires 3 of 5 on that pass.
12. Select the real upload-title hook and the hook-forward video preview. The first visible seconds must show the strongest money shot unless the source already opens with it.
13. Run `shorts_remake_harness.py --stage analysis`. Stop on FAIL.
14. Generate assets: SRT, OCR layout, hook-forward source when needed, original audio reference, BGM, and status files. Supertone generation is OFF by default; use `voice_generation_mode=user_supplied` and `supertone_generation_enabled=false` unless the user explicitly asks for generated voice.
15. Run `shorts_remake_harness.py --stage assets`. Stop on FAIL.
16. Create the CapCut draft with `capcut_factory_profile.py`.
17. Patch only known factory defects if needed, such as OCR overlay font size becoming 15 instead of 12.
18. Run `shorts_remake_harness.py --stage capcut --draft-name "{draft_name}"`. Stop on FAIL.
19. Run final `--stage all --draft-name "{draft_name}"`.
20. Report work folder, CapCut draft path, harness states, voice mode, BGM, blocker, next action, and upload text.

## Meccha Chameleon / Hidden Picture Upload Description Rule

For game Shorts production, insert the required block only when all conditions
below are true:

1. The job is a game Shorts job.
2. The user prompt, source title, metadata, analysis, upload title, tags, or
   normalized topic identifies the game/source as Meccha/Mecha Chameleon or
   `메카 카멜레온`.
3. The same job context is specifically a hide-and-seek / hidden-picture /
   object-finding Meccha Chameleon video.

Do not insert this block for `숨은그림찾기` alone, generic hide-and-seek content,
generic game content, or a Meccha/Mecha Chameleon video that is not in the
hide-and-seek / hidden-picture lane. If the scope is uncertain, omit the block
until the source or user confirms that exact combination.

Condition keywords:

```text
meccha chameleon
mecha chameleon
Meccha Chameleon
Mecha Chameleon
메카 카멜레온
AND one of:
숨은그림찾기
숨은 그림 찾기
숨바꼭질
숨박꼭질
hide and seek
hidden picture
object finding
```

Insert this block inside `내용` before the final `출처:{source_url}` line. Do not
replace the source line, and do not shorten the player/source list. This rule
applies to `upload_text.md`, copy-ready final reports, handoff packages, and
any YouTube Shorts upload-text response.

```text
메카 카멜레온의 황당한 순간, 웃긴 장면, 실패, 최고의 그림과 프로 아티스트

이 영상에는 메카 카멜레온의 실패 장면, 웃긴 순간, 최고의 그림과 프로 아티스트, 황당한 순간, 최고의 장소, 팁과 요령, 하이라이트 등 250가지가 담겨 있습니다! 이 메카 카멜레온 웃긴 순간 영상 제작에 많은 시간을 투자했으니, 재밌게 보셨다면 좋아요와 구독 부탁드립니다! :)

🎮 주요 플레이어: chuukooky: https://redarca.de/Lj3zS
aimsey: https://redarca.de/5jQXV
alcolive: https://redarca.de/SpBr8
dizzy: https://redarca.de/b6jX6
heyyouvideogame: https://redarca.de/WxPrK
rprx: https://redarca.de/QJtq0
nikkisia: https://redarca.de/7aCNO
northernlion: https://redarca.de/UPXqL
yukinasagi: https://redarca.de/kMYbj
miaiow: https://redarca.de/dmwFh
smajor: https://redarca.de/FxoD2
niekbeats: https://redarca.de/M2YFm
ellum: https://redarca.de/JBWFN
elasticdroid: https://redarca.de/Y2kNh
slackatk: https://redarca.de/N3I3p
gmart: https://redarca.de/JqENZ
squeex: https://redarca.de/OGMB6
impulsesv: https://redarca.de/ILPeM
criken: https://redarca.de/yBAfI
covent: https://redarca.de/BjwOp
jennybeartv: https://redarca.de/QXMu8
caseoh_: https://redarca.de/smBYn
Miaru: https://redarca.de/2JuM0
jennmcallister: https://redarca.de/ifctg
minky: https://redarca.de/pqW5T
bnans: https://redarca.de/6HVzY
wayneradiotv: https://redarca.de/1ytgC
flackblag: https://redarca.de/rLW9T
grian: https://redarca.de/I4vbK
ethannestor: https://redarca.de/rR7LX
theburntpeanut: https://redarca.de/adjsP
Blaggers: https://redarca.de/iH4qx
smii7y: https://redarca.de/r2moJ
cochard: https://redarca.de/9WhK4
sodapoppin: https://redarca.de/L0TcH
pearlescentmoon: https://redarca.de/Z7pp3
ludwig: https://redarca.de/5I8NY
bonsaibroz: https://redarca.de/wyndw
antonychenn: https://redarca.de/xY9rC
hakonoriginal: https://redarca.de/KDW5z
SodaGang6: https://redarca.de/GCFr5
geminitay: https://redarca.de/jKzvv
스키즐맨: https://redarca.de/svZd5
발키래: https://redarca.de/Tj8Yr
제리코: https://redarca.de/3TPm3
엑스초코바: https://redarca.de/RHvVN

© 귀하의 영상 삭제를 원하시면 takktwo@naver.com으로 이메일을 보내주세요.
```

## Brainstorm Gate

Before file edits, media generation, Gemini calls, TTS, or CapCut creation, output a compact Korean brief:

```text
Brainstorm
- 사용자 의도:
- 작업 종류:
- 입력 소스:
- 원하는 결과물:
- 적용 스킬/프로젝트:
- 보이는 모델/API:
- 자막/화면 규칙:
- 파일/폴더 규칙:
- 금지/주의:
- 내가 할 가정:
- 완료 기준:

Execution TODO
- [ ] 규칙/소스 확인
- [ ] Gemini 분석
- [ ] analysis 정규화
- [ ] assets 생성
- [ ] CapCut 초안 생성
- [ ] harness all PASS
- [ ] 결과 보고
```

Proceed after this gate unless an ambiguity blocks production.

## Path Contract

Use these roots:

```powershell
$env:WORKSPACE_ROOT = "$env:USERPROFILE\OneDrive\22utube"
$env:UTUBE_ROOT = "$env:WORKSPACE_ROOT\11utube"
$env:SHORT_ROOT = "$env:UTUBE_ROOT\11short"
```

Expected work folder:

```text
${UTUBE_ROOT}\11short\000short-production-agent\episodes\{yyMMdd-videoid-or-profile}
```

Read [pc-setup.md](references/pc-setup.md) when setting up or debugging another PC.

## Handoff Package Mode

Use handoff package mode when one machine prepares analysis/assets and another machine creates the local CapCut project. The handoff package in OneDrive is the portable source of truth; a live CapCut draft folder is not portable and must not be treated as the canonical cross-machine artifact.

Canonical handoff root:

```text
${UTUBE_ROOT}\11short\11short_handoff
```

Package shape:

```text
${UTUBE_ROOT}\11short\11short_handoff\{episode_id}\
  handoff_manifest.json
  work\
    source.mp4
    analysis.json
    guide_ko.srt
    onscreen_ko.srt
    onscreen_layout.json
    source_original_audio.mp3
    status.json
  capcut_jobs\
    macmini\
    home_windows\
    office_windows\
```

Designer mode:

- Create or update the handoff package under `11short_handoff\{episode_id}`.
- Put portable work files under `work\`.
- Run `analysis` and `assets` harness gates.
- Set manifest status to `ready_for_capcut` only after required files exist and both gates pass.
- Do not create or copy a live CapCut draft as the handoff source unless the user explicitly asks for recovery/forensics.

Project-writer mode:

- Scan `11short_handoff\*\handoff_manifest.json` and list buildable packages first.
- A buildable package has `package_version=11short_handoff_v1`, valid status, no active lock, required files present, `analysis_pass=true`, and `assets_pass=true`.
- Before building, lock one package by setting `locked_by`, `locked_at`, `lock_reason`, and `status=capcut_building`.
- Build a fresh local CapCut draft from the package `work\` files, then run `capcut` and final `all` harness gates.
- Update `capcut_created`, `capcut_created_by`, `capcut_created_at`, `capcut_draft_name`, `capcut_harness_pass`, `all_harness_pass`, and `upload_ready` from actual results.

Required manifest fields:

```json
{
  "package_version": "11short_handoff_v1",
  "status": "ready_for_capcut",
  "created_by": "macmini",
  "created_at": "",
  "source_url": "",
  "episode_id": "",
  "draft_name": "",
  "work_dir": "work",
  "paths_are_relative": true,
  "analysis_pass": true,
  "assets_pass": true,
  "required_files_ok": true,
  "locked_by": null,
  "locked_at": null,
  "lock_reason": null,
  "capcut_created": false,
  "capcut_created_by": null,
  "capcut_created_at": null,
  "capcut_draft_name": null,
  "capcut_harness_pass": false,
  "all_harness_pass": false,
  "upload_ready": false,
  "uploaded": false,
  "required_files": [],
  "notes": ""
}
```

Allowed status values are `drafting`, `analysis_ready`, `assets_ready`, `ready_for_capcut`, `capcut_building`, `capcut_created`, `capcut_harness_pass`, `all_harness_pass`, `upload_ready`, `uploaded`, and `blocked`.

Allowed machine names for `created_by`, `locked_by`, and `capcut_created_by` are `macmini`, `home_windows`, `office_windows`, and `unknown`.

## Gemini Analysis Contract

Use Gemini/AI Studio first for URL-only remake work, but never paste Gemini text straight into production. Save:

```text
gemini_request.md
aistudio_clipboard.txt
analysis_raw_gemini.json
gemini_master_request.md when used
aistudio_master_clipboard.md when used
analysis_master_gemini.md or .json when used
analysis_crosscheck.md
```

Canonical Gemini prompt:

```text
references/gemini-capcut-remake-system-prompt.md
```

Build the actual request file with:

```powershell
py -3 "{skill_dir}\scripts\build_gemini_request.py" --url "{url}" --out "{work}\gemini_request.md"
```

The request must contain the canonical system prompt and this final input line:

```text
[입력]
video_url: {url}
```

Do not replace this with an ad hoc short prompt. Gemini should output only the raw JSON schema requested by that prompt.

Before finalizing `analysis.json`, run the local `watch`/`claude-video` check and compare it with Gemini output:

```powershell
py -3 "$env:USERPROFILE\.codex\skills\watch\scripts\watch.py" "{work}\source.mp4" --no-whisper --max-frames 80 --out-dir "{work}\watch" 2>&1 | Tee-Object -FilePath "{work}\watch_report.md"
```

If a Groq or OpenAI Whisper key is configured in `%USERPROFILE%\.config\watch\.env`, omit `--no-whisper` so audio-only speech can be transcribed. Without a key, frames and native captions are still usable; do not treat missing Whisper fallback as a production blocker unless the source has critical speech that Gemini and native captions cannot verify.

`analysis_crosscheck.md` must state what was confirmed or corrected from `watch`: scene order, timestamp ranges, OCR text, strongest opening visual, visible subject, and any speech/caption uncertainty.

Normalize into `analysis.json` with these required top-level fields:

```text
video_url, video_summary_ko, duration_seconds, duration_formatted,
layout_rules, title_candidates, top_title_text, opening_voice_line,
main_subject, tone, onscreen_overlays, segments,
script_writer_mode, script_writer_pass_complete,
viewer_to_keep_ko, viewer_to_ignore_ko, click_emotion_ko,
memory_anchor_ko, big_open_loop_ko, first_5_seconds_hook_ko,
title_strategy_ko, bottom_caption_strategy_ko, purple_overlay_strategy_ko,
upload_title_hook_ko, hook_forward_plan_ko, hook_forward_edit
```

The raw Gemini JSON may include these additional prompt fields; keep them in `analysis_raw_gemini.json` and normalize or copy useful values into `analysis.json`:

```text
analysis_status, analysis_error_reason, video_duration_sec,
all_detected_texts, timeline_summary_ko,
text_removal_assessment, automation_judgment, predicted_comments
```

Normalization compatibility:

- Map `video_duration_sec` to `duration_seconds`.
- Keep `predicted_comments` exactly 3 in raw output; map them to `best_comments_predicted` when needed.
- Convert each segment's `onscreen_text_original`/`speech_original` into the older compatibility keys (`onscreen_text_en`, `speech_en`) when downstream tools expect them.
- Recompute OCR `capcut_y` from overlay center with `(0.5 - y) * 2` before CapCut/harness, even if Gemini returned a screen-ratio-looking value.
- If `automation_judgment.usable_for_remake=false` or `text_removal_assessment.difficulty=reject`, stop before assets and report the blocker.

Required segment fields:

```text
start, end, time_range_note, visual_ko, action_ko,
onscreen_text_en, onscreen_text_ko_natural,
speech_en, speech_ko_natural, sfx_ko,
caption_ko_final, reframe, importance
```

11short tone is polite Korean by default. Write visible captions, purple overlays, upload text, and narration guide text in 존댓말, normally ending with `습니다`, `합니다`, or `됩니다`. Do not use 반말, 음슴체, or clipped endings such as `함`, `됨`, `아님`, `개웃김`, or casual command endings unless the user explicitly asks for that style.

`caption_ko_final` is the source for `guide_ko.srt` and the bottom yellow caption layer. It must be descriptive Korean narration, not a short keyword label. Each cue should make the clip understandable with original/source audio muted by showing situation, action, and reason/result within the 2-line, 14-character-per-line layout. Use more timed cues when needed instead of deleting meaning. `onscreen_ko.srt` may remain short keyword/OCR-cover cards, but it does not replace explanatory bottom captions.

Before `assets` PASS, inspect `guide_ko.srt`. If it reads like labels, vibes, or topic cards rather than situation-action-result narration, rewrite `analysis.json` `segments[].caption_ko_final`, regenerate `guide_ko.srt`, then rerun `analysis` and `assets`.

Required `reframe` fields:

```text
focus_bbox, focus_center, important_object_ko, suggested_zoom,
pan_direction, mirror_allowed, mirror_reason
```

Read [gemini-normalization.md](references/gemini-normalization.md) before repairing Gemini JSON or OCR overlays.

## Hook Title And Hook-Forward Edit

This is mandatory for Shorts production.

- The upload title is not a neat topic label. It must sound like a viewer-facing hook that makes the first image obvious. For example, use `자 1000칼로리 들어갑니다` for a greasy bread clip, not `기름빵 한 입에 끝나는 맛`.
- `title_candidates` remains only the short profile/draft name. Do not use it as the upload title.
- `top_title_text` should be a short visible hook, but the final upload title can be longer and more spoken.
- Before CapCut, pick the strongest visual beat: bite, fall, reveal, payoff, shock face, transformation, price reveal, or punchline.
- If the strongest beat is not already in the first 1-2 seconds, create a 0.5-2.0 second hook preview at the very front, then return to the chronological source flow.
- Do not over-explain the hook. Show the moment first, then let captions explain why it matters.
- If hook-forward editing is not applied, record a concrete reason such as `source already opens with strongest beat`, `source audio sync would break`, or `OCR story must stay chronological`.

Save this in `analysis.json` or `status.json`:

```json
{
  "upload_title_hook_ko": "자 1000칼로리 들어갑니다",
  "hook_forward_plan_ko": "가장 강한 한입 장면을 0초에 1.2초 선공개 후 원래 흐름으로 복귀",
  "hook_forward_edit": {
    "applied": true,
    "source_start": "00:12.300",
    "source_end": "00:13.500",
    "target_start": "00:00.000",
    "target_end": "00:01.200",
    "return_to_chronological_at": "00:01.200",
    "reason_ko": "클릭 후 바로 보상 장면을 보여 주기 위해"
  }
}
```

When the preview is applied by preprocessing, use `source_hooked.mp4` as the CapCut video and extract `source_original_audio.mp3` from that hooked file, not from the unmodified source.

## Locked 3-Text Layout

Every valid draft has exactly these visible text classes:

- Top fixed title: `top_title_text`, white with black stroke, one line up to 10 Korean chars or two lines up to 16 total and 8 per line.
- Bottom yellow captions: `segments[].caption_ko_final`, descriptive sentence-style polite Korean, max 2 lines, max 14 Korean chars per line.
- Middle purple overlays: `onscreen_overlays[]`, `#8100ff` box, white text, `font_size=12`, one visible at a time, never inside top/bottom black bands.

For OCR covers:

- `cover_original=true`
- `style_hint="purple_box_white_text"`
- `source_bbox` and `overlay_bbox` are normalized 0..1 screen ratios.
- `overlay_bbox` must fully cover `source_bbox`.
- If `capcut_y` is present, use `(0.5 - y) * 2`, normalized -1..1.

## Voice And Audio

Default audio mode:

```text
voice_generation_mode: user_supplied
supertone_generation_enabled: false
```

Always extract original source audio as a separate MP3 and add it as a separate CapCut audio track. Add one BGM track from `${UTUBE_ROOT}\11short\assets\always_bgm` unless the user explicitly says no BGM.

Generated voice is opt-in only. When the user explicitly asks for generated voice, use:

```text
intro/opening voice_id: 6e43a7b9ffa9834c154ab7
main body voice_id: 049d87c31d8e431b15f468
model: sona_speech_2
```

Never expose `SUPERTONE_API_KEY`. Do not check balance or run Supertone scripts unless generated voice was explicitly requested. After Supertone generation, record and report `credit_balance`.

## Harness Gates

Run gates in order:

```powershell
py -3 ${env:UTUBE_ROOT}\11short\shorts_remake_harness.py "{work}" --stage analysis
py -3 ${env:UTUBE_ROOT}\11short\shorts_remake_harness.py "{work}" --stage assets
py -3 ${env:UTUBE_ROOT}\11short\shorts_remake_harness.py "{work}" --stage capcut --draft-name "{draft_name}"
py -3 ${env:UTUBE_ROOT}\11short\shorts_remake_harness.py "{work}" --stage all --draft-name "{draft_name}"
```

Copy each successful report to:

```text
shorts_remake_harness_report_analysis.json
shorts_remake_harness_report_assets.json
shorts_remake_harness_report_capcut.json
shorts_remake_harness_report_all.json
```

If any stage FAILs, stop. Do not proceed to the next stage until fixed.

## CapCut Draft Rules

Use `capcut_factory_profile.py`, not hand-written draft JSON:

```powershell
py -3 ${env:UTUBE_ROOT}\tools\youtube_ko_subtitles\capcut_factory_profile.py `
  --draft-name "{draft_name}" `
  --video "{work}\source.mp4" `
  --srt "{work}\guide_ko.srt" `
  --top-title "{top_title_text}" `
  --source-audio "{work}\source_original_audio.mp3" `
  --ocr-srt "{work}\onscreen_ko.srt" `
  --ocr-layout-json "{work}\onscreen_layout.json" `
  --analysis-json "{work}\analysis.json"
```

Only add these optional arguments when generated voice was explicitly requested and the files exist:

```powershell
  --intro-audio "{work}\voice_opening.mp3" `
  --voiceover-audio "{work}\voiceover_body.mp3" `
  --voiceover-srt "{work}\voice_body_split.srt" `
```

Use the current reference factory draft when it exists:

```text
%LOCALAPPDATA%\CapCut\User Data\Projects\com.lveditor.draft\0613 FIRE
```

If this reference draft is missing on another PC, read [pc-setup.md](references/pc-setup.md). Do not silently substitute a different visual standard when the user asked for the exact process.

## Instagram Layout Mode

Use this mode when the user says `인스타용`, `인스타`, or asks for an Instagram variant of a 11short draft.

Canonical template:

```text
%USERPROFILE%\OneDrive\인스타용 기본세팅
%LOCALAPPDATA%\CapCut\User Data\Projects\com.lveditor.draft\인스타용 기본세팅
```

Required template assets:

```text
assets\픽셀링_20260601_230021_이미지.png
assets\instagram_form_pixel_frame.png
assets\2026-05-17 04 16 50.png
assets\instagram_animals_lower_right.png
assets\KakaoTalk_20260601_234914113.mp4
assets\instagram_cat_top_left.mp4
```

Rules:

- Do not edit `인스타용 기본세팅` directly for an episode.
- Copy the template draft to `{original_draft_name}-인스타`.
- Keep the template text styles, positions, pixel frame, top-left cat video, and lower-right animal image.
- Replace only `source.mp4`, `source_original_audio.mp3`, top title, middle captions, bottom yellow captions, and optional BGM.
- If Korean filenames fail on another local machine, use the English alias filenames.
- The source video track may be muted, but `source_original_audio.mp3` must be added as a separate audio track.
- Before claiming the Instagram variant is ready, verify `draft_content.json` parses and all required template assets exist.

## Required Work Files

Each completed work folder should contain:

```text
source.mp4
source.info.json
best_comments.json when comments are available
contact_sheet.jpg or contact_sheet_1s.jpg
watch_report.md
watch\frames\*.jpg
analysis_raw_gemini.json
analysis_crosscheck.md
analysis.json
guide_ko.srt
lite_guide_ko.srt
onscreen_ko.srt
ocr_overlay.srt
onscreen_layout.json
source_original_audio.mp3
voice_opening.txt
voice_body.txt
voice_opening.mp3 only when generated voice is explicitly requested
voiceover_body.mp3 only when generated voice is explicitly requested
voice_body_split.srt only when generated voice is explicitly requested and body voice is split
status.json
production_console.json
upload_text.md
shorts_remake_harness_report_*.json
```

## Final Report Format

In the final answer, report:

```text
[진행판]
- URL/source:
- Gemini analysis:
- analysis/assets/capcut/all:
- n8n:
- blocker:

작업 폴더:
CapCut 초안:
최종 하네스:
BGM:
Voice mode:
Supertone balance: N/A unless explicit voice generation ran

제목:
...

내용:
...

출처:{source_url}

태그:
tag1,tag2,tag3,
```

Use tag words only, without `#`, and put a comma after every tag including the final tag.

### Copyable Markdown Output

For every final report and every upload-text response, output these four fields as separate copyable markdown fenced code blocks. Use the exact labels below.

제목

```text
{final upload title}
```

내용

```text
{short upload description}
출처:{source_url}
```

쉼표테그

```text
tag1,tag2,tag3,
```

프로젝트검색용 이름

```text
{video_id or episode_id} - {short searchable Korean label}
```

Do not combine the four fields into one block. `쉼표테그` uses tag words only, without `#`, and every tag ends with a comma. `프로젝트검색용 이름` is the string saved into or searched from `PROJECT_INDEX.md`, such as `_IF_P5KUvy4 - 골든리트리버 아기 강아지`.

## Detailed Commands

For exact command templates, read [production-commands.md](references/production-commands.md).

---
name: 00-tikitaka
description: Use only when the user explicitly asks for Tikitaka Korean Shorts source analysis, remake scripting, 티키타카 하자, 우라까이, hook candidates, 상단/timed 중단 draft creation, Gemini raw intake for Shorts URLs, or Gemini Shorts source notes. Do not use for SRT, CapCut, production packages, or polishing-only existing scripts.
---

# 00 Tikitaka

## Active Instruction Authority - 2026-07-06

Authority: `shorts_script_analysis_single_source_v20260706.md`.

For current Shorts script analysis and Tikitaka drafts, use only the
2026-07-06 single-source contract:

- Output `상단 + timed 중단 + 중단 TTS 글자만 복사`.
- Do not output legacy `하단`, `하단 원문`, 3-layer script packages, or bottom
  first-line candidate blocks.
- Treat any legacy reference that says `TTS 만들 글자만 복사` as
  `중단 TTS 글자만 복사`.
- Use quoted lines only for verified source speech.
- Use parenthesized lines for reaction, emotion, situation, visual, SFX, or
  meme captions.
- Derive the TTS copy block only from timed `중단` lines intended for voice.

## TTS Copy Text Naming Rule

Canonical contract label:

```text
중단 TTS 글자만 복사
```

Accepted legacy alias:

```text
TTS 만들 글자만 복사
```

`TTS 만들 글자만 복사` is a legacy alias of `중단 TTS 글자만 복사`.
The legacy alias is allowed only as a backward-compatible label for the same
block. It must be interpreted as `중단 TTS 글자만 복사`, not as a separate legacy
output.

Internal artifact:

```text
tts_copy_text.txt
```

Meaning:

- timed `중단` 중 voice/TTS 의도 줄만 시간표 없이 모은 순수 복사용 텍스트
- 음성파일 아님
- SRT 아님
- CapCut production asset 아님
- 사용자가 직접 복사해서 TTS/나레이션 툴에 붙여넣는 원문 블록
- visual-only `(...)` 상황설명은 기본 제외
- verified `"..."` 화자발언은 기본 제외

## Tikitaka Current Order

Current Tikitaka work is a reproducible design stage, not an abstract script
stage. The stage order is:

```text
source evidence
-> 1차설계서
-> timeline_design.json
-> timeline_design_gate.json
-> humanize_korean_gate.json
-> block_map.json / block_role_map.json / block_voice_switch_map.json
-> tts_copy_text.txt
-> script_handoff_gate.json
-> report1_handoff.json
```

`1차설계서` is the operator-facing CapCut timeline design. It must show the real
track/time layout as a table, including expandable rows for `T1/T2/TTS`,
`"" 화자발언 A/B/C...`, `() 상황설명 A/B/C...`, video, and audio lanes. If a
speaker quote or situation caption needs multiple rows, add rows; do not
compress them into one abstract paragraph.

`timeline_design.json` is the machine-readable version of that design. Every
segment must preserve protected fields:

```text
time_start/time_end/track/caption_type/audio_policy
```

`timeline_design_gate.json` must be PASS before the design can be treated as a
handoff artifact.

Humanize Korean runs after the 1차설계서 is structurally fixed and before the
handoff gate. Humanize may change wording only: visible Korean in T1/T2/TTS,
`"" 화자발언`, and `() 상황설명`. It must not change time ranges, track rows,
caption roles, edit order, audio policy, verified quotes, source facts, names,
numbers, or the separation between quote/situation/TTS roles. Record the result
as `humanize_korean_gate.json` with `humanize_korean_gate.json=PASS`.

Do not run SCRIPT_HANDOFF_GATE before humanize_korean_gate.json=PASS. If Humanize
needs a structural change, return to Tikitaka design repair instead of silently
patching the script.

`00script-writer is not a default stage`. Use it only when the user explicitly
asks for a rewrite or when the 1차설계서 text fails readability/hook pressure.
Even then it may patch wording only; it may not change
`time_start/time_end/track/caption_type/audio_policy`.

## Purpose Of 1차설계서

`00-tikitaka` is not a pretty-script generator. It is the Stage 1 design owner
for reproducible Shorts production.

The purpose of `1차설계서` is to lock the production contract before CapCut work:
what the viewer sees, when it appears, which semantic lane owns it, whether it
is TTS narration, verified speaker quote, situation caption, source video, or
audio policy, and what the next production skill must implement without
reinterpretation.

Human operators approve `1차설계서`.
Production agents implement `timeline_design.json`.

Downstream production must not rewrite hooks, reorder beats, change time ranges,
change tracks, change caption_type, change audio_policy, convert speaker_quote
to TTS, convert situation_caption to speaker_quote, or add BGM/SFX unless the
locked handoff explicitly allows it.

## timeline_design.json audio track

Audio rows in `timeline_design.json` must not leave `track` empty.
Stage 1에서는 A9/A10/A11/A12 같은 real CapCut track id를 직접 잠그지 않는다.
Tikitaka locks semantic audio tracks only; 실제 CapCut A-track 매핑은 Stage 2의
`000short-production-agent`가 `shrt white` 기준으로 해결한다.

Required audio track shape:

```json
{
  "track": "audio.narration_tts",
  "semantic_lane": "narration_tts",
  "resolved_capcut_track": null,
  "resolved_by": "000short-production-agent"
}
```

Allowed semantic tracks:

```text
audio.narration_tts
audio.speaker_source
audio.sfx
audio.bgm
```

1차설계서 audio row labels:

```text
오디오 / 나레이션·TTS
오디오 / 화자발언·원본화자
오디오 / SFX
오디오 / BGM
```

## Gemini Raw Intake First

When the user says `티키타카 하자` without source notes, ask for the Shorts URL
first:

```text
URL 주소 주면 Gemini 분석합니다.
```

When the user provides a YouTube Shorts/Reels/TikTok URL for Tikitaka intake,
run Gemini raw analysis before writing Tikitaka script. Use the exact system
prompt in `references/gemini_raw_intake_prompt.md`, verify the output includes
`final_warning_ko`, and save the Gemini result as JSON/Markdown through the
AI Studio dedicated-profile runner.

Codex must use the shared no-API AI Studio runner first, not manual paste:

```powershell
$env:PYTHONPATH = ""
py -3 "$env:USERPROFILE\OneDrive\22utube\22factory_20260628\00_asset_tools\ai_studio_runner\scripts\run_ai_studio_short.py" "<SHORTS_URL>" --retries 0 --run-timeout-sec 240
```

Compatibility wrapper:

```powershell
powershell -ExecutionPolicy Bypass -File "$env:USERPROFILE\OneDrive\22utube\22factory_20260628\00_asset_tools\tools\gemini_raw_paste_run.ps1" -Url "<SHORTS_URL>"
```

Manual/operator web-UI option:

```text
%USERPROFILE%\OneDrive\22utube\22factory_20260628\00_asset_tools\browser_extensions\ai-studio-shorts-runner
```

This Chrome extension is allowed because it is still AI Studio web UI only: it
fills System instructions, inserts the Shorts URL, tries URL context, clicks Run,
and copies the last Model JSON. The CDP runner now uses this extension artifact
automatically: it launches only the dedicated AI Studio Chrome profile with
`--load-extension`, checks for the extension content-script marker, and if Chrome
ignores command-line unpacked extension loading, injects the same extension files
(`src/core-browser.js` + `content.js`) into the dedicated AI Studio page via CDP
Runtime. This fallback is still web-UI automation, not API usage, and it does not
touch the user's normal Chrome. When using the extension manually, reload it
after file changes, use `/u/0`, and still reject any copied JSON that fails
source identity/duration/id checks. The extension is not an API path and must not
upload source videos unless the user explicitly approves upload.

Runner contract:

- It opens only the dedicated AI Studio Chrome profile under local app data; it
  must not touch the user's normal Chrome profile/tabs.
- Gemini raw intake is **web UI only** for this user. Do not ask for, suggest,
  or implement Gemini API fallback. If the web UI fails or returns source
  mismatch, report the blocker and continue only with allowed web-UI/reset/source
  identity checks unless the user explicitly reverses this rule.
- It launches real installed Chrome with the dedicated `--user-data-dir` and a
  `--remote-debugging-port`, then attaches through Playwright CDP. Do not switch
  back to Playwright `launch_persistent_context`; on this Windows PC that path
  can click Run but AI Studio returns `permission denied` even for `안녕`.
- The successful AI Studio account currently redirects to `/u/0`; do not force
  stale `/u/1` unless the user explicitly changes the logged-in account.
- Use `py -3` with `PYTHONPATH` cleared. Hermes venv `python` may not have
  Playwright, while the Windows Python 3 runtime does.
- Before launching, the runner may kill only Chrome processes whose command line
  contains the dedicated AI Studio profile path. It must never kill normal Chrome.
- The user may continue other work while the runner is active. The runner uses
  CDP/DOM control, not OS-level keyboard/mouse focus stealing, so normal Chrome,
  CapCut, Telegram, VS Code, and other apps can be used during the run.
- Before filling a new prompt, explicitly click the AI Studio left-nav
  `Playground` item (`span.nav-item-main-text` text `Playground`) and then force
  `/prompts/new_chat` again. This prevents stale restored chats/old Model JSON
  from being treated as the new Shorts result.
- The runner may launch the dedicated Chrome window offscreen/minimized and must
  close it cleanly when done so Chrome does not show a next-run restore-pages
  bubble. If the dedicated window is visible, do not ask the user to interact
  with it unless login or a human Google challenge is required.
- Success is `status: SAVED` plus real files under the default save folder below.
  `permission denied`, `RESULT_TIMEOUT`, source identity mismatch, duration/id
  mismatch, unrelated animal/old-video output, or missing `final_warning_ko` is
  FAIL, not a saved result. `final_warning_ko` alone is never enough.

Only use manual AI Studio copy/save as a fallback when the runner is blocked and
report the blocker. Do not use the old `+ Create new instruction` -> `0701경`
preset-selection path for this Gemini raw intake flow.

Default save folder:

```text
%USERPROFILE%\OneDrive\22utube\22factory_20260628\01_shorts_factory\germini
```

Default filename shape:

```text
YYYYMMDD_<shorts_title>_gemini_raw.md
```

Do not use Google Docs by default. Treat the saved Gemini JSON as raw source
notes only; it is not verified timing, OCR, STT, source dialogue, or final
script truth.

For Tikitaka work that needs an actual draft, do not stop at Gemini raw notes.
Download or confirm `source.mp4`, then verify the important beats with source
evidence: duration, frame checks, OCR/STT when needed, and raw-vs-source
timecode mismatch notes. Keep any unverified Gemini ranges as
`PROPOSED_SOURCE_TIMECODE`.

## Ownership Matrix

- `00-tikitaka`: Shorts source analysis, remake script draft, hook, top/timed-middle, and script handoff only.
- `00script-writer`: polish/review an existing script draft only.
- `000short-production-agent`: SRT, layout JSON, CapCut, validation, exports, upload packages, and other production assets only.
- `22utube-production-agent`: shared factory policy only.

## Escalation Rule

Do not move to the next owner unless the user explicitly asks for that owner's
stage.

Adjacent intent is not permission to escalate. A Tikitaka request does not imply
production, `production_allowed`, `SCRIPT_LOCK`, `PASS`, export, upload,
completion, audio generation, SRT generation, layout JSON, or CapCut work.

If the user already has a draft and asks only for wording, rhythm, retention,
or writer review, route to `00script-writer` instead of rewriting it here.

## Stage Scope Gate

When the user provides a Shorts URL plus Gemini/source notes, first separate the
scope before any production escalation:

```text
stage_1_script = 대본/티키타카 only
stage_2_full = source/TTS/SRT/CapCut project
```

If the scope is unclear, stop at `WAIT_USER_STAGE_DECISION` and ask where to
stop before any TTS, SRT, layout, CapCut, render, export, or upload work.

If the user says `대본까지`, `대본만`, `초벌`, `티키타카`, `초안만`, `검토용`,
or `스크립트만`, this skill produces the stage-1 package only: `1차설계서`,
상단, timed 중단, `중단 TTS 글자만 복사`, `timeline_design.json`,
`timeline_design_gate.json`, `humanize_korean_gate.json`, `block_map.json`,
`block_role_map.json`, `block_voice_switch_map.json`,
`script_handoff_gate.json`, and 보고서1. Then stop at
`WAIT_REPORT1_APPROVAL_TTS_DECISION` until the user says OK and chooses the
TTS/audio route.

If the user already says `끝까지`, `자동으로 다`, `최종`, `다음단계`,
`업로드까지`, `슈퍼톤`, `슈퍼톤으로`, `supertone`, `TTS 만들어`, `tts 만들`,
`TTS 생성`, `tts 생성`, `TTS mp3`, `tts mp3`, `캣컵프로젝트파일까지`,
`캣컵 프로젝트 파일까지`, `캐컷프로젝트파일까지`, or `capcut project`, mark
`user_stage_decision=stage_2_full` as future intent. Still output 보고서1 and
wait for `report1_approved=true` plus `voice_audio_route_decided=true` before
route to `000short-production-agent`. A generic `진행/해줘` next to stage-1
wording is not stage-2 permission.

`자동모드` is an explicit stage-2 token: user says 자동모드 = stage_2_full.

Mandatory gate map for URL + Gemini/source intake:

```text
G0 INTAKE = ask "어디까지 만들까?" unless the user text already says stage_1_script or stage_2_full
G1 STAGE 1 = create 1차설계서, timeline_design.json, timeline_design_gate.json, humanize_korean_gate.json, block_map.json, block_role_map.json, block_voice_switch_map.json, tts_copy_text.txt, and script_handoff_gate.json
G2 STAGE 1 STOP = output 1차설계서/보고서1 and stop until report1_approved + voice_audio_route_decided
G3 STAGE 2 ENTRY = only after stage_2_full intent plus report1_approved and voice_audio_route_decided
G4 FINAL = only the production owner may output [FINAL_LOCK 최종 보고] after all production gates pass
```

The harness must write `stage_gate_todo.md` and `stage_scope_report.md` when it
audits a package. The todo/report are not optional narration: they are the
visible checklist that proves where the run stopped.

RE-ENTRY rule:

```text
REWORK_IN_NEW_CHAT_ANALYZE_FIRST
MIDDLE_PACKAGE_REWORK_REVIEW_GATE
REPORT_BEFORE_ACTION
```

If the user brings a middle package, old handoff folder, or a CapCut project
rework request in a new chat, analyze the package before action and report the
resume point:

- `draft_content.json` + `script_handoff_gate.json` PASS + `block_map.json`
  exists => this reached CapCut; resume at CapCut rework.
- `draft_content.json` alone is not enough; report `WAIT_SCRIPT_HANDOFF_GATE`
  and resume at `stage_1_repair`.
- `script_handoff_gate.json` FAIL or invalid => report
  `WAIT_SCRIPT_HANDOFF_GATE_REPAIR` and resume at `stage_1_repair`.
- `script_handoff_gate.json` PASS with `SCRIPT_LOCK_PACKAGE` => stage 1 is done; resume at stage 2 only after user decision.
- neither exists => restart from G0 and ask where to stop.

Use `INTERACTIVE_SCRIPT_APPROVAL` when the user asks to choose or decide during
the script process. Stop and ask at the requested checkpoints:

```text
URAKKAI_DIRECTION_CHECKPOINT
SCRIPT_APPROVAL_CHECKPOINT
TEMPLATE_APPROVAL_CHECKPOINT
```

Use `DRAFT_FAST_EXPLICIT_ONLY` only for an explicit fast CapCut draft request,
not for `대본/초벌/티키타카` stage-1 script work. Do not choose DRAFT_FAST just
because the output is not upload-ready.

Do not choose DRAFT_FAST just because the output is not upload-ready.

## Report 1 Contract

`보고서1` is the Tikitaka 대본 승인용 report. It is not a CapCut, export, upload,
or production report.

Write 보고서1 in 한글 우선, short, scan-friendly form. Use 예/아니오 단답 for
gate items whenever possible. The operator should be able to approve or reject
the script without reading implementation labels.

Required 보고서1 shape:

```text
# 보고서1

대본 승인용: 예
CapCut 생성: 아니오
TTS 생성: 아니오
업로드 준비: 아니오

1차설계서:
메타:
episode_id:
source_url:
source_title:
source_evidence_status: VERIFIED | PARTIAL | PROPOSED
source_tags:
upload_tags:
remake_title_ko:
upload_title_candidate:
content_summary_ko:
channel_family:
story_type:
production_type:
shorts_design_type:
caption_policy:
audio_policy:
template_direction:
default_capcut_base: shrt white
tts_route:
source_speech_policy:
card_asset_role:

| 트랙 / 시간 | 0-3초 | 3.1-5초 | ... |
| T1 | ... | ... | ... |
| T2 | ... | ... | ... |
| TTS | ... | 없음 | ... |
| "" 화자발언 A | 없음 | "..." | 없음 |
| "" 화자발언 B | 없음 | 없음 | "..." |
| () 상황설명 A | (...) | 없음 | 없음 |
| 영상 | ... | ... | ... |
| 오디오 / 나레이션·TTS | ... | 없음 | ... |
| 오디오 / 화자발언·원본화자 | 없음 | source_audio | ... |
| 오디오 / SFX | 없음 | optional | 없음 |
| 오디오 / BGM | optional | optional_duck | optional |

상단:
...

timed 중단:
[블록 1 | 편집 00:00-00:03 | 원본 제안 ... | 상태 PROPOSED_SOURCE_TIMECODE]
...

중단 TTS 글자만 복사:
...

확인:
- 이 대본으로 갈까요? 예/아니오
- TTS는 사용자가 줄까요? 예/아니오
- Codex/API TTS 생성으로 갈까요? 예/아니오

상태:
- 사용자 OK 대기
- TTS_USER_DECISION_WAIT
- timeline_design_gate.json 확인
- humanize_korean_gate.json 확인

handoff:
- 다음 스킬: 000short-production-agent
- 다음 단계: 보고서2 / CAPCUT_OPENABLE_PROJECT
- 다음 채팅에 붙일 지시: Use $000short-production-agent
- 필요 조건: 보고서1 승인 + TTS/오디오 방식 결정
- 00-tikitaka는 보고서2를 작성하지 않는다
```

After 보고서1, stop until the user approves the script. Only after 사용자가 OK한 뒤
and one TTS route is chosen may the work move to 보고서2:

- 사용자 제공 TTS
- Codex/API TTS 생성
- no-TTS/source/BGM route explicitly approved

If the user approves the script and asks for CapCut, route to
`000short-production-agent` and mark the next stage as 보고서2로 이동.
The Tikitaka harness must also write `report1_handoff.json` with
`next_skill=000short-production-agent`; if it is missing, treat the package as
not ready for a new-chat stage-2 handoff.

CapCut base handoff note: `00-tikitaka` does not build CapCut, but when it names
the next production stage it must not name an old derived project as the base.
Unless the user explicitly names another root CapCut template later in
`000short-production-agent`, the stage-2 default base is `shrt white`.
`260707-Fk5D_FboO6M-game-character-comments-CAPCUT_v1`, `260708 short`,
`*_base_v2`, `*_base_v3`, and previous episode projects are prior derived/style
samples only.

## Default Boundary

Default state is `DRAFT_EYE_REVIEW`.

This skill owns only Korean Shorts remake scripting:

- hook candidates
- `우라까이`
- `상단`
- timed `중단`
- copy text that may later be used by a voice tool

Voice-copy text is part of the draft script only. This skill does not create
voice, audio files, SRT files, layout JSON, render plans, CapCut drafts, exports,
upload packages, or production packages.

## Supertone TTS Handoff

When the user says the script will become TTS/voice in a YouTube production,
make the handoff obvious, but do not generate audio from this skill.

- The production-side default TTS route is Supertone via:
  `${env:WORKSPACE_ROOT}\22factory_20260628\00_asset_tools\tools\make_supertone_tts.py`.
- On Windows, the safe launcher is `py -3.14`, not bare `python`.
- The script reads `SUPERTONE_API_KEY`, `SUPERTONE_VOICE_ID`,
  `SUPERTONE_PITCH`, `SUPERTONE_SPEED`, and `SUPERTONE_MODEL` from environment
  variables; never paste, print, or store the API key in chat, files, JSON,
  CapCut drafts, reports, or Git.
- On `home_windows`, User-scope Supertone variables may exist even when the
  current Codex process does not show them. The shared script checks Windows
  User environment as a fallback.
- Default voice/model are whatever the environment variables specify
  (`SUPERTONE_VOICE_ID` is currently the Chunsik setup on home_windows).
- If the user explicitly asks to generate audio, route to
  `000short-production-agent`; do not silently use Edge TTS, ElevenLabs,
  browser TTS, or any fallback provider.

If the user asks to make the video, create SRT/layout, build CapCut, render,
export, package upload files, or continue production, switch to
`000short-production-agent`.

If the user asks to polish an already-written script without production, switch
to `00script-writer`.

If the user asks about folder/root/rule policy, read `22utube-production-agent`
as a reference only.

## Active Root

For current 22utube work, check:

```text
${env:WORKSPACE_ROOT}\22factory_20260628\AGENTS.md
```

For new Tikitaka/Shorts script work, create or use an episode folder under:

```text
22factory_20260628\01_shorts_factory\episodes\SH_YYYYMMDD_slug
```

Legacy `11utube/11short` paths are read-only reference or explicit repair
targets unless the user asks for legacy work.

## Input Authority

Treat Gemini Shorts JSON, model summaries, pasted analysis, comments, and user
notes as source notes for remake scripting. They are not production truth.

Do not invent verified source timing, source dialogue, OCR, or scene order from
Gemini alone. Mark any proposed source range as
`PROPOSED_SOURCE_TIMECODE` until the user confirms it or a source-evidence tool
verifies it.

If source verification is needed before script confidence, use `watch` or the
current source-evidence workflow before claiming final timing.

## Story And Production Type Gate

Tikitaka must decide these before writing the first draft. This is the first
routing gate for Shorts remake work: the story structure decides how the script
opens and pays off, and the production type decides the audio, caption, and
later CapCut direction.

Required fields before drafting:

- `story_type`: one of the S1-S7 story structures below.
- `production_type`: one of the A-F production types below.
- `shorts_design_type`: one of `SD1`, `SD2`, `SD3`, `SD4`, or `unknown`.
  Use `unknown` when source ambiguity remains; do not force SD1-SD4 before the
  design evidence supports it.
- `audio_policy`: the high-level source/TTS/BGM choice.
- `caption_policy`: top, timed middle, quote, situation/card, or explicit
  template exception.
- `caption_layer_mix`: which visible text layers are expected.
- `source_speech_policy`: `verified_only`, `none_verified`, or
  `selected_verified_speech`.
- `card_asset_role`: `visual_situation_card` only for card/comment/community
  formats; otherwise `none`.

### Story Type Matrix (S1-S7)

```text
S1 reversal_preview    | 반전 선공개형       | 제일 센 장면을 앞에 먼저 보여줌
S2 ranking_reorder     | 랭킹 재배열형       | TOP-N, 순서 재배열 필수
S3 tikitaka_variety    | 티키타카/예능형    | 실제 대사/리액션/말맛 중심
S4 observation_caption | 관찰/상황설명형    | 화면 행동을 자막이 짚어줌
S5 emotion_payoff      | 감동 회수형         | 오해/긴장 -> 감정 회수
S6 info_explainer      | 정보/설명형         | 하나의 지식/사건을 쉽게 설명
S7 card_story          | 카드사연형          | 커뮤니티글/댓글/사연 카드화
```

Story type is not the same thing as production type. `반전형`, `랭킹형`,
`티키타카형`, and `카드사연형` are story structures; TTS/BGM, source audio,
speaker quotes, original audio preservation, and card assets are production
implementation choices.

Default caption policy is `top + timed_middle + situation_caption`.
yellow_lower_caption is not default. Use a yellow lower caption only when a
specific template explicitly locks it.

CapCut layers: T1/T2 top, T3 TTS, T4/T5 quote, T6 situation/card.

## Output Contract

Default chat output:

```text
쇼츠 유형
- story_type: S5 emotion_payoff
- production_type: narration_plus_speaker
- shorts_design_type: unknown
- audio_policy: tts_narration + selected_original_speech + bgm_optional
- caption_policy: top + timed_middle + situation_caption
- caption_layer_mix: top + timed_middle + quote/situation as needed
- source_speech_policy: verified_only
- card_asset_role: none
- template: none

상단
...

중단 초벌대본
[블록 1 | 편집 00:00-00:03 | 원본 제안 00:00-00:00 | 상태 PROPOSED_SOURCE_TIMECODE]
...

구간 오디오 정책표
1구간 | caption_type=speaker_quote | source_audio=on | tts=off | bgm=optional_duck
2구간 | caption_type=tts_narration | source_audio=off | tts=on | bgm=optional
...

중단 TTS 글자만 복사
...

1차설계서
| 트랙 / 시간 | 0-3초 | 3.1-4초 | 4.1-8초 |
| T1 | 텍스트 | 텍스트 | 텍스트 |
| T2 | 텍스트 | 텍스트 | 텍스트 |
| TTS | 없음 | 없음 | 텍스트 |
| "" 화자발언 A | 텍스트 | 텍스트 | 없음 |
| "" 화자발언 B | 없음 | 텍스트 | 텍스트 |
| () 상황설명 A | (행복한표정) | 없음 | 없음 |
| 영상 | source_visual | source_visual | source_visual |
| 오디오 / 나레이션·TTS | intro_narration | 없음 | 없음 |
| 오디오 / 화자발언·원본화자 | 없음 | source_audio | source_audio |
| 오디오 / SFX | 없음 | optional | 없음 |
| 오디오 / BGM | optional | optional_duck | optional |

상태
- script_status: DRAFT_EYE_REVIEW
- production_status: WAIT_EXPLICIT_000SHORT_REQUEST
- timeline_design_gate: PASS|WAIT|FAIL
- humanize_korean_gate.json: PASS|WAIT|FAIL
```

## Urakkai Edit-Order Handoff Contract

`urakkai` complete does not mean script-only complete. It means the short has a
block-by-block edit design that can be consumed by production. The downstream
target is `CAPCUT_EDIT_READY`, not upload-ready and not a final production pass.

Stage 1 = SCRIPT_LOCK_PACKAGE. This is the only stage this skill may lock. It
does not create CapCut, audio files, SRT, exports, or upload packages.

`SCRIPT_LOCK_PACKAGE` must contain:

- `shorts type locked`: `story_type`, `production_type`,
  `shorts_design_type`, and template direction.
- `source structure summary`: original title/core, source block order, and key
  source captions/dialogue.
- `urakkai structure locked`: changed viewpoint, hook, reversal, and emotional
  line.
- `1차설계서`: operator-facing CapCut timeline table with track/time rows.
- `timeline_design.json`: machine-readable design with protected time, track,
  caption role, and audio policy fields.
- `timeline_design_gate.json`: PASS before handoff.
- `humanize_korean_gate.json`: PASS after visible Korean cleanup and before
  `script_handoff_gate.json`.
- `wow point reordered`: strongest payoff/visual point moved to the edit order
  where it creates the best retention.
- `source-to-urakkai delta table`: original block -> remake block changes.
- `block role map`: each block marked as `"..."`, `(...)`, or TTS narration.
- `block audio map`: source_audio, TTS, SFX, and BGM policy by edit block.
- `tts_copy_text.txt`: narration-only copy text.
- `TTS copy body`: narration-only copy text.
- `source voice ON/OFF/duck ranges locked`: original/source voice switch ranges.

Status wording:

```text
script_status: SCRIPT_LOCK_PACKAGE
production_status: WAIT_CAPCUT_OPENABLE_PROJECT
```

Do not confuse this with final/upload lock. When `SCRIPT_HANDOFF_GATE` is PASS,
record:

```text
capcut_permission: CAPCUT_OPENABLE_PROJECT_ALLOWED
production_status: WAIT_CAPCUT_OPENABLE_PROJECT
```

`persona_mode/script_gate/n8n are FINAL_LOCK blockers`, not CAPCUT_OPENABLE_PROJECT blockers.
`final_report_allowed=false` means the final or upload report is blocked; it
does not block the second stage. continue to 000short-production-agent for
`CAPCUT_OPENABLE_PROJECT` when the handoff gate is PASS.

Required handoff files or equivalent machine-readable blocks before production
may start:

- `original_block_map`: source blocks in original order.
- `wow_point_map`: the strongest visual or emotional point to pull forward.
  `wow_overlay_text is optional`; the user may add these in CapCut manually.
- `urakkai_order_map`: original order vs remake order, for example
  `1-2-3-4-5 -> 4-3-5-1-2-3`.
- `timeline_design.json`: canonical design table for tracks, time ranges, text
  roles, video, and audio lanes.
- `timeline_design_gate.json`: design validation result.
- `humanize_korean_gate.json`: visible Korean cleanup result, with no protected
  structure changes.
- `edit_block_sequence`: the actual edit timeline order that production must
  implement.
- `block_map.json`: canonical source-of-truth map for every edit block.
- `block_role_map.json`: readable table for `"..."`, `(...)`, and TTS roles.
- `block_role_map`: readable table for `"..."`, `(...)`, and TTS roles.
- `block_voice_switch_map`: readable table for source audio, TTS, SFX, and BGM
  switching by edit block.
- `tts_copy_text.txt`: narration-only copy text. Text with
  `included_in_tts_copy=false` must not be placed into the TTS body.
- `tts_copy_text`: narration-only copy text.
- `script_handoff_gate.json`: the `SCRIPT_HANDOFF_GATE` result.

`block_map.json` must keep both source and edit identities:

```text
edit_id
source_block_id
original_order
urakkai_order
source_time
edit_time
mid_caption
caption_type
display_zone=middle_under_video
source_audio=on/off/duck
tts=on/off
audio_lane
sfx_policy
bgm_policy
source_range_status
exception_reason
```

Middle captions are one screen zone with different semantic roles. `"..."`,
`(...)`, and TTS-visible text all use `display_zone=middle_under_video`, directly
under the video. Do not move narration body text to a lower body-caption zone.

```text
"..."          -> caption_type=speaker_quote    -> source_audio=on,  tts=off
(...)          -> caption_type=situation_caption -> source_audio=off, tts=off by default
plain narration -> caption_type=tts_narration   -> source_audio=off, tts=on
```

Bottom/body captions are not a Tikitaka remake lane:

```text
bottom_body_caption_forbidden
```

`SCRIPT_HANDOFF_GATE` may set `capcut_allowed=true` only when the edit order,
roles, and audio switches are locked:

```json
{
  "gate_name": "SCRIPT_HANDOFF_GATE",
  "status": "PASS",
  "edit_blocks_locked": true,
  "caption_roles_locked": true,
  "voice_switch_locked": true,
  "capcut_allowed": true
}
```

Hard fails:

- `original_block_map`, `wow_point_map`, `urakkai_order_map`,
  `timeline_design.json`, `timeline_design_gate.json`,
  `humanize_korean_gate.json`, `edit_block_sequence`, `block_map.json`,
  `block_role_map`, `block_voice_switch_map`, `tts_copy_text`, or
  `script_handoff_gate.json` is missing when production handoff is requested.
- `speaker_quote` has no verified or explicitly proposed source range.
- `tts_narration` keeps `source_audio=on`.
- `situation_caption` has `tts=on` without an `exception_reason`.
- `capcut_allowed=true` appears before role and voice switch maps are locked.

Use `1/2/3/4/5` labels only as temporary source-range confirmation IDs, not as
the creative structure. The creative structure must be functional: hook,
misread, escalation, reversal, payoff, or another stated role.

## Segment Audio Policy Contract

Tikitaka must decide the segment audio policy at script time, before production
starts. `000short-production-agent` must validate and implement this plan; it
must not be the first place where quote/TTS/source-audio policy is guessed.

For every timed `중단` block, include one explicit row in `구간 오디오 정책표`.

Allowed values:

```text
caption_type:
- speaker_quote        = original/source speaker line, shown with "..."
- tts_narration        = generated voice narration
- situation_caption    = visual/situation explanation, shown with (...)
- tts_plus_source      = TTS while source audio remains intentionally audible
- ranking_item         = ranking/TOP-N beat

source_audio:
- on     = original/source video audio must be audible
- off    = original/source video audio must be muted
- duck   = original/source video audio remains low under TTS/BGM

tts:
- on
- off

bgm:
- optional       = no BGM is forced; user may choose it later
- optional_duck  = no BGM is forced; if user later chooses BGM, duck it here
- on             = BGM is explicitly required by the user or locked plan
- off            = no BGM in this segment
- duck           = required BGM remains low in this segment
```

Default mapping:

```text
"화자발언" / speaker_quote      -> source_audio=on,   tts=off, bgm=optional_duck
TTS 나레이션 / tts_narration    -> source_audio=off,  tts=on,  bgm=optional
(상황설명) / situation_caption  -> source_audio=off,  tts=off, bgm=optional
TTS+원본현장음 / tts_plus_source -> source_audio=duck, tts=on,  bgm=optional_duck
랭킹형 / ranking_item           -> source_audio=off by default; use on only for verified quote/reaction beats
```

BGM is never mandatory by default. Use `bgm=on` or `bgm=duck` only when the user
explicitly chose a BGM/SFX asset, asked for a specific music mood, or the locked
production plan names a BGM file. Otherwise keep BGM as `optional` or
`optional_duck` so production can continue without adding music.

If the user gives a remix such as `원본 1-2-3-4-5 -> 우라까이 4-3-1-5-2`,
audio policy follows the remixed timeline order, not the original source order.
Every row must keep both:

```text
source_order: original source segment id such as 1,2,3,4,5
timeline_order: remixed position such as 4,3,1,5,2
```

Narration is an audio authority, not disposable filler. If a TTS narration line
is longer than the planned visual beat, do not shorten or cut the narration in
the handoff. Mark the segment for production expansion instead:

```text
narration_duration_policy=preserve_full_tts
production_adjustment=extend_visual_or_shift_source_audio
```

The handoff must let production assemble separate lanes:

```text
narration=TTS lane
source_audio=on/off/duck by segment
bgm=separate optional/required lane
source_video_audio=muted unless explicitly extracted as source_audio
```

Example:

```text
구간 오디오 정책표
1구간 | source_order=4 | timeline_order=1 | caption_type=speaker_quote | source_audio=on | tts=off | bgm=optional_duck
2구간 | source_order=3 | timeline_order=2 | caption_type=tts_narration | source_audio=off | tts=on | bgm=optional
3구간 | source_order=1 | timeline_order=3 | caption_type=speaker_quote | source_audio=on | tts=off | bgm=optional_duck
4구간 | source_order=5 | timeline_order=4 | caption_type=tts_plus_source | source_audio=duck | tts=on | bgm=optional_duck
5구간 | source_order=2 | timeline_order=5 | caption_type=tts_narration | source_audio=off | tts=on | bgm=optional
```

When production is likely to continue, also provide a copyable JSON handoff:

```json
{
  "story_type": "emotion_payoff",
  "story_type_code": "S5",
  "production_type": "narration_plus_speaker",
  "shorts_design_type": "SD3",
  "audio_policy": "tts_narration + selected_original_speech + bgm_optional",
  "caption_policy": "top + timed_middle + situation_caption",
  "caption_layer_mix": ["top", "timed_middle", "quote", "situation_caption"],
  "source_speech_policy": "verified_only",
  "card_asset_role": "none",
  "tikitaka_segment_audio_plan": [
    {
      "segment_id": "seg_001",
      "source_order": 4,
      "timeline_order": 1,
      "edit_range": "00:00-00:03",
      "source_range_status": "PROPOSED_SOURCE_TIMECODE",
      "caption_type": "speaker_quote",
      "source_audio_policy": "on",
      "tts_policy": "off",
      "bgm_policy": "optional_duck",
      "visible_text_role": "speaker_quote"
    }
  ]
}
```

Hard fails:

- timed `중단` blocks exist but `구간 오디오 정책표` is missing
- `"..."` speaker quote block has `source_audio=off`
- TTS narration block keeps source audio `on` without explicit
  `caption_type=tts_plus_source`
- remixed order is shown, but `source_order` and `timeline_order` are not both
  recorded
- production handoff is requested, but no machine-readable
  `tikitaka_segment_audio_plan` is provided
- the first draft omits `story_type`, `production_type`, or
  `shorts_design_type` or sets it to a value outside
  `SD1|SD2|SD3|SD4|unknown`
- `instagram_card_tts` card/comment/community text is marked as
  `speaker_quote` or `tts_narration`
- `yellow_lower_caption` is used without an explicit locked template

## Shorts A-F Production Type Matrix

Before writing the draft, classify the video into one of 6 production types.
The type determines the entire audio/mute/TTS/caption/asset policy.

```text
코드 | production_type          | 이름                              | 오디오/자막 정책
A    | full_tts_bgm             | TTS 나레이션 + BGM형              | source_audio mostly off, TTS leads, BGM optional/on
B    | bgm_caption_only         | BGM 위주 + 자막형                 | TTS off, source audio off/low, captions lead
C    | narration_plus_speaker   | 나레이션 + 화자발언형             | TTS explanation + selected verified source speech
D    | original_audio_caption   | 원본음성 살림 + 번역/해설자막형   | original/source audio leads, Korean captions support
E    | tts_intro_original_body  | TTS 도입 + 원본 후킹형            | first 2-5s TTS, then original/source body leads
F    | instagram_card_tts       | 인스타/커뮤니티 카드형            | card/comment/community/story asset + TTS/BGM
```

### F Card Role Rule

`instagram_card_tts` is a production format, not a dialogue type. In the script
and handoff, card/comment/community/story card text is treated as a visual
situation/card asset:

```text
production_type=instagram_card_tts
caption_type=situation_caption
visible_text_role=situation
capcut_text_layer=T6
card_asset_role=visual_situation_card
not speaker_quote
not tts_narration
```

This means a card image, comment card, community post card, or story card is
shown as `(상황설명)`, `(댓글 카드 표시)`, `(커뮤니티 글 카드 표시)`, or
`(사연 카드 이미지 표시)`. It is not a verified source speaker line, not a
source quote, and not the TTS narration body itself.

### Muting Decision Rule

```text
원본 음성 ON  → 해당 구간이 "" 화자발언으로 표기되어 있을 때
원본 음성 OFF → "" 가 아닌 구간 (TTS/자막/BGM만 쓸 때)
예외          → "" 구간이더라도 원본 음질이 너무 나쁘면 TTS로 대체 (작가 판단)
```

### Per-Type Mute Detail

- **A full_tts_bgm**: source audio mostly off. Use TTS narration as the main
  carrier and keep BGM optional unless the user/template locks it.
- **B bgm_caption_only**: TTS off. Source audio off/low unless a verified
  reaction beat is intentionally preserved.
- **C narration_plus_speaker**: TTS explains the arc; only verified source
  speaker lines use `speaker_quote` and source audio on/duck.
- **D original_audio_caption**: original/source audio is the main carrier.
  Korean captions translate, explain, or frame the source.
- **E tts_intro_original_body**: TTS only establishes context in the first 2-5s;
  the body follows original/source audio unless a later segment explicitly
  switches policy.
- **F instagram_card_tts**: card/comment/community/story visual assets plus
  TTS/BGM. Card text uses `caption_type=situation_caption` and
  `card_asset_role=visual_situation_card`, never `speaker_quote`.

## Shorts Design Type Matrix (SD1-SD4)

`shorts_design_type` is the practical Shorts 설계유형. It does not replace
`story_type` or `production_type`; it locks how TTS, BGM, verified quotes, and
situation captions are mixed in the 1차설계서 and `timeline_design.json`.

Allowed values:

```text
SD1
SD2
SD3
SD4
unknown
```

```text
코드 | 설계 의미
SD1  | TTS나레이션초반 only 이후 BGM/자막형
SD2  | TTS 설명 / BGM형
SD3  | TTS 설명 / "" 화자발언 / () 상황설명형
SD4  | "" 화자발언 / () 상황설명 / TTS 혼합형
unknown | source/design ambiguity remains
```

### SD1 Intro TTS Then BGM Caption

Use when TTS should hook only the first 2-5 seconds, then the video continues
with BGM, visual captions, or light situation captions. Source audio is off by
default except for explicitly verified reaction or quote beats.

### SD2 TTS Explain BGM

Use when TTS explanation carries the whole short and BGM is the support bed.
Most source audio stays off, and verified `"..."` 화자발언 is absent or rare.

### SD3 TTS Explain Quote Situation

Use when TTS explains the arc, selected verified source speech appears as
`"..."` 화자발언, and visual/emotional context appears as `()` 상황설명. This is
the default mixed remake design for many Tikitaka Shorts.

### SD4 Quote Situation TTS Mix

Use when verified `"..."` 화자발언, `()` 상황설명, and TTS are all active across
the timeline. Every segment must lock source_audio on/off/duck, tts on/off, and
BGM/SFX policy before handoff.

## Dual Writer Mode (우라까이/와우포인트/유형 확정)

When confirming wow point, urakai structure, story type, and production type,
use two real CLI-based writer agents to debate before locking.

### CLI Tools

- **Writer A (Codex CLI / GPT 5.5)**: aggressive hook, emotional escalation,
  retention-first, willing to dramatize for engagement.
  ```bash
  codex exec "당신은 GPT 5.5 작가모드입니다. ... <분석 지시> ..." 2>&1
  ```
- **Writer B (Claude CLI / GLM 6.2)**: fact-grounded, structural balance,
  risk-aware, prioritizes coherence and policy safety.
  ```bash
  claude -p --bare --dangerously-skip-permissions "당신은 GLM 6.2 작가모드입니다. ... <분석 지시> ..." 2>&1
  ```

### Debate Protocol

1. **Round 1**: Both CLIs receive the same video context independently.
   Each outputs: type recommendation, wow point, urakai, disagreement point.
2. **Round 2**: Share Round 1 outputs cross-wise. Each CLI responds:
   동의/부분동의/유지 with reasoning.
3. **Synthesis**: The orchestrator resolves cross-convergence (both writers
   moving to each other's position = middle ground) into a final decision.

Both writers must output:
- recommended `story_type` (S1-S7) with reasoning
- recommended `production_type` (A-F canonical code) with reasoning
- recommended `shorts_design_type` (`SD1`, `SD2`, `SD3`, `SD4`, or `unknown`)
  with reasoning
- wow point confirmation or correction
- urakai structure recommendation
- one concrete disagreement point

The final decision is the synthesis of both perspectives. If they disagree on
production type, the higher-audio-fidelity type wins unless the source has no
usable speech at all. If they disagree on story type, the type that best
preserves the strongest source-backed viewer question wins.

## Draft Workflow

1. State the frame: what situation the remake is using and why.
2. **Run Story And Production Type Gate**: choose `story_type`,
   `production_type`, `shorts_design_type`, audio policy, caption policy,
   source speech policy, and card asset role before the first draft.
3. Map source notes into functional beats.
4. Write hook candidates if requested or useful.
5. **Run dual writer mode** to confirm wow point, urakai, story type, and
   production type.
6. Produce `1차설계서`: a CapCut-style time/track layout table, not an abstract
   script report.
7. Write `timeline_design.json` from the same layout and pass
   `timeline_design_gate.json`.
8. Run Humanize Korean on visible text only and record
   `humanize_korean_gate.json` before handoff.
9. Produce `상단 + timed 중단`, `block_map.json`, `block_role_map.json`,
   `block_voice_switch_map.json`, and `tts_copy_text.txt` from
   `중단 TTS 글자만 복사`.
10. Run `SCRIPT_HANDOFF_GATE`; keep status at `DRAFT_EYE_REVIEW` unless the
    user explicitly asks for the next owner.

## Shorts TTS Storytelling Mode

If a Shorts remake can be told as TTS narration, story, or 썰풀이, this mode is
mandatory, not optional.

This mode is not separate from 우라까이. 우라까이는 the baseline condition: the
remake must not keep the same expression, scene-entry order, emotional angle, or
payoff wording. The TTS story gate decides how aggressively the same visual
source must be reframed through a stronger writer premise.

Do not start as a flat event summary. Lead with the strongest hookable
emotional premise, deadline, loss, desire, misunderstanding, or irreversible
action. In Tikitaka writer mode, the hook is allowed to use a plausible dramatic
premise that is not directly verifiable when it is needed to make the story work,
especially for TTS-heavy videos with little or no source speech.

If the user says `후킹 쎄게`, `작가모드`, `우라까이`, or directly corrects the
agent to make the opening more provocative, treat that as a hard routing signal:
choose `hook_first_writer_premise` unless the video is clearly an information,
news, politics, medical, legal, safety, accident, crime, finance, or other
fact-first lane. Ask the user only when the lane is genuinely unclear.

```text
weak: 할아버지가 손자를 만났다
strong: 시한부 할아버지가 마지막으로 손자를 보러 왔다
```

The strong version is a writer premise, not source evidence. Use it when it fits
the visual/emotional arc and creates a better hook. Do not flatten the opening
just because the premise is not independently verified.

For example, if the source only proves "a soldier met his daughter at a
graduation ceremony", do not write the flat version first. Build a hookable
story premise such as:

```text
못 만날 줄 알았던 딸이,
수료식장에 와 있었습니다.
```

or:

```text
수료식만 끝나면 다시 기다려야 할 줄 알았습니다.
그런데 뒤돌자마자, 딸이 품에 안겼습니다.
```

This is valid Tikitaka story framing even when the source does not prove the
father literally heard "she cannot come." The public script may use the premise
to create curiosity; internal reports must still avoid calling it verified
source evidence.

Avoid only inventions that create a materially different or harmful claim, such
as crime accusations, medical diagnoses, death, abuse, political/news claims,
or other high-risk facts that would change the video's basic meaning. For
ordinary emotional/family/TTS story hooks, prefer dramatic premise over flat
fact-reporting.

Required TTS story fields:

- `tts_story_mode_required: true|false`
- `truth_mode: fact_first|hook_first_writer_premise`
- `source_supported_emotional_condition`
- `writer_premise_for_hook`
- `writer_premise_status: verified|plausible_unverified|fictionalized_hook`
- `flat_event_summary`
- `emotional_entry_line`
- `changed_scene_entry_order`
- `changed_korean_expression_strategy`
- `viewer_emotion_target`
- `payoff_recovery_line`

For emotional story/remake Shorts, prefer:

- person before explanation
- loss or deadline before background
- concrete action before abstract feeling
- one emotional question before the answer
- final line that returns to the first emotional anchor

Do not over-explain visible action when TTS is the main carrier. Use captions to
hit the emotional angle and leave simple visuals to do their own work.

Hard fails:

- flat event summary when TTS narration can carry the story
- synonym-only Korean replacement
- same source flow with only different words
- refusing a strong hook only because the emotional premise is not directly
  verifiable in a TTS-heavy ordinary story
- invented high-risk facts such as illness, death, crime, abuse, political/news
  claims, or other materially harmful claims unless the source actually supports
  them
- emotionally strong wording where a first-time viewer cannot tell who wants
  what and what may be lost

## Required Gates Before Stronger Claims

- Do not claim `SCRIPT_LOCK` from this skill alone.
- Do not claim production allowed.
- Do not claim source-verified truth from raw Gemini notes.
- Do not run `SCRIPT_HANDOFF_GATE` before `timeline_design_gate.json` and
  `humanize_korean_gate.json` are PASS.
- Do not skip human Korean cleanup before any final visible Korean text.
- Do not proceed past missing source evidence when the script depends on exact
  timing, OCR, or dialogue.
- Do not call a TTS-capable story/remake draft eye-ready unless the TTS
  storytelling mode has been considered and, when applicable, the emotional
  entry line is source-supported and non-flat.

## Reference Routing

- Active Shorts script analysis authority is
  `shorts_script_analysis_single_source_v20260706.md`; apply it before any
  reference file below.
- For hook review, read `references/pre_script_hook_review.md`.
- For Shorts craft rules, read `references/shorts-academy.md`.
- For old contract details or legacy repair only, read
  `references/archived-full-skill-20260629.md`.

Keep this `SKILL.md` as the active router. Do not re-expand it with legacy
examples, PASS templates, production reports, CapCut details, or long handoff
instructions.

---
name: 00-tikitaka
description: Use only when the user explicitly asks for Tikitaka Korean Shorts source analysis, remake scripting, 티키타카 하자, 우라까이, hook candidates, 상단/timed 중단 draft creation, Gemini raw intake for Shorts URLs, or Gemini Shorts source notes. Do not use for SRT, CapCut, production packages, or polishing-only existing scripts.
---

# 00 Tikitaka

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

## Continuation Mode Gate

When the user provides a Shorts URL plus Gemini/source notes and asks to
`진행`, `해`, `끝까지`, `골기능`, `캣컵프로젝트파일까지`, `CapCut project`, or
equivalent project-file completion, mark the handoff as:

```text
URL_PLUS_GEMINI_PLUS_PROJECT_FILE
AUTO_FULL_CAPCUT_PROJECT
```

Do not stop at DRAFT_EYE_REVIEW when the user explicitly asks for project-file completion.
In that case, this skill still owns only the urakkai/script decision, but it
must prepare a production-ready handoff and route to `000short-production-agent`
without requiring another generic permission question.

Use `INTERACTIVE_SCRIPT_APPROVAL` when the user asks to choose or decide during
the script process. Stop and ask at the requested checkpoints:

```text
URAKKAI_DIRECTION_CHECKPOINT
SCRIPT_APPROVAL_CHECKPOINT
TEMPLATE_APPROVAL_CHECKPOINT
```

Use `DRAFT_FAST_EXPLICIT_ONLY` only when the user explicitly says `DRAFT_FAST`,
`빠른 초안`, `기술 초안`, `초안만`, `검토용 draft만`, or a clear equivalent.
Do not choose DRAFT_FAST just because the output is not upload-ready.

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

상태
- script_status: DRAFT_EYE_REVIEW
- production_status: WAIT_EXPLICIT_000SHORT_REQUEST
```

## Urakkai Edit-Order Handoff Contract

`urakkai` complete does not mean script-only complete. It means the short has a
block-by-block edit design that can be consumed by production. The downstream
target is `CAPCUT_EDIT_READY`, not upload-ready and not a final production pass.

Stage 1 = SCRIPT_LOCK_PACKAGE. This is the only stage this skill may lock. It
does not create CapCut, audio files, SRT, exports, or upload packages.

`SCRIPT_LOCK_PACKAGE` must contain:

- `shorts type locked`: `story_type`, `production_type`, and template direction.
- `source structure summary`: original title/core, source block order, and key
  source captions/dialogue.
- `urakkai structure locked`: changed viewpoint, hook, reversal, and emotional
  line.
- `wow point reordered`: strongest payoff/visual point moved to the edit order
  where it creates the best retention.
- `source-to-urakkai delta table`: original block -> remake block changes.
- `block role map`: each block marked as `"..."`, `(...)`, or TTS narration.
- `block audio map`: source_audio, TTS, SFX, and BGM policy by edit block.
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
- `edit_block_sequence`: the actual edit timeline order that production must
  implement.
- `block_map.json`: canonical source-of-truth map for every edit block.
- `block_role_map`: readable table for `"..."`, `(...)`, and TTS roles.
- `block_voice_switch_map`: readable table for source audio, TTS, SFX, and BGM
  switching by edit block.
- `tts_copy_text`: narration-only copy text. Text with
  `included_in_tts_copy=false` must not be placed into the TTS body.
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
  `edit_block_sequence`, `block_map.json`, `block_role_map`,
  `block_voice_switch_map`, `tts_copy_text`, or `script_handoff_gate.json` is
  missing when production handoff is requested.
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
- the first draft omits `story_type` or `production_type`
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
   `production_type`, audio policy, caption policy, source speech policy, and
   card asset role before the first draft.
3. Map source notes into functional beats.
4. Write hook candidates if requested or useful.
5. **Run dual writer mode** to confirm wow point, urakai, story type, and
   production type.
6. Produce `상단 + timed 중단` with type-appropriate audio policy.
7. Provide the copy-only voice text block as script text, not as audio work.
8. Keep status at `DRAFT_EYE_REVIEW` unless the user explicitly asks for the
   next owner.

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
- Do not skip human Korean cleanup before any final visible Korean text.
- Do not proceed past missing source evidence when the script depends on exact
  timing, OCR, or dialogue.
- Do not call a TTS-capable story/remake draft eye-ready unless the TTS
  storytelling mode has been considered and, when applicable, the emotional
  entry line is source-supported and non-flat.

## Reference Routing

- For hook review, read `references/pre_script_hook_review.md`.
- For Shorts craft rules, read `references/shorts-academy.md`.
- For old contract details or legacy repair only, read
  `references/archived-full-skill-20260629.md`.

Keep this `SKILL.md` as the active router. Do not re-expand it with legacy
examples, PASS templates, production reports, CapCut details, or long handoff
instructions.

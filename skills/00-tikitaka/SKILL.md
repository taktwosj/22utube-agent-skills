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
tikitaka_source_request.json
-> source evidence
-> source_identity_lock.json + verified source_fingerprint_sha256
-> SOURCE_VOICE_SEPARATION_GATE
-> 10_analysis/audio/full_source_audio.wav
-> 10_analysis/audio/vocals.wav
-> 1차설계서
-> timeline_design.json
-> caption_beat_map.json
-> timeline_design_gate.json
-> chatgpt_review/round1_review_packet.md
-> chatgpt_review/round1_chatgpt_raw.md
-> chatgpt_review/round1_codex_decisions.json
-> humanize_korean_gate.json
-> block_map.json / block_role_map.json / block_voice_switch_map.json
-> tts_copy_text.txt
-> tts_duration_probe.json
-> tts_timing_reconciliation_gate.json
-> chatgpt_review/round2_audit_packet.md
-> chatgpt_review/round2_chatgpt_raw.md
-> chatgpt_review_gate.json
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
edit_id/source_ref/source_order/timeline_order/assembly_role/
caption_type/visible_text_role/audio_role/time_start/time_end/track/
duration_basis/duration_status/audio_policy/visual_strategy
```

`timeline_design_gate.json` must be PASS before the design can be treated as a
handoff artifact.

## Full-Source Demucs Preprocessing

After `source_identity_lock.json` and before `1차설계서`, run:

```text
source.mp4
-> extract the complete audio to 10_analysis/audio/full_source_audio.wav
-> run Demucs on that complete WAV with separation_scope=FULL_SOURCE_AUDIO
-> save the stable vocal stem as 10_analysis/audio/vocals.wav
-> validate SOURCE_VOICE_SEPARATION_GATE
-> identify and lock speaker ranges from vocals.wav
```

Invoke:

```powershell
py -3 skills/00-tikitaka/scripts/prepare_source_voice.py --root <episode-root> --source 00_source/source.mp4
```

This is a narrow Stage 1 source-analysis preprocessing exception. It creates
only the full-source analysis WAV and Demucs vocal stem. It does not create Q
clips, TTS, SRT, CapCut, render, export, upload, or other production assets.
The harness calls `validate_source_voice_separation.py`; it never launches
Demucs or the next skill.

The only valid skip is:

```text
NOT_REQUIRED_NO_SOURCE_SPEECH
```

Use it only when the source has no audio stream or when the user/source
evidence explicitly confirms that no human speech exists. Missing Demucs is
`WAIT_DEMUCS_AVAILABLE`; never fall back to mixed source audio.

Every `speaker_quote` must record:

```json
{
  "source_audio_ref": "10_analysis/audio/vocals.wav",
  "source_audio_provenance": "demucs_full_source_vocals"
}
```

Missing or different provenance is `WAIT_SOURCE_VOICE_Q_PROVENANCE`.
`source_audio=on` now means the separated speaker/Q lane is audible. It never
authorizes embedded source-video audio in CapCut. `no_vocals.wav` is not used.

## Vmake Clean Visual Preprocessing

When the user requests `stage_2_full`, CapCut, or an automatic production run,
prepare a second video through Vmake after `source_identity_lock.json` exists:

```text
00_source/source.mp4
-> source identity, OCR, STT, frame checks, full-source Demucs

Vmake link import
-> 00_source/clean_source.mp4
-> production visual only
-> embedded_audio_policy=muted_always
```

The original `source.mp4` remains the only analysis and source-truth video.
Never replace it with the Vmake result for OCR, STT, timing verification,
source identity, or Demucs. The Vmake result is the later production visual;
its embedded audio is never authorized.

### User-Confirmed Existing Vmake Result

Use `USER_CONFIRMED_VMAKE_REUSE` only when the user explicitly says the Vmake
result is already complete or confirmed and also says not to download or test
it again. This current-request instruction overrides the default Vmake browser,
download, registration, and validation steps below for the named existing clean
files.

- Do not open Vmake, download or re-download, replay, inspect, or re-analyze the
  confirmed clean files.
- Do not run `register_vmake_clean_source.py` or `validate_vmake_clean_source.py`.
  Do not run ffprobe duration/aspect-ratio
  parity, OCR, STT, frame analysis, or visual quality review on those files.
- Keep the original-source analysis, timing, edit order, captions, and audio plan unchanged.
  The clean files replace only the production visuals, one-for-one
  and in the already approved order.
- Keep every clean file's embedded audio muted. Use only the separately approved
  narration/source-audio lanes.
- Place the user-specified narration at the first scene when the user requests
  that placement. Do not redesign later beats merely because the visual file was
  cleaned.
- Pass the existing clean paths and this reuse state to
  `000short-production-agent`; `00-tikitaka` still does not build CapCut.

Record:

```text
vmake_reuse_mode=USER_CONFIRMED_NO_REDOWNLOAD_NO_RETEST
user_vmake_confirmation=true
analysis_authority=original_sources
timeline_authority=existing_approved_design
clean_visual_review_status=USER_CONFIRMED
```

This is a user-confirmed reuse state, not a newly agent-validated
`VMAKE_CLEAN_SOURCE_GATE=PASS`. If any named existing clean file is missing or
inaccessible, stop with `WAIT_EXISTING_VMAKE_CLEAN_FILE`; do not start a new
Vmake download unless the user asks.

Read `references/vmake_clean_source_workflow.md` before browser action. Use the
existing signed-in Chrome session and browser DOM control. Do not use OS-level
mouse/keyboard control. The workflow covers `Import from link`, the rights
checkbox, `Apply`, `Processing...`, `Download`, IDM/browser interception, and
the exact signed-download recovery rule.

Rights confirmation is URL-specific. Check Vmake's rights checkbox only when
the user explicitly authorized it for the current source. Otherwise stop with:

```text
WAIT_VMAKE_RIGHTS_CONFIRMATION
```

After download, register and validate:

```powershell
py -3 skills/00-tikitaka/scripts/register_vmake_clean_source.py --root <episode-root> --download <File_from_link_*.mp4> --source-url <shorts-url> --job-id <vmake-job-id> --rights-confirmed --confirmation-source user
py -3 skills/00-tikitaka/scripts/validate_vmake_clean_source.py --root <episode-root>
```

The validator writes no production assets. It verifies
`VMAKE_CLEAN_SOURCE_GATE`, the locked source/video ID, the Vmake job and
download filename, clean-file hash, duration/aspect-ratio parity, and:

```text
00_source/clean_source.mp4
embedded_audio_policy=muted_always
source_voice_policy=separate_demucs_q_only
```

For `stage_1_script`, this gate is `NOT_REQUIRED_STAGE1_ONLY`. For
`stage_2_full`, missing or invalid clean visual evidence is
`WAIT_VMAKE_CLEAN_SOURCE`. The harness validates the manifest only; it never
opens Vmake, clicks the UI, downloads a file, or launches the next skill.

## CAPTION_BEAT_MAP_HANDOFF

Every timed middle-caption row that continues to CapCut must carry a reference
to `caption_beat_map.json`. This is the timing contract for visible text; it is
not a TTS audio file and it does not replace `tts_duration_probe.json`.

Each beat records `beat_id`, `edit_id`, `caption_role`, `audio_basis`, `text`,
`start_sec`, `end_sec`, `timing_source`, `max_chars_per_line`, `max_lines`,
and `y`. The design owner assigns the semantic role and the production skill
resolves the CapCut text track. A missing beat map blocks Stage 2 with
`CAPTION_BEAT_MAP_REQUIRED`.

The handoff preserves these production profiles:

```text
profile_version=caption_profiles_v2
TTS: y=-900, max_chars_per_line=10, max_lines=1
speaker_quote: y=-500, max_chars_per_line=10, max_lines=1
situation_caption: y=700, max_chars_per_line=10, max_lines=1
video_scale=1.20
face_avoidance=fixed_lower_safe_zone_v1
```

`audio_basis` distinguishes `tts_audio`, `source_speech`, and `caption_only`.
The caption beat map controls visible-text timing only; it must never shorten
source speech or TTS audio.

Humanize Korean runs after the 1차설계서 is structurally fixed and before the
handoff gate. Humanize may change wording only: visible Korean in T1/T2/TTS,
`"" 화자발언`, and `() 상황설명`. It must not change time ranges, track rows,
caption roles, edit order, audio policy, verified quotes, source facts, names,
numbers, or the separation between quote/situation/TTS roles. Record the result
as `humanize_korean_gate.json` with `humanize_korean_gate.json status=PASS`.

Do not run SCRIPT_HANDOFF_GATE before humanize_korean_gate.json status=PASS. If
Humanize needs a structural change, return to Tikitaka design repair instead of
silently patching the script.

Wording polish is an optional pass inside this skill when the user explicitly
asks for a rewrite or when the 1차설계서 text fails readability/hook pressure.
That pass may patch wording only; it may not change
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

## Assembly Role Sequence Contract

`00-tikitaka` does not only reorder source blocks.

The purpose of Tikitaka design is to create a new editable Shorts assembly plan:
the sequence of narration audio, visible captions, verified speaker quotes,
situation captions, source video, source audio, TTS audio, SFX, and BGM policy.

`source_order` records where the material came from.
`timeline_order` records where it appears in the remake.
`assembly_role` records what function the segment performs in the new Shorts
design.

A valid Tikitaka design may transform:

```text
source 1-2-3-4-5
```

into a new role sequence such as:

```text
TTS narration -> situation caption -> speaker quote -> TTS narration -> payoff quote
```

or:

```text
narration -> caption -> caption -> speaker quote -> situation caption
```

This is not a script rewrite after handoff. This is the Stage 1 design itself.

Production must implement this assembly role sequence without reinterpretation.

## Assembly Role Enum

Allowed `assembly_role` values:

```text
intro_narration
context_narration
payoff_narration
ending_narration
verified_speaker_quote
situation_caption
reaction_caption
card_or_comment_caption
source_visual_hold
source_visual_action
transition_or_separator
ranking_item
```

Meaning:

```text
caption_type = 자막/오디오의 종류
assembly_role = 쇼츠 안에서 이 beat가 수행하는 기능
source_order = 원본에서 몇 번째 재료인가
timeline_order = 리메이크에서 몇 번째로 보여주는가
```

Examples:

```json
{
  "caption_type": "tts_narration",
  "assembly_role": "intro_narration"
}
```

```json
{
  "caption_type": "situation_caption",
  "assembly_role": "reaction_caption"
}
```

## TTS Caption vs Narration Audio

`TTS` alone can mean visible text only. It does not automatically mean an audio
file exists or must be generated.

Narration audio is locked only when the design explicitly uses a narration
signal such as:

```text
caption_type=tts_narration
audio_role=audio.narration_tts
오디오 / 나레이션·TTS
```

If the segment is only a visible TTS-style caption, use:

```text
caption_type=tts_caption
audio_role=none
```

`tts_duration_probe.json` and `tts_timing_reconciliation_gate.json` are required
only for narration-audio segments, not for TTS caption-only text.

## Duration Basis Enum

Allowed `duration_basis` values:

```text
source_range
estimated_tts_duration
actual_tts_duration
fixed_design_duration
visual_hold
```

Allowed `duration_status` values:

```text
SOURCE_AUDIO_LOCKED
ESTIMATED_ACCEPTED
ACTUAL_AUDIO_LOCKED
FIXED_DESIGN_LOCKED
WAIT_ACTUAL_TTS_AUDIO
```

## TTS Timing Reconciliation Gate

If any `caption_type=tts_narration` or `audio_role=audio.narration_tts` segment
exists, Tikitaka must distinguish estimated timing from actual-audio timing.

Before final `SCRIPT_HANDOFF_GATE`, one of these must be true:

1. `tts_duration_status=ESTIMATED_ACCEPTED`
   - no actual TTS audio file is available yet
   - timeline uses estimated narration duration
   - Stage 2 must stop with `WAIT_TTS_TIMING_RELOCK` if generated/provided audio exceeds tolerance

2. `tts_duration_status=ACTUAL_AUDIO_LOCKED`
   - actual TTS/audio duration was measured
   - `timeline_design.json` was reconciled to the measured duration
   - `tts_timing_reconciliation_gate.json` is PASS

Actual TTS duration must not be solved by cutting narration.

If actual narration is longer than the planned visual beat, return to Tikitaka
design repair unless the locked design explicitly allows one of:

```text
none
extend_visual
shift_later_beats
hold_frame
freeze_frame
repeat_visual
shorten_text_and_regenerate_tts
```

`tts_duration_probe.json` shape:

```json
{
  "status": "PASS",
  "source": "user_tts_audio|generated_tts|estimated_text",
  "tts_items": [
    {
      "edit_id": "E1",
      "tts_text_ref": "tts_001",
      "text": "이 사람이 성공한 이유는 3가지라고 합니다.",
      "planned_duration_sec": 3.0,
      "actual_duration_sec": 4.0,
      "estimated_duration_sec": null,
      "delta_sec": 1.0,
      "within_tolerance": false,
      "reconciliation_action": "extend_visual"
    }
  ]
}
```

`tts_timing_reconciliation_gate.json` shape:

```json
{
  "status": "PASS",
  "gate_name": "TTS_TIMING_RECONCILIATION_GATE",
  "duration_basis": "actual_audio|estimated_text",
  "tts_duration_status": "ACTUAL_AUDIO_LOCKED|ESTIMATED_ACCEPTED",
  "timeline_design_updated": true,
  "protected_fields_changed": true,
  "change_reason": "actual TTS duration exceeded planned slot",
  "reconciliation_action": "extend_visual",
  "requires_new_timeline_design_gate": true,
  "requires_new_humanize_korean_gate": true,
  "requires_new_script_handoff_gate": true
}
```

`protected_fields_changed=true` is allowed only inside design repair before
`SCRIPT_HANDOFF_GATE`. After `SCRIPT_HANDOFF_GATE`, protected field changes are
forbidden.

## User Design Revision Loop

If the user changes the assembly order, narration order, role sequence,
duration, or audio policy after seeing `1차설계서`, this is not Humanize.

It is Tikitaka design repair.

Examples:

```text
34215 구조를 32145로 변경
나레이션을 먼저 넣기
화자발언을 뒤로 밀기
TTS 3초 구간을 실제 음성 4초에 맞추기
상황설명 beat를 추가하기
speaker_quote를 TTS narration으로 바꾸기
나레이션 -> 자막 -> 자막 -> 화자발언 순서로 변경하기
```

When design repair occurs, invalidate and regenerate:

```text
1차설계서
timeline_design.json
caption_beat_map.json
timeline_design_gate.json
humanize_korean_gate.json
block_map.json
block_role_map.json
block_voice_switch_map.json
tts_copy_text.txt
tts_duration_probe.json
tts_timing_reconciliation_gate.json
chatgpt_review/round1_review_packet.md
chatgpt_review/round1_chatgpt_raw.md
chatgpt_review/round1_codex_decisions.json
chatgpt_review/round2_audit_packet.md
chatgpt_review/round2_chatgpt_raw.md
chatgpt_review_gate.json
script_handoff_gate.json
report1_handoff.json
```

Humanize may only change Korean wording. Humanize must not change
`assembly_role`, `source_order`, `timeline_order`, time ranges, `caption_type`,
`audio_policy`, `duration_basis`, or semantic audio lanes.

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

## Optional Gemini Raw Observation

Gemini is optional raw observation, not an intake gate.

Use this routing order:

1. If Gemini JSON or notes are already supplied, do not rerun Gemini. Read them
   as unverified raw observation notes for likely `T1`, `T2`, TTS, `""`
   speaker quotes, `()` situation captions, and useful source ranges.
2. If no Gemini result is supplied and a URL or local source is available,
   acquire or confirm `source.mp4` and continue with direct source analysis.
3. Run the AI Studio raw-intake path only when the user explicitly asks for Gemini,
   AI Studio analysis, or Gemini raw notes.

Do not block Tikitaka only because Gemini raw intake is absent.
Gemini failure alone is not a WAIT condition when source media is available or can be acquired.
Final timing, dialogue, OCR, source identity, and design decisions must come from
`source.mp4`, ffprobe, STT, OCR, and frame checks. Gemini ranges and labels remain
`PROPOSED_SOURCE_TIMECODE` until that verification is complete.

When Gemini is explicitly requested, use the complete second-by-second
raw-observation prompt in `references/gemini_raw_intake_prompt.md`. Require this
exact completion value before accepting the response:

```text
final_warning_ko=이 JSON은 Gemini 초벌 초단위 관찰값이다. 최종 대본, 화자발언 확정, 컷타이밍, TTS/상황설명 배치, CapCut 제작은 Codex가 source.mp4와 STT/OCR/프레임 검증으로 확정해야 한다.
```

Save the result as JSON/Markdown through AI Studio web UI automation.

For unattended/background work, use the shared no-API dedicated-profile runner:

```powershell
$env:PYTHONPATH = ""
py -3 "$env:USERPROFILE\OneDrive\22utube\22factory_20260628\00_asset_tools\ai_studio_runner\scripts\run_ai_studio_short.py" "<SHORTS_URL>" --retries 0 --run-timeout-sec 240
```

Compatibility wrapper:

```powershell
powershell -ExecutionPolicy Bypass -File "$env:USERPROFILE\OneDrive\22utube\22factory_20260628\00_asset_tools\tools\gemini_raw_paste_run.ps1" -Url "<SHORTS_URL>"
```

When the user explicitly asks to watch or control ordinary Chrome, use the
normal-Chrome extension instead of forcing the dedicated profile:

```text
%USERPROFILE%\OneDrive\22utube\22factory_20260628\00_asset_tools\browser_extensions\ai-studio-shorts-runner
```

This Chrome extension is allowed because it is still AI Studio web UI only. It
pastes the Shorts URL first, waits at least 3 seconds for the `YouTube Video`
attachment, pastes the URL-free prompt, submits with Ctrl+Enter, and copies the
last fresh Model JSON. URL context is not required for this attachment flow.
The CDP runner uses this extension artifact
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
  mismatch, report the Gemini result as unavailable. Continue through direct
  source analysis when `source.mp4` is available or can be acquired. Use a WAIT
  state only when the required source evidence is also unavailable.
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
- The extension bridge result is accepted only when all run-binding fields are
  present: `playgroundStatus=VERIFIED_NEW_CHAT`,
  `urlContextStatus=NOT_REQUIRED_YOUTUBE_ATTACHMENT`,
  `urlStageVerified=true`, `mediaAttachmentStatus=VERIFIED_YOUTUBE_VIDEO`,
  `promptStageVerified=true`, `promptStageUrlAbsent=true`,
  `promptInputMode=SEQUENTIAL_URL_THEN_PROMPT`, and `generationStarted=true`.
- Generate a unique internal `run_nonce` per attempt and verify it in the
  extension bridge/run manifest. Do not inject `run_nonce`, `source_video_id`,
  or `observed_source_title` into the Gemini prompt and do not require Gemini
  JSON to echo them. Bind the requested URL/video id/title/duration using trusted
  yt-dlp metadata, the verified YouTube attachment, and the saved run manifest.
- Missing URL metadata, title/duration/id mismatch, a stale internal nonce, or a bridge
  status outside the allowlist is `RESULT_SOURCE_MISMATCH` or a WAIT blocker;
  it must never reach the save function.
- When source media exists, bind raw intake, script handoff, and production to
  `10_analysis/source_identity_lock.json`. The lock contains canonical URL,
  video id, local source path, SHA256, and duration. Raw JSON without the same
  source identity remains analysis hint only.
- At Shorts intake, write `10_analysis/tikitaka_source_request.json` from the
  exact URL in the current request before Gemini or source acquisition. Match
  its URL/video id to the source identity lock before design lock. Then carry the lock SHA256 as
  `source_fingerprint_sha256` in `timeline_design.json`,
  `script_handoff_gate.json`, and `report1_handoff.json`. A missing or unequal
  fingerprint is `WAIT_SOURCE_HANDOFF_FINGERPRINT`, never a valid Stage 2 handoff.

```json
{
  "status": "PASS",
  "owner_skill": "00-tikitaka",
  "requested_source_url": "https://www.youtube.com/shorts/<video-id>",
  "requested_video_id": "<video-id>"
}
```
- The runner may launch the dedicated Chrome window offscreen/minimized and must
  close it cleanly when done so Chrome does not show a next-run restore-pages
  bubble. If the dedicated window is visible, do not ask the user to interact
  with it unless login or a human Google challenge is required.
- Success is `status: SAVED` plus real files under the default save folder below.
  `permission denied`, `RESULT_TIMEOUT`, source identity mismatch, duration/id
  mismatch, unrelated animal/old-video output, or missing `final_warning_ko` is
  FAIL, not a saved result. `final_warning_ko` alone is never enough.
- Manual copy/save follows the same run nonce and source-identity checks. Never
  save a copied JSON merely because it contains `final_warning_ko`.

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

- `00-tikitaka`: Shorts source analysis, full-source Demucs analysis
  preprocessing, remake script draft, hook, top/timed-middle, and script
  handoff. It creates `full_source_audio.wav` and `vocals.wav`; for an approved
  `stage_2_full` route it also registers `clean_source.mp4` as a production
  visual handoff. It does not create final Q clips or other production assets.
- `000short-production-agent`: SRT, layout JSON, CapCut, validation, exports, upload packages, and other production assets only.

## Stage Transition And n8n Contract

Use this default routing contract:

```text
n8n_stage_transition=NOT_USED
stage_transition_owner=Codex
harness_role=VALIDATOR_ONLY
n8n_default_status=NOT_REQUIRED
```

The harness validates artifacts and writes gate/status files. It does not launch
the next skill. After user approval and `SCRIPT_HANDOFF_GATE` PASS, Codex reads
`report1_handoff.json` and invokes `000short-production-agent`.

Require n8n only when the current package explicitly sets `n8n_required=true`
or selects `orchestration.route=n8n`. Without that explicit selection, record
`n8n=NOT_REQUIRED`, not `NOT_RUN`, and do not block Stage 1, Stage 2, or final
validation because n8n evidence is absent.

## Escalation Rule

Do not move to the next owner unless the user explicitly asks for that owner's
stage.

Adjacent intent is not permission to escalate. A Tikitaka request does not imply
production, `production_allowed`, `SCRIPT_LOCK`, `PASS`, export, upload,
completion, audio generation, SRT generation, layout JSON, or CapCut work.

If the user already has a draft and asks only for wording, rhythm, retention,
or review, perform that wording-only pass here without changing the story plan.

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
`script_handoff_gate.json`, and 설계도. Then stop at
`WAIT_REPORT1_APPROVAL_TTS_DECISION` until the user says OK and chooses the
TTS/audio route.

If the user already says `끝까지`, `자동으로 다`, `최종`, `다음단계`,
`업로드까지`, `슈퍼톤`, `슈퍼톤으로`, `supertone`, `TTS 만들어`, `tts 만들`,
`TTS 생성`, `tts 생성`, `TTS mp3`, `tts mp3`, `캣컵프로젝트파일까지`,
`캣컵 프로젝트 파일까지`, `캐컷프로젝트파일까지`, or `capcut project`, mark
`user_stage_decision=stage_2_full` as future intent. Still output 설계도 and
wait for `report1_approved=true` plus `voice_audio_route_decided=true` before
route to `000short-production-agent`. A generic `진행/해줘` next to stage-1
wording is not stage-2 permission.

`자동모드` is an explicit stage-2 token: user says 자동모드 = stage_2_full.

Mandatory gate map for URL + Gemini/source intake:

```text
G0 INTAKE = ask "어디까지 만들까?" unless the user text already says stage_1_script or stage_2_full
G1 STAGE 1 = create 1차설계서, timeline_design.json, caption_beat_map.json, timeline_design_gate.json, ChatGPT Project Round 1, Codex decisions, humanize_korean_gate.json, block_map.json, block_role_map.json, block_voice_switch_map.json, tts_copy_text.txt, ChatGPT Project Round 2, chatgpt_review_gate.json, and script_handoff_gate.json
G2 STAGE 1 STOP = output 설계도 and stop until report1_approved + voice_audio_route_decided
G3 STAGE 2 ENTRY = only after stage_2_full intent plus report1_approved, voice_audio_route_decided, and either VMAKE_CLEAN_SOURCE_GATE PASS for a new Vmake run or USER_CONFIRMED_VMAKE_REUSE for named existing clean files
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

## 설계도 계약

`설계도` is the Tikitaka 제작 승인용 blueprint. It combines the operator-facing
`1차설계서` with the locked script, time, track, caption-role, video, and audio
lane decisions required before CapCut assembly. It is not a CapCut, export,
upload, or production result.

Write 설계도 in 한글 우선, short, scan-friendly form. Use 예/아니오 단답 for
gate items whenever possible. The operator should be able to approve or reject
the complete Stage 1 production design without reading implementation labels.

Required 설계도 shape:

```text
# 설계도

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
source_fingerprint_sha256:
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

조립 역할 순서:
E1 intro_narration        | source=S4 | timeline=1 | 나레이션·TTS | source_audio=off | duration=4.0s | duration_basis=actual_tts_duration
E2 verified_speaker_quote | source=S3 | timeline=2 | "화자발언" | source_audio=on | duration=2.0s | duration_basis=source_range
E3 reaction_caption       | source=S2 | timeline=3 | (상황설명) | source_audio=off | duration=2.0s | duration_basis=fixed_design_duration
E4 payoff_narration       | source=S1 | timeline=4 | 나레이션·TTS | source_audio=off | duration=3.0s | duration_basis=estimated_tts_duration
E5 verified_speaker_quote | source=S5 | timeline=5 | "화자발언" | source_audio=on | duration=2.5s | duration_basis=source_range

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
- 필요 조건: 설계도 승인 + TTS/오디오 방식 결정
- 00-tikitaka는 보고서2를 작성하지 않는다
```

After 설계도, stop until the user approves the design. Only after 사용자가 OK한 뒤
and one TTS route is chosen may the work move to 보고서2:

- 사용자 제공 TTS
- Codex/API TTS 생성
- no-TTS/source/BGM route explicitly approved

If the user approves the script and asks for CapCut, route to
`000short-production-agent` and mark the next stage as 보고서2로 이동.
The Tikitaka harness must also write the legacy-compatible internal
`report1_handoff.json` with `report=설계도` and
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

Voice-copy text is part of the draft script only. Except for the required
full-source analysis artifacts `full_source_audio.wav` and `vocals.wav`, plus
the `stage_2_full` Vmake handoff visual `clean_source.mp4`, this skill does not
create voice clips, TTS, SRT files, layout JSON, render plans, CapCut drafts,
exports, upload packages, or production packages.

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

If the user asks to polish an already-written script without production, keep
the work in this skill and preserve all locked timing/source fields.

For folder/root/rule policy, follow the workspace `AGENTS.md` and
`docs/YOUTUBE_PRODUCTION_WORK_ORDER.md` directly.

## Active Root

For current 22utube work, check:

```text
${env:WORKSPACE_ROOT}\22factory_20260628\AGENTS.md
```

Treat `${env:WORKSPACE_ROOT}` as a portable placeholder, not proof that the
current process has the variable. Resolve the active factory root from the
opened workspace or OneDrive location and verify both `AGENTS.md` and
`docs/YOUTUBE_PRODUCTION_WORK_ORDER.md` exist before running commands. If the
root cannot be resolved, stop with `WAIT_FACTORY_ROOT_NOT_RESOLVED`.

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

For script confidence, use the current source-evidence workflow only. Acquire or
confirm `source.mp4`, lock its identity, run full-source Demucs preprocessing,
and then create the required frame/STT/OCR evidence and speaker ranges from
`10_analysis/audio/vocals.wav`. If source media cannot be acquired or
confirmed, stop and ask the user to provide it; do not invoke a separate
video-watching skill or invent final timing.

`00_source/clean_source.mp4` is never source evidence. When `stage_2_full` is
selected, bind it to the locked original through
`10_analysis/vmake_clean_source.json` and keep all analysis on `source.mp4`.

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
- `caption_beat_map.json`: timed visible-text beats and fixed layout profile.
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

n8n is a FINAL_LOCK blocker only when the current package explicitly sets
`n8n_required=true`; otherwise its status is `NOT_REQUIRED`.
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
- `10_analysis/source_voice_separation.json`: full-source Demucs gate bound to
  the locked source fingerprint. `10_analysis/audio/vocals.wav` is required
  when source speech exists.
- `timeline_design.json`: canonical design table for tracks, time ranges, text
  roles, video, and audio lanes.
- `timeline_design_gate.json`: design validation result.
- `humanize_korean_gate.json`: visible Korean cleanup result, with no protected
  structure changes.
- `edit_block_sequence`: the actual edit timeline order that production must
  implement.
- `block_map.json`: canonical source-of-truth map for every edit block.
- `block_role_map.json`: readable table for `"..."`, `(...)`, and TTS roles.
- `block_voice_switch_map.json`: readable table for source audio, TTS, SFX, and
  BGM switching by edit block.
- `tts_copy_text.txt`: narration-only copy text. Text with
  `included_in_tts_copy=false` must not be placed into the TTS body.
- `tts_duration_probe.json`: required only when narration audio is planned.
- `tts_timing_reconciliation_gate.json`: required only when narration audio is
  planned.
- `chatgpt_review_gate.json`: proves both ChatGPT project review rounds
  completed, Round 1 suggestions were dispositioned by Codex, Round 2 returned
  `PASS_RECOMMENDED`, and packet/response hashes match the preserved files.
- `script_handoff_gate.json`: the `SCRIPT_HANDOFF_GATE` result.

Legacy aliases without extensions are accepted only for old packages.

`block_map.json` must keep both source and edit identities:

```text
edit_id
source_block_id
original_order
urakkai_order
source_order
timeline_order
assembly_role
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
  `10_analysis/source_voice_separation.json`, `timeline_design.json`,
  `timeline_design_gate.json`,
  `humanize_korean_gate.json`, `edit_block_sequence`, `block_map.json`,
  `block_role_map.json`, `block_voice_switch_map.json`, `tts_copy_text.txt`, or
  `script_handoff_gate.json` is missing when production handoff is requested.
- `timeline_design.json` segment is missing `source_order`, `timeline_order`,
  `assembly_role`, `visible_text_role`, `audio_role`, `duration_basis`,
  `duration_status`, or `visual_strategy`.
- narration-audio segment exists but `tts_duration_probe.json` or
  `tts_timing_reconciliation_gate.json` is missing.
- `chatgpt_review_gate.json status=PASS` is missing, either ChatGPT project
  review round is missing, or Round 2 is not `PASS_RECOMMENDED`.
- actual narration duration exceeds the planned visual slot without an allowed
  reconciliation action; use `WAIT_TTS_TIMING_RELOCK`.
- `speaker_quote` has no verified or explicitly proposed source range.
- `speaker_quote` does not reference `10_analysis/audio/vocals.wav` with
  `source_audio_provenance=demucs_full_source_vocals`.
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
- tts_caption          = TTS-style visible caption only; no voice file implied
- situation_caption    = visual/situation explanation, shown with (...)
- tts_plus_source      = TTS while source audio remains intentionally audible
- ranking_item         = ranking/TOP-N beat

source_audio:
- on     = separated speaker/Q audio from vocals.wav must be audible
- off    = original/source video audio must be muted
- duck   = separated speaker/Q audio remains low under TTS/BGM

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
TTS 자막만 / tts_caption        -> source_audio=off,  tts=off, bgm=optional
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
source_video_audio=muted_always
speaker_q=separate_vocals.wav
```

Legacy compatibility wording:

```text
source_video_audio=muted unless explicitly extracted as source_audio
```

Here, `explicitly extracted as source_audio` means the separately approved
Demucs speaker/Q lane. It never authorizes embedded source-video audio; the
production video itself remains `muted_always`.

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

## Dual Writer Mode (Explicit Optional Mode)

Use two CLI-based writer agents only when the user explicitly asks for
`작가모드`, `2명 토론`, `울트라 검토`, or an equivalent multi-writer review.
Ordinary Tikitaka Stage 1 must not be blocked when either CLI is unavailable.

### CLI Tools

- **Writer A (Codex CLI)**: aggressive hook, emotional escalation,
  retention-first, willing to dramatize for engagement.
  ```bash
  codex exec "당신은 후킹·리텐션 중심 작가입니다. ... <분석 지시> ..." 2>&1
  ```
- **Writer B (Claude CLI)**: fact-grounded, structural balance,
  risk-aware, prioritizes coherence and policy safety.
  ```bash
  claude -p --bare "당신은 사실·구조 중심 작가입니다. ... <분석 지시> ..." 2>&1
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

## ChatGPT Project Two-Pass Review (Required)

Every new Tikitaka Stage 1 design must be reviewed twice in the existing
ChatGPT project `쇼츠대본분석`:

```text
https://chatgpt.com/g/g-p-6a245b804c2c8191907088f317842a55-syoceudaebonbunseog/project
```

Use one new project chat per episode and keep both review rounds in that same
chat. Use the logged-in normal Chrome session through available Chrome/browser
control. Do not substitute a generic ChatGPT chat, API call, Claude CLI, or a
different project. If the project cannot be opened, login is unavailable, or a
fresh response cannot be copied, stop with:

```text
WAIT_CHATGPT_PROJECT_REVIEW
```

Read the complete Shorts two-pass contract in
`shorts_script_analysis_single_source_v20260706.md` before creating either
packet. The ChatGPT project's Shorts-only instructions must match
`references/chatgpt_project_router_instruction.md`; if the live project router
does not require `content_type: shorts` and `review_round: 1|2`, or still
contains a `politics_longform`/`politics_shortform` route or political review
contract, stop with `WAIT_CHATGPT_PROJECT_ROUTER_UPDATE`.

Round 1 occurs only after `timeline_design_gate.json status=PASS`:

```yaml
content_type: shorts
review_round: 1
```

Save the exact sent packet and unedited response:

```text
chatgpt_review/round1_review_packet.md
chatgpt_review/round1_chatgpt_raw.md
```

ChatGPT performs `INDEPENDENT_REVIEW` and `REVISION_PROPOSAL`. Its result always
remains `PENDING_CODEX_REVIEW`. Codex then verifies every suggestion against
source evidence and records one of `ADOPTED`, `PARTIALLY_ADOPTED`, `REJECTED`,
or `PENDING_EVIDENCE` in:

```text
chatgpt_review/round1_codex_decisions.json
```

Apply accepted changes and rerun invalidated design, caption, Humanize, and TTS
timing gates.

Round 2 occurs after the revised candidate, Humanize, block maps, TTS copy, and
TTS timing reconciliation are ready, but before `SCRIPT_HANDOFF_GATE`:

```yaml
content_type: shorts
review_round: 2
```

Save:

```text
chatgpt_review/round2_audit_packet.md
chatgpt_review/round2_chatgpt_raw.md
```

Round 2 performs `EVIDENCE_AUDIT` and returns one external recommendation:
`PASS_RECOMMENDED`, `REVISE_REQUIRED`, or `EVIDENCE_REQUIRED`. All responses
still end in `PENDING_CODEX_REVIEW`; ChatGPT cannot make the final adoption or
handoff decision.

Codex may write `chatgpt_review_gate.json status=PASS` only when both exact
packets and raw responses are preserved, every Round 1 suggestion is
dispositioned, Round 2 says `PASS_RECOMMENDED`, the source fingerprint matches,
and no protected field changed silently. The gate name is:

```text
CHATGPT_PROJECT_TWO_PASS_REVIEW_GATE
```

`REVISE_REQUIRED`, `EVIDENCE_REQUIRED`, a missing response, a mismatched packet
hash, or a different project blocks `SCRIPT_HANDOFF_GATE`.

### Browser-Assisted Automation Sequence

Use `scripts/chatgpt_review_workflow.py` for deterministic packets, response
checks, and gate creation. Use the signed-in normal Chrome session only to send
the packets and copy fresh responses from project `쇼츠대본분석`.

```powershell
py -3 skills/00-tikitaka/scripts/chatgpt_review_workflow.py build-round1 --work-dir <20_script-dir> --review-cycle-id <cycle-id>
py -3 skills/00-tikitaka/scripts/chatgpt_review_workflow.py record-response --work-dir <20_script-dir> --round 1 --input <copied-round1-response.md>
py -3 skills/00-tikitaka/scripts/chatgpt_review_workflow.py build-round2 --work-dir <20_script-dir> --review-cycle-id <cycle-id>
py -3 skills/00-tikitaka/scripts/chatgpt_review_workflow.py record-response --work-dir <20_script-dir> --round 2 --input <copied-round2-response.md>
py -3 skills/00-tikitaka/scripts/chatgpt_review_workflow.py finalize-gate --work-dir <20_script-dir>
```

If the project returns `SOURCE_CONTRACT_MISSING`, attach only
`shorts_script_analysis_single_source_v20260706.md` to the project sources,
remove any political review contract, keep the Shorts-only instructions from
`references/chatgpt_project_router_instruction.md`, and rerun the same packet
in a fresh episode chat. Do not use Computer Use or an OS-level mouse/keyboard
fallback.

## Draft Workflow

1. State the frame: what situation the remake is using and why.
2. **Run Story And Production Type Gate**: choose `story_type`,
   `production_type`, `shorts_design_type`, audio policy, caption policy,
   source speech policy, and card asset role before the first draft.
3. Map source notes into functional beats.
4. Write hook candidates if requested or useful.
5. If the user explicitly selected Dual Writer Mode, run it to review wow point,
   urakai, story type, and production type. Otherwise continue with the single
   Tikitaka design owner.
6. Produce `1차설계서`: a CapCut-style time/track layout table, not an abstract
   script report.
7. Write `timeline_design.json` from the same layout and pass
   `timeline_design_gate.json`.
8. Send ChatGPT Project Round 1, save the raw response, adjudicate every
   suggestion, and rerun invalidated design gates.
9. Run Humanize Korean on visible text only and record
   `humanize_korean_gate.json` before handoff.
10. Produce `상단 + timed 중단`, `block_map.json`, `block_role_map.json`,
   `block_voice_switch_map.json`, and `tts_copy_text.txt` from
   `중단 TTS 글자만 복사`.
11. Complete the TTS duration probe and timing reconciliation when narration
    audio is planned.
12. Send ChatGPT Project Round 2 and pass
    `CHATGPT_PROJECT_TWO_PASS_REVIEW_GATE`.
13. Run `SCRIPT_HANDOFF_GATE`; keep status at `DRAFT_EYE_REVIEW` unless the
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

- Do not claim generic `SCRIPT_LOCK` from this skill alone. This skill may emit
  `SCRIPT_LOCK_PACKAGE` only when `script_handoff_gate.json status=PASS` and all
  required Stage 1 artifacts, including `caption_beat_map.json`, exist.
- Do not claim production allowed.
- Do not claim source-verified truth from raw Gemini notes.
- Do not run `SCRIPT_HANDOFF_GATE` before `timeline_design_gate.json` and
  `humanize_korean_gate.json` are PASS.
- Do not run `SCRIPT_HANDOFF_GATE` before
  `chatgpt_review_gate.json status=PASS` proves both required ChatGPT project
  review rounds completed.
- Do not replace a missing ChatGPT project review with Claude, a generic chat,
  an API call, or Codex self-review.
- Do not skip human Korean cleanup before any final visible Korean text.
- Do not proceed past missing source evidence when the script depends on exact
  timing, OCR, or dialogue.
- Do not call a TTS-capable story/remake draft eye-ready unless the TTS
  storytelling mode has been considered and, when applicable, the emotional
  entry line is source-supported and non-flat.

## Reference Routing

- Active Shorts script analysis authority is
  `shorts_script_analysis_single_source_v20260706.md`; apply it before any
  reference file below. This same file is the single Shorts contract attached
  to the ChatGPT project and contains the two-pass review protocol.
- For hook review, read `references/pre_script_hook_review.md`.
- When configuring or auditing the ChatGPT project, read
`references/chatgpt_project_router_instruction.md` and use it as the complete
  Shorts-only project instruction.
- For Shorts craft rules, read `references/shorts-academy.md`.
- For old contract details or legacy repair only, read
  `references/archived-full-skill-20260629.md`.

Keep this `SKILL.md` as the active router. Do not re-expand it with legacy
examples, PASS templates, production reports, CapCut details, or long handoff
instructions.

## Integrated Blueprint Output Contract

The human-facing artifact is always `20_script/design_blueprint.md`. Stage 1
must create it with the exact first heading `# 설계도` and H2 sections `기본 정보`,
`제작 판단`, `상단 고정 문구`, `조립 역할 순서`, `트랙별 타임라인`,
`TTS 복사용 문구`, and `승인 전 점검`. The two timeline sections must be
markdown tables and the TTS section must be non-empty.

Stage 1 owns only the design portion. Stage 2 appends `## 조립도` and the
production skill owns that section. The final section is reserved for the
production skill's `## 업로드 패키지`.

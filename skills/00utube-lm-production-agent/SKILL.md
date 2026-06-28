---
name: 00utube-lm-production-agent
description: Dedicated 22utube/11utube landscape midform and longform production agent. Use for youtube_midform, youtube_longform, 00utube lm, mid/longform tech/mindset/story videos, Google Flow image production, Official Image2 fallback, Supertone/Kokoro TTS, SRT resync, CapCut landscape drafts, clean draft repair, review renders, ffprobe, frame QA, and final gates. Do not use for Shorts; use dedicated Shorts skills instead.
---

# 00utube LM Production Agent

This skill owns actual landscape midform/longform production for `22utube/11utube`.
`22utube-production-agent` remains the common factory guide; this skill is the worker for `youtube_midform` and `youtube_longform`.

## Global Gates

This skill obeys the 11utube global gates in `11utube/00_TOP_LEVEL_DIRECTIVE.md`.

- Any new script, serious rewrite, or script finalization must pass `00script-writer` 작가모드, the YouTube Policy Gate, and the visible random 5-persona retention/readability gate before it is called final. If fewer than 3 of 5 approve, rewrite from the feedback and run the remaining 5 personas as the second pass; final PASS still requires 3 of 5 on that pass.
- Any image, Flow/Image2 route, TTS, SRT, CapCut, render, upload package, or final report must show the shared `A. n8n 실행` / `B. 하네스 검증` board.
- If n8n is not used or unreachable, mark it as `WAIT - local run`; never fake a pass.
- Script contract, image manifest, CapCut/SRT, visual snapshot, ffprobe, frame QA, and final harness are the PASS/FAIL authorities.

## Scope

Use this skill when the user asks to create, continue, fix, review, or finalize a landscape midform/longform video under:

```text
{OneDrive}\22utube\11utube\{tech,mindset,story,...}\episodes\{episode}
```

Resolve `{OneDrive}` on the current PC. Prefer, in order:

```text
$env:OneDrive\22utube
$env:OneDriveCommercial\22utube
$env:USERPROFILE\OneDrive\22utube
current workspace ancestor named 22utube
```

Do not hardcode a machine-specific Windows user home path when writing portable instructions or scripts. If the user pastes a path with another username, adapt it to the current machine only after verifying the actual folder exists.

## Required Bootstrap

Before production edits or runs, read only what is needed from:

```text
{OneDrive}\22utube\11utube\AGENTS.md
{OneDrive}\22utube\11utube\00_TOP_LEVEL_DIRECTIVE.md
{OneDrive}\22utube\11utube\shared_script_reading_rules.md
{OneDrive}\22utube\11utube\{channel}\agent.md
{OneDrive}\22utube\11utube\video\VIDEO_LAYOUT_SPEC.md
{OneDrive}\22utube\11utube\video\CAPCUT_JSON_EDITING_SPEC.md
{OneDrive}\22utube\11utube\n8n\VISUAL_PHASE_WORKFLOW_SPEC.md
```

If `$1brainstorm` is present, run the intent brief first. Then use this skill.

Before creating, importing, or routing images, read `references/IMAGE_AGENT_ROUTE.md`.

## Local Control Surfaces

This skill can use n8n and the YouTube production console only when the current PC can reach them. A skill is an instruction package; it does not create a network tunnel by itself.

Treat the Mac mini as the default server for both n8n and the YouTube production console. Other PCs are clients that use OneDrive sync for files and Tailscale to reach the Mac mini services.

Do not use the current Windows/office PC's Tailscale IP as the service address. For remote access, use the Mac mini Tailscale IP. Confirm it on the Mac mini from the Tailscale menu when it is unknown. If prior project context mentions `100.117.220.7`, treat it only as a candidate Mac mini Tailscale IP and verify reachability before reporting it as active.

Remote client access requires all three conditions:

- The office/Windows PC is connected to the same Tailscale account.
- The Mac mini is powered on and connected to Tailscale.
- The Mac mini production console and/or n8n server is running.

On client PCs, keep responsibilities separate:

```text
File work: current PC's OneDrive\22utube
Production console: Mac mini Tailscale IP:47831
n8n: Mac mini Tailscale IP:5678
CapCut draft: local CapCut project on whichever PC creates the draft
```

On each PC, resolve these surfaces in this order:

### Production Console

1. If an episode-specific console URL is provided by the user, use it.
2. If the Mac mini Tailscale IP is known, check the Mac mini console first:

```text
http://{Mac mini Tailscale IP}:47831/?v=.
http://{Mac mini Tailscale IP}:47831
```

For an episode-specific view, use:

```text
http://{Mac mini Tailscale IP}:47831/?dir={url-encoded episode_dir}
```

Use an episode `dir` query only when the path is valid from the Mac mini server's point of view. Do not send a Windows-only path to the Mac mini console unless the console explicitly maps it.

3. If this PC is the Mac mini or the user explicitly asks for a local-only run, check the local console route:

```text
http://127.0.0.1:47831/?dir={url-encoded episode_dir}
```

4. If the console should run on the current PC and is not running locally, start it from:

```text
{OneDrive}\22utube\11utube\tools\production_console\start_console.ps1
```

5. If the user provides another Tailscale/remote URL such as `http://100.x.x.x:47831`, use it only after confirming it is the Mac mini or an explicitly approved server and the current PC can reach it.

### n8n

Use n8n only when a reachable local or remote endpoint exists. Check these routes in order:

```text
http://{Mac mini Tailscale IP}:5678
user-provided n8n URL
http://127.0.0.1:5678
http://localhost:5678
```

Use local n8n before Mac mini only when the current PC is the Mac mini, the user explicitly requested a local n8n run, or the Mac mini route is unknown and cannot be verified.

If n8n is not reachable, mark `A. n8n 실행` as `WAIT - local run; n8n not reachable` and continue with local production files and harnesses. Do not block local CapCut/Image2/TTS/SRT work just because n8n is not open.

### What To Report

When working from another PC, include the resolved endpoints in the first status update:

```text
관제 URL: reachable|not reachable - {url}
n8n URL: reachable|not reachable - {url}
OneDrive root: {resolved path}
```

## Mandatory Status Board

Every production update and final report must start with this exact A/B structure, with statuses changed to match checked reality:

```text
A. n8n 실행
01 시작웹훅 ⏳ WAIT - local run
02 폴더생성 ⏳ WAIT
03 대본생성 ⏳ WAIT
04 이미지생성 ⏳ WAIT 0/0
05 TTS생성 ⏳ WAIT
06 렌더실행 ⏳ WAIT
07 리포트 ⏳ WAIT

B. 하네스 검증
01 작업상태 ⏳ WAIT
02 타겟잠금 ⏳ WAIT youtube_midform|youtube_longform landscape 16:9
03 대본검사 ⏳ WAIT
04 이미지검사 ⏳ WAIT 0/0
05 음성검사 ⏳ WAIT
06 자막검사 ⏳ WAIT
07 렌더검사 ⏳ WAIT
08 ffprobe ⏳ WAIT
09 프레임QA ⏳ WAIT
10 FINAL게이트 🚫 BLOCKED
```

Rules:

- `A` is execution flow only.
- `B` is validation/pass-fail only.
- Do not mark `OK` or `PASS` until the command, file, API result, visual snapshot, or harness result was actually checked.
- `FINAL게이트` remains `BLOCKED` until render, ffprobe, frame QA, and the applicable harness pass.

## Production Contract

### Target And Layout

- Midform/longform is always landscape `16:9`.
- Use `youtube_midform` or `youtube_longform`; never silently switch to Shorts.
- A major scene count such as `8 scenes` means chapter structure, not image count.
- Actual image cuts must meet density: minimum `7 cuts/minute` for image-only videos unless the user explicitly lowers the density.
- Example: 6 minutes -> at least 42 image cuts. 10 minutes -> at least 70 image cuts.

### Opening Cut Duration Lock

For every `youtube_midform` and `youtube_longform` draft, the first two visual cuts are fixed replacement slots:

- `scene_01` / cut 01: exactly `0.0s -> 8.0s`
- `scene_02` / cut 02: exactly `8.0s -> 16.0s`

This is mandatory even when the opening narration would be shorter or longer. The reason is operational: the user may later replace either still image with an 8-second video clip, and the CapCut timeline must accept that replacement without rippling later cuts.

Rules:

- Do not auto-fit cut 01 or cut 02 duration to TTS, SRT, or image-density calculations.
- Do not shorten, extend, or ripple these two slots during CapCut draft generation.
- Store the fixed start/end/duration in `storyboard.json`, `production_console.json`, and the CapCut draft manifest when those files exist.
- Captions and title overlays may change inside these slots, but the base visual segment duration remains 8.0 seconds each.
- Distribute remaining visual cuts from `16.0s` onward according to narration timing, SRT, and density rules.
- If the user provides an 8-second intro/video asset, place it into one of these slots without changing the timeline.

### Input Priority

1. User-provided Gemini/AI Studio result file or pasted result.
2. Existing package files in the episode directory.
3. Source transcript and local metadata.

Do not rerun Gemini, AI Studio, or GPT analysis when the user already provided a valid Gemini result. Reopen AI Studio only if the result is missing, corrupt, or the user explicitly asks.

### Style Planning

Before image generation, choose and record an image style. Offer compact options when not already locked:

- cinematic infographic illustration
- realistic editorial composite
- simplified icon/diagram style

For finance, tech, and macroeconomic longform, default recommendation is `cinematic infographic illustration`: readable, dramatic, and compatible with chart/map/asset-flow scenes.

### Image Generation Route

Default midform/longform still-image production is Google Flow first.

Use this priority unless the user explicitly overrides it:

1. Google Flow / Google image generation route for normal midform and longform bulk cuts.
2. Official Image2 only as fallback, thumbnail-quality route, or when a harness/user specifically requires Image2.
3. No Codex `image_gen`, local placeholder images, or CapCut internal AI image generation for 22utube production.

Flow production contract:

- calculate dense cut count from runtime and density rules
- write one prompt per cut in `06_longform_flow_prompts.md`
- include `route: google_flow` and `prompt_format: image_and_video`
- save generated images as `images/flow/scene_01.*` through `scene_NN.*`
- maintain `images/flow/flow_manifest.json`
- sync video assets to `video/images/flow/`
- detect missing, failed, or duplicate-hash images before CapCut so scene order never drifts
- validate with `tools/google_flow_manifest.py --sync-video-assets` or `tools/n8n_youtube_runner.py --action flow_manifest`

Official Image2 fallback uses `06_image2_prompts.md` and Image2 manifests only after Flow is blocked, insufficient, or explicitly not selected.

Do not search for image API keys. Do not require `OPENAI_API_KEY` unless an explicit direct API image mode is selected. If Flow and the approved fallback route are unavailable, mark the image stage `BLOCKED - image route unavailable` instead of silently switching tools.

### HyperFrames Image-Led Mode

For landscape midform/longform, HyperFrames is an image-led compositor, not a black-slide/chart-only renderer.

Use generated visual backgrounds as the primary visual layer whenever the episode already has generated cuts. Google Flow is the default source; Image2 is allowed only as the fallback/imported asset route described above. Code and effect assets are added on top of those images to create motion and emphasis.

Layer contract:

1. Background: full-bleed Google Flow or approved Image2 cinematic/infographic image.
2. Subject/effect overlays: transparent PNG, WebM, or Lottie for shapes that need a real form, such as sparks, smoke, burst, warning marks, money icons, cracks, and glow.
3. Code motion: GSAP/CSS/SVG/Canvas for camera push, pan, shake, flow lines, chart draw, number count-up, flash, glitch, and focus highlights.
4. Text: HTML/CSS top layer for Korean titles, captions, numbers, labels, and source badges. Never bake important Korean text into generated images.

Reject HyperFrames scenes that look like generic black PPT slides unless the script explicitly calls for a pure data board. For this channel, the default look is `generated background + animated overlays + stable Korean text + synced SFX`, not static card screens.

### Production Console

The console must show landscape mode. Do not list one scene per row for dense cuts. Use a horizontal grid of image cut cards:

```text
[cut][cut][cut][cut][cut][cut]
[cut][cut][cut][cut][cut][cut]
```

Each card should show only:

- image
- script
- caption
- voice/audio
- transition/effect

Prompts, notes, exact paths, metadata, and revision fields belong behind details.

When `production_console.json` stores media paths relative to the episode directory, such as `video/images/flow/scene_01.png` or `video/images/image2/scene_01.png`, the console must resolve them under `episodeDir`, not under the shared `11utube` root. Broken thumbnails with only title/caption overlays count as a console display bug even if the image files exist.

The console preview must match the CapCut draft's title and caption style closely enough to catch real layout issues: landscape 16:9, yellow stroked title when the draft uses that style, white stroked lower captions, and no extra cyan caption box unless the draft actually uses one.

The console should also expose a compact production workflow panel above review/editing:

```text
source/project -> script -> voice/pronunciation -> style -> storyboard -> images -> CapCut/render
```

This panel is a status surface, not a marketing page. It must derive from real files and `production_console.json`, including target/layout, duration, cuts per minute, image count, audio/SRT count, selected image style, CapCut draft path, render status, and FINAL gate.

Use it to mirror the best parts of external automation tools while preserving 22utube rules:

- Pronunciation and SRT state are first-class checks, not hidden inside TTS.
- Hook/Body/Emphasis storyboard density should be visible when available.
- Image generation status must show actual generated/imported image count and the route: Flow, Image2 fallback, or manual import.
- CapCut/review render state must remain separate from FINAL; FINAL stays blocked until ffprobe, frame QA, and harness pass.

## Stage Workflow

1. Lock target: `youtube_midform` or `youtube_longform`, `landscape 16:9`.
2. Validate or create script from the accepted source.
3. Plan major scenes and dense image cuts.
4. Reserve opening replacement slots: cut 01 `0.0s -> 8.0s`, cut 02 `8.0s -> 16.0s`.
5. Select image style and create Flow prompts by default.
6. Generate or import Flow images according to `references/IMAGE_AGENT_ROUTE.md`. Image count must satisfy density.
7. Generate TTS.
8. Resync SRT against actual audio duration.
9. Update `production_console.json`, `storyboard.json`, and package manifests.
10. Build or update CapCut draft.
11. Apply visual motion, transitions, overlays, and optional low-volume SFX.
12. Run CapCut SRT harness.
13. Generate visual snapshots/contact sheet.
14. Render review video.
15. Run ffprobe and frame QA.
16. Only then allow REVIEW -> FINAL.

## SRT Sync Rule

Never map chapter text directly onto Whisper segment timings. This causes drift.

Required method:

1. Use the final TTS source text, usually `script/long_script_voice.txt` or `script/03_final_script.txt`.
2. Use Whisper/faster-whisper only as the timing source.
3. Align the original TTS script sequentially to Whisper timing segments.
4. Write:
   - `audio/main_capcut.srt`
   - `video/audio/full.srt`
   - `audio/voice_segments_synced.json`
5. Rebuild the CapCut `auto_captions` track from the same cue list.
6. Run `11utube/video/capcut_draft_srt_harness.py`.

Read `references/SRT_SYNC_RULES.md` before fixing any audio/caption mismatch.

## CapCut Draft Rules

- Keep the local draft visible under the user's CapCut draft directory.
- Do not overwrite a user-edited draft without backing up `draft_content.json`.
- Use existing local draft structures as templates; do not invent CapCut JSON fields.
- For midform/longform REVIEW drafts on Windows, prefer a recently verified Windows-clean CapCut skeleton over an old Mac-origin template.
- The first two base visual segments must be exact 8-second replacement slots: segment 01 `0.0s -> 8.0s`, segment 02 `8.0s -> 16.0s`. Do not let SRT sync, auto scene duration, or image density code ripple these slots.
- After writing Korean title or captions into `draft_content.json`, re-read the file and verify the exact string. If shell encoding may corrupt Korean, write Korean strings with Unicode code points or read them from UTF-8 source files.
- Title and caption text must be checked separately. A normal `production_console.json` does not prove the CapCut draft text is normal.
- After any title/caption edit, re-run the CapCut SRT harness because some tools snap caption timings to frames.

### CapCut Clean Draft Repair

If a midform/longform CapCut REVIEW project does not open, investigate draft structure before blaming image files.

Known failure pattern:

- Shorts drafts open, but landscape mid/longform draft does not.
- Images exist and pass manifest checks.
- `timeline_layout.json` references stale IDs.
- `Timelines/project.json` `main_timeline_id` differs from layout IDs.
- root `draft_content.json` / `draft_info.json` differs from `Timelines/<main>/draft_content.json` / `draft_info.json`.
- `draft_virtual_store.json` child IDs do not match current material IDs.
- `platform`, `last_modified_platform`, or `draft_settings` still say Mac on Windows CapCut.

Required repair workflow:

1. Close all CapCut processes before editing or recreating a draft.
2. Do not keep patching a polluted draft folder after structural mismatch is confirmed.
3. Create a clean draft with the same name plus `-clean`.
4. Use a recently opening Windows CapCut skeleton when available.
5. Set `Timelines/project.json.main_timeline_id` to the one active timeline ID.
6. Set `timeline_layout.json` to reference only that same ID.
7. Make root and timeline `draft_content.json` / `draft_info.json` identical after injection.
8. Rebuild `draft_virtual_store.json` from all current `materials[*].id` values.
9. Set `platform.os`, `last_modified_platform.os`, and `draft_settings cloud_last_modify_platform` to Windows CapCut 8.6.x local values.
10. Refresh `draft_meta_info.json` and `root_meta_info.json` with the new draft name, folder path, draft ID, modified time, and duration.
11. Run the CapCut/SRT harness and an open-check snapshot before reporting the draft as ready.

Read `references/CAPCUT_QA_RULES.md` before editing CapCut JSON by hand.

## Effects For Image-Only Videos

Because there is no source video, static images must carry motion:

- image motion: slow zoom, pan, push, pull, diagonal drift, or shake where appropriate
- transitions: dissolve, flash, push, slide, impact cuts
- overlays: scanlines, warning flash, cyan frame, burst, chart highlights
- SFX: optional, low volume, only when it does not break harness or distract from narration

Use existing shared effect packs first, especially under:

```text
{OneDrive}\22utube\11utube\0shrt\assets\emotion_pack
```

## Validation Gates

Minimum gates before claiming a draft is ready:

- script contract PASS
- Flow manifest PASS or explicit Image2 fallback manifest PASS
- image count and path PASS
- audio duration PASS
- SRT/caption PASS
- opening cut duration lock PASS: cut 01 exactly 8.0s, cut 02 exactly 8.0s
- CapCut draft structure PASS: main timeline, layout, draft_info sync, virtual store, Windows platform
- `capcut_draft_srt_harness.py` PASS
- visual snapshot PASS

Minimum gates before FINAL:

- review render exists
- ffprobe duration/resolution/audio stream PASS
- frame QA PASS
- applicable channel/final harness PASS

Common harness caveat: if `channel_episode_harness.py` misroutes a `tech/episodes` folder to `misc/episodes`, report that route bug and rely on the specific CapCut/SRT/render/frame checks until the common harness is fixed. Do not mark FINAL from a misrouted harness.

## Portable Use On Another PC

The distributable copy of this skill should live in:

```text
{OneDrive}\22utube\codex_skills\00utube-lm-production-agent
```

Install it on each PC by copying that folder to:

```text
%USERPROFILE%\.codex\skills\00utube-lm-production-agent
```

The bundled `scripts/install_local.ps1` performs that copy for the current Windows user.

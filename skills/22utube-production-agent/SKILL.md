---
name: 22utube-production-agent
description: Use as the 22utube/11utube common operating guide for mindset/story longform production, shared video-stage rules, n8n/harness checks, CapCut/Image2 routing, and production-system debugging. Dedicated Shorts skills should perform actual Shorts production; this skill defines the shared factory rules they must respect.
---

# 22utube Production Agent

## Current 11short Routing Note - 2026-06-13

For Shorts factory work, do not create or use `$env:WORKSPACE_ROOT\00tube`
as a production root. It was a temporary cleanup folder only.

Current 11short work must stay under:

```text
$env:UTUBE_ROOT\11short
$env:UTUBE_ROOT\11short\000short-production-agent\episodes
```

Dedicated `000short-production-agent` remains the actual Shorts worker. This
common skill only enforces shared boundaries and must not revive old 11short
rules such as `하단`, `1번 제미나이 분석본`, `source_audio_only`, or per-episode
large builders as the default path.

## Current Role - 2026-05-22

This skill is the common 22utube/11utube production-system guide. It is not the default worker for every Shorts job, and it is not the actual worker for landscape midform/longform jobs when `00utube-lm-production-agent` is installed.

Use this skill directly for:

- Shared planning and debugging for `mindset`, `story`, and `tech` longform systems.
- Shared video-stage rules: CapCut, Image2, final MP4, SRT timing, BGM/SFX, thumbnail, visual snapshot, final harness.
- n8n recovery, webhook checks, status-board checks, runner/harness routing, and production-gate debugging.
- Explaining or enforcing the shared folder boundary: real production stays under `$env:UTUBE_ROOT`.

Do not use this skill as the primary production worker when a dedicated production skill applies:

- `00utube-lm-production-agent`: landscape `youtube_midform` / `youtube_longform` production under `11utube/{tech,mindset,story,...}`.
- `000short-production-agent`: normal 11short YouTube Shorts remake.
- `11short-animal-agent`: animal Shorts.
- `11short-cryung-agent`: crying-news/sad-news Shorts.
- `0shrt-korea-production-agent`: Korean history Shorts.
- `0shrt-reality-saida-production-agent`: modern reality/revenge Shorts.
- `0shorts-yellowman-production-agent`: Yellowman Shorts.

In those cases, use the dedicated Shorts skill for the actual production, but still obey this skill's shared system rules:

- Do not create a new production root. `AUTOJUNTUBE` may be a dashboard/launcher only, not the production home.
- Keep production files inside the existing `22utube/11utube` channel folders and shared `11utube/video`, `11utube/tools`, and `11utube/n8n` folders.
- n8n is the status board and remote execution gate; it does not replace CapCut, Image2, ffmpeg, or harness QA.
- Harness is the real PASS/FAIL authority. A failed harness blocks the next stage and blocks completion reports.
- Every n8n `production/run` action must leave status-board records through `tools/agent_status_store.py`: start as `running`, finish as `passed`, `failed`, or `blocked`.
- Failure patterns must be added to the relevant harness or skill rules, not scattered into new folders.

Shared role map:

```text
00utube-lm-production-agent = actual landscape midform/longform production worker
Dedicated Shorts skills = actual Shorts production workers
22utube-production-agent = shared factory rules and gatekeeper guide
11utube/video = common video/layout/CapCut/Image2 rules
11utube/n8n = status board and remote runner
11utube/tools = runners, manifests, CapCut helpers, status store
channel harnesses = stage PASS/FAIL enforcement
AUTOJUNTUBE = optional dashboard/launcher only
```

## Mandatory Skill Folder Boundary

New Shorts production must be created inside the folder owned by the selected skill. Do not create new episode/work folders directly under `0shrt\episodes` or directly under `11short`.

Current folder map:

```text
11utube\0shrt\history-chunsik\episodes\{episode}              = 0shrt-korea-production-agent
11utube\0shrt\reality-saida\episodes\{episode}                = 0shrt-reality-saida-production-agent
11utube\11short\000short-production-agent\episodes\{work}      = 000short-production-agent
11utube\11short\11short-animal-agent\episodes\{work}          = 11short-animal-agent
11utube\11short\11short-cryung-agent\episodes\{work}          = 11short-cryung-agent
```

Shared scripts, harnesses, templates, BGM folders, and helper tools stay at the channel root, for example `11utube\11short\shorts_remake_harness.py` and `11utube\11short\assets`. Only generated work folders move into the skill-owned `episodes` folder.

When creating a new skill or a new production system such as HyperFrames, first add a dedicated skill-owned folder under the existing channel root, then update this map and the dedicated skill's `Skill Folder Contract`. Do not add a new top-level production root unless the user explicitly approves it.

## Scope

Use this skill for `$env:UTUBE_ROOT` YouTube production work.

Do not use this skill for `0shrt`, `0쇼츠`, or standalone shorts-only 0shrt episode work. Those requests must be routed to the separate 0shrt skill when available.

## Mandatory 11utube Bootstrap

When this skill is triggered, do not rely only on the user's pasted rules. First anchor the session to the real project root:

```text
$env:UTUBE_ROOT
```

Before planning, drafting, editing, producing, or reviewing, read the project-level operating files if they exist:

```text
$env:UTUBE_ROOT\AGENTS.md
$env:UTUBE_ROOT\00_TOP_LEVEL_DIRECTIVE.md
$env:UTUBE_ROOT\shared_script_reading_rules.md
```

Then read the selected channel's local rules:

```text
$env:UTUBE_ROOT\{channel}\agent.md
```

For any video-stage request, also read:

```text
$env:UTUBE_ROOT\video\VIDEO_LAYOUT_SPEC.md
$env:UTUBE_ROOT\n8n\N8N_AGENT_PARALLEL_TODO.md
$env:UTUBE_ROOT\n8n\VISUAL_PHASE_WORKFLOW_SPEC.md
```

Apply these files as the source of truth. The user should not need to restate n8n, Image2, CapCut, manifest, final mp4, or harness rules in every new chat.

## Mandatory Intent Brainstorm Gate

For any 22utube production, continuation, script, audio, SRT, Image2, CapCut, n8n, thumbnail, or harness request, run this gate before editing files or running production commands. This is the step that translates the user's rough request into an executable production brief.

Do not run it for a simple factual question, folder-open request, one-off command, or status check. If the user says `브레인스톰`, `brainstorm`, `찰떡같이 이해`, or gives a messy production request, run it even if the rest of the task is not fully specified.

Report this first:

```text
Brainstorm
- 사용자 의도:
- 채널/모드:
- 입력 소스:
- 결과물:
- 제작 방식:
- 보이스/자막:
- n8n/하네스 단계:
- 금지/주의:
- 애매한 점:
```

Proceed after posting the gate unless the user objects or a listed ambiguity blocks production.

## Mandatory 11short Remake Workflow

For 11short / 11쇼츠 work, prefer the dedicated `000short-production-agent` skill when available. Treat this section as fallback guidance only; the dedicated skill owns the 3-text layout, visual-truth rule, and 11short-specific review format.

When the request is under `$env:UTUBE_ROOT\11short`, or the user is remaking YouTube Shorts with CapCut overlays, first read:

```text
$env:UTUBE_ROOT\11short\agent.md
$env:UTUBE_ROOT\11short\SHORTS_REMAKE_CONTRACT.md
$env:UTUBE_ROOT\11short\GEMINI_SHORTS_ANALYSIS_PROMPT.md
```

Use this locked workflow:

1. Brainstorm the clip before generating a draft: classify the situation, decide whether OCR overlays are needed, choose the fixed top title, choose the Chunsik opening line, and compress bottom captions.
2. Treat `segments[].caption_ko_final` as bottom black-band situation captions only.
3. Treat `onscreen_overlays[]` as the only source for Korean text placed inside the video frame over original on-screen text.
4. Top black band gets one fixed title for the full project duration.
5. Chunsik intro audio requires original video audio fade-in for the same duration.
6. Never overwrite a user-edited CapCut profile. If a draft name exists, stop or create a new draft name after reporting it.
7. Run the 11short harness before moving stages:

```powershell
py -3 $env:UTUBE_ROOT\11short\shorts_remake_harness.py {work_dir} --stage analysis
py -3 $env:UTUBE_ROOT\11short\shorts_remake_harness.py {work_dir} --stage assets
py -3 $env:UTUBE_ROOT\11short\shorts_remake_harness.py {work_dir} --stage capcut --draft-name "{draft_name}"
```

If the harness fails, do not proceed to the next stage. Report the failed checks and fix them first.

## Mandatory Production Console And Progress Board

For any YouTube production, continuation, render, Image2, TTS, CapCut, or QA report, include a compact progress board before the narrative summary. This is mandatory even when the work is done manually outside n8n.

### Mandatory Todo Status Board

Every visible TODO/status update for any YouTube video production must start with this board. This applies to all production routes: n8n, local runs, CapCut, FFmpeg, HyperFrames, Image2, TTS, QA, fixes, and resumed work.

```text
[ 진행판 ]

A. n8n 실행
01 시작웹훅 ⏳ WAIT
02 폴더생성 ⏳ WAIT
03 대본생성 ⏳ WAIT
04 이미지생성 ⏳ WAIT 0/0
05 TTS생성 ⏳ WAIT
06 렌더실행 ⏳ WAIT
07 리포트 ⏳ WAIT

B. 하네스 검증
01 작업상태 ⏳ WAIT
02 타겟잠금 ⏳ WAIT
03 대본검사 ⏳ WAIT
04 이미지검사 ⏳ WAIT 0/0
05 음성검사 ⏳ WAIT
06 자막검사 ⏳ WAIT
07 렌더검사 ⏳ WAIT
08 ffprobe ⏳ WAIT
09 프레임QA ⏳ WAIT
10 FINAL게이트 🚫 BLOCKED

현재 막힌 곳:
- 없음

다음 액션:
- 다음 확인 단계 진행
```

Rules:

- `A. n8n 실행` is execution flow only: webhook, folder, script, image, TTS, render, report.
- `B. 하네스 검증` is validation/pass-fail only: state, target, script, image, audio, caption, render, ffprobe, frame QA, final gate.
- Do not mark `OK` or `PASS` until the command, file, API response, or harness result was actually checked.
- If n8n was not invoked, mark the relevant A steps as `WAIT - local run; n8n webhook not invoked` or `WAIT`.
- If a stage is partially complete, show a count such as `RUNNING 4/7`, `WAIT 4/7`, or `PASS 7/7`.
- `FINAL게이트` stays `BLOCKED` until the correct skill-specific harness passes.
- For 11short routes, adapt the A labels to source intake, download, Gemini analysis, assets, CapCut, and report, but keep the same A/B split.

Use this shape:

```text
[ 진행판 ]

A. n8n 실행
01 시작웹훅 ✅ OK
02 폴더생성 ✅ OK
03 대본생성 ✅ OK
04 이미지생성 🔄 RUNNING 4/7
05 TTS생성 ✅ OK
06 렌더실행 ⏳ WAIT
07 리포트 ⏳ WAIT

B. 하네스 검증
01 작업상태 ✅ PASS
02 타겟잠금 ✅ PASS
03 대본검사 ✅ PASS
04 이미지검사 ⏳ WAIT 4/7
05 음성검사 ✅ PASS
06 자막검사 ✅ PASS
07 렌더검사 ⏳ WAIT
08 ffprobe ⏳ WAIT
09 프레임QA ⏳ WAIT
10 FINAL게이트 🚫 BLOCKED

현재 막힌 곳:
- Image2 scene_05~07 미완료

다음 액션:
- 이미지 3장 생성 완료 후 하네스 04 재검사
```

For Shorts production, keep these locks unless the user explicitly changes the target:

```text
target: youtube_shorts
instagram_status: not_requested
Create the YouTube Shorts master first unless the user explicitly says the current deliverable is Instagram/Reels.
If the user says "인스타", "인스타용", "인스타로 만들어", or "릴스", switch to target: instagram_reels and follow $env:UTUBE_ROOT\11short\INSTAGRAM_LAYOUT_CONTRACT.md.
Before user review and harness PASS, output names and reports must say REVIEW or DRAFT, never FINAL.
FINAL is blocked until n8n/harness checks pass.
```

Use the internal console for scene-level editing and review:

```text
$env:UTUBE_ROOT\tools\production_console
```

The console is a dashboard/editor only. It must not become a new production root. It saves per-episode edits to:

```text
{episode_dir}\production_console.json
```

During production, fill or update each scene with script, SRT/caption, voice/audio path, Image2 prompt, generated image path, BGM, timing/layout, and notes. If the user splits a cut, split the corresponding caption/script/voice/image prompt in `production_console.json` first, then regenerate or relink assets from that updated scene plan.

When changing the production console UI, use its local design contract:

```text
$env:UTUBE_ROOT\tools\production_console\DESIGN.md
$env:UTUBE_ROOT\tools\production_console\UI_QA_CHECKLIST.md
```

Run `qa_console.ps1` before reporting UI/layout work as complete. Fix P0 failures before continuing.

After script/audio analysis, the console and report must also show the top situation summary:

```text
영상 제목
내용 요약
태그
사용된 보이스 버전
사용된 voice_id by role, for example 내레이션/성우/남편/여성대사
총 시간, for example 1분11초
하네스모드/하네스상태
n8n 상태
컴파운드 상태
```

These values belong in `production_console.json.summary`. If Compound is not yet linked to a real log source, write `WAIT - compound log not linked` instead of pretending it passed.

### Global YouTube Production Skill Coverage

This production-console rule applies to every YouTube video production skill, not only this shared guide:

- `0shrt-korea-production-agent`
- `0shrt-reality-saida-production-agent`
- `0shorts-yellowman-production-agent`
- `000short-production-agent`
- `11short-animal-agent`
- `11short-cryung-agent`
- `josun-historychoon-production-agent` when it proceeds beyond planning into actual image/TTS/CapCut/video work

### 0shrt vs 11short n8n/harness split

The progress-board concept is shared, but the phase-map/checklist is not shared.

For `0shrt-korea-production-agent`, `0shrt-reality-saida-production-agent`, and original 0shorts/Yellowman production, use `phaseMap: 0shrt_original_production`.

- n8n phases: start webhook, folder create, script, Image2 prompts/images, TTS/SRT, CapCut/render, report.
- harness phases: task state, target lock, script, image, voice, caption, render, ffprobe, frame QA, FINAL gate.
- evidence files: `job_state.json`, `work_order.json`, `todo_plan.json`, `asset_manifest.json`, `image2_manifest.json`, final script, `audio/main_capcut.srt`, `audio/full_with_outro.mp3`, `capcut_ready/image_timeline.md` or `video/capcut_draft_manifest.json`, `images/image2/scene_*.png`, `validation_report.json`, `evidence_pack.json`, `final_report.md`.

For `000short-production-agent`, `11short-animal-agent`, and `11short-cryung-agent`, use `phaseMap: 11short_remake_production`.

- n8n phases: URL/source intake, source download, Gemini/AI Studio analysis, normalized analysis, TTS/SRT/assets, CapCut draft, report.
- harness phases: task state, target lock, analysis, assets, source media, voice/caption, 3-text/CapCut, ffprobe, frame QA, FINAL gate.
- evidence files: `source.mp4`, `source_original_audio.*` or `source_audio.*`, `analysis_raw_gemini.json` when used, `analysis_master_gemini.md` or `analysis_master_gemini.json` when the integrated YouTube analyzer is used, `analysis_crosscheck.md`, `analysis.json`, `guide_ko.srt`, `onscreen_ko.srt`, `onscreen_layout.json`, `voice_opening.txt`, `voice_body.txt`, `voice_opening.mp3`, `voiceover_body.mp3`, CapCut draft manifest/name, and exactly the approved 3 visible text classes.

Before 11short assets/CapCut, compare the short-form Gemini JSON analyzer against the integrated YouTube master analyzer when a URL was analyzed for long writing, complex source interpretation, or production verification. If `analysis_crosscheck.md` is missing or blocked, fix/re-run analysis before TTS/SRT/CapCut.

Never block 11short because 0shrt-only `image2_manifest.json`, `job_state.json`, `evidence_pack.json`, or `final_report.md` is missing. Never pass 0shrt by checking only 11short `analysis/assets/capcut`.

When any of those skills creates or resumes a YouTube video, update the current episode/work folder's `production_console.json` at each major stage: script, audio, Image2/assets, CapCut/draft, render, ffprobe, frame QA, and final gate. If the local console server is available, load/save through `http://127.0.0.1:47831/api/episode`; otherwise write the same per-episode JSON directly.

Do not fake n8n or Compound status. If production was executed locally without the n8n webhook, write `WAIT` with a detail such as `local run; n8n webhook not invoked`. If Compound has no linked failure-memory log for the episode, write `WAIT - compound log not linked`.

The console summary must include at minimum: title, content summary, tags, target, `instagram_status`, total duration, voice model/version, voice_id by role, n8n state, harness state, Compound state, output video path, and current blocker/next action.

## Mandatory Video-Stage TODO Checklist

When the user asks to produce a video, render, make CapCut output, generate images, or run n8n, show and maintain this checklist in the working response or status file. Check items one by one as they are completed; do not mark all items complete only at the end.

```text
[ ] n8n UI opened: http://100.117.220.7:5678
[ ] n8n board checked: $env:UTUBE_ROOT\n8n\N8N_AGENT_PARALLEL_TODO.md
[ ] Layout source checked: $env:UTUBE_ROOT\video\VIDEO_LAYOUT_SPEC.md
[ ] CapCut selected as default production method
[ ] Skill phase-map selected: 0shrt_original_production or 11short_remake_production
[ ] Harness stage set selected from that skill phase-map
[ ] 0shrt only: official Image2 route selected and image2_manifest.json checked
[ ] 11short only: source.mp4, analysis.json, guide_ko/onscreen_ko SRT, voice files checked
[ ] CapCut draft created
[ ] Visual snapshot eye-check completed
[ ] Final mp4 saved under episode/video/*.mp4
```

If any checklist item cannot be completed, stop and report the exact blocker before continuing.

Supported channels:

- `mindset`: psychology/counseling style videos.
- `story`: story/yadam videos.

Default production route:

1. Script work.
2. User confirmation.
3. Video/audio/image/thumbnail production or CapCut preparation.
4. Harness/n8n checks.

Do not move from confirmed script into video creation, CapCut project editing, render setup, or thumbnail generation until the user confirms video production.

## First-Run Numbered Menu

When the user says a broad production request such as `유튜브 영상 제작`, `영상 하나 만들자`, `유튜브 제작`, `새 에피소드`, or similar, do not start drafting immediately. First show a numbered menu.

Step 1 channel/folder menu:

```text
어느 폴더/채널로 진행할까요?

1. mindset - 심리상담/마인드셋
2. story - 야담/스토리
```

When the user replies with only a number, treat it as the selected option and continue to the next menu. Do not ask them to retype the channel name.

Step 2 start-type menu:

```text
어디서부터 시작할까요?

1. 주제부터 정하기
2. 대본 초안 붙여넣기
3. 기존 에피소드 폴더 이어하기
```

Step 3 length menu:

For `mindset` or `story`:

```text
몇 분짜리로 갈까요?

1. 약 3분
2. 5~9분
3. 10~14분
```

Step 4 topic/draft discovery:

- If start type is `주제부터 정하기`, keep asking concise questions until the topic is concrete enough to draft.
- If start type is `대본 초안 붙여넣기`, ask the user to paste the draft and wait.
- If start type is `기존 에피소드 폴더 이어하기`, ask for the folder path and wait.

Topic-first questions should be asked one at a time, with numbered choices when possible. Ask until these are known:

- target viewer or situation
- core conflict/problem
- desired emotional ending
- channel/mode
- length range

Do not produce the full script until the topic is sufficiently defined. If the user gives only a vague topic, propose 3 concrete angles and ask the user to pick a number.

## Entry Point Detection

First classify the user input.

- Topic only: a subject, concern, viewer pain, or rough idea without a script.
- Draft script: a rough or complete script, transcript, scene list, or narration text.
- Video-stage request: asks for CapCut, images, audio, SRT, thumbnail, BGM, render, export, n8n, or harness.

If channel is missing, infer from folder path or words like `마인드셋`, `심리`, `상담`, `스토리`, `야담`, `썰`. If still unclear, ask one short question. If the input points to `0shrt`, `0쇼츠`, or standalone shorts-only 0shrt work, do not handle it with this skill; route it to the separate 0shrt skill.

If the input is broad and does not include a clear channel, start with the First-Run Numbered Menu instead of asking a free-form question.

## Channel Rules

### Mindset

Allowed starts:

- Topic-first start.
- Draft-script start.

For topic-first starts:

1. Convert the idea into a counseling theme.
2. Identify the target viewer pain, the unsafe instinct to avoid, and the healthier reframe.
3. Produce longform and shorts script direction.
4. Include estimated Korean character count and estimated runtime.
5. Draft or refine scripts unless the user only asked for topic options.

For draft-script starts:

1. Review the draft for counseling tone, clarity, pacing, and overclaim risk.
2. Preserve the user's intended point.
3. Convert to final longform and/or shorts scripts as requested.
4. Include character/runtime estimates.

Mindset tone:

- Calm, practical, non-diagnostic.
- Avoid pretending to provide medical treatment.
- Use "이럴 수 있습니다", "먼저 이렇게 말해도 됩니다" style.
- Prefer concrete workplace/family/relationship situations.

### Story

Allowed default start:

- Draft-script start.

For story drafts:

1. Review the draft for hook, chronology, character motivation, emotional escalation, and spoilers.
2. Preserve the story's core premise.
3. Produce final script and shorts extraction as requested.
4. Include character/runtime estimates.

If the user gives only a story topic, do not invent the whole story by default. Ask for a draft or explicit permission to build a premise.

For `11utube/story` episode work, obey the project harness rule after each stage:

```bash
python $env:UTUBE_ROOT/story/scripts/harness_validate.py {episode_dir} --stage {stage}
```

Do not continue to the next story stage if the harness fails.

## Script Outputs

When producing or confirming scripts, include:

- Entry basis: topic or draft.
- Channel and mode: `mindset` or `story`, `longform`, `shorts`, or both.
- Estimated character count.
- Estimated runtime.
- Longform script if requested or implied.
- Shorts script if requested or implied.
- Open issues that block video production.

Runtime estimate rule:

- If audio or SRT exists, use its real duration.
- Otherwise estimate Korean narration at about `350-420` Korean characters per minute.
- For shorts, keep the default target near `45-70` seconds unless the user asks otherwise.
- For longform, use the requested length; if absent, choose a practical range and state the assumption.

After final script approval, stop and ask:

`대본은 여기서 확정입니다. 이 기준으로 이미지/음성/CapCut 비디오 제작 단계로 넘어갈까요?`

## Video Production Gate

Only proceed to video stage after user approval, unless the user's latest message is already a direct video-stage command.

n8n visibility rule:

- When starting video-stage production, open the n8n UI in a visible Chrome window before running long tasks so the user can watch executions.
- Default n8n UI: `http://100.117.220.7:5678`.
- The preferred user-facing workflow is one operations canvas: `11utube/n8n/workflows/22utube_ops_console.webhook.json`.
- Do not make the user monitor normal production across multiple n8n workflows; split files may exist only as backend/legacy/import-by-part helpers.
- Prefer opening the execution/workflow UI once at production start; do not repeatedly steal focus while rendering unless the user asks.
- If n8n is unreachable, report that and continue with local harness only when local execution is still safe.
- Do not leave n8n as a hidden background-only dependency for video work.

n8n visual workflow rule:

- Do not rely on a single monolithic `Webhook -> Code runner` view for user-visible production. It is acceptable as a backend runner, but it does not show the actual production state.
- User-visible n8n workflows should expose the production phases as separate nodes: start, channel/script branch, approval, audio, prompts, official Image2, imagegen gate, CapCut profile/draft, visual snapshot gate, render/export, final/upload package.
- Parallel agent mode must be visible as separate branches or status-signal nodes, with each branch reporting `queued/running/passed/failed`.
- n8n can highlight active nodes and execution paths while the workflow runs; agent work outside n8n must send explicit status events/webhooks if the user needs live blinking/progress in n8n.
- Every long-running agent/phase should emit status JSON through `tools/agent_status_store.py` or `POST /webhook/22utube/status/update`.
- Status storage is `11utube/n8n/status/agent_status.sqlite`; do not add Redis or another service until sqlite proves insufficient.

Resolution lock for fast default production:

- Shorts render/canvas: `720x1280`.
- Longform render/canvas: `1280x720`.
- Image2 landscape source: `1280x720`.
- Image2 portrait source: `720x1280`.
- Image2 square source: `1024x1024` native, then fit/downscale into a `720x720` shorts image box.
- Do not request `720x720` directly from GPT Image2; it is below the model's native minimum pixel count.
- Use GPT Image2 low quality for fast drafts unless the user explicitly asks for final/key-art quality.

Image2 provenance lock:

- Final video images must be real Image2 outputs with provenance. Do not use local PIL/storyboard/mock images as final `images/image2` assets.
- Chrome UI automation is only a fallback when explicitly requested. The preferred no-Chrome route is the project command/API runner for the selected mindset/story channel.
- Codex built-in `/image gen` or `image_gen` is forbidden for 22utube production episodes, including previews, key-art exploration, batch scenes, replacement stills, and emergency fallback.
- For episode scenes, use only the official project route: ChatGPT Image2 project / Chrome Prompt Runner / numbered downloads / `images/image2/image2_manifest.json`.
- Local placeholder generation is forbidden. Do not run `create_local_storyboard_images.py` or any PIL/mock/storyboard image generator for production episodes.
- If a local placeholder image already exists, treat the episode as blocked until official Image2 files replace it.
- Before CapCut or final render, require `images/image2/image2_manifest.json` with `official_image2=true`, Image2 provenance (`gpt-image-2`, `gpt_image2`, `chatgpt_image2`, or `openai_images_api`), and a complete scene file list.
- If the image2 manifest is missing, marks `local_placeholder`, `placeholder`, `fallback`, `mock`, or `dry_run`, or does not cover every prompt scene, imagegen/capcut/final must fail.
- Prompt Runner/ChatGPT manual downloads must still create or update the same manifest after files are saved.

Single-scene Image2 prompt lock:

```text
Create image [number].
After creating the image, reply with exactly [number]생성 and nothing else.
Filename: [number].png.

IMPORTANT:
Generate only this one scene.
Do not combine with any other scene.
Do not create a storyboard, collage, grid, multi-panel layout, or sequence.
Create only one single full-frame image for this filename.

Create one single image for the episode. Do not add any text, captions, subtitles, UI, logos, or watermarks.

SCENE: [one scene only]
```

Default route after approval:

- CapCut is the default production method.
- CapCut route means more than a package: create the local CapCut draft under the fixed CapCut profile/project store, register it in `root_meta_info.json`, write `video/capcut_draft_manifest.json`, then run the channel harness.
- Before final/export review, create the fast visual snapshot gate from the CapCut draft. Default eye-check is 3 PNG frames plus a contact sheet, not a 5-second preview render.
- Run `tools/capcut_visual_snapshot.py` after the CapCut draft/profile stage and before final harness. Require `video/visual_snapshot/visual_snapshot_manifest.json` with at least 3 valid PNG snapshots.
- Direct MP4 render is a separate route. Use `render_images` or Hyperframe only when the user explicitly asks for direct render/export instead of CapCut.
- Final exports must go into the episode `video` folder.

Shared rules:

- Use `$env:UTUBE_ROOT\video\VIDEO_LAYOUT_SPEC.md`.
- If rules change, update the video spec and the relevant n8n/harness scripts together.
- SRT timing is the source of truth for captions and voice alignment.
- Display captions must use viewer-readable text, not TTS pronunciation text. Years, centuries, and quantities must stay as display forms such as `1795년`, `14세기`, `500여 석`; spoken forms such as `천칠백구십오년` belong only in TTS/voice fields.
- If pronunciation needs to differ from display text, write the script source as `1795년[[천칠백구십오년]]`, generate audio from the bracket pronunciation, and generate SRT/CapCut captions from the display text before `[[`.
- Upload tags for every YouTube Shorts skill must be comma-separated. Put a comma immediately after every tag, including the final tag. Example: `김만덕, 제주역사, 한국사쇼츠, shorts,` or `#김만덕, #제주역사, #한국사쇼츠, #shorts,` depending on that skill's tag style.
- Image, voice, SRT, BGM, and final mp4 paths must stay inside the episode folder or shared `11utube/video` reference folders.

## Episode Root Frontstage

The user-facing `episode/` root must stay clean. It should show only files the user needs to inspect:

- `01_롱폼_이미지프롬프트.md`
- `02_숏폼_이미지프롬프트.md`
- `03_i2v_동영상프롬프트.md`
- `04_유튜브업로드정보.txt`
- `결과물_롱폼.mp4`
- `결과물_쇼츠1.mp4`
- `썸네일_롱폼.png`
- `썸네일_옵션01.png`
- `썸네일_옵션02.png`

Backend folders and working files such as `audio`, `images`, `render`, `video`, raw scripts, review files, and package JSONs may stay in place for scripts and CapCut, but mark them hidden on Windows so the root is not confusing.

Refresh the frontstage after prompt/video/thumbnail/export changes:

```bash
python $env:UTUBE_ROOT/tools/episode_frontstage.py {episode_dir}
```

The i-to-v prompts come from `video_prompt:` blocks inside the longform/shorts image prompt files and are copied into `03_i2v_동영상프롬프트.md`.

Mindset shorts CapCut style lock:

- Use `$env:UTUBE_ROOT\video\CAPCUT_MINDSET_SHORTS_STYLE_LOCK.json`.
- Keep title/subtitle layout, CTA, BGM/SFX, and tail linger unless the user explicitly changes them.
- Replace only episode images, voice audio, SRT captions, and title text for new episodes.

Current locked mindset shorts audio style:

- Typewriter SFX: `video/배경음/타자음3초.MP3`.
- Soft piano BGM: `video/배경음/shorts/잔잔은은피아노.MP3`.
- Tail linger: SRT end plus `3.22s`.
- BGM must sit below voice, normally about `8-14 dB` lower.

Supertone model default:

- Current 11utube default is Sona Speech 2 `sona_speech_2`.
- Treat plain "Sona 2", "소나 투", "기본 음성", or "원래대로" as `sona_speech_2`.
- Use Supertonic 3 `sona_speech_2t` only when the user explicitly asks for Supertonic 3 or `sona_speech_2t`.
- Never report a voice job as complete without stating the exact model used.
- Use old `supertonic_api_1` only when the user explicitly says `supertonic1` or `Supertonic API 1`.
- After Supertone API generation or balance checks, report the remaining `credit_balance`. Never print or expose `SUPERTONE_API_KEY`.

## Supertone Voice Map By Production Skill

Use this as the common index before generating audio. Dedicated skills may contain the detailed workflow, but this table defines where each voice belongs so voices are not guessed or swapped between channels.

Common rule:

- Default model for all current 11utube Supertone calls is `sona_speech_2`.
- Use `sona_speech_2t` only when the user explicitly asks for Supertonic 3.
- Always report the exact model and voice ID used.
- Never expose `SUPERTONE_API_KEY`; only report `credit_balance`.

| Production skill / channel | Default voice placement | Voice ID / source |
| --- | --- | --- |
| `000short-production-agent` | Opening hook / intro voice | `6e43a7b9ffa9834c154ab7` |
| `000short-production-agent` | Main body voice for strongest 1-3 moments | `4f8ed5978a174902ad2fc9` |
| `11short-animal-agent` | Same as base 11short: opening hook | `6e43a7b9ffa9834c154ab7` |
| `11short-animal-agent` | Same as base 11short: body voice | `4f8ed5978a174902ad2fc9` |
| `11short-cryung-agent` | Intro is male hook; body is full sad/news narration | Inherits base 11short voice pattern unless its local rule or user override names another voice |
| `0shrt-korea-production-agent` / history shorts | Body-only Chunsik-style Korean history narration | `4f8ed5978a174902ad2fc9` |
| `josun-historychoon-production-agent` | Planning/script/upload package only; actual TTS follows 0shrt-korea | `4f8ed5978a174902ad2fc9` when production is handed to 0shrt-korea |
| `0shrt-reality-saida-production-agent` | Saida YouTube/basic narration | `42b52760fe9ecf701f8ed3` |
| `0shrt-reality-saida-production-agent` | Saida Instagram narration, only after explicit Instagram conversion request | `56e1a6c42fc4968d15a394` |
| `0shrt-reality-saida-production-agent` | Sister-in-law / Sujin female dialogue | `9d5dfb8036afacd09cd125` |
| `0shrt-reality-saida-production-agent` | Husband dialogue | `4653d63d07d5340656b6bc` |
| `0shrt-reality-saida-production-agent` | Other victim/villain character dialogue | `references/saida_voice_cast.md`, one clip per speaker segment |
| `0shorts-yellowman-production-agent` | Yellowman main / narration info | `yellow/config/voices.json#yellowman_main` and `#narration_info` -> `42b52760fe9ecf701f8ed3` |
| `0shorts-yellowman-production-agent` | Female question voice | `yellow/config/voices.json#female_question` -> `084714312eb4ec06fbfe51` |
| `story` longform/yadam | Default story/history narrator lock | `story/config/VOICE_POLICY_OPERATOR_APPROVED.md` -> `chunsik_plain` / `4f8ed5978a174902ad2fc9` |
| `story` longform/yadam | Role-based cast voices | `story/config/voices.json` personas |
| `mindset` longform/derived shorts | No single locked Supertone ID in this skill; follow channel rule or episode-local voice decision | Confirm selected voice before TTS if not already fixed |

Story voice safety:

- `story/config/VOICE_POLICY_OPERATOR_APPROVED.md` overrides the raw `story/config/voices.json` persona table for approvals and bans.
- Approved sad male voice: `58662d5bd86d1b7837f197`.
- Hard banned voice IDs: `751ba7d5af37a49d68f2a7`, `63481531575c53a193ba0d`, `7f8873011eeba6f11b750f`.
- Do not use a banned ID even if it still appears in an older persona table or test file.

Reference files:

```text
$env:UTUBE_ROOT\11short\README.md
$env:UTUBE_ROOT\0shrt\README.md
$env:UTUBE_ROOT\0shrt\channel_style.json
$env:UTUBE_ROOT\story\config\voices.json
$env:UTUBE_ROOT\story\config\VOICE_POLICY_OPERATOR_APPROVED.md
$env:UTUBE_ROOT\yellow\config\voices.json
$env:UTUBE_ROOT\video\VOICE_TEST_SUMMARY.md
$env:UTUBE_ROOT\video\SUPERTONE_API_KEY_LOCATION.md
```

## Harness Checks

Use local checks when working on this Windows machine.

CapCut package gate:

```bash
python $env:UTUBE_ROOT/tools/n8n_capcut_prepare.py --episode-dir {episode_dir} --mode {mode}
```

Common video asset gate:

```bash
python $env:UTUBE_ROOT/video/channel_episode_harness.py {episode_dir} --channel {channel} --mode {mode} --stage assets
```

CapCut SRT timing gate, when a draft exists:

```bash
python $env:UTUBE_ROOT/video/capcut_draft_srt_harness.py --mode shorts --draft {draft_content_json} --srt {srt_path} --audio {voice_audio_path}
```

Fast visual snapshot gate, after CapCut draft/profile and before final export:

```bash
python $env:UTUBE_ROOT/tools/capcut_visual_snapshot.py --episode-dir {episode_dir} --mode {mode}
```

This gate writes `video/visual_snapshot/snapshot_01_first.png`, `snapshot_02_middle.png`, `snapshot_03_end.png`, `snapshot_contact_sheet.png`, and `visual_snapshot_manifest.json`. Use it for quick eye-checks. Only render a short preview video when motion/audio sync needs inspection.

Final gate after export:

```bash
python $env:UTUBE_ROOT/video/channel_episode_harness.py {episode_dir} --channel {channel} --mode {mode} --stage final
```

n8n may be used as the remote gate server when available, but do not depend on n8n for local file edits.

## Thumbnail Gate

For thumbnails, use:

- `$env:UTUBE_ROOT\video\THUMBNAIL_SPEC.md`
- Episode `video/thumbnail_*` outputs.

Do not create thumbnails before script approval unless the user directly asks for thumbnails.

## Response Style

Keep Korean responses direct and operational.

When reporting script work, keep the user focused on:

- What entry point was detected.
- What script/version is now the source of truth.
- Expected length.
- Whether video production is waiting for approval.

When reporting video work, include exact files changed and checks passed or failed.

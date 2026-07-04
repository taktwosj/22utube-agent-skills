---
name: 000short-production-agent
description: Use only when the user explicitly asks to create, validate, or repair production assets, subtitles, layout JSON, CapCut drafts, render packages, export packages, upload packages, or production packages. Do not use for script creation, urakkai decisions, hook/channel planning, or draft-only polishing.
---

# 11short Production Agent

## Ownership Matrix

- `00-tikitaka`: Shorts source analysis, remake script draft, hook, top/timed-middle, and script handoff only.
- `00script-writer`: polish/review an existing script draft only.
- `000short-production-agent`: SRT, layout JSON, CapCut, validation, exports, upload packages, and other production assets only.
- `22utube-production-agent`: shared factory policy only.

## Escalation Rule

Do not start this skill from script-adjacent intent alone. Use it only when the
user explicitly asks for subtitles, layout JSON, render plans, CapCut drafts,
exports, upload packages, production packages, production validation, or repair.

Route Tikitaka, 우라까이, hook, 상단, timed 중단, or Gemini source-note scripting
to `00-tikitaka`; wording-only improvement to `00script-writer`; shared policy
questions to `22utube-production-agent`.

Do not originate the script, choose the urakkai angle, create hook/channel
planning, or polish a draft inside this skill. Confirm script authority first,
then build or validate the requested production files.

## Default Boundary

Default state is `PRODUCTION_GATE`.

No production pass is allowed from intent alone. Do not claim `PASS`,
`SCRIPT_LOCK`, upload-ready, export-ready, or complete unless the required
evidence files exist and the relevant validator has been run in this turn.

Working drafts, compatibility drafts, and draft-fast packages are intermediate
states. They are not production approval.

## Active Root

For new 22utube Shorts production, read:

```text
${env:WORKSPACE_ROOT}\22factory_20260628\AGENTS.md
```

Create new Shorts episode outputs under:

```text
22factory_20260628\01_shorts_factory\episodes\SH_YYYYMMDD_slug
```

Store CapCut metadata, manifests, snapshots, reports, and upload/final packages
in OneDrive. The editable CapCut draft itself stays in the local CapCut project
directory on the machine that builds it.

Legacy `11utube/11short/000short-production-agent/episodes` folders are
reference or explicit repair targets unless the user asks for legacy work.

## Production Inputs

Before generating or repairing production assets, identify the current authority:

- `source.mp4` or equivalent source file
- source provenance and usable-file check
- source-evidence/watch/direct-frame findings when the video content matters
- script authority, usually `final_script_ko.txt` or the current Tikitaka draft
- Tikitaka segment audio plan when the script came from `00-tikitaka`
  (`tikitaka_segment_audio_plan` or equivalent `구간 오디오 정책표`)
- humanized final Korean text when visible text is final
- target template/layout
- requested voice/audio policy, if any
- requested BGM/SFX asset, if any. BGM is optional unless the user explicitly
  chooses or requires it.

Missing `source.mp4` is a hard stop for source-derived production. Do not proceed
to source evidence, verified analysis, SRT/layout, CapCut, export, upload, or
final validation without source acquisition and provenance.

If the script came from Tikitaka and timed `중단` blocks exist, missing segment
audio policy is a hard stop:

```text
WAIT_TIKITAKA_SEGMENT_AUDIO_PLAN
```

Do not infer quote/TTS/source-audio policy inside production. Use the Tikitaka
plan as the authority:

- `caption_type=speaker_quote` or visible `"..."` => source audio must be audible
- `caption_type=tts_narration` => source audio must be muted unless
  `caption_type=tts_plus_source` explicitly allows ducking
- `caption_type=situation_caption` => source audio muted by default
- `caption_type=ranking_item` => source audio muted by default, except verified
  quote/reaction beats
- `source_order` and `timeline_order` must be preserved when the script remixes
  source order
- `bgm_policy=optional` or `optional_duck` never requires a BGM track. Treat BGM
  as mandatory only when the plan says `bgm_policy=on` or `duck`, or when the
  user named a specific BGM/SFX asset.

## Supertone TTS / Voice Generation

When the user explicitly asks for TTS, voice generation, narration audio, or
voice files for a YouTube/Shorts production, use the local Supertone route
before considering any other provider.

Default local command on Windows:

```powershell
py -3.14 "${env:WORKSPACE_ROOT}\22factory_20260628\00_asset_tools\tools\make_supertone_tts.py" "<대본 텍스트>" "<출력파일.wav>"
```

Required behavior:

- Read configuration only from environment variables:
  `SUPERTONE_API_KEY`, `SUPERTONE_VOICE_ID`, `SUPERTONE_PITCH`,
  `SUPERTONE_SPEED`, `SUPERTONE_MODEL`.
- Never paste, print, write, serialize, or report the API key. Do not put it in
  Git, OneDrive production files, CapCut JSON, manifests, logs, reports, or
  chat.
- On `home_windows`, User-scope Supertone variables may be registered even when
  the current Codex process environment is stale. The shared script reads the
  Windows User environment as a fallback.
- Use `py -3.14` because the installed Supertone SDK is on that interpreter; do
  not rely on bare `python` unless you have verified `import supertone` there.
- The default voice/model are controlled by env vars. Current home_windows
  setup uses Chunsik through `SUPERTONE_VOICE_ID` and `sona_speech_1`.
- If env variables or SDK are missing, stop with
  `WAIT_SUPERTONE_ENV_OR_SDK_MISSING`; do not switch to Edge TTS, ElevenLabs,
  browser TTS, Kokoro, or any fallback provider without explicit user approval.
- Record generated audio path, duration, voice id label, model, pitch, and
  speed in the production manifest, but never record the API key.

For TTS-capable story, narration, 사연, 미담, photo-explainer, 군림보-style, or
썰풀이 Shorts, script authority must show the TTS storytelling gate was handled.
Before SRT/layout/CapCut work, confirm which truth mode the script owner chose:

- `fact_first`: information, knowledge, news, politics, medical, legal, safety,
  accident, crime, finance, or source-sensitive factual explainers. Require
  source-supported claims and do not accept unverifiable hook premises as fact.
- `hook_first_writer_premise`: 감동형 narration, TTS-only, BGM-heavy, family,
  reunion, cute/moment, photo-explainer, or ordinary emotional story Shorts.
  If the user says `후킹 쎄게`, `작가모드`, `우라까이`, or directly tells the agent
  to make the hook stronger, production must accept a strong writer premise
  from the script authority even when it is not source-verifiable. Do not block
  it just because it is not evidence-backed; block only high-risk or materially
  harmful invented claims.

For `fact_first`, confirm the script has source-supported fields. For
`hook_first_writer_premise`, confirm the script has a strong emotional hook or
equivalent fields such as:

- `tts_story_mode_required`
- `truth_mode`
- `source_supported_emotional_condition`
- `writer_premise_for_hook`
- `writer_premise_status`
- `emotional_entry_line`
- `changed_scene_entry_order`
- `changed_korean_expression_strategy`
- `viewer_emotion_target`
- `payoff_recovery_line`

If this is missing or the draft opens as a flat event summary, stop at
`WAIT_SCRIPT_REWRITE_REQUIRED` and route back to `00-tikitaka` or
`00script-writer`. Do not rewrite the story inside production. Do not reject an
ordinary emotional/TTS script solely because the hook premise is plausible,
fictionalized, or not source-verifiable.

## Owned Outputs

This skill may create, validate, or repair:

- SRT/subtitle files
- caption/layout JSON
- render plans
- explicitly requested voice/audio files for production use
- CapCut draft folders and draft JSON
- production manifests
- export packages
- upload packages
- reports and validation logs

This skill does not originate Tikitaka creative structure when no script authority
exists. Ask for or route to the script owner first.

## Standard Sequence

1. Confirm active root and episode folder.
2. Confirm source file and provenance.
3. Confirm script authority and visible-text cleanup status.
4. Confirm `tikitaka_segment_audio_plan` / `구간 오디오 정책표` when the script came from Tikitaka.
5. Build or repair SRT/layout/render-plan assets from that segment audio plan.
6. Build or repair the local CapCut draft.
7. If reference sameness is requested or required, run the bounded similarity
   loop from `08_SIMILARITY_LOOP_CONTRACT.md`; patch only failed dimensions.
8. Snapshot CapCut draft JSON into the episode metadata folder.
9. Run the required harness or validator for the current stage.
10. Report `PASS/FAIL/WAIT` with evidence paths and one concrete next blocker.

## Mandatory CapCut Media Settings — HARNESS LOCK

This is a **HARNESS_LOCK** production gate. It is not an optional style checklist and not something to remember verbally. The coordinator must require the harness/validator result before claiming any CapCut draft/project/profile is production-ready.

Every source video segment must carry the Git manifest media settings from `manifests/capcut-template-set.json` and pass `scripts/validate_capcut_timeline_order.py`:

- 품질보정 / QualityEnhance: `HD`
- 사운드 노멀라이즈: enabled, target loudness `-14 LUFS`
- 자동조정 / smart_color_adjust: `30~50`
- 선명하게 / clear: `30~50`
- 선명도 / sharpen: `30~50`
- 입자 / particle: `5~30`
- 인접 source segment는 자동조정/선명하게/선명도 값이 최소 `5` 이상 차이 나야 함

Required validator evidence:

```text
mandatory_capcut_media_settings_status: PASS
```

If any of these are missing, out of range, or not checked by the validator, the state is:

```text
FINAL: BLOCKED
reason: MANDATORY_CAPCUT_MEDIA_SETTINGS_NOT_HARNESS_VERIFIED
```

Coordinator rule: whenever the operator asks about CapCut video/sound settings, CapCut readiness, draft quality, or finalization, answer with this harness-locked media gate first. Do not answer only with export settings such as 9:16/1080p/30fps.

## CapCut Rules

For any CapCut draft/project/profile creation, modification, repair, patch, or
validation response, the final answer must end with a `캣컵복사하기` Markdown
block containing only the CapCut project name. Put paths and reports in the main
body, never inside that block.

## Validation Rules

Use validators and harness scripts that already exist in this skill before
claiming a stage is complete.

If a validator fails, stop at that stage, report the failing item, fix it if the
request allows, and re-run validation. Do not continue downstream on a failed
stage.

Do not confuse:

- working draft created
- harness pass
- production gate pass
- upload ready

Each state needs its own evidence.

## Reference Routing

- For CapCut text effect presets, read
  `references/capcut_text_effect_presets.md`.
- For Shorts craft constraints after an explicit production request and script
  authority, read `references/shorts-academy.md`.
- For the old Tikitaka production-script contract, read
  `references/tikitaka-script-v17.md`.
- For work-order, pipeline, layout, harness, cut-assembly, DRAFT_FAST /
  FINAL_LOCK report-contract, and reference-similarity loop details, read the
  numbered root docs in this skill folder, including
  `07_DRAFT_FAST_REPORT_CONTRACT.md` and
  `08_SIMILARITY_LOOP_CONTRACT.md`.
- For old full-contract details or legacy repair only, read
  `references/archived-full-skill-20260629.md`.

Keep this `SKILL.md` as the active production router. Do not re-add broad
Tikitaka, 우라까이, channel-family, hook, or analysis triggers to the description.

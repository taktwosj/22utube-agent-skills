---
name: 00-tikitaka
description: Use only when the user explicitly asks for Tikitaka Korean Shorts remake scripting, 우라까이, hook candidates, 상단/timed 중단 draft creation, or provides Gemini Shorts source notes for remake scripting.
---

# 00 Tikitaka

## Ownership Matrix

- `00-tikitaka`: script draft only.
- `00script-writer`: polish existing script only.
- `000short-production-agent`: production assets only.
- `22utube-production-agent`: shared factory policy only.

## Escalation Rule

Do not move to the next owner unless the user explicitly asks for that owner's
stage.

Adjacent intent is not permission to escalate. A Tikitaka request does not imply
production, handoff, `SCRIPT_LOCK`, `PASS`, export, upload, completion, audio
generation, SRT generation, layout JSON, or CapCut work.

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

## Output Contract

Default chat output:

```text
상단
...

중단 초벌대본
[블록 1 | 편집 00:00-00:03 | 원본 제안 00:00-00:00 | 상태 PROPOSED_SOURCE_TIMECODE]
...

중단 TTS 글자만 복사
...

상태
- script_status: DRAFT_EYE_REVIEW
- production_status: WAIT_EXPLICIT_000SHORT_REQUEST
```

Use `1/2/3/4/5` labels only as temporary source-range confirmation IDs, not as
the creative structure. The creative structure must be functional: hook,
misread, escalation, reversal, payoff, or another stated role.

## Draft Workflow

1. State the frame: what situation the remake is using and why.
2. Map source notes into functional beats.
3. Write hook candidates if requested or useful.
4. Produce `상단 + timed 중단`.
5. Provide the copy-only voice text block as script text, not as audio work.
6. Keep status at `DRAFT_EYE_REVIEW` unless the user explicitly asks for the
   next owner.

## Shorts TTS Storytelling Mode

If a Shorts remake can be told as TTS narration, story, or 썰풀이, this mode is
mandatory, not optional.

This mode is not separate from 우라까이. 우라까이는 the baseline condition: the
remake must not keep the same expression, scene-entry order, emotional angle, or
payoff wording. The TTS story gate decides how aggressively the same
source-supported meaning must be reframed through emotion.

Do not start as a flat event summary. Lead with the strongest source-supported
emotional condition, deadline, loss, desire, or irreversible action.

```text
weak: 할아버지가 손자를 만났다
strong: 시한부 할아버지가 마지막으로 손자를 보러 왔다
```

The strong version is allowed only when the source supports `시한부` and
`마지막`. If the source only proves a visit, intensify through framing,
sequence, suspense, and viewer emotion without inventing facts.

Required TTS story fields:

- `tts_story_mode_required: true|false`
- `source_supported_emotional_condition`
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
- invented illness, death, family motive, deadline, confession, or final meeting
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

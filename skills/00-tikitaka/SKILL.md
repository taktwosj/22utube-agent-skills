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

## Required Gates Before Stronger Claims

- Do not claim `SCRIPT_LOCK` from this skill alone.
- Do not claim production allowed.
- Do not claim source-verified truth from raw Gemini notes.
- Do not skip human Korean cleanup before any final visible Korean text.
- Do not proceed past missing source evidence when the script depends on exact
  timing, OCR, or dialogue.

## Reference Routing

- For hook review, read `references/pre_script_hook_review.md`.
- For Shorts craft rules, read `references/shorts-academy.md`.
- For old contract details or legacy repair only, read
  `references/archived-full-skill-20260629.md`.

Keep this `SKILL.md` as the active router. Do not re-expand it with legacy
examples, PASS templates, production reports, CapCut details, or long handoff
instructions.

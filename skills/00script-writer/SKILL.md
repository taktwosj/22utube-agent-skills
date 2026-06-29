---
name: 00script-writer
description: Use only when the user already has a Korean video or Shorts script draft and asks to polish wording, rhythm, tone, hook pressure, retention, readability, or policy-safe rewrite.
---

# Script Writer

## Ownership Matrix

- `00-tikitaka`: script draft only.
- `00script-writer`: polish existing script only.
- `000short-production-agent`: production assets only.
- `22utube-production-agent`: shared factory policy only.

## Escalation Rule

This skill improves an existing Korean script draft. It does not start a Shorts
remake lane, create production files, build CapCut drafts, generate SRT/layout
assets, export video, or package uploads.

If the user asks for Tikitaka remake scripting, 우라까이, hook candidates, 상단,
timed 중단, or Gemini source-note scripting, route to `00-tikitaka`.

If the user asks for production assets, subtitles, layout JSON, CapCut, render,
export, upload, or production validation, route to `000short-production-agent`.

If the user asks about shared folder/root/archive policy, read
`22utube-production-agent` as reference.

## Default Boundary

Default state is `REWRITE_DRAFT`.

Do not claim `SCRIPT_LOCK`, `PASS`, production-ready, upload-ready, or complete
from a rewrite alone. A rewrite can be stronger, cleaner, and policy-safer while
still requiring downstream owner gates.

## Active Root

For current 22utube work, check:

```text
${env:WORKSPACE_ROOT}\22factory_20260628\AGENTS.md
```

If saving rewrite outputs for new Shorts work, use the active episode folder:

```text
22factory_20260628\01_shorts_factory\episodes\SH_YYYYMMDD_slug
```

Legacy paths are references or explicit repair targets only.

## Input Requirements

Require an existing draft or a clearly quoted text block to polish.

If the user provides only a topic, source URL, Gemini notes, or a vague idea,
do not silently become the initial remake writer. Route to `00-tikitaka` for
Shorts remake scripting or ask for the current draft.

## Owned Work

This skill may improve:

- Korean wording and compression
- hook pressure
- rhythm and spoken readability
- retention beats
- memory anchors
- policy-safe phrasing
- title/thumbnail copy when tied to an existing script review

This skill may run writer/persona review when the user asks for a gate or when
the current contract requires a visible rewrite gate. Keep the output focused on
rewrite findings and the revised draft.

## Output Contract

Use a compact status block:

```text
상태
- rewrite_status: REWRITE_DRAFT
- production_status: WAIT_EXPLICIT_000SHORT_REQUEST
- notes: ...
```

When rewriting Shorts captions, preserve the active visible structure unless the
user asks to restructure it:

- `상단`
- timed `중단`
- copy-only voice text when present in the draft

Do not add production labels to public-facing text.

## Policy and Evidence

If factual, legal, medical, financial, political, safety, or source-claim risk is
present, run a policy/evidence pass before calling wording final.

Do not add unsupported facts, verified dialogue, source timing, OCR, or scene
order. Use source evidence or route back to the source owner when needed.

## Reference Routing

- For persona gates, read `references/parallel-persona-gate.md`.
- For rhythm, read `references/rhythm-rules.md`.
- For policy, read `references/youtube-policy-gate.md`.
- For evidence tiers, read `references/evidence-tier.md`.
- For hooks and memory anchors, read the relevant `references/*anchor*.md` and
  `references/hook-loop-structure.md`.
- For old full-contract details or legacy repair only, read
  `references/archived-full-skill-20260629.md`.

Keep this `SKILL.md` as the rewrite router. Do not re-add broad production,
CapCut, SRT, handoff, or initial-remake triggers to the description.

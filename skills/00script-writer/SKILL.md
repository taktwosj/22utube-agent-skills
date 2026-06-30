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

## Reader Comprehension Gate

Before calling a rewrite clean, run a first-reader check on every viewer-facing
line, especially lower T1/chapter text and Shorts captions.

Hard fail the line if a fresh reader cannot explain it in one plain sentence
after one read. If agent/subagent mode is available, ask an isolated reader
agent to answer `PASS/FAIL`, `what does this mean?`, and `why did it fail?`.
If the reader says `I do not understand`, hesitates, or explains a different
claim than intended, rewrite the line. Do not defend the original by explaining
context.

Common fail patterns:

- circular premise: `내란에 기여한 사람` and `왜 내란 연루자가 됐어야 했나`
- subject-role collision: actor, victim, suspect, and beneficiary roles blur
- why-question inversion: the question asks why a consequence should happen
  after the line already states the reason
- abstract noun pileup: `핵심 의혹`, `역설적 질문`, `전체의 본질` without a
  concrete actor or action
- reread requirement: a viewer must stop and parse grammar instead of following
  the video

Rewrite rule: one line carries one clear claim or question; the next line
explains why it matters. Prefer concrete actor + action + consequence.

Use the old writer-mode hole/anchor system for serious rewrites:

```text
구멍: what exact question is opened for the viewer?
앵커: what concrete person, object, number, action, or sentence holds the viewer?
보상: what answer or clue arrives within the next beat?
회수: where does the text return to the same anchor?
```

A viewer-facing line fails if it opens no clear `구멍`, has no concrete `앵커`,
or cannot be recovered later. Do not substitute abstract labels such as
`핵심`, `본질`, `의혹`, `역설`, or `프레임` for the anchor. Those words may appear
only after the concrete actor/action is already clear.

For longform or midform drafts, this gate should use an isolated reader when
agent mode is available. Ask the reader to answer:

```text
PASS/FAIL
이 문장을 한 문장으로 설명하면?
막힌 단어/논리/주어는?
더 쉬운 2줄 자막은?
```

If the reader cannot explain the line without extra context, the line is
`REWRITE_REQUIRED`.

Example fail:

```text
챕터5_ 내란에 기여한 사람이 왜 내란 연루자가 됐어야 했나
이 역설적 질문이 특검 전체의 핵심 의혹이다
```

Example pass:

```text
챕터5_ 내란에 기여했다면 왜 수사 대상에서 빠졌나
2차 종합특검의 핵심은 바로 이 질문이다
```

## TTS Story Rewrite Gate

For Shorts drafts that can be told as TTS narration, story, 사연, 미담, photo
explainer, 군림보-style narration, or 썰풀이, do not polish the draft into a flat
summary.

The rewrite must preserve or create a source-supported emotional entry line:
strong condition, deadline, loss, desire, contradiction, or irreversible action
before background explanation.

```text
weak: 할아버지가 손자를 만났다
strong: 시한부 할아버지가 마지막으로 손자를 보러 왔다
```

Use the strong version only when the source supports the stronger facts. Do not
invent illness, death, family motive, deadline, confession, or a final meeting.
If the source is weaker, intensify through Korean expression, entry order,
suspense, viewer question, and payoff recovery.

Mark the draft `REWRITE_REQUIRED` if:

- TTS can carry the story but the opening is a neutral event summary
- the rewrite changes only synonyms while keeping the source flow
- the emotional line is unsupported by evidence
- a first-time viewer cannot tell who wants what and what may be lost

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

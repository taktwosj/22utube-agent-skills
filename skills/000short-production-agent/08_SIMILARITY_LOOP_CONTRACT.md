# Similarity Loop Contract

This contract borrows the evidence-led loop shape from LazyCodex/OmO style
workflows, but it is scoped to 11short production. It is not a general
autonomous agent loop and must not install or invoke LazyCodex.

## Purpose

Use the similarity loop only to make a candidate Shorts script, subtitle plan,
layout JSON, or CapCut draft converge toward a known reference.

The goal is:

```text
reference_fingerprint -> candidate -> compare -> patch failed dimensions -> revalidate
```

The goal is not open-ended creative improvement.

## REFERENCE_FINGERPRINT_REQUIRED

Before the loop starts, create or locate a reference fingerprint. It must name
the reference authority and record the intended sameness dimensions:

- `source_reference`: source URL, source file, or locked reference package
- `structure_order`: hook, setup, escalation, reversal, payoff
- `rhythm_map`: edit beats, caption timing, emphasis points
- `caption_roles`: top text, timed middle captions, TTS/narration text
- `visual_layout`: template, text roles, T1-T6 order, forbidden bottom layers
- `audio_policy`: source audio, TTS, BGM, mute, ducking, quote handling
- `tone_target`: Tikitaka pressure, emotional premise, humor, comment trigger
- `nonnegotiable_gates`: source, script, humanize, CapCut, and upload gates

If the reference is missing, vague, or not comparable, stop with:

```text
WAIT_REFERENCE
```

Do not guess a reference fingerprint from memory.

## DRAFT_FAST_SIMILARITY_LOOP

The loop may run in `DRAFT_FAST` after the required source and script authority
exist. A successful similarity loop still means working draft similarity, not
production approval.

Allowed candidate surfaces:

- Tikitaka script draft
- polished script from `00script-writer`
- SRT or timed subtitle JSON
- layout/render-plan JSON
- CapCut `draft_content.json` and metadata snapshots
- rendered preview screenshots or frame samples when available

Do not run this loop before `source.mp4` or equivalent source media exists for
source-derived production. Do not use Gemini text alone as source authority.

## Compare Dimensions

Every iteration must compare the candidate against the reference fingerprint in
these dimensions:

```text
structure_similarity
rhythm_similarity
caption_role_similarity
visual_layout_similarity
audio_policy_similarity
tone_similarity
gate_integrity
```

Each dimension must be reported as `PASS`, `PATCH`, or `WAIT`, with a short
reason. `gate_integrity` must be `PASS` before the loop can close.

Loop closure rule: the loop may close with SIMILARITY_LOOP_PASS only when
every dimension is PASS. If any dimension is PATCH, run another bounded
iteration. If any dimension is WAIT, stop with WAIT_REFERENCE or the
matching gate state.

gate_integrity is reflective only. It reports the current state of the
existing gate files (source, script, humanize, CapCut, upload). It does
not create, override, or substitute any gate result. A similarity loop
run never turns a missing or failing gate into PASS.

## SIMILARITY_LOOP_MAX_ITERATIONS

Bound the loop. Never run indefinitely.

```text
script_similarity_max_iterations=3
subtitle_layout_similarity_max_iterations=3
capcut_similarity_max_iterations=2
combined_similarity_max_iterations=3
```

capcut_similarity_max_iterations is lower because each CapCut rebuild is
expensive and risks regressing passing dimensions.

If any dimension is still PATCH after the iteration limit, stop with:

```text
FAIL_SIMILARITY_LOOP_EXHAUSTED
```

If the remaining mismatch depends on user taste, missing source ranges, missing
reference frames, or unavailable CapCut evidence, stop with `WAIT_REFERENCE` or
the more specific existing gate.

## Patch Rule

patch only the failed similarity dimensions. Preserve all passing dimensions.

Do not rewrite the whole script, regenerate the whole layout, or rebuild the
whole CapCut draft when a narrow patch can fix the mismatch. Each patch note
must name:

- failed dimension
- old value or behavior
- new value or behavior
- evidence used for the decision
- validator or reviewer used after the patch

## Ledger

Record loop evidence under the episode report folder:

```text
90_reports/similarity_loop_ledger.jsonl
```

For draft-only or isolated validation work, use the nearest report or scratch
report folder and state the path in the final report.

Each JSONL row should include:

```json
{
  "iteration": 1,
  "mode": "DRAFT_FAST",
  "candidate_path": "relative/path",
  "reference_path": "relative/path",
  "score": "dimension_vector_only",
  "dimensions": {
    "structure_similarity": "PASS",
    "rhythm_similarity": "PATCH",
    "caption_role_similarity": "PASS",
    "visual_layout_similarity": "PATCH",
    "audio_policy_similarity": "PASS",
    "tone_similarity": "PASS",
    "gate_integrity": "PASS"
  },
  "patches": ["patched timed middle caption beat 3"],
  "evidence": ["validator/report/path.json"],
  "next_status": "PATCH"
}
```

Do not write secrets, API keys, cookies, raw private logs, or personal session
data into the ledger.

## Stop Rules

Do not use similarity loops to bypass any hard gate, including:

- missing `source.mp4` or failed source provenance
- missing Tikitaka segment audio plan
- missing user-confirmed source timecodes when required
- missing humanize pass for final visible Korean text
- missing `SCRIPT_LOCK` for `FINAL_LOCK`
- failed production gate
- failed post-CapCut gate
- failed mandatory CapCut media settings harness
- missing upload package evidence

If a hard gate is missing, return the existing `WAIT_*`, `FAIL_*`, or
`FINAL: BLOCKED` state. The similarity loop may propose what to fix, but it
does not convert the state to `PASS`.

## Report Tokens

When this loop is used, include these report tokens:

```text
DRAFT_FAST_SIMILARITY_LOOP
REFERENCE_FINGERPRINT_REQUIRED
SIMILARITY_LOOP_MAX_ITERATIONS
similarity_loop_ledger.jsonl
```

Close only with one of:

```text
SIMILARITY_LOOP_PASS
WAIT_REFERENCE
FAIL_SIMILARITY_LOOP_EXHAUSTED
FINAL: BLOCKED
```

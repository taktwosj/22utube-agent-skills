# Politics ChatGPT Two-Pass Review Design

## Status

Approved by the user on 2026-07-18 for implementation and Git publication.

## Goal

Extend `111-politics-longform` so a master political-commentary draft is reviewed
in one continuous ChatGPT project conversation through:

1. independent diagnosis and revision proposals;
2. Codex decision and repair;
3. a second evidence and whole-flow audit;
4. Codex gate evaluation;
5. explicit user approval.

The ChatGPT project never owns `ADOPTED`, final approval, CapCut assembly, or
upload readiness.

## Authority and v3 Preflight

The production authority remains the current workspace `AGENTS.md` and
`docs/YOUTUBE_PRODUCTION_WORK_ORDER.md`.

The installed skill must expose all of these markers before politics-longform
work continues:

```text
target_profile: jungchilong_base_v3_intro15
canvas: 1920x1080
YP007: legacy visual reference only
```

The only default root package is:

```text
{WORKSPACE_ROOT}\22factory_20260628\00_asset_tools\templates\capcut\jungchilong\jungchilong_v3_intro15_CAPCUT_20260715.zip
```

The restored local root project is `jungchilong`. The archive and restored root
are immutable; episode work modifies only a full clone. Missing v3 markers stop
with `WAIT_POLITICS_SKILL_V3_SYNC_REQUIRED`.

## Review Boundary

Master-script review and lower two-line review are separate contracts.

```text
MASTER_COMMENTARY_REVIEW_GATE
  Whole master narration, fact map, argument, counterargument, and continuity.

EXTERNAL_LOWER_COMMENTARY_GATE
  Existing commentary_review_packet_* lower two-line review and pipeline gate.
```

The existing `commentary_review_packet_sent.md`,
`commentary_review_packet_returned.md`, and
`commentary_review_packet_manifest.json` names remain reserved for the lower
commentary pipeline. The master-script workflow must not reuse or overwrite
them.

## Canonical Master-Review Artifacts

Store the two-pass evidence under:

```text
20_script/master_commentary_review/
├─ round1_packet_sent.md
├─ round1_manifest.json
├─ round1_returned.md
├─ round1_receipt.json
├─ round1_codex_decisions.json
├─ round2_packet_sent.md
├─ round2_manifest.json
├─ round2_returned.md
├─ round2_receipt.json
└─ master_commentary_review_gate.json
```

The round-1 manifest pins the packet, original master script, fact map, timeline,
core question, and ordered segment IDs. The round-2 manifest pins:

```text
round1_return_sha256
round1_codex_decisions_sha256
revised_script_sha256
revised_fact_map_sha256
timeline_design_sha256
conversation_id
ordered_segment_ids
```

Receipts record the exact ChatGPT conversation URL and normalized conversation
ID. Round 2 must use the same conversation ID as round 1.

## Round 1

Round 1 performs:

```text
INDEPENDENT_REVIEW
REVISION_PROPOSAL
```

It does not run `EVIDENCE_AUDIT` against a hypothetical revision and does not
emit an approved script. Every suggestion has a stable `suggestion_id`,
`segment_id`, `claim_id`, `source_id`, `before`, `after`, `derived_from`,
evidence, counterargument, risk, and verification state.

Codex records exactly one decision for every suggestion:

```text
ADOPTED
PARTIALLY_ADOPTED
REJECTED
PENDING_EVIDENCE
```

Every decision includes a reason and the resulting segment or claim ID. Missing
or duplicate decisions block round 2.

## Round 2

Round 2 is sent in the same ChatGPT conversation. Its packet is self-contained
even though the conversation supplies continuity. It includes:

- the complete round-1 return;
- the complete Codex decision table;
- the full revised master script in chronological order;
- the revised fact map;
- the full chapter or timeline order;
- the unchanged core question and governing thesis;
- unresolved evidence items.

Round 2 performs `EVIDENCE_AUDIT` and a whole-flow audit. It verifies:

- every round-1 issue is resolved, rejected with evidence, or still blocked;
- facts, quotations, dates, roles, numbers, and interpretations remain grounded;
- the governing thesis advances consistently from start to finish;
- every block receives the previous block and prepares the next block;
- chronology and causal order remain intact;
- source speech, verified fact, interpretation, counterargument, and judgment
  remain audibly distinguishable;
- no surgical rewrite introduces repetition, a pronoun gap, an abrupt topic
  jump, or a conclusion that is not earned;
- `ordered_segment_ids` and timeline order are unchanged unless a reopening
  decision explicitly authorizes a new round-1 cycle.

Round 2 returns one recommendation:

```text
PASS_RECOMMENDED
REVISE_REQUIRED
EVIDENCE_REQUIRED
```

It also returns `flow_continuity_status`, `remaining_blockers`, and adjacency
findings using `previous_segment_id`, `segment_id`, and `next_segment_id`.
`external_review_status` remains `PENDING_CODEX_REVIEW`.

If round 2 returns a blocker, the gate remains `WAIT_CHATGPT_REVIEW_REPAIR`.
Additional repair audits may continue in the same conversation, but the system
must never reinterpret a failed second audit as approval.

## Deterministic Gate

Add a validator under the skill that fails closed when:

- either round is missing;
- packet or artifact hashes differ;
- round 2 uses a different conversation;
- round-1 suggestions and Codex decisions are not a one-to-one set;
- `PENDING_EVIDENCE` remains;
- ordered segment IDs or timeline digest drift without a reopening decision;
- round 2 does not return `PASS_RECOMMENDED`;
- flow continuity is not `PASS`;
- remaining blockers are nonempty;
- either external response claims `ADOPTED`, `FINAL`, or user approval.

On success, the gate may report `status=PASS` only for the external-review stage.
It never creates `commentary_master_script_approved.md`. Explicit user approval
remains a separate later gate.

## Workflow Order

```text
verified sources and transcript
→ master script draft + fact map + timeline
→ round 1 in ChatGPT project
→ Codex decisions
→ revised full script + fact map + timeline revalidation
→ round 2 in the same ChatGPT conversation
→ deterministic MASTER_COMMENTARY_REVIEW_GATE
→ Codex final assessment
→ explicit user approval
→ commentary_master_script_approved.md
→ lower commentary derivation and existing lower-review gate
→ Stage 2 assembly
```

## Test Requirements

Tests must first fail for the missing behavior and then cover:

- missing round 2;
- mismatched conversation ID;
- changed round-1 return hash;
- missing, duplicate, or unknown suggestion decisions;
- `PENDING_EVIDENCE`;
- revised script, fact map, or timeline hash drift;
- segment-order drift;
- `REVISE_REQUIRED` and `EVIDENCE_REQUIRED`;
- failed flow continuity or nonempty blockers;
- forbidden external final-approval claims;
- a complete same-conversation two-pass fixture.

The skill contract test must also require the v3 profile, 1920x1080 canvas, and
YP007 legacy-only markers.


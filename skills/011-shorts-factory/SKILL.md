---
name: 011-shorts-factory
description: Create or reset a clean Paperclip Shorts P0 company using 001short-production-agent. Use for a new Paperclip Shorts company, replacement of legacy Shorts agents, P0 agent deployment, or Paperclip Shorts skill attachment verification.
---

# 011 Shorts Factory

Use one clean P0 company when legacy agents, tasks, or rules must not affect new work. Keep legacy companies and their tasks unchanged.

## Preconditions

1. Confirm the exact 001 source package and SHA-256.
2. Require user approval before company creation, agent creation, skill import, agent enablement, or a real production task.
3. Do not treat a Paperclip card, draft skill, zero-agent version, or model configuration alone as deployment PASS.
4. Keep external creative review user-controlled. Never auto-approve a draft or advance to CapCut without user approval.

## Fixed P0 Layout

Create exactly three agents and attach the same verified 001 version to all three:

| Agent | Role | Boundary |
|---|---|---|
| P0 coordinator | Routes work, owns episode state and user-facing reports | No CapCut edit, upload, or self-promotion |
| P0 producer | Executes approved production work on one writer machine | No user-approval bypass |
| P0 verifier | Reproduces deterministic checks and package hashes | Read-only; no edits or enablement |

Read `references/paperclip-operating-direction.md` when configuring agents, assigning an episode, or handing this company to another AI. It is the detailed model matrix and Mac mini urakkai route.

## Mandatory Episode Entry And Fault Prevention

- `쇼츠팩토리 P0` is the only entry for every new `001short-production-agent` episode. `P0-총괄` creates one Paperclip issue before source analysis; no local standalone episode may bypass it.
- The coordinator writes `{episode_root}/90_workflow/paperclip_entry.json` with `episode_id`, Paperclip issue ID, `macmini` writer, all three P0 role names, and the attached 001 `SKILL.md` SHA-256. The producer must run the 001 entry validator before Stage 01; missing evidence is `WAIT_PAPERCLIP_ENTRY`.
- The producer applies approved settings. The read-only verifier owns the Stage 08 profile verdict and must check source-audio vocal-retain, narration mute, -14 LUFS, `W Flash` joins, AI HD/adjustment values, and dynamic text evidence. A producer result is never its own PASS.
- Treat a visible still/frozen clip, unmuted source under A9, voice removed instead of vocal-retain, a missing transition, or an outline-style situation caption as a `FAIL` routed back to `P0-제작`; do not advance the issue.

## Deployment Order

1. Create the empty company.
2. Import one verified 001 package and record its SHA-256.
3. Create the three fixed agents manually; do not spend model tokens on organisation generation.
4. Attach the verified version without enabling production.
5. Run the verifier on a read-only task.
6. Read back the SHA, passing checks, and each agent attachment.
7. Before assigning production, confirm an explicit model and thinking effort for every agent. Never leave a live P0 agent on adapter-default Spark or Auto.
8. Enable coordinator and producer only after the verifier passes.

## Stops

Report `WAIT` when the source SHA is missing, the verifier cannot reproduce validation, a live CapCut draft is open, the writer machine differs from the draft owner, or the user has not approved the next action.

Do not attach `top5isu-shorts` to this P0 company. It remains a separate Git skill and production lane.

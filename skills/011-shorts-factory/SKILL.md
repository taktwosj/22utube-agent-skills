---
name: 011-shorts-factory
description: Set up or reset a clean Paperclip company for a Korean Shorts production team. Use when the user says 011 쇼츠팩터리, asks to replace legacy Paperclip Shorts agents, create a clean Shorts P0 company, or deploy a verified Shorts skill to a fresh coordinator, producer, and read-only verifier layout.
---

# 011 Shorts Factory

Use a new company when legacy agents, tasks, or rules must not affect new work.
Keep the legacy company intact; do not migrate its agents or open tasks.

## Preconditions

1. Confirm the source skill package and SHA-256.
2. Require explicit approval before creating a company, assigning agents, importing a skill, or enabling an agent.
3. Do not treat a Paperclip card, draft skill, or zero-agent skill as production-ready.
4. Keep any external review stage user-controlled. Never add automatic review loops.

## Clean Company Layout

Create one company named by the user. Start with exactly these three agents:

| Agent | Role | Hard boundary |
|---|---|---|
| `P0-총괄` | Routes work, owns state and locks | No CapCut edits, upload, or promotion |
| `P0-제작` | Executes approved production work | One active writer machine; no state promotion |
| `P0-검증` | Repeats deterministic checks and SHA comparison | Read-only; no edits or enablement |

Attach the same verified production skill version to all three. Put role boundaries in each agent's instructions; do not fork the skill solely to express a role.

## Deployment Order

1. Create the empty company.
2. Import one exact verified skill package and record its SHA-256.
3. Create the three agents manually. Do not spend model tokens on auto-generated organization design unless the user asks.
4. Attach the verified skill version without enabling production work.
5. Run `P0-검증` on a read-only task.
6. Enable `P0-총괄` and `P0-제작` only after the verifier reports matching SHA and passing checks.

## Stops

Stop and report `WAIT` when the package SHA is missing, the verifier cannot reproduce validation, a live CapCut draft is open, the assigned writer machine differs from the draft owner, or the user has not approved agent enablement.

Never overwrite the legacy company, alter its agents, move its tasks, or claim promotion from a successful import alone.

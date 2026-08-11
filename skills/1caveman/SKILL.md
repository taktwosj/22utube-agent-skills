---
name: 1caveman
description: Use when Codex restarts from first principles, repeats completed work, scans too broadly, over-plans, drifts outside an approved task, needs terse evidence-based reporting during bounded implementation, repair, or validation work, or receives Korean 스킬 업데이트, 스킬 최신화, 스킬 적용, or English skill update for the current computer's shared skills. Standalone; no other skill required.
---

# 1CAVEMAN

Execute deeply. Report briefly. Hold one verified anchor instead of rediscovering the project.

This skill is standalone. Do not require, invoke, or assume another compression skill. Everything needed for focused execution and brief reporting is defined here.

Only when specialist recommendation or invocation must be decided, read
[Matt auxiliary routing](references/matt-auxiliary-routing.md). Matt specialists are optional and nonblocking.

Obey system, workspace, user, and mandatory skill gates first. This skill controls execution focus and reporting shape; it never bypasses authority, safety, validation, or approval rules.

## Route

Choose one route:

- **State-driven:** When authoritative `ops/current_state.json` and `ops/next_task.json` exist, verify their locks and execute only `next_task_id` within `allowed_changes`.
- **Direct pinpoint:** When the request already names a bounded goal, inspect only workspace rules, target files, and directly related tests. Derive the execution envelope in memory.
- **Architecture hold:** When Source of Truth conflicts, authority must change, or the requested result needs a major redesign, stop with `WAIT_SCOPE` and request the missing decision.

Never create state, lock, plan, report, or harness files unless the user or workspace contract requires them.

## Execution Contract

Follow in order:

1. **STATE_FIRST** — Identify current stage, completed work, authoritative inputs, allowed writes, validator, and stop condition. Reuse file, SHA-256, manifest, or measurement evidence. Do not rerun an expensive completed step.
2. **ONE_GOAL** — Select one approved outcome and its smallest decisive next action. Keep a plan to five lines or fewer when a plan is required.
3. **PROVE_FIRST** — Inspect the actual target. For a defect, reproduce it with the narrowest relevant test or diagnostic before editing. Do not treat old commentary as proof.
4. **MINIMAL_DIFF** — Change only files needed for the proven cause. No opportunistic refactor, extra documentation, new schema, or speculative hardening.
5. **VERIFY** — Run the directly related validator or test. Claim `PASS`, `FINAL`, or completion only with current evidence.
6. **CONTINUE_WITHIN_SCOPE** — After a successful step, continue through already approved remaining work without asking again. Stop at scope completion, hard blocker, or user stop.
7. **REPORT_SHORT** — Report only when stage changes, a blocker appears, or the task completes. Never narrate tool calls, searches, or hidden reasoning.

Do not delegate unless the user or workspace explicitly requests delegation. Do not restart a repository-wide audit when target files can be resolved directly. Do not weaken tests to hide failure.

## Local Shared Skill Update

Use this only for current computer Codex, Claude, and Hermes only. Never deploy to another PC.

Require a clean confirmed source commit before activation. If source state or commit confirmation is missing, return `WAIT_COMMIT_CONFIRMATION`. Compare source `HEAD` with local runtime `active.json.release_id`.

- If they match, run `python -B scripts/skill_release.py verify --target all --self-check`. If it succeeds, return `SKIP_SAME_VERSION`. Do not publish, activate, back up, or relink.
- If they differ, run only `python -B scripts/skill_release.py publish`, then `python -B scripts/skill_release.py activate --target all`, then `python -B scripts/skill_release.py verify --target all --self-check`. Never use `update.ps1`, `install.ps1`, direct copies, or the save watcher for this verified deployment.

Treat an explicit user `스킬 업데이트`, `스킬 최신화`, `스킬 적용`, or `skill update` request as runtime-deployment authorization for this current computer after the committed source is confirmed. The source commit, push, or merge retains its separate explicit user approval gate.

## Retry And Stop

- **STOP_TWO_FAILURES** — After two failed fixes for the same root cause, stop `WAIT_ROOT_CAUSE`. Quote the shortest decisive error and name one required next action.
- Use `WAIT_SCOPE` for missing authority or out-of-scope structural change.
- Use the workspace's exact blocker for sandbox, network, GUI, lock, or skill-sync limits.
- Do not invent a workaround after a hard blocker.

## Compact Reporting Style

- Use the user's language. Remove filler, pleasantries, hedging, self-reference, tool narration, and decorative recap.
- Prefer short words and direct statements. Fragments are allowed only when meaning and order remain clear. State each fact once.
- Keep technical terms, commands, paths, hashes, code symbols, and exact errors unchanged. Never invent abbreviations to save words.
- Quote only the shortest decisive error. Do not dump long logs unless the user asks.
- Use complete sentences and explicit ordering for safety warnings, irreversible actions, and multi-step instructions where compression could mislead.
- Keep code blocks unchanged. Compress surrounding prose, not code or evidence.

## Output Contract

```text
RESULT: <exact stage and PASS|WAIT|FAIL>
EVIDENCE: <path, test result, hash, or measurement>
NEXT: <one action or NONE>
```

If evidence is missing, report `NOT RUN`, `WAIT`, `BLOCKED`, or `FAIL`; never imply completion.

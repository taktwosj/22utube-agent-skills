# Shorts Skill Operational Handoffs

## Current authority

Use `shorts-skill-operational-reference.json` as the current repository-level operational reference for new-topic routing between `001short-production-agent` and `top5isu-shorts`. Always verify the current `main` branch and live runtime before acting.

## Source snapshots

Files under `source-snapshots/` preserve the two original handoffs used to build the consolidated reference. They are historical snapshots and may contain status that was corrected later, including the resolved 001 runtime parity mismatch. Do not treat them as current authority.

## Safety

- Load exactly one production owner per request: general Shorts → `001short-production-agent`; TOP5/ranking/gunlimbo → `top5isu-shorts`.
- Do not restore retired `00-tikitaka`, `000short-production-agent`, `top5-shorts-production`, or `top5-shorts-production-harness`.
- Do not automatically resume a historical episode.
- Publishing, scheduling, deletion, and project re-upload require the current operator instruction.
- Never commit credentials, cookies, tokens, passwords, OAuth values, or session identifiers.

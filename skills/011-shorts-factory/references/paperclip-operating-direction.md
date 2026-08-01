# 011 P0 Operating Direction

This is the handoff reference for another AI. It governs one clean Paperclip P0 company using `001short-production-agent` as its production skill.

## Fixed team and models

| Agent | Purpose | Model and reasoning | Boundary |
|---|---|---|---|
| P0 coordinator | Route work, preserve state, collect user direction, and report | `gpt-5.6-terra` / Low | No CapCut edit, upload, or self-promotion |
| P0 producer | Produce approved work on the Mac mini | `gpt-5.6-sol` / Medium | One writer machine; no approval bypass |
| P0 verifier | Reproduce checks and hashes | `gpt-5.6-sol` / Low | Read-only; no edits or enablement |

Set both primary and cheap profiles explicitly where Paperclip exposes them. Do not start a production task using adapter-default Spark or Auto.

## Urakkai route

1. The coordinator records the user's episode-specific direction in the current task: emotional emphasis, hook angle, tone, or requested revision.
2. The producer works on the Mac mini. At Stage 04, it calls Claude CLI with Claude Opus 5 / Low to review the urakkai draft.
3. If Claude CLI fails because of authentication, quota, availability, or a non-zero exit, the producer calls Codex CLI `gpt-5.6-sol` / Low using the same review packet.
4. The producer applies accepted review changes, writes review evidence, and reports the revised `URAKKAI_BLUEPRINT.md` to the user.
5. The user can request revisions repeatedly. Nothing moves to CapCut until explicit user approval.
6. The verifier checks technical contracts, not subjective creative preference.

## Authority

- 001 owns durable rules: source identity, structural reorder, audio/video mapping, situation-caption doctrine, reviewer fallback, and the approval gate.
- The user owns episode-specific creative direction and revisions.
- The coordinator transmits and tracks user direction; it does not invent creative preferences.
- `top5isu-shorts` remains separate and is never attached to this P0 company.

## Deployment evidence

For every 001 change: test the source package, record SHA-256, import one exact Paperclip version, attach it to all three agents, and read back attachment state. A company card or zero-agent version is not deployment PASS.

# Matt Auxiliary Routing

Use this only to decide whether to recommend or invoke a specialist. Matt specialists are optional
and nonblocking. The active owner skill, task scope, protocol, state, validators, and approval evidence
remain authoritative; specialist output is advisory unless that owner contract explicitly adopts it.

## User-invoked flows

`$grill-with-docs`, `$to-spec`, `$to-tickets`, `$implement`, and `$wayfinder` are user-invoked.
An agent may recommend the exact call but runs one only after the user explicitly invokes it.

- For clear large work, recommend `$to-spec` followed by `$to-tickets`.
- Reserve `$wayfinder` for foggy multi-session work.
- For a large contract change, recommend `$grill-with-docs` -> `$to-spec` -> `$to-tickets` -> `$implement` -> `$code-review`. Run each user-invoked step only after the user explicitly invokes it; `$implement` owns its TDD loop.

## Agent-selected support

- Concrete new behavior required after diagnosis uses `$tdd`, then a separate `$code-review`.
- Agent-facing document edits use `$writing-for-agents`; important or shared changes finish with a separate `$code-review`.
- `$codebase-design` is reference-only, then work returns to the owning implementation route.

## Limited utilities

- `$wizard`: repeatable setup that a human must perform.
- `$to-questionnaire`: unanswered questions owned by an external stakeholder, only when the user invokes it.
- `$wait-what`: restatement only when the user invokes it.

If Matt is unavailable or fails, continue through the owner workflow unless its own contract has a real blocker.

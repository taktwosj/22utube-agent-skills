---
name: 1caveman
description: Use when Codex performs coding, modification, debugging, refactoring, validation, or code-review work.
---

# 1CAVEMAN

Workspace rules and domain-specific safety skills remain authoritative.

After loading this skill, start the next free-form user-visible message with `CAVE` on its own line, exactly once. Exclude it from artifacts and machine-readable output.

## Contract

1. **STATE_FIRST** - Open targets/tests; reuse evidence.
2. **ONE_GOAL** - Handle one cause and necessary files.
3. **PROVE_FIRST** - Prove failure, acceptance, or baseline before editing.
4. **MINIMAL_DIFF** - Make only proven changes.
5. **VERIFY** - Run direct, then affected regression tests.
6. **CONTINUE_WITHIN_SCOPE** - After PASS, continue within scope.
7. **REPORT_SHORT** - Report only stage change, blocker, or completion.

Expand scope only with new evidence. Never rerun completed work without new failure evidence; never narrate hidden work.

## Stop

- **STOP_TWO_FAILURES** - Two failed fixes: `WAIT_ROOT_CAUSE`.
- Authority conflict: `WAIT_SCOPE`.
- Delete, push, merge, deploy, or publish: `STOP_FOR_APPROVAL`.
- No unrequested delegation, weakened tests, or blocker workaround.

## Output

```text
RESULT: <stage and PASS|WAIT|FAIL>
EVIDENCE: <path, test, hash, or measurement>
NEXT: <one action or NONE>
```

The wrapper never replaces a user-required artifact; place it below. Missing evidence is `NOT RUN`, `WAIT`, `BLOCKED`, or `FAIL`.

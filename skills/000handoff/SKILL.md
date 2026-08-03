---
name: 000handoff
description: Create one compact, copy-ready conversation handoff for a new chat. Use when the user says "핸드오프해", "핸드오프", "000핸드오프", or "새 채팅으로 넘겨". Use only information already confirmed in the current conversation; do not inspect files, run commands, or perform work while generating the handoff.
---

# 000handoff

Compress only the confirmed current-chat context so a new chat can verify it and execute exactly one next action.

## Absolute rules

During handoff generation, do not:

- run Shell or terminal commands;
- search for or read files;
- inspect Git, recompute SHA, or inspect processes;
- implement, modify, or complete work;
- ask the user a follow-up question.

Use only information already present in the current conversation. Set unknown values to `null` or `unresolved`; never infer them.

## Output

Return no explanation: output exactly one copy-ready fenced `text` code block.

Start the block with these six lines:

```text
HANDOFF_RESTART_V1
MODE=READ_ONLY_VERIFY_THEN_EXECUTE_ONE
VERIFY=SOT_EXISTS,SOT_HASH_OR_GIT_HEAD,GIT_STATUS_AND_CHANGED_FILES,CURRENT_STAGE_AND_ARTIFACTS,NEXT_ACTION_EXECUTABLE
PRIORITY=LATEST_USER>ACTUAL_FILES_GIT_RUNTIME>HANDOFF_JSON>INFERENCE
ON_CONFLICT=STOP_AND_REPORT_FIRST_CONFLICT
ON_PASS=NO_SCOPE_EXPANSION;EXECUTE_NEXT_ACTION_ONLY;REPORT_VALIDATION
```

Append one valid JSON object using this minimum structure:

```json
{
  "protocol": "CONTEXT_HANDOFF_V1",
  "created_at": "YYYY-MM-DDTHH:MM:SS+09:00",
  "latest_user_instruction": "",
  "task_goal": "",
  "current_stage": "",
  "current_status": "HANDOFF_READY|HANDOFF_LIMITED",
  "source_of_truth": [
    {
      "path": "",
      "role": "",
      "sha256": null,
      "verification_status": "SHA_VERIFIED|EXISTS_ONLY|UNRESOLVED"
    }
  ],
  "locked_decisions": [],
  "completed_work": [{"claim": "", "evidence": []}],
  "failed_attempts": [{"attempt": "", "cause": "", "do_not_repeat": ""}],
  "constraints": [],
  "unresolved_issues": [],
  "next_action": {
    "action": "",
    "execution_instruction": "",
    "expected_result": "",
    "stop_conditions": []
  },
  "validation_plan": [],
  "rollback_plan": [],
  "user_approval_required": false
}
```

## Content rules

- Preserve the latest confirmed user instruction, current goal/stage, actual SOT paths, already-confirmed SHA or Git facts, locks, completed evidence, failed-attempt boundaries, and validation/rollback conditions.
- Prefix evidence statements only with `[USER]`, `[MCP]`, or, only when unavoidable, `[EST]`.
- Record exactly one `next_action`, using `execution_instruction` rather than `command`; keep its scope bounded and include its expected result and stop conditions.
- Remove repeated discussion, superseded proposals, file bodies, long logs, long-term plans, self-evaluation, and unverified completion claims.
- Use `HANDOFF_READY` only when core file, stage, and next-action facts are sufficient; otherwise use `HANDOFF_LIMITED`.
- Keep the block at or below 6,000 characters; allow up to 10,000 only for complex code or CapCut work.

Before responding, internally check that there is one code block, all six header lines, parseable JSON, exactly one next action, and no invented values. Do not use tools for this check.

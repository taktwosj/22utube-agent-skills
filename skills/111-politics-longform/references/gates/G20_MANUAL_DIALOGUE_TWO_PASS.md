# G20 — Manual Dialogue and Two-Pass Review

Sequence: Stage 1 blueprint → user-returned narration/dialogue → Codex precheck
→ user-returned Round 1 → one Codex decision per suggestion → user-returned
Round 2 in the same conversation → Codex evidence/flow audit → editorial lock.

External transport is user-manual only. External output is recommendation
evidence, never `FINAL`, `PASS`, `SCRIPT_LOCK`, or `DESIGN_LOCK`. Pending
evidence blocks. Material scope changes require user editorial confirmation.
The existing `validate_chatgpt_two_pass_review.py` result is required evidence.


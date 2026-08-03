# Stage 04 — Urakkai Draft Review and User Approval

Run this stage only after the original blueprint and first recommendation are ready.

1. On the Mac mini creator machine, create or revise `20_script/URAKKAI_BLUEPRINT.md`.
2. Call Claude CLI with **Claude Opus 5 / low** to review the draft against `references/stage04-external-review-contract.md`.
3. If that CLI call fails because of authentication, quota, availability, or a non-zero exit, call Codex CLI with **gpt-5.6-sol / low** once using the same read-only review packet. Record the failure category, not credentials or command output containing secrets.
4. Apply the accepted review changes to the same draft. Keep segment IDs, approved ranges, source order evidence, and audio mapping under the 001 contract.
5. Write `20_script/external-review.md` and `.json`: input SHA-256, selected reviewer, fallback status, findings, applied changes, and output SHA-256.
6. Report the revised draft and concise review summary. In normal mode set `current_stage=04`, `status=WAIT_USER_URAKKAI_APPROVAL`, and `final_design_locked=false`. In exact Paperclip P0 automatic mode, after the same review evidence is written, set `status=HERMES_DELEGATED_ROUTINE_APPROVAL_AFTER_EVIDENCE` and continue to Stage 05.

In normal mode the user is the approval authority, and a correction repeats this same single-review stage on the draft; do not advance until explicit approval is recorded. Exact Paperclip P0 automatic mode uses Hermes delegated routine authority after evidence and must not create a user-wait gate. That delegated route never authorizes publication, credentials, payment, destructive actions, account changes, or final creative judgment.

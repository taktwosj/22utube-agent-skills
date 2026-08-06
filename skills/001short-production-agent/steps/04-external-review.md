# Stage 04 — Urakkai Draft Review and User Approval

Run this stage only after the original blueprint and first recommendation are ready.

1. On the Mac mini creator machine, create or revise `20_script/URAKKAI_BLUEPRINT.md`.
2. Call Claude CLI with **Claude Opus 5 / low** to review the draft against `references/stage04-external-review-contract.md` and `references/mara-urakkai-review-rubric.md`. Send the episode's `*_ORIGINAL_CAPCUT_GRID.md` and the Stage 03 urakkai design in the same read-only packet; the rubric compares them against each other.
3. If that CLI call fails because of authentication, quota, availability, or a non-zero exit, call Codex CLI with **gpt-5.6-sol / low** once using the same read-only review packet. Record the failure category, not credentials or command output containing secrets.
4. Apply the accepted review changes to the same draft. Keep segment IDs, approved ranges, source order evidence, and audio mapping under the 001 contract.
5. Write `20_script/external-review.md` and `.json`: input SHA-256, selected reviewer, fallback status, rubric `verdict`, the rubric item table, the P0–P4 must-fix list, the declared audio policy, findings, applied changes, and output SHA-256. A review without a verdict fails with `URAKKAI_REVIEW_RUBRIC_MISSING`; a draft with no declared audio policy fails with `URAKKAI_AUDIO_POLICY_UNDECLARED`.
6. Report the revised draft and concise review summary to the user. Set `current_stage=04`, `status=WAIT_USER_URAKKAI_APPROVAL`, and `final_design_locked=false`.

The user is the approval authority. `PASS_CANDIDATE` is a reviewer recommendation, not approval; every verdict still ends at `WAIT_USER_URAKKAI_APPROVAL`. A user correction repeats this stage on the same draft. Do not compile the final blueprint, open CapCut, or advance to Stage 05 until explicit approval is recorded.

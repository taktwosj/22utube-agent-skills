# Stage 04 — Urakkai Table Report and Approval

Run this stage after the original blueprint and first recommendation are ready.

1. Complete `20_script/original-capcut-grid.md` on the source time axis.
2. Complete `20_script/urakkai-capcut-grid.md` on the reordered target time axis.
3. Keep `20_script/URAKKAI_BLUEPRINT.md` consistent with both tables.
4. Show the original table first and the urakkai table second in the user message.
5. Do not call Claude, Codex, or another external AI reviewer.

In manual mode, stop at `WAIT_USER_URAKKAI_APPROVAL`. After explicit user
approval, record `USER_URAKKAI_APPROVED` and continue to Stage 05.

When the user requests automatic mode, do not ask for approval. Preserve the
same three report artifacts, record `URAKKAI_AUTO_APPROVED`, and continue to
Stage 05. Automatic mode skips the approval conversation, not the two tables or
their alignment with the final 15-track CapCut assembly.

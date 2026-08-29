# Agent Rules

Rules every agent follows in this repo — Codex, Claude, Hermes alike. Skill contracts live in
`skills/<skill>/SKILL.md`; this file governs how work reaches `main`.

## Branch lifecycle

브랜치는 PR 하나를 위한 일회용이다. 작업이 끝나면 남기지 않는다.

- One branch per PR. Push a branch only when a PR follows it — a branch with no PR is dirt.
- Delete the head branch as soon as its PR merges. `.github/workflows/branch-hygiene.yml`
  does it automatically; the repo setting **Settings → General → Automatically delete head
  branches** must stay on as the backstop.
- Close a PR you abandoned, and delete its branch in the same move.
- A branch that outlives its PR by more than 45 days is reported by the weekly hygiene job.
  Answer that issue by deleting or by reopening a PR — not by ignoring it.

Naming: `<kind>/<subject>` with `kind` in `feat`, `fix`, `docs`, `chore`, `refactor`.
Date suffixes are allowed but never carry meaning; `backup/` and `archive/` are the only
prefixes exempt from automatic deletion, and they are for snapshots kept on purpose.

## Never rewrite `main`

`main` was rebuilt on a fresh root on 2026-08-15. Every branch older than that lost its merge
base, so git and GitHub can no longer tell that even a merged branch was merged — 37 branches
went permanently un-deletable in one move. See `docs/branch-cleanup-20260829.md`.

- No force-push, rebase, amend, or orphan-root replacement on `main`. Ever.
- If a rewrite is genuinely unavoidable, delete every branch cut from the old root in the same
  operation, and record their SHAs first the way `docs/branch-cleanup-20260829.md` does.

## Merging

Squash merge is the default here, so a merged branch never becomes an ancestor of `main`.
`git branch --merged` therefore proves nothing about what landed — check the PR, not the graph.

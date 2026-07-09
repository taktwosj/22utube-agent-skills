#!/usr/bin/env bash
set -euo pipefail

HOOK_NAME="${1:-manual}"
REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
cd "$REPO_ROOT"

case "$HOOK_NAME" in
  post-commit)
    CHANGED="$(git diff-tree --no-commit-id --name-only -r HEAD 2>/dev/null || true)"
    ;;
  post-merge)
    if git rev-parse -q --verify ORIG_HEAD >/dev/null 2>&1; then
      CHANGED="$(git diff --name-only ORIG_HEAD HEAD 2>/dev/null || true)"
    else
      CHANGED="skills"
    fi
    ;;
  post-rewrite)
    CHANGED="skills manifests scripts .githooks"
    ;;
  *)
    CHANGED="skills manifests scripts .githooks"
    ;;
esac

if ! printf '%s\n' "$CHANGED" | grep -Eq '^(skills/|manifests/|scripts/(install|update|verify)\.(ps1|sh)|scripts/auto_sync_runtime_skills\.sh|\.githooks/)'; then
  echo "22utube skill auto-sync: skip ($HOOK_NAME, no managed skill changes)"
  exit 0
fi

if [ -n "$(git status --porcelain 2>/dev/null)" ]; then
  echo "22utube skill auto-sync: skip ($HOOK_NAME, dirty worktree; run install/update after committing or cleaning)" >&2
  exit 0
fi

LOCK_FILE="$REPO_ROOT/.git/22utube-skill-auto-sync.lock"
if [ -e "$LOCK_FILE" ]; then
  echo "22utube skill auto-sync: skip ($HOOK_NAME, lock exists)"
  exit 0
fi
trap 'rm -f "$LOCK_FILE"' EXIT
printf '%s\n' "$$" > "$LOCK_FILE"

echo "22utube skill auto-sync: install+verify all after $HOOK_NAME"

POWERSHELL_EXE=""
if command -v pwsh.exe >/dev/null 2>&1; then
  POWERSHELL_EXE="pwsh.exe"
elif command -v powershell.exe >/dev/null 2>&1; then
  POWERSHELL_EXE="powershell.exe"
fi

if [ -n "$POWERSHELL_EXE" ] && [ -f "$REPO_ROOT/scripts/install.ps1" ]; then
  "$POWERSHELL_EXE" -NoProfile -ExecutionPolicy Bypass -File "$REPO_ROOT/scripts/install.ps1" -Target all -Prune
  "$POWERSHELL_EXE" -NoProfile -ExecutionPolicy Bypass -File "$REPO_ROOT/scripts/verify.ps1" -Target all
else
  bash "$REPO_ROOT/scripts/install.sh" --target all --prune
  bash "$REPO_ROOT/scripts/verify.sh" --target all
fi

echo "22utube skill auto-sync: PASS"

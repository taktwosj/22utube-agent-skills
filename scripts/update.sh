#!/usr/bin/env bash
set -euo pipefail

TARGET="all"
PRUNE="0"
STRICT="0"
DRY_RUN="0"
ONLY=()

while [ "$#" -gt 0 ]; do
  case "$1" in
    --target)
      TARGET="$2"
      shift 2
      ;;
    --only)
      ONLY+=("$2")
      shift 2
      ;;
    --prune)
      PRUNE="1"
      shift
      ;;
    --strict)
      STRICT="1"
      shift
      ;;
    --dry-run)
      DRY_RUN="1"
      shift
      ;;
    *)
      echo "Unknown argument: $1" >&2
      exit 2
      ;;
  esac
done

if [ "$PRUNE" = "1" ] && [ "${#ONLY[@]}" -gt 0 ]; then
  echo "--only and --prune cannot be used together." >&2
  exit 2
fi
if [ "$STRICT" = "1" ] && [ "${#ONLY[@]}" -gt 0 ]; then
  echo "--only and --strict cannot be used together." >&2
  exit 2
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

if [ -n "$(git -C "$REPO_ROOT" status --porcelain)" ]; then
  echo "Dirty worktree. Commit or discard local changes before update." >&2
  exit 1
fi

if [ -n "$(git -C "$REPO_ROOT" remote)" ]; then
  if [ "$DRY_RUN" = "1" ]; then
    echo "DRYRUN git pull --ff-only"
  else
    git -C "$REPO_ROOT" pull --ff-only
  fi
else
  echo "NO_REMOTE skip git pull"
fi

INSTALL_ARGS=(--target "$TARGET")
if [ "${#ONLY[@]}" -gt 0 ]; then
  for skill in "${ONLY[@]}"; do
    INSTALL_ARGS+=(--only "$skill")
  done
fi
if [ "$PRUNE" = "1" ]; then
  INSTALL_ARGS+=(--prune)
fi
if [ "$STRICT" = "1" ]; then
  INSTALL_ARGS+=(--strict)
fi
if [ "$DRY_RUN" = "1" ]; then
  INSTALL_ARGS+=(--dry-run)
fi

bash "$SCRIPT_DIR/install.sh" "${INSTALL_ARGS[@]}"

if [ "$DRY_RUN" = "1" ]; then
  echo "DRYRUN skip target verify"
else
  bash "$SCRIPT_DIR/verify.sh" --target "$TARGET"
fi

echo "DONE update target=$TARGET dry_run=$DRY_RUN"

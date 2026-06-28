#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
COMMANDS_PATH="$REPO_ROOT/manifests/telegram-hermes.commands.json"
HERMES_HOME="${HERMES_HOME:-"$HOME/.hermes"}"
ENV_PATH="$HERMES_HOME/.env"

echo "telegram-hermes doctor"
echo "repo=$REPO_ROOT"
echo "commands_manifest=$COMMANDS_PATH"
echo "hermes_home=$HERMES_HOME"

if [ -f "$COMMANDS_PATH" ]; then
  echo "commands_manifest_exists=True"
else
  echo "commands_manifest_exists=False"
fi

if [ -d "$HERMES_HOME" ]; then
  echo "hermes_home_exists=True"
else
  echo "hermes_home_exists=False"
fi

if [ -f "$ENV_PATH" ]; then
  echo "env_file_exists=True"
else
  echo "env_file_exists=False"
fi

python3 - "$COMMANDS_PATH" "$ENV_PATH" <<'PY'
import json
import os
import re
import sys
from pathlib import Path

commands_path = Path(sys.argv[1])
env_path = Path(sys.argv[2])

if commands_path.exists():
    manifest = json.loads(commands_path.read_text(encoding="utf-8"))
    print(f"allowed_commands={len(manifest.get('allowed_commands', []))}")
    print(f"blocked_commands={len(manifest.get('blocked_commands', []))}")

env_text = env_path.read_text(encoding="utf-8") if env_path.exists() else ""

for key in ("TELEGRAM_BOT_TOKEN", "TELEGRAM_ALLOWED_CHAT_IDS", "HONCHO_API_KEY"):
    is_set = bool(re.search(rf"(?m)^\s*{re.escape(key)}\s*=", env_text)) or bool(os.environ.get(key))
    print(f"{key}={'set' if is_set else 'unset'}")
PY

echo "DONE telegram-hermes doctor"

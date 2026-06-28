#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
COMMANDS_PATH="$REPO_ROOT/manifests/telegram-hermes.commands.json"
HERMES_HOME="${HERMES_HOME:-"$HOME/.hermes"}"
ENV_PATH="$HERMES_HOME/.env"
CONFIG_PATH="$HERMES_HOME/config.yaml"
CHANNEL_DIRECTORY_PATH="$HERMES_HOME/channel_directory.json"
GATEWAY_STATE_PATH="$HERMES_HOME/gateway_state.json"

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

if [ -f "$CONFIG_PATH" ]; then
  echo "config_exists=True"
else
  echo "config_exists=False"
fi

if [ -f "$CHANNEL_DIRECTORY_PATH" ]; then
  echo "channel_directory_exists=True"
else
  echo "channel_directory_exists=False"
fi

if [ -f "$GATEWAY_STATE_PATH" ]; then
  echo "gateway_state_exists=True"
else
  echo "gateway_state_exists=False"
fi

python3 - "$COMMANDS_PATH" "$ENV_PATH" "$CONFIG_PATH" "$CHANNEL_DIRECTORY_PATH" "$GATEWAY_STATE_PATH" <<'PY'
import json
import os
import re
import sys
from pathlib import Path

commands_path = Path(sys.argv[1])
env_path = Path(sys.argv[2])
config_path = Path(sys.argv[3])
channel_directory_path = Path(sys.argv[4])
gateway_state_path = Path(sys.argv[5])

if commands_path.exists():
    manifest = json.loads(commands_path.read_text(encoding="utf-8"))
    print(f"allowed_commands={len(manifest.get('allowed_commands', []))}")
    print(f"blocked_commands={len(manifest.get('blocked_commands', []))}")

env_text = env_path.read_text(encoding="utf-8") if env_path.exists() else ""

for key in ("TELEGRAM_BOT_TOKEN", "HONCHO_API_KEY"):
    is_set = bool(re.search(rf"(?m)^\s*{re.escape(key)}\s*=", env_text)) or bool(os.environ.get(key))
    print(f"{key}={'set' if is_set else 'unset'}")

config_text = config_path.read_text(encoding="utf-8") if config_path.exists() else ""
match = re.search(r"(?m)^\s*allowed_chats:\s*(.*?)\s*$", config_text)
value = match.group(1).strip().strip("'\"") if match else ""
print(f"telegram_allowed_chats_config={'set' if value and value != '[]' else 'unset'}")

known_chats = 0
if channel_directory_path.exists():
    channel_directory = json.loads(channel_directory_path.read_text(encoding="utf-8"))
    known_chats = len(channel_directory.get("platforms", {}).get("telegram", []) or [])
print(f"telegram_known_chats_count={known_chats}")

gateway_state = "unknown"
if gateway_state_path.exists():
    state_doc = json.loads(gateway_state_path.read_text(encoding="utf-8"))
    gateway_state = state_doc.get("platforms", {}).get("telegram", {}).get("state") or "unknown"
print(f"telegram_gateway_state={gateway_state}")
PY

echo "DONE telegram-hermes doctor"

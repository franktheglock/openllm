#!/usr/bin/env bash
# Quick start script for macOS
# - Creates/activates venv
# - Installs dependencies if missing
# - Runs setup wizard if needed
# - Starts the bot in a new Terminal window and opens the dashboard in the default browser

set -e
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

echo "========================================"
echo "Discord LLM Bot - Quick Start (macOS)"
echo "========================================="

# Choose python executable
PY_CMD="python3"
if ! command -v "$PY_CMD" >/dev/null 2>&1; then
  PY_CMD="python"
fi

# Create venv if missing
if [ ! -d "venv" ]; then
  echo "Creating virtual environment..."
  "$PY_CMD" -m venv venv
fi

# Activate venv for this script
# shellcheck source=/dev/null
source venv/bin/activate

# Install dependencies if missing
if ! python -c "import discord" >/dev/null 2>&1; then
  echo "Installing dependencies..."
  pip install -r requirements.txt
fi

# Create .env from template if missing
if [ ! -f .env ]; then
  if [ -f .env.example ]; then
    echo "Creating .env from .env.example..."
    cp .env.example .env
    echo "Please edit .env and set your DISCORD_TOKEN and API keys. Opening .env now..."
    ${EDITOR:-open -a TextEdit} .env
    read -p "After editing .env press Enter to continue..."
  else
    echo ".env.example not found; make sure you create .env with required values." 
  fi
fi

# Run setup wizard if not configured
python - <<'PY'
from src.config.manager import ConfigManager
cm = ConfigManager()
import sys
if not cm.is_configured():
    print('Running setup wizard...')
    import subprocess
    subprocess.run(["python","main.py","--setup"]) 
else:
    print('Configuration present.')
PY

# Start the bot in a new Terminal window using AppleScript
echo "Starting Discord LLM Bot in a new Terminal window..."
ABS_ROOT="$ROOT_DIR"
CMD="cd '$ABS_ROOT' ; source venv/bin/activate ; python main.py"

osascript <<APPLESCRIPT
tell application "Terminal"
    activate
    do script "$CMD"
end tell
APPLESCRIPT

# Open dashboard in default browser
sleep 3
open "http://127.0.0.1:5000"

echo "Launched dashboard in your default browser. The bot is running in a new Terminal window."
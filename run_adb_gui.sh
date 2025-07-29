#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

VENV_PATH="$SCRIPT_DIR/.venv"

# Check for python3
if ! command -v python3 > /dev/null; then
  echo "Error: python3 is not installed."
  exit 1
fi

# Create venv if not exists
if [ ! -d "$VENV_PATH" ]; then
  echo "Creating virtual environment in .venv..."
  python3 -m venv .venv
fi

echo "Activating .venv..."
source "$VENV_PATH/bin/activate"

pip install --upgrade pip
pip install -r requirements.txt

python -m adb_gui.main

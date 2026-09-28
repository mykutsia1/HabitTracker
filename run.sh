#!/usr/bin/env bash
set -e

# Change directory to the script's folder
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Launch the Habit Tracker application using the virtual environment or system python
if [ -f "$SCRIPT_DIR/.venv/bin/python3" ]; then
    "$SCRIPT_DIR/.venv/bin/python3" "$SCRIPT_DIR/main.py" "$@"
else
    python3 "$SCRIPT_DIR/main.py" "$@"
fi

#!/bin/bash

# --- Configuration ---
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
VENV_DIR="$SCRIPT_DIR/.venv"
GUI_SCRIPT="$SCRIPT_DIR/gui_analyzer.py"
VENV_PYTHON_EXEC="$VENV_DIR/bin/python"

# --- Run the GUI ---
if [ ! -f "$VENV_PYTHON_EXEC" ]; then
    echo "ERROR: Python executable not found in virtual environment: \"$VENV_PYTHON_EXEC\""
    echo "Please run setup_env.sh first to create the environment."
    exit 1
fi

if [ ! -f "$GUI_SCRIPT" ]; then
    echo "ERROR: GUI script \"$GUI_SCRIPT\" not found."
    exit 1
fi

echo "Launching GUI application: $GUI_SCRIPT"
"$VENV_PYTHON_EXEC" "$GUI_SCRIPT"
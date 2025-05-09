#!/bin/bash

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
VENV_DIR="$SCRIPT_DIR/.venv"

PYTHON_CMD="python3"

if [ ! -f "$VENV_DIR/bin/activate" ]; then
    echo "Creating virtual environment at \"$VENV_DIR\"..."
    $PYTHON_CMD -m venv "$VENV_DIR"
    if [ $? -ne 0 ]; then
        echo "ERROR: Failed to create Python virtual environment."
        exit 1
    fi
else
    echo "Virtual environment already exists at \"$VENV_DIR\"."
fi

echo "Activating virtual environment..."
source "$VENV_DIR/bin/activate"

echo "Upgrading pip..."
pip install --upgrade pip

echo "Installing torch (CUDA 11.8, if available)..."
pip3 install torch --index-url https://download.pytorch.org/whl/cu118

echo "Installing other dependencies..."
pip install llama-cpp-python huggingface_hub openai
pip install tkinterdnd2

if [ $? -ne 0 ]; then
    echo "ERROR: Failed to install dependencies."
    exit 1
fi

echo "Python environment setup complete."
exit 0
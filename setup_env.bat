@echo off
SETLOCAL


REM --- Create Virtual Environment ---
echo Setting up Python virtual environment...
call .venv\Scripts\activate
IF ERRORLEVEL 1 (
    echo Creating virtual environment.
    virtualenv .venv --python=3.11
    IF ERRORLEVEL 1 (
        echo ERROR: Failed to create virtual environment.
        exit /b 1
    )
    call .venv\Scripts\activate
)

echo Virtual environment activated.

REM --- Install Dependencies ---
call pip install --upgrade pip
call pip3 install torch --index-url https://download.pytorch.org/whl/cu118
call pip install llama-cpp-python huggingface_hub openai
call pip install tkinterdnd2
IF ERRORLEVEL 1 (
    echo ERROR: Failed to install dependencies.
    exit /b 1
)

echo Python environment setup complete.
ENDLOCAL
exit /b 0
@echo off
SETLOCAL

REM --- Configuration ---
SET "SCRIPT_DIR=%~dp0"
SET "VENV_DIR=%SCRIPT_DIR%.venv"
SET "GUI_SCRIPT=%SCRIPT_DIR%gui_analyzer.py"
SET "VENV_PYTHON_EXEC=%VENV_DIR%\Scripts\python.exe"

REM --- Run the GUI ---
IF NOT EXIST "%VENV_PYTHON_EXEC%" (
    echo ERROR: Python executable not found in virtual environment: "%VENV_PYTHON_EXEC%"
    echo Please run setup_env.bat first to create the environment.
    goto EndScript
)

IF NOT EXIST "%GUI_SCRIPT%" (
    echo ERROR: GUI script "%GUI_SCRIPT%" not found.
    goto EndScript
)

echo Launching GUI application: %GUI_SCRIPT%
"%VENV_PYTHON_EXEC%" "%GUI_SCRIPT%"

:EndScript
ENDLOCAL
pause
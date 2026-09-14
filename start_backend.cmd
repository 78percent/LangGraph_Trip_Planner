@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
    echo Missing .venv. See README.md for setup instructions.
    pause
    exit /b 1
)
".venv\Scripts\python.exe" -u "run.py"
if errorlevel 1 (
    echo.
    echo Backend failed to start. Keep the error above for diagnosis.
    pause
)

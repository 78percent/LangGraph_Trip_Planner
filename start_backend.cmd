@echo off
setlocal
cd /d "%~dp0"
title Tujian Backend - 127.0.0.1:8000
set "PYTHONUTF8=1"
set "HOST=127.0.0.1"
set "PORT=8000"
if not exist ".venv\Scripts\python.exe" (
    echo Missing .venv. See README.md for setup instructions.
    pause
    exit /b 1
)
powershell.exe -NoProfile -Command "try { $r = Invoke-RestMethod -Uri 'http://127.0.0.1:8000/health' -TimeoutSec 2; if ($r.status -eq 'ready' -and $r.service) { exit 0 } } catch {}; exit 1" >nul 2>&1
if not errorlevel 1 (
    echo Backend is already running. No need to start it again.
    echo Open http://127.0.0.1:5173/ after starting start_frontend.cmd.
    exit /b 0
)
echo Demo URL: http://127.0.0.1:5173/
echo Keep this window open while presenting.
".venv\Scripts\python.exe" -u "run.py"
if errorlevel 1 (
    echo.
    echo Backend failed to start. Keep the error above for diagnosis.
    pause
    exit /b 1
)

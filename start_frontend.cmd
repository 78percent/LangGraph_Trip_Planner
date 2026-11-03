@echo off
setlocal
cd /d "%~dp0frontend"
title Tujian Frontend - 127.0.0.1:5173
echo Frontend: http://127.0.0.1:5173/
echo Also start start_backend.cmd for queries and trip planning.
powershell.exe -NoProfile -Command "try { $r = Invoke-WebRequest -UseBasicParsing -Uri 'http://127.0.0.1:5173/' -TimeoutSec 2; if ($r.StatusCode -eq 200 -and $r.Content.Contains('/src/main.ts')) { exit 0 } } catch {}; exit 1" >nul 2>&1
if not errorlevel 1 (
    echo Frontend is already running. Open http://127.0.0.1:5173/
    exit /b 0
)
where npm.cmd >nul 2>&1
if errorlevel 1 (
    echo Node.js / npm was not found. Install Node.js or check PATH.
    pause
    exit /b 1
)
if not exist "node_modules\vite\bin\vite.js" (
    echo Frontend dependencies are missing. Run npm ci in the frontend folder.
    pause
    exit /b 1
)
echo Keep this window open while presenting.
call npm.cmd run dev -- --host 127.0.0.1 --port 5173 --strictPort
if errorlevel 1 (
    echo Frontend failed to start. Keep the error above for diagnosis.
    pause
    exit /b 1
)

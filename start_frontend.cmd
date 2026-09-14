@echo off
setlocal
cd /d "%~dp0frontend"
echo Frontend: http://127.0.0.1:5173/
echo Also start start_backend.cmd for queries and trip planning.
call npm.cmd run dev
if errorlevel 1 pause

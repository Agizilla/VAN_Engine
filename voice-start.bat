@echo off
REM Start the PAI voice pipeline (voice-server + SAAS transposer)
title VAN_Engine Voice Pipeline
echo.
echo [VAN] Starting Voice Server on :8888 ...
start /min "VS-8888" node "%~dp0voice-server.mjs"
echo [VAN] Starting SAAS Transposer on :9999 ...
start /min "SAAS-9999" py -3.10 "%~dp0Services\ClawdiaBridge\transposer.py" --serve
echo.
echo [OK] Voice Server  -> http://localhost:8888
echo [OK] SAAS Transposer -> http://localhost:9999
echo.
echo Close this window to keep servers running in background.
echo To stop them, use Task Manager (VS-8888, SAAS-9999).
pause

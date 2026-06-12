@echo off
echo ========================================
echo HOUSE CODEX - Lyrical Engine
echo ========================================
echo.

echo [*] Port cleanup (7860-7870)...
for /L %%p in (7860,1,7870) do (
    for /F "tokens=5" %%a in ('netstat -ano ^| findstr ":%%p" ^| findstr "LISTENING"') do (
        echo [*] Killing %%a on port %%p
        taskkill /f /pid %%a 2>nul
    )
)

echo [*] Repairing Dependencies...
call npm install @vitejs/plugin-react@^5.1.0 --save-dev 2>nul
call npm install 2>nul

echo.
echo [*] Starting API server (Python)...
start "House Codex API" python backend_api.py

echo [*] Waiting for API...
timeout /t 3 /nobreak >nul

echo.
echo [*] Starting Vite dev server...
start "Vite Dev" npm run dev

echo.
echo [*] Starting Electron...
npm start
pause
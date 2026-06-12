@echo off
echo ========================================
echo HOUSE CODEX - Lyrical Engine (V2.1)
echo ========================================
echo.

echo [*] Enforcing ESM config...
if exist "vite.config.js" (
    echo [*] Renaming vite.config.js to vite.config.mjs...
    move /y vite.config.js vite.config.mjs
)

echo [*] Port cleanup (7860-7870)...
for /L %%p in (7860,1,7870) do (
    for /F "tokens=5" %%a in ('netstat -ano ^| findstr ":%%p" ^| findstr "LISTENING"') do (
        echo [*] Killing process %%a on port %%p
        taskkill /f /pid %%a 2>nul
    )
)

echo [*] Clearing Vite cache...
if exist "node_modules\.vite" (
    rd /s /q "node_modules\.vite"
)

echo [*] Verifying dependencies...
call npm install @vitejs/plugin-react@^5.1.0 --save-dev 2>nul

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

echo.
echo ========================================
echo READY: http://localhost:5173 or Electron
echo ========================================
pause
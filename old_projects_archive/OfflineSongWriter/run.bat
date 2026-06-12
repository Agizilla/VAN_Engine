@echo off
:: Kill any Python processes on port 7860-7870
for /L %%p in (7860,1,7870) do (
    for /F "tokens=5" %%a in ('netstat -ano ^| findstr "%%p" ^| findstr "LISTENING"') do (
        echo Killing process %%a on port %%p
        taskkill /F /PID %%a 2>nul
    )
)

echo Starting Gradio UI...
python app_gradio.py
pause
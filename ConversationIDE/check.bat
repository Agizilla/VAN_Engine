@echo off
echo Checking LLMGateway...
curl -s http://127.0.0.1:44444/health
echo.
if %errorlevel% neq 0 (
  echo [ERROR] LLMGateway not running!
  echo Start it with: cd src\VanEngine.LLMGateway && dotnet run
) else (
  echo [OK] LLMGateway is running
)
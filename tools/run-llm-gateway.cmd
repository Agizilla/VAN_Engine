@echo off
setlocal

set "SCRIPT_DIR=%~dp0"
pushd "%SCRIPT_DIR%"

if "%VAN_LLMGATEWAY_PORT%"=="" set "VAN_LLMGATEWAY_PORT=11434"
if "%VAN_LLMGATEWAY_MODELS%"=="" set "VAN_LLMGATEWAY_MODELS=van_engine-brain,van_engine-brain-quantized"

dotnet run --project "src\VanEngine.LLMGateway\VanEngine.LLMGateway.csproj" -- %*
set "EXIT_CODE=%ERRORLEVEL%"

popd
endlocal & exit /b %EXIT_CODE%

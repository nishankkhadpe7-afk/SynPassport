@echo off
REM Starts the SynPassport API (port 8765) and the web dashboard (port 3005).
REM Port 3005 is used so the dashboard never clashes with other tools on port 3000.
cd /d "%~dp0"

set "PYTHONPATH=%~dp0src"

REM Start the API only if it is not already running
curl -s -o nul http://127.0.0.1:8765/health
if errorlevel 1 (
  start "SynPassport API (8765)" cmd /k ""%~dp0.venv\Scripts\python.exe" -m uvicorn synpassport.api.main:app --host 127.0.0.1 --port 8765"
) else (
  echo API already running on http://127.0.0.1:8765
)

REM Build the dashboard once, then serve the production build (faster and more stable than dev mode)
start "SynPassport Web (3005)" cmd /k "cd /d "%~dp0web" && npm run build && npm run start -- -p 3005"

echo.
echo SynPassport is starting.
echo   Dashboard: http://localhost:3005   (the first build takes about a minute)
echo   API:       http://127.0.0.1:8765/health
echo.
echo Opening the dashboard in your browser in 60 seconds...
timeout /t 60
start "" http://localhost:3005

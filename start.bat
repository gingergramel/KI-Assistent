@echo off
cd /d "%~dp0"

echo Alte Server auf Port 8000 und 5500 beenden...
for %%P in (8000 5500) do (
  for /f "tokens=5" %%A in ('netstat -ano ^| findstr ":%%P " ^| findstr LISTENING') do (
    taskkill /PID %%A /F >nul 2>&1
  )
)

echo Backend starten...
start "Backend (Port 8000)" /D "%~dp0backend" cmd /k python -m uvicorn main:app --host 127.0.0.1 --port 8000

echo Frontend starten...
start "Frontend (Port 5500)" /D "%~dp0frontend" cmd /k python -m http.server 5500

timeout /t 3 /nobreak >nul
start http://localhost:5500
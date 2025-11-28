@echo off
setlocal

set "ROOT=%~dp0"
set "FRONTEND_DIR=Peroperochat\frontend"
set "BACKEND_DIR=Peroperochat\backend"

set "BACKEND_PY=%ROOT%%BACKEND_DIR%\.venv\Scripts\python.exe"
if exist "%BACKEND_PY%" (
  set "PY_CMD=%BACKEND_PY%"
) else (
  set "PY_CMD=py"
)

start "Backend API" cmd /k "cd /d %ROOT%%BACKEND_DIR% && %PY_CMD% -m pip install -r requirements.txt && %PY_CMD% -m uvicorn app.main:app --host 0.0.0.0 --port 8000"
start "Frontend Dev" cmd /k "cd /d %ROOT%%FRONTEND_DIR% && npm install && set VITE_API_BASE=http://localhost:8000 && npm run dev"

exit /b 0

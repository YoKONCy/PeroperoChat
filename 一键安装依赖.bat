@echo off
setlocal
set "ROOT=%~dp0"
cd /d "%ROOT%"

echo Installing backend Python dependencies...
pushd "Peroperochat\backend"
if not exist ".venv\Scripts\python.exe" (
  python -m venv .venv
)
".venv\Scripts\python.exe" -m pip install --upgrade pip
".venv\Scripts\python.exe" -m pip install -r requirements.txt
popd

echo Installing frontend npm dependencies...
pushd "Peroperochat\frontend"
npm install
popd

echo Done.
endlocal

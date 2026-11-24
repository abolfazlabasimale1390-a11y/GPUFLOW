@echo off
setlocal
cd /d "%~dp0"
echo.
echo  GPUFlow Local Lab - Windows launcher
echo  -----------------------------------
if not exist "gpuflow.runtime" (
  echo ERROR: gpuflow.runtime is missing.
  echo Copy the companion file from the Execution Build into this folder.
  pause
  exit /b 1
)
where python >nul 2>nul
if errorlevel 1 (
  echo ERROR: Python 3.10 or newer was not found.
  echo Install Python from https://www.python.org/downloads/ and enable Add Python to PATH.
  pause
  exit /b 1
)
python -c "import sys; raise SystemExit(0 if sys.version_info >= (3,10) else 1)"
if errorlevel 1 (
  echo ERROR: Python 3.10 or newer is required.
  pause
  exit /b 1
)
echo Installing or checking Python dependencies...
python -m pip install -r requirements.txt
if errorlevel 1 (
  echo ERROR: Dependency installation failed. Check your internet connection and try again.
  pause
  exit /b 1
)
echo.
python run_server.py
pause

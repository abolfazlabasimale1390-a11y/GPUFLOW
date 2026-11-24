@echo off
setlocal
cd /d "%~dp0"
echo Building GPUFlow Windows application folder...
if not exist "gpuflow.runtime" (
  echo ERROR: gpuflow.runtime is required. Run this script from the Execution Build folder.
  pause
  exit /b 1
)
where python >nul 2>nul
if errorlevel 1 (
  echo ERROR: Python was not found.
  pause
  exit /b 1
)
python -m pip install -r requirements.txt pyinstaller
if errorlevel 1 (
  echo ERROR: Could not install build dependencies.
  pause
  exit /b 1
)
pyinstaller --noconfirm --clean --onedir --name GPUFlow --add-data "app\static;app\static" --hidden-import app.main --hidden-import app.security --collect-all fastapi --collect-all uvicorn run_server.py
if errorlevel 1 (
  echo ERROR: PyInstaller build failed.
  pause
  exit /b 1
)
copy /Y "gpuflow.runtime" "dist\GPUFlow\gpuflow.runtime" >nul
if errorlevel 1 (
  echo ERROR: Could not copy the required companion file.
  pause
  exit /b 1
)
echo.
echo BUILD COMPLETE: dist\GPUFlow\GPUFlow.exe
echo Keep gpuflow.runtime next to GPUFlow.exe. The app will not start without it.
pause

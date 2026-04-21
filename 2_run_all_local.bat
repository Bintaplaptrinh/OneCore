@echo off
setlocal EnableExtensions
cd /d "%~dp0"

echo ================================================
echo LeadsMap local run
echo ================================================
echo.

call "%~dp01_check_machine.bat"
if errorlevel 1 exit /b 1

echo.
echo [STEP] Preparing backend virtual environment
if not exist "app\backend\.venv\Scripts\python.exe" (
  py -3.13 -m venv "app\backend\.venv"
  if errorlevel 1 (
    echo [FAIL] Cannot create Python virtual environment
    exit /b 1
  )
)

call "app\backend\.venv\Scripts\activate.bat"
python -m pip install --upgrade pip
pip install -r "app\backend\requirements.txt"
if errorlevel 1 (
  echo [FAIL] Backend dependency install failed
  exit /b 1
)

echo.
echo [STEP] Preparing frontend dependencies
if not exist "app\frontend\node_modules" (
  call npm --prefix "app\frontend" install
  if errorlevel 1 (
    echo [FAIL] Frontend dependency install failed
    exit /b 1
  )
)

echo.
echo [STEP] Starting backend and frontend in separate windows
start "LeadsMap Backend" cmd /k "cd /d ""%~dp0app\backend"" && call ".venv\Scripts\activate.bat" && uvicorn main:app --host 0.0.0.0 --port 8000 --reload"
start "LeadsMap Frontend" cmd /k "cd /d ""%~dp0app\frontend"" && npm run dev"

echo.
echo [RUNNING] Frontend http://localhost:3000
echo [RUNNING] Backend  http://localhost:8000
echo [TIP] Close both spawned windows to stop services.
exit /b 0

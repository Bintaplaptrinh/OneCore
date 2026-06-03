@echo off
setlocal EnableExtensions
cd /d "%~dp0"

set "HAS_ERROR=0"

echo ================================================
echo CoreOne machine check
echo ================================================
echo.

call :check_cmd git "Git"
call :check_cmd python "Python"
call :check_cmd node "Node.js"
call :check_cmd npm "npm"
call :check_cmd powershell "PowerShell"

echo.
if %HAS_ERROR%==1 (
  echo [FAIL] Missing required tools. Install them and run this file again.
  exit /b 1
)

for /f "delims=" %%V in ('python --version 2^>^&1') do set "PY_VER=%%V"
for /f "delims=" %%V in ('node --version 2^>^&1') do set "NODE_VER=%%V"
for /f "delims=" %%V in ('npm --version 2^>^&1') do set "NPM_VER=%%V"

echo [OK] %PY_VER%
echo [OK] %NODE_VER%
echo [OK] npm %NPM_VER%

if not exist "app\backend\.env" (
  if exist "app\backend\.env.example" (
    copy /y "app\backend\.env.example" "app\backend\.env" >nul
    echo [INFO] Created app\backend\.env from .env.example
    echo [INFO] Fill API keys in app\backend\.env before production usage.
  ) else (
    echo [WARN] app\backend\.env not found and no .env.example found.
  )
) else (
  echo [OK] app\backend\.env exists
)

if not exist "app\frontend\.env.local" (
  > "app\frontend\.env.local" echo NEXT_PUBLIC_API_URL=http://127.0.0.1:8000
  echo [INFO] Created app\frontend\.env.local with local backend URL
) else (
  echo [OK] app\frontend\.env.local exists
)

echo.
echo [DONE] Machine check passed.
exit /b 0

:check_cmd
where %~1 >nul 2>nul
if errorlevel 1 (
  echo [MISSING] %~2
  set "HAS_ERROR=1"
) else (
  echo [OK] %~2
)
exit /b 0

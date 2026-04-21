@echo off
setlocal EnableExtensions
cd /d "%~dp0"

echo ================================================
echo LeadsMap run with public tunnel
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
echo [STEP] Starting backend window
start "LeadsMap Backend" cmd /k "cd /d ""%~dp0app\backend"" && call ".venv\Scripts\activate.bat" && uvicorn main:app --host 0.0.0.0 --port 8000 --reload"

echo [STEP] Creating tunnel URL for frontend port 3000
set "TUNNEL_URL="
for /f "usebackq delims=" %%U in (`powershell -NoProfile -ExecutionPolicy Bypass -Command "$ErrorActionPreference='Stop'; $log=Join-Path $env:TEMP 'leadsmap_tunnel.log'; if(Test-Path $log){Remove-Item $log -Force}; $pidFile=Join-Path $env:TEMP 'leadsmap_tunnel.pid'; if(Test-Path $pidFile){Remove-Item $pidFile -Force}; if(Get-Command cloudflared -ErrorAction SilentlyContinue){$exe='cloudflared'; $args=@('tunnel','--url','http://localhost:3000','--no-autoupdate'); $pattern='https://[-a-z0-9]+\.trycloudflare\.com'} else {$exe='npx.cmd'; $args=@('--yes','localtunnel','--port','3000'); $pattern='https://[a-z0-9-]+\.loca\.lt'}; $p=Start-Process -FilePath $exe -ArgumentList $args -PassThru -RedirectStandardOutput $log -RedirectStandardError $log -WindowStyle Hidden; $deadline=(Get-Date).AddSeconds(60); $url=''; while((Get-Date) -lt $deadline){ Start-Sleep -Milliseconds 500; if(Test-Path $log){ $txt=Get-Content $log -Raw; if($txt -match $pattern){ $url=$matches[0]; break } } }; if(-not $url){ try{Stop-Process -Id $p.Id -Force}catch{}; throw 'Tunnel URL not detected. Install cloudflared or verify npm can run localtunnel.' }; Set-Content -Path $pidFile -Value $p.Id -Encoding ascii; Write-Output $url"`) do set "TUNNEL_URL=%%U"

if not defined TUNNEL_URL (
  echo [FAIL] Could not create tunnel URL
  echo [HINT] Install cloudflared or ensure npm can run localtunnel
  exit /b 1
)

echo [OK] Public URL: %TUNNEL_URL%
echo.
echo [STEP] Starting frontend with NEXT_PUBLIC_API_URL set to tunnel URL
start "LeadsMap Frontend" cmd /k "cd /d ""%~dp0app\frontend"" && set NEXT_PUBLIC_API_URL=%TUNNEL_URL% && npm run dev"

echo.
echo [RUNNING] Local frontend  http://localhost:3000
echo [RUNNING] Local backend   http://localhost:8000
echo [RUNNING] Public demo URL %TUNNEL_URL%
echo [TIP] Share the public URL with client after frontend is fully started.
echo [TIP] To stop tunnel, run: taskkill /PID ^<pid in %%TEMP%%\leadsmap_tunnel.pid^> /F

start "" "%TUNNEL_URL%"
exit /b 0

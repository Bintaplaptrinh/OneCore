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
set "TUNNEL_URL_FILE=%TEMP%\leadsmap_tunnel.url"
if exist "%TUNNEL_URL_FILE%" del /f /q "%TUNNEL_URL_FILE%" >nul 2>&1

powershell -NoProfile -ExecutionPolicy Bypass -Command "$ErrorActionPreference='Stop'; $runId=[guid]::NewGuid().ToString('N'); $logOut=Join-Path $env:TEMP ('leadsmap_tunnel.' + $runId + '.out.log'); $logErr=Join-Path $env:TEMP ('leadsmap_tunnel.' + $runId + '.err.log'); $pidFile=Join-Path $env:TEMP 'leadsmap_tunnel.pid'; if(Test-Path $pidFile){Remove-Item $pidFile -Force -ErrorAction SilentlyContinue}; $urlFile=Join-Path $env:TEMP 'leadsmap_tunnel.url'; if(Test-Path $urlFile){Remove-Item $urlFile -Force -ErrorAction SilentlyContinue}; if(Get-Command cloudflared -ErrorAction SilentlyContinue){$exe='cloudflared'; $args=@('tunnel','--url','http://localhost:3000','--no-autoupdate'); $pattern='https://[-a-z0-9]+\.trycloudflare\.com'} else {$exe='npx.cmd'; $args=@('--yes','localtunnel','--port','3000'); $pattern='https://[a-z0-9-]+\.loca\.lt'}; $p=Start-Process -FilePath $exe -ArgumentList $args -PassThru -RedirectStandardOutput $logOut -RedirectStandardError $logErr -WindowStyle Hidden; $deadline=(Get-Date).AddSeconds(60); $url=''; while((Get-Date) -lt $deadline){ Start-Sleep -Milliseconds 500; $txt=''; if(Test-Path $logOut){ $txt += (Get-Content $logOut -Raw) }; if(Test-Path $logErr){ $txt += [Environment]::NewLine + (Get-Content $logErr -Raw) }; if($txt -match $pattern){ $url=$matches[0].Trim(); break } }; if(-not $url){ try{Stop-Process -Id $p.Id -Force}catch{}; throw ('Tunnel URL not detected. Logs: ' + $logOut + ' ; ' + $logErr) }; Set-Content -Path $pidFile -Value $p.Id -Encoding ascii; Set-Content -Path $urlFile -Value $url -Encoding ascii"
if errorlevel 1 (
  echo [FAIL] Could not create tunnel URL
  echo [HINT] Install cloudflared or ensure npm can run localtunnel
  echo [HINT] Check logs matching: %TEMP%\leadsmap_tunnel.*.out.log and %TEMP%\leadsmap_tunnel.*.err.log
  exit /b 1
)

for /f "usebackq tokens=* delims=" %%U in ("%TUNNEL_URL_FILE%") do if not defined TUNNEL_URL set "TUNNEL_URL=%%~U"
if exist "%TUNNEL_URL_FILE%" del /f /q "%TUNNEL_URL_FILE%" >nul 2>&1

if not defined TUNNEL_URL (
  echo [FAIL] Could not create tunnel URL
  echo [HINT] Install cloudflared or ensure npm can run localtunnel
  echo [HINT] Check logs matching: %TEMP%\leadsmap_tunnel.*.out.log and %TEMP%\leadsmap_tunnel.*.err.log
  exit /b 1
)

echo %TUNNEL_URL% | findstr /R /C:"^https://" >nul
if errorlevel 1 (
  echo [FAIL] Tunnel URL format is invalid
  echo [HINT] Check logs matching: %TEMP%\leadsmap_tunnel.*.out.log and %TEMP%\leadsmap_tunnel.*.err.log
  exit /b 1
)

echo [OK] Public URL: %TUNNEL_URL%
echo.
echo [STEP] Starting frontend (API proxied via Next.js rewrites to localhost:8000)
start "LeadsMap Frontend" cmd /k "cd /d ""%~dp0app\frontend"" && npm run dev"

echo.
echo [RUNNING] Local frontend  http://localhost:3000
echo [RUNNING] Local backend   http://localhost:8000
echo [RUNNING] Public demo URL %TUNNEL_URL%
echo [TIP] Share the public URL with client after frontend is fully started.
echo [TIP] To stop tunnel, run: taskkill /PID ^<pid in %%TEMP%%\leadsmap_tunnel.pid^> /F

start "" "%TUNNEL_URL%"
exit /b 0

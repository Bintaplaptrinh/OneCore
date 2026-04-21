# HaiVo LeadsMap - Windows Quick Start

This repository includes one-click batch scripts for clone-and-run on a new Windows machine.

## Script List

1. `1_check_machine.bat`
- Checks required tools: Git, Python, Node.js, npm, PowerShell.
- Auto-creates `app/backend/.env` from `app/backend/.env.example` if missing.
- Auto-creates `app/frontend/.env.local` if missing.

2. `2_run_all_local.bat`
- Runs machine check.
- Creates Python virtual environment in `app/backend/.venv` if missing.
- Installs backend dependencies from `app/backend/requirements.txt`.
- Installs frontend dependencies if `app/frontend/node_modules` is missing.
- Starts backend and frontend in separate terminal windows.

3. `3_run_all_with_tunnel.bat`
- Same setup as local run.
- Starts backend.
- Creates a public tunnel URL for frontend port `3000`.
	- Uses `cloudflared` if installed.
	- Falls back to `npx localtunnel`.
- Starts frontend with `NEXT_PUBLIC_API_URL` mapped to tunnel URL.
- Opens the public URL in browser so you can share it with clients.

## How to Use on a New Machine

1. Clone repository.
2. Double click `1_check_machine.bat`.
3. If all checks pass, run either:
- `2_run_all_local.bat` for local usage.
- `3_run_all_with_tunnel.bat` for sharing demo via internet.

## Notes

- Stop backend/frontend by closing their spawned terminal windows.
- Tunnel process runs in background. If needed, stop it by PID from `%TEMP%\\leadsmap_tunnel.pid`.
- For production usage, update secrets in `app/backend/.env`.
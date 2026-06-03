# Bintaplaptrinh CoreOne

Bintaplaptrinh CoreOne is a supporter management app for project/contact intelligence, data management, graph exploration, AI chat, and professional Vietnamese Report & Analyst exports.

## Features

- Data Manager for uploads, table building, and structured supporter data.
- Chat AI for assistant workflows, analysis, and data-aware actions.
- Reports with AI-written HTML, visual charts, and PDF export.
- Graph and contact views for relationship exploration.
- Light-first dashboard UI with the Bintaplaptrinh brand.

## Project Structure

- `app/frontend` - Next.js web app.
- `app/backend` - FastAPI API, data layer, report generation, and AI routes.
- `awesome_agent_skills` - local skill references used to guide agent/report behavior.
- `1_check_machine.bat` - validates local Windows dependencies and creates env files.
- `2_run_all_local.bat` - starts backend and frontend locally.

## Local Setup

1. Install Git, Python, Node.js, npm, and MongoDB.
2. Copy environment examples if the scripts have not created them yet:
   - `app/backend/.env.example` to `app/backend/.env`
   - `app/frontend/.env.example` to `app/frontend/.env.local`
3. Run `1_check_machine.bat`.
4. Run `2_run_all_local.bat`.

## Manual Run

Backend:

```powershell
cd app/backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

Frontend:

```powershell
cd app/frontend
npm install
npm run dev
```

Open the app at `http://localhost:3000`. The backend runs at `http://localhost:8000`.

## Repository Notes

- Runtime report exports are generated under `app/backend/reports` and ignored by git.
- Local secrets and environment files are ignored. Keep production keys out of the repository.
- Legacy vault/data folders are intentionally excluded from this code repo.

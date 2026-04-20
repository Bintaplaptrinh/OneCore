"""HaiVo LeadsMap — FastAPI Backend."""
from contextlib import asynccontextmanager

from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Load .env from the backend directory regardless of where uvicorn is launched
_env_path = Path(__file__).resolve().parent / ".env"
load_dotenv(dotenv_path=_env_path, override=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle manager."""
    from core.database import init_db

    await init_db()
    print("[startup] MongoDB connected and indexes created")
    yield
    print("[shutdown] LeadsMap backend stopped")


app = FastAPI(
    title="HaiVo LeadsMap API",
    version="2.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from routers.chat import router as chat_router
from routers.mutate import router as mutate_router
from routers.projects import router as projects_router
from routers.upload import router as upload_router

app.include_router(projects_router, prefix="/api", tags=["Data"])
app.include_router(chat_router, prefix="/api", tags=["Chat"])
app.include_router(mutate_router, prefix="/api", tags=["Mutate"])
app.include_router(upload_router, prefix="/api", tags=["Upload"])


@app.get("/")
def root():
    return {"status": "ok", "service": "HaiVo LeadsMap API", "version": "2.0.0"}


@app.get("/health")
async def health():
    from core.database import get_stats

    stats = await get_stats()
    return {"status": "healthy", "db": stats.get("counts", {})}

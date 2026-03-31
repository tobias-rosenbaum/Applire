import os
import subprocess
import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text

from apliqa import __version__
from apliqa.config import settings
from apliqa.db.session import AsyncSessionLocal
from apliqa.routers import application, cv, flow, health, job, profile, session
from apliqa.services.thumbnails import ensure_thumbnails

_STUB_USER_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")
_STUB_EMAIL = "local@apliqa.community"

STATIC_DIR = Path(os.getenv("STATIC_DIR", "./data/static"))
STATIC_DIR.mkdir(parents=True, exist_ok=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    subprocess.run(["alembic", "upgrade", "head"], check=True)
    async with AsyncSessionLocal() as db:
        await db.execute(
            text(
                "INSERT INTO users (id, email, created_at) VALUES (:id, :email, :created_at)"
                " ON CONFLICT (id) DO NOTHING"
            ),
            {"id": str(_STUB_USER_ID), "email": _STUB_EMAIL, "created_at": datetime.now(timezone.utc)},
        )
        await db.commit()
    await ensure_thumbnails(STATIC_DIR)
    yield


app = FastAPI(
    title="Apliqa API",
    description="AI-powered DACH CV tailoring — Community Edition",
    version=__version__,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.cors_origins.split(",")],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

app.include_router(health.router)
app.include_router(job.router)
app.include_router(profile.router)
app.include_router(session.router)
app.include_router(flow.router)
app.include_router(cv.router)
app.include_router(application.router)

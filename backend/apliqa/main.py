import subprocess
import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from apliqa import __version__
from apliqa.config import settings
from apliqa.db.session import AsyncSessionLocal
from apliqa.routers import cv, flow, health, job, profile, session

_STUB_USER_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")
_STUB_EMAIL = "local@apliqa.community"


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
    yield


app = FastAPI(
    title="Apliqa API",
    description="AI-powered DACH CV tailoring — Community Edition",
    version=__version__,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(job.router)
app.include_router(profile.router)
app.include_router(session.router)
app.include_router(flow.router)
app.include_router(cv.router)

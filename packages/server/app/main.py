"""FastAPI application entrypoint."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.projects import router as projects_router
from app.api.suites import router as suites_router
from app.db.base import Base
from app.db.session import engine


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield


app = FastAPI(
    title="AgentGuard API",
    description="Release gate API for AI agent evaluation",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(projects_router, prefix="/api/v1")
app.include_router(suites_router, prefix="/api/v1")


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}

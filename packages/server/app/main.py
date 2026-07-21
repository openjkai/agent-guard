"""AgentGuard FastAPI application entrypoint."""

from __future__ import annotations

from fastapi import FastAPI

app = FastAPI(
    title="AgentGuard API",
    description="Release gate API for AI agent evaluation",
    version="0.1.0",
)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}

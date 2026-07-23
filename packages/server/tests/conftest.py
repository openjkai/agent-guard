"""Server test fixtures."""

from __future__ import annotations

from collections.abc import Generator
from pathlib import Path

import fakeredis
import pytest
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[3]


@pytest.fixture(autouse=True)
def _test_env(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    from app.config import get_settings

    monkeypatch.setenv("DATABASE_URL", "sqlite+aiosqlite:///:memory:?cache=shared")
    monkeypatch.setenv("REDIS_URL", "redis://localhost:6379/0")
    monkeypatch.setenv("AGENTGUARD_API_KEY", "test-key")
    monkeypatch.setenv("CELERY_TASK_ALWAYS_EAGER", "true")
    monkeypatch.setenv("REPO_ROOT", str(ROOT))
    monkeypatch.setenv("ARTIFACTS_DIR", str(tmp_path / "artifacts"))
    get_settings.cache_clear()

    fake = fakeredis.FakeRedis(decode_responses=True)
    monkeypatch.setattr(
        "app.services.progress.redis.Redis.from_url",
        lambda *args, **kwargs: fake,
    )


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    from app.main import app

    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def auth_headers() -> dict[str, str]:
    return {"X-API-Key": "test-key"}

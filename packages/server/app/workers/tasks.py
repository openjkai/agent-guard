"""Celery tasks for suite execution."""

from __future__ import annotations

import asyncio
import concurrent.futures
from collections.abc import Coroutine
from typing import Any

from app.config import get_settings
from app.db.session import SessionLocal
from app.services.suite_service import SuiteService
from app.workers.celery_app import celery_app


async def _execute_suite(project_id: str, suite_id: str, task_id: str | None) -> None:
    settings = get_settings()
    async with SessionLocal() as session:
        service = SuiteService(session, settings)
        project = await service.get_project(project_id)
        if project is None:
            await service.mark_failed(suite_id, f"Project not found: {project_id}")
            return
        await service.mark_running(suite_id, task_id=task_id)
        try:
            suite_result, gate_report = service.execute_suite_sync(project, suite_id)
            await service.persist_suite_result(suite_id, suite_result, gate_report)
        except Exception as exc:
            await service.mark_failed(suite_id, str(exc))
            raise


def _run_async(coro: Coroutine[Any, Any, None]) -> None:
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        asyncio.run(coro)
        return

    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(asyncio.run, coro)
        future.result()


@celery_app.task(name="agentguard.run_suite", bind=True)  # type: ignore[untyped-decorator]
def run_suite_task(self: object, project_id: str, suite_id: str) -> str:
    task_id = getattr(self, "request", None)
    celery_id = getattr(task_id, "id", None) if task_id else None
    _run_async(_execute_suite(project_id, suite_id, celery_id))
    return suite_id

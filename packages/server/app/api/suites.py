"""Suite and run routes."""

from __future__ import annotations

import asyncio
import json
from typing import Any

from fastapi import APIRouter, HTTPException, status
from sse_starlette.sse import EventSourceResponse

from app.deps import SessionDep, SettingsDep
from app.schemas.api import GateReportRead, RunDetail, RunRead, SuiteRead
from app.services.progress import ProgressPublisher
from app.services.suite_service import SuiteService

router = APIRouter(tags=["suites"])


@router.get("/suites/{suite_id}", response_model=SuiteRead)
async def get_suite(suite_id: str, session: SessionDep, settings: SettingsDep) -> Any:
    service = SuiteService(session, settings)
    suite = await service.get_suite(suite_id)
    if suite is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Suite not found")
    return suite


@router.get("/suites/{suite_id}/runs", response_model=list[RunRead])
async def list_suite_runs(suite_id: str, session: SessionDep, settings: SettingsDep) -> list[Any]:
    service = SuiteService(session, settings)
    if await service.get_suite(suite_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Suite not found")
    return await service.list_runs(suite_id)


@router.get("/runs/{run_id}", response_model=RunDetail)
async def get_run(run_id: str, session: SessionDep, settings: SettingsDep) -> Any:
    service = SuiteService(session, settings)
    run = await service.get_run(run_id)
    if run is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Run not found")
    return run


@router.get("/suites/{suite_id}/report", response_model=GateReportRead)
async def get_suite_report(
    suite_id: str, session: SessionDep, settings: SettingsDep
) -> GateReportRead:
    service = SuiteService(session, settings)
    suite = await service.get_suite(suite_id)
    if suite is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Suite not found")
    if suite.gate_report_json is None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Suite not completed")
    return GateReportRead(
        suite_id=suite_id,
        decision=str(suite.release_decision),
        pass_rate=suite.pass_rate,
        report=suite.gate_report_json,
    )


@router.get("/suites/{suite_id}/events")
async def suite_events(
    suite_id: str,
    session: SessionDep,
    settings: SettingsDep,
) -> EventSourceResponse:
    service = SuiteService(session, settings)
    suite = await service.get_suite(suite_id)
    if suite is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Suite not found")

    publisher = ProgressPublisher(settings)

    async def event_generator() -> Any:
        yield {
            "event": "progress",
            "data": json.dumps(
                {
                    "suite_id": suite_id,
                    "status": suite.status,
                    "completed": suite.progress_completed,
                    "total": suite.progress_total,
                    "message": "Connected",
                }
            ),
        }
        if suite.status in {"completed", "failed"}:
            return

        pubsub = publisher.subscribe(suite_id)

        def _listen() -> list[dict[str, str]]:
            messages: list[dict[str, str]] = []
            message = pubsub.get_message(timeout=1.0)
            if message and message.get("type") == "message":
                data = message["data"]
                messages.append({"event": "progress", "data": data})
            return messages

        while True:
            events = await asyncio.to_thread(_listen)
            for item in events:
                yield item
                payload = json.loads(item["data"])
                if payload.get("status") in {"completed", "failed"}:
                    pubsub.close()
                    return
            await asyncio.sleep(0.2)

    return EventSourceResponse(event_generator())

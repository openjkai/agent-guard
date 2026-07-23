"""Project routes."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select

from app.db.models import Project, SuiteRun
from app.deps import SessionDep, SettingsDep, verify_api_key
from app.schemas.api import ProjectCreate, ProjectRead, SuiteCreate, SuiteRead
from app.services.suite_service import SuiteService
from app.workers.tasks import run_suite_task

router = APIRouter(prefix="/projects", tags=["projects"])


@router.post("", response_model=ProjectRead, status_code=status.HTTP_201_CREATED)
async def create_project(body: ProjectCreate, session: SessionDep) -> Project:
    project = Project(
        name=body.name,
        description=body.description,
        agent_module_path=body.agent_module_path,
        scenarios_path=body.scenarios_path,
        config_json=body.config_json,
    )
    session.add(project)
    await session.commit()
    await session.refresh(project)
    return project


@router.get("", response_model=list[ProjectRead])
async def list_projects(session: SessionDep) -> list[Project]:
    result = await session.scalars(select(Project).order_by(Project.created_at.desc()))
    return list(result.all())


@router.get("/{project_id}", response_model=ProjectRead)
async def get_project(project_id: str, session: SessionDep) -> Project:
    project = await session.get(Project, project_id)
    if project is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    return project


@router.post(
    "/{project_id}/suites",
    response_model=SuiteRead,
    status_code=status.HTTP_202_ACCEPTED,
)
async def start_suite(
    project_id: str,
    session: SessionDep,
    settings: SettingsDep,
    _: Annotated[None, Depends(verify_api_key)],
    _body: SuiteCreate | None = None,
) -> SuiteRun:
    service = SuiteService(session, settings)
    project = await service.get_project(project_id)
    if project is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    suite = await service.create_suite(project)
    if not settings.celery_task_always_eager:
        suite.status = "queued"
        await session.commit()
    task = run_suite_task.delay(project_id, suite.id)
    suite.celery_task_id = task.id
    await session.commit()
    await session.refresh(suite)
    return suite

"""API request/response schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class ProjectCreate(BaseModel):
    name: str
    description: str | None = None
    agent_module_path: str
    scenarios_path: str
    config_json: dict[str, Any] = Field(default_factory=dict)


class ProjectRead(BaseModel):
    model_config = {"from_attributes": True}

    id: str
    name: str
    description: str | None
    agent_module_path: str
    scenarios_path: str
    config_json: dict[str, Any]
    created_at: datetime


class SuiteCreate(BaseModel):
    """Optional overrides; defaults to project paths/config."""


class SuiteRead(BaseModel):
    model_config = {"from_attributes": True}

    id: str
    project_id: str
    status: str
    pass_rate: float | None
    release_decision: str | None
    progress_completed: int
    progress_total: int
    error: str | None
    created_at: datetime
    finished_at: datetime | None


class RunRead(BaseModel):
    model_config = {"from_attributes": True}

    id: str
    suite_id: str
    scenario_id: str
    status: str
    agent_output: str | None
    latency_ms: float
    cost_usd: float
    passed: bool
    created_at: datetime


class RunDetail(RunRead):
    model_config = {"from_attributes": True}

    trace_json: dict[str, Any]
    evaluations_json: dict[str, Any]


class GateReportRead(BaseModel):
    suite_id: str
    decision: str
    pass_rate: float | None
    report: dict[str, Any]


class ProgressEvent(BaseModel):
    suite_id: str
    status: str
    completed: int
    total: int
    scenario_id: str | None = None
    message: str = ""

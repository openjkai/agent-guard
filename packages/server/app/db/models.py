"""SQLAlchemy ORM models."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

from app.db.base import Base
from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON


def utcnow() -> datetime:
    return datetime.now(UTC)


def new_uuid() -> str:
    return str(uuid.uuid4())


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    agent_module_path: Mapped[str] = mapped_column(String(1024), nullable=False)
    scenarios_path: Mapped[str] = mapped_column(String(1024), nullable=False)
    config_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    suites: Mapped[list[SuiteRun]] = relationship(back_populates="project")


class SuiteRun(Base):
    __tablename__ = "suite_runs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id"), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="pending")
    pass_rate: Mapped[float | None] = mapped_column(Float, nullable=True)
    release_decision: Mapped[str | None] = mapped_column(String(64), nullable=True)
    result_json: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    gate_report_json: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    celery_task_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    progress_completed: Mapped[int] = mapped_column(Integer, default=0)
    progress_total: Mapped[int] = mapped_column(Integer, default=0)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    project: Mapped[Project] = relationship(back_populates="suites")
    runs: Mapped[list[RunRecord]] = relationship(back_populates="suite")


class RunRecord(Base):
    __tablename__ = "run_records"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    suite_id: Mapped[str] = mapped_column(ForeignKey("suite_runs.id"), nullable=False, index=True)
    scenario_id: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    agent_output: Mapped[str | None] = mapped_column(Text, nullable=True)
    trace_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    evaluations_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    cassette_json: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    latency_ms: Mapped[float] = mapped_column(Float, default=0.0)
    cost_usd: Mapped[float] = mapped_column(Float, default=0.0)
    passed: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    suite: Mapped[SuiteRun] = relationship(back_populates="runs")

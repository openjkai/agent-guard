"""Trace domain models aligned with OpenTelemetry GenAI conventions."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field, computed_field

from agentguard.types import RunStatus, StepType


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def new_id() -> str:
    return str(uuid4())


class Usage(BaseModel):
    input_tokens: int = 0
    output_tokens: int = 0

    @computed_field  # type: ignore[prop-decorator]
    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens


class Cost(BaseModel):
    input_usd: float = 0.0
    output_usd: float = 0.0

    @computed_field  # type: ignore[prop-decorator]
    @property
    def total_usd(self) -> float:
        return round(self.input_usd + self.output_usd, 8)


class ToolCallRecord(BaseModel):
    tool_name: str
    arguments: dict[str, Any] = Field(default_factory=dict)
    result: Any | None = None
    error: str | None = None
    latency_ms: float = 0.0
    step_id: str | None = None
    policy_violation: str | None = None


class RetrievalRecord(BaseModel):
    query: str
    document_ids: list[str] = Field(default_factory=list)
    documents: list[dict[str, Any]] = Field(default_factory=list)
    latency_ms: float = 0.0
    step_id: str | None = None


class Step(BaseModel):
    step_id: str = Field(default_factory=new_id)
    type: StepType
    started_at: datetime = Field(default_factory=utcnow)
    finished_at: datetime | None = None
    latency_ms: float = 0.0
    input: dict[str, Any] = Field(default_factory=dict)
    output: dict[str, Any] = Field(default_factory=dict)
    usage: Usage | None = None
    cost: Cost | None = None
    error: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    def finish(
        self, *, output: dict[str, Any] | None = None, error: str | None = None
    ) -> None:
        self.finished_at = utcnow()
        if self.started_at.tzinfo is None:
            self.started_at = self.started_at.replace(tzinfo=timezone.utc)
        delta = self.finished_at - self.started_at
        self.latency_ms = delta.total_seconds() * 1000
        if output is not None:
            self.output = output
        if error is not None:
            self.error = error


class ToolCallCollection:
    """Helper to query tool calls recorded on a run."""

    def __init__(self, steps: list[Step]) -> None:
        self._records: list[ToolCallRecord] = []
        for step in steps:
            if step.type != StepType.TOOL:
                continue
            self._records.append(
                ToolCallRecord(
                    tool_name=str(step.input.get("tool_name", "")),
                    arguments=dict(step.input.get("arguments", {})),
                    result=step.output.get("result"),
                    error=step.error,
                    latency_ms=step.latency_ms,
                    step_id=step.step_id,
                    policy_violation=step.output.get("policy_violation"),
                )
            )

    def find(self, name: str) -> ToolCallRecord | None:
        matches = self.all(name)
        return matches[0] if matches else None

    def all(self, name: str) -> list[ToolCallRecord]:
        return [record for record in self._records if record.tool_name == name]

    def names(self) -> list[str]:
        return [record.tool_name for record in self._records]


class Run(BaseModel):
    run_id: str = Field(default_factory=new_id)
    scenario_id: str
    suite_id: str | None = None
    agent_config_hash: str = ""
    status: RunStatus = RunStatus.RUNNING
    started_at: datetime = Field(default_factory=utcnow)
    finished_at: datetime | None = None
    user_messages: list[str] = Field(default_factory=list)
    agent_output: str | None = None
    steps: list[Step] = Field(default_factory=list)
    usage: Usage = Field(default_factory=Usage)
    cost: Cost = Field(default_factory=Cost)
    latency_ms: float = 0.0
    metadata: dict[str, Any] = Field(default_factory=dict)
    error: str | None = None

    @property
    def tool_calls(self) -> ToolCallCollection:
        return ToolCallCollection(self.steps)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def retrievals(self) -> list[RetrievalRecord]:
        records: list[RetrievalRecord] = []
        for step in self.steps:
            if step.type != StepType.RETRIEVAL:
                continue
            records.append(
                RetrievalRecord(
                    query=str(step.input.get("query", "")),
                    document_ids=list(step.output.get("document_ids", [])),
                    documents=list(step.output.get("documents", [])),
                    latency_ms=step.latency_ms,
                    step_id=step.step_id,
                )
            )
        return records

    def finish(
        self, *, status: RunStatus | None = None, error: str | None = None
    ) -> None:
        self.finished_at = utcnow()
        if self.started_at.tzinfo is None:
            self.started_at = self.started_at.replace(tzinfo=timezone.utc)
        self.latency_ms = (self.finished_at - self.started_at).total_seconds() * 1000
        if status is not None:
            self.status = status
        if error is not None:
            self.error = error

    def recompute_totals(self) -> None:
        usage = Usage()
        cost = Cost()
        for step in self.steps:
            if step.usage:
                usage.input_tokens += step.usage.input_tokens
                usage.output_tokens += step.usage.output_tokens
            if step.cost:
                cost.input_usd += step.cost.input_usd
                cost.output_usd += step.cost.output_usd
        self.usage = usage
        self.cost = cost

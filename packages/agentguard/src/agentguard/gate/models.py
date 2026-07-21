"""Release gate models."""

from __future__ import annotations

from pydantic import BaseModel, Field

from agentguard.evaluators.result import EvalResult
from agentguard.types import ReleaseDecision


class GateMetrics(BaseModel):
    pass_rate: float
    avg_cost_usd: float
    avg_latency_ms: float
    p95_latency_ms: float
    critical_failure_count: int
    major_failure_count: int
    regression_vs_baseline: float | None = None


class ReleaseReport(BaseModel):
    decision: ReleaseDecision
    suite_id: str
    metrics: GateMetrics
    previous_pass_rate: float | None = None
    critical_failures: list[EvalResult] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    recommended_actions: list[str] = Field(default_factory=list)
    summary: str = ""


DECISION_EXIT_CODES = {
    "SHIP": 0,
    "SHIP_WITH_WARNING": 10,
    "REQUIRE_HUMAN_REVIEW": 20,
    "BLOCK": 30,
}

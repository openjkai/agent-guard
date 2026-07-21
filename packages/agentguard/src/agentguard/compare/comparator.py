"""Compare suite results across agent configurations."""

from __future__ import annotations

from pydantic import BaseModel, Field

from agentguard.scenarios.runner import SuiteResult


class MetricDelta(BaseModel):
    name: str
    baseline: float
    candidate: float

    @property
    def delta(self) -> float:
        return self.candidate - self.baseline

    @property
    def delta_pct(self) -> float | None:
        if self.baseline == 0:
            return None
        return (self.delta / self.baseline) * 100


class ComparisonReport(BaseModel):
    baseline_suite_id: str
    candidate_suite_id: str
    metrics: list[MetricDelta] = Field(default_factory=list)
    scenario_regressions: list[str] = Field(default_factory=list)
    scenario_improvements: list[str] = Field(default_factory=list)
    summary: str = ""


def compare_suites(baseline: SuiteResult, candidate: SuiteResult) -> ComparisonReport:
    metrics = [
        MetricDelta(
            name="pass_rate", baseline=baseline.pass_rate, candidate=candidate.pass_rate
        ),
        MetricDelta(
            name="avg_cost_usd",
            baseline=baseline.avg_cost_usd,
            candidate=candidate.avg_cost_usd,
        ),
        MetricDelta(
            name="avg_latency_ms",
            baseline=baseline.avg_latency_ms,
            candidate=candidate.avg_latency_ms,
        ),
        MetricDelta(
            name="critical_failures",
            baseline=float(len(baseline.critical_failures())),
            candidate=float(len(candidate.critical_failures())),
        ),
    ]

    baseline_map = {item.run.scenario_id: item.passed for item in baseline.runs}
    candidate_map = {item.run.scenario_id: item.passed for item in candidate.runs}
    regressions = [
        scenario_id
        for scenario_id, passed in baseline_map.items()
        if passed and scenario_id in candidate_map and not candidate_map[scenario_id]
    ]
    improvements = [
        scenario_id
        for scenario_id, passed in baseline_map.items()
        if not passed and scenario_id in candidate_map and candidate_map[scenario_id]
    ]

    summary = (
        f"Pass rate {baseline.pass_rate:.0%} -> {candidate.pass_rate:.0%}; "
        f"avg cost ${baseline.avg_cost_usd:.3f} -> ${candidate.avg_cost_usd:.3f}; "
        f"{len(regressions)} regressions, {len(improvements)} improvements."
    )

    return ComparisonReport(
        baseline_suite_id=baseline.suite_id,
        candidate_suite_id=candidate.suite_id,
        metrics=metrics,
        scenario_regressions=regressions,
        scenario_improvements=improvements,
        summary=summary,
    )

"""Release gate policy evaluation."""

from __future__ import annotations

import re

from agentguard.gate.models import GateMetrics, ReleaseReport
from agentguard.scenarios.models import GatePolicy
from agentguard.scenarios.runner import SuiteResult
from agentguard.types import ReleaseDecision


def _metric_value(
    name: str, suite: SuiteResult, baseline: SuiteResult | None
) -> float | int | bool:
    mapping = {
        "pass_rate": suite.pass_rate,
        "avg_cost_usd": suite.avg_cost_usd,
        "avg_latency_ms": suite.avg_latency_ms,
        "p95_latency_ms": suite.p95_latency_ms,
        "any_critical_failure": bool(suite.critical_failures()),
        "any_major_failure": any(
            not result.passed and result.severity == "major"
            for item in suite.runs
            for result in item.eval_results
        ),
    }
    if name == "regression_vs_baseline" and baseline is not None:
        return baseline.pass_rate - suite.pass_rate
    if name in mapping:
        value = mapping[name]
        return value if isinstance(value, (float, int, bool)) else bool(value)
    match = re.match(r"pass_rate\s*([<>]=?)\s*([0-9.]+)", name)
    if match:
        operator, raw = match.groups()
        threshold = float(raw)
        if operator == "<":
            return suite.pass_rate < threshold
        if operator == "<=":
            return suite.pass_rate <= threshold
        if operator == ">":
            return suite.pass_rate > threshold
        if operator == ">=":
            return suite.pass_rate >= threshold
    match = re.match(r"regression_vs_baseline\s*([<>]=?)\s*([0-9.]+)", name)
    if match and baseline is not None:
        operator, raw = match.groups()
        delta = baseline.pass_rate - suite.pass_rate
        threshold = float(raw)
        if operator == ">":
            return delta > threshold
        if operator == ">=":
            return delta >= threshold
    match = re.match(r"(avg_cost_usd|p95_latency_ms)\s*([<>]=?)\s*([0-9.]+)", name)
    if match:
        metric_name, operator, raw = match.groups()
        metric_value = mapping[metric_name]
        value = float(metric_value) if isinstance(metric_value, (int, float)) else 0.0
        threshold = float(raw)
        if operator == ">":
            return value > threshold
        if operator == ">=":
            return value >= threshold
    return False


def _rule_matches(rule: str, suite: SuiteResult, baseline: SuiteResult | None) -> bool:
    if rule in {"any_critical_failure", "any_major_failure"}:
        return bool(_metric_value(rule, suite, baseline))
    if rule.startswith("pass_rate") or rule.startswith("regression_vs_baseline"):
        return bool(_metric_value(rule, suite, baseline))
    if rule.startswith("avg_cost_usd") or rule.startswith("p95_latency_ms"):
        return bool(_metric_value(rule, suite, baseline))
    return bool(_metric_value(rule, suite, baseline))


def evaluate_gate(
    suite: SuiteResult,
    policy: GatePolicy,
    *,
    baseline: SuiteResult | None = None,
) -> ReleaseReport:
    metrics = GateMetrics(
        pass_rate=suite.pass_rate,
        avg_cost_usd=suite.avg_cost_usd,
        avg_latency_ms=suite.avg_latency_ms,
        p95_latency_ms=suite.p95_latency_ms,
        critical_failure_count=len(suite.critical_failures()),
        major_failure_count=sum(
            1
            for item in suite.runs
            for result in item.eval_results
            if not result.passed and result.severity == "major"
        ),
        regression_vs_baseline=(baseline.pass_rate - suite.pass_rate)
        if baseline
        else None,
    )
    warnings: list[str] = []
    recommended: list[str] = []
    decision: ReleaseDecision = "SHIP"

    if any(_rule_matches(rule, suite, baseline) for rule in policy.block_if):
        decision = "BLOCK"
    elif any(_rule_matches(rule, suite, baseline) for rule in policy.require_review_if):
        decision = "REQUIRE_HUMAN_REVIEW"
    elif any(_rule_matches(rule, suite, baseline) for rule in policy.warn_if):
        decision = "SHIP_WITH_WARNING"

    critical_failures = suite.critical_failures()
    if critical_failures:
        top = critical_failures[0]
        recommended.append(
            "Investigate critical evaluator failures and add deterministic checks before tool execution."
        )
        recommended.append(f"Top failure: {top.name} — {top.reason}")

    if metrics.regression_vs_baseline and metrics.regression_vs_baseline > 0.02:
        warnings.append(
            f"Pass rate regressed by {metrics.regression_vs_baseline * 100:.1f} percentage points vs baseline."
        )

    if metrics.pass_rate < 0.95:
        recommended.append(
            "Review failing scenarios and replay traces for the largest regressions."
        )

    summary = (
        f"Release decision: {decision.replace('_', ' ')}\n"
        f"Overall pass rate: {metrics.pass_rate * 100:.0f}%\n"
        f"Critical failures: {metrics.critical_failure_count}\n"
        f"Average latency: {metrics.avg_latency_ms / 1000:.1f} seconds\n"
        f"Average cost: ${metrics.avg_cost_usd:.3f} per run"
    )

    return ReleaseReport(
        decision=decision,
        suite_id=suite.suite_id,
        metrics=metrics,
        previous_pass_rate=baseline.pass_rate if baseline else None,
        critical_failures=critical_failures,
        warnings=warnings,
        recommended_actions=recommended,
        summary=summary,
    )

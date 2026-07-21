"""Custom evaluator decorator."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from agentguard.evaluators.registry import GLOBAL_REGISTRY, EvaluatorFn
from agentguard.evaluators.result import EvalResult
from agentguard.tracing.models import Run


def evaluator(
    name: str,
) -> Callable[[Callable[[Run], EvalResult | dict[str, Any]]], EvaluatorFn]:
    return evaluator_fn(name)


def _coerce_result(name: str, value: EvalResult | dict[str, Any]) -> EvalResult:
    if isinstance(value, EvalResult):
        return value
    passed = bool(value.get("passed", False))
    return EvalResult(
        name=name,
        passed=passed,
        severity=value.get("severity", "info"),
        reason=str(value.get("reason", "")),
        score=value.get("score"),
    )


def evaluator_fn(
    name: str,
) -> Callable[[Callable[[Run], EvalResult | dict[str, Any]]], EvaluatorFn]:
    def decorator(fn: Callable[[Run], EvalResult | dict[str, Any]]) -> EvaluatorFn:
        def wrapped(run: Run) -> EvalResult:
            return _coerce_result(name, fn(run))

        GLOBAL_REGISTRY.register(name, wrapped)
        return wrapped

    return decorator

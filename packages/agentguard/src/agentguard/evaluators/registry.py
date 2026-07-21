"""Evaluator registry."""

from __future__ import annotations

from collections.abc import Callable

from agentguard.errors import EvaluatorNotFoundError
from agentguard.evaluators.result import EvalResult
from agentguard.tracing.models import Run

EvaluatorFn = Callable[[Run], EvalResult]


class EvaluatorRegistry:
    def __init__(self) -> None:
        self._evaluators: dict[str, EvaluatorFn] = {}

    def register(self, name: str, fn: EvaluatorFn) -> None:
        self._evaluators[name] = fn

    def get(self, name: str) -> EvaluatorFn:
        if name not in self._evaluators:
            raise EvaluatorNotFoundError(f"Evaluator not found: {name}")
        return self._evaluators[name]

    def run(self, run: Run, names: list[str]) -> list[EvalResult]:
        return [self.get(name)(run) for name in names]

    def names(self) -> list[str]:
        return sorted(self._evaluators)


GLOBAL_REGISTRY = EvaluatorRegistry()

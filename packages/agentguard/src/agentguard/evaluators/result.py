"""Evaluation result model."""

from __future__ import annotations

from pydantic import BaseModel, Field

from agentguard.types import Severity


class EvalResult(BaseModel):
    name: str
    passed: bool
    severity: Severity = "info"
    reason: str = ""
    score: float | None = None
    metadata: dict[str, str] = Field(default_factory=dict)

    @classmethod
    def ok(cls, name: str, reason: str = "", score: float | None = None) -> EvalResult:
        return cls(name=name, passed=True, reason=reason, score=score)

    @classmethod
    def fail(
        cls,
        name: str,
        reason: str,
        *,
        severity: Severity = "major",
        score: float | None = None,
    ) -> EvalResult:
        return cls(
            name=name, passed=False, severity=severity, reason=reason, score=score
        )

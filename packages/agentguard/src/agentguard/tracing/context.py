"""Run trace capture context."""

from __future__ import annotations

from typing import Any

from agentguard.tracing.models import Cost, Run, Step, Usage, utcnow
from agentguard.types import StepType


class RunContext:
    """Accumulates trace steps during agent execution."""

    def __init__(self, run: Run) -> None:
        self.run = run

    def record_llm(
        self,
        *,
        request: dict[str, Any],
        response: dict[str, Any],
        usage: Usage | None = None,
        cost: Cost | None = None,
        metadata: dict[str, Any] | None = None,
        error: str | None = None,
    ) -> Step:
        step = Step(
            type=StepType.LLM,
            input={"request": request},
            output={"response": response},
            usage=usage,
            cost=cost,
            metadata=metadata or {},
            error=error,
        )
        step.finish(output=step.output, error=error)
        self.run.steps.append(step)
        return step

    def record_tool(
        self,
        *,
        tool_name: str,
        arguments: dict[str, Any],
        result: Any,
        error: str | None = None,
        policy_violation: str | None = None,
    ) -> Step:
        step = Step(
            type=StepType.TOOL,
            input={"tool_name": tool_name, "arguments": arguments},
            output={"result": result, "policy_violation": policy_violation},
            error=error,
        )
        step.finish(output=step.output, error=error)
        self.run.steps.append(step)
        return step

    def record_retrieval(
        self,
        *,
        query: str,
        document_ids: list[str],
        documents: list[dict[str, Any]],
    ) -> Step:
        step = Step(
            type=StepType.RETRIEVAL,
            input={"query": query},
            output={"document_ids": document_ids, "documents": documents},
        )
        step.finish(output=step.output)
        self.run.steps.append(step)
        return step

    def record_state(self, *, before: dict[str, Any], after: dict[str, Any]) -> Step:
        step = Step(
            type=StepType.STATE,
            input={"before": before},
            output={"after": after},
        )
        step.finish(output=step.output)
        self.run.steps.append(step)
        return step

    def set_output(self, output: str) -> None:
        self.run.agent_output = output

    def mark_started(self) -> None:
        self.run.started_at = utcnow()

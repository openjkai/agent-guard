"""Diff two runs step-by-step."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from agentguard.tracing.models import Run, Step


class StepDiff(BaseModel):
    index: int
    changed: bool
    left: dict[str, Any] | None = None
    right: dict[str, Any] | None = None
    fields_changed: list[str] = Field(default_factory=list)


class RunDiff(BaseModel):
    run_id_left: str
    run_id_right: str
    steps: list[StepDiff] = Field(default_factory=list)
    output_changed: bool = False
    status_changed: bool = False

    @property
    def has_changes(self) -> bool:
        return (
            self.output_changed
            or self.status_changed
            or any(step.changed for step in self.steps)
        )


def _step_snapshot(step: Step) -> dict[str, Any]:
    return {
        "type": step.type.value,
        "input": step.input,
        "output": step.output,
        "error": step.error,
        "latency_ms": step.latency_ms,
    }


def diff_runs(left: Run, right: Run) -> RunDiff:
    result = RunDiff(
        run_id_left=left.run_id,
        run_id_right=right.run_id,
        output_changed=left.agent_output != right.agent_output,
        status_changed=left.status != right.status,
    )
    max_len = max(len(left.steps), len(right.steps))
    for index in range(max_len):
        left_step = left.steps[index] if index < len(left.steps) else None
        right_step = right.steps[index] if index < len(right.steps) else None
        left_data = _step_snapshot(left_step) if left_step else None
        right_data = _step_snapshot(right_step) if right_step else None
        changed = left_data != right_data
        fields_changed: list[str] = []
        if left_data and right_data:
            keys = set(left_data) | set(right_data)
            fields_changed = [
                key for key in keys if left_data.get(key) != right_data.get(key)
            ]
        result.steps.append(
            StepDiff(
                index=index,
                changed=changed,
                left=left_data,
                right=right_data,
                fields_changed=fields_changed,
            )
        )
    return result

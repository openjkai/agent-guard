"""Evaluator tests."""

from agentguard.evaluators.registry import GLOBAL_REGISTRY
from agentguard.tracing.models import Run, Step
from agentguard.types import StepType


def test_refund_limit_evaluator() -> None:
    run = Run(scenario_id="over-limit")
    run.steps.append(
        Step(
            type=StepType.TOOL,
            input={"tool_name": "issue_refund", "arguments": {"amount": 780}},
            output={"result": {}},
        )
    )
    result = GLOBAL_REGISTRY.get("refund_limit")(run)
    assert result.passed is False
    assert result.severity == "critical"

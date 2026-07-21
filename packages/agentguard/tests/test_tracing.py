"""Trace model tests."""

from agentguard.tracing.models import Cost, Run, Step, Usage
from agentguard.types import StepType


def test_run_recompute_totals() -> None:
    run = Run(scenario_id="demo")
    run.steps.append(
        Step(
            type=StepType.LLM,
            usage=Usage(input_tokens=100, output_tokens=20),
            cost=Cost(input_usd=0.001, output_usd=0.002),
        )
    )
    run.recompute_totals()
    assert run.usage.total_tokens == 120
    assert run.cost.total_usd == 0.003


def test_tool_call_collection() -> None:
    run = Run(scenario_id="demo")
    run.steps.append(
        Step(
            type=StepType.TOOL,
            input={"tool_name": "issue_refund", "arguments": {"amount": 700}},
            output={"result": {"status": "processed"}},
        )
    )
    refund = run.tool_calls.find("issue_refund")
    assert refund is not None
    assert refund.arguments["amount"] == 700

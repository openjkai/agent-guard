"""Release gate tests."""

from agentguard.evaluators.result import EvalResult
from agentguard.gate.engine import evaluate_gate
from agentguard.scenarios.models import GatePolicy
from agentguard.scenarios.runner import EvaluatedRun, SuiteResult
from agentguard.tracing.models import Run
from agentguard.types import RunStatus


def _suite_with_pass_rate(rate: float) -> SuiteResult:
    total = 10
    passed_count = int(rate * total)
    runs: list[EvaluatedRun] = []
    for index in range(total):
        passed = index < passed_count
        run = Run(
            scenario_id=f"s-{index}",
            status=RunStatus.PASSED if passed else RunStatus.FAILED,
        )
        results = (
            [EvalResult.ok("demo")]
            if passed
            else [EvalResult.fail("demo", "fail", severity="critical")]
        )
        runs.append(EvaluatedRun(run=run, eval_results=results))
    return SuiteResult(suite_id="suite-1", runs=runs)


def test_gate_blocks_on_critical_failures() -> None:
    suite = _suite_with_pass_rate(0.9)
    report = evaluate_gate(suite, GatePolicy())
    assert report.decision == "BLOCK"

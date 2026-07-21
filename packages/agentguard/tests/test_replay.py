"""Replay tests."""

from agentguard.replay.cassette import Cassette, interaction_hash
from agentguard.replay.diff import diff_runs
from agentguard.tracing.models import Run
from agentguard.types import InteractionKind


def test_interaction_hash_is_stable() -> None:
    payload = {"messages": [{"role": "user", "content": "hello"}]}
    assert interaction_hash(InteractionKind.LLM, payload) == interaction_hash(
        InteractionKind.LLM, payload
    )


def test_diff_runs_detects_output_change() -> None:
    left = Run(scenario_id="a", agent_output="escalate")
    right = Run(scenario_id="a", agent_output="approved")
    result = diff_runs(left, right)
    assert result.output_changed is True


def test_cassette_find_by_hash() -> None:
    cassette = Cassette(run_id="run-1")
    request = {"tool_name": "issue_refund", "arguments": {"amount": 10}}
    response = {"result": {"ok": True}}
    cassette.add(InteractionKind.TOOL, request, response)
    found = cassette.find(InteractionKind.TOOL, request)
    assert found is not None
    assert found.response == response

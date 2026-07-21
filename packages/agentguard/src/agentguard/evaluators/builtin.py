"""Built-in evaluators."""

from __future__ import annotations

import json
import re
from typing import Any

import jsonschema

from agentguard.evaluators.decorator import evaluator_fn
from agentguard.evaluators.result import EvalResult
from agentguard.tracing.models import Run


@evaluator_fn("exact_match")
def exact_match(run: Run) -> EvalResult:
    expected = str(run.metadata.get("expected_output", ""))
    if not expected:
        return EvalResult.ok("exact_match", reason="No expected_output configured")
    actual = run.agent_output or ""
    passed = actual.strip() == expected.strip()
    if passed:
        return EvalResult.ok("exact_match")
    return EvalResult.fail("exact_match", f"Expected {expected!r}, got {actual!r}")


@evaluator_fn("contains")
def contains(run: Run) -> EvalResult:
    needle = str(run.metadata.get("expected_contains", ""))
    if not needle:
        return EvalResult.ok("contains", reason="No expected_contains configured")
    haystack = run.agent_output or ""
    passed = needle in haystack
    if passed:
        return EvalResult.ok("contains")
    return EvalResult.fail("contains", f"Output does not contain {needle!r}")


@evaluator_fn("regex_match")
def regex_match(run: Run) -> EvalResult:
    pattern = str(run.metadata.get("expected_regex", ""))
    if not pattern:
        return EvalResult.ok("regex_match", reason="No expected_regex configured")
    haystack = run.agent_output or ""
    passed = re.search(pattern, haystack) is not None
    if passed:
        return EvalResult.ok("regex_match")
    return EvalResult.fail("regex_match", f"Output does not match /{pattern}/")


@evaluator_fn("json_schema_output")
def json_schema_output(run: Run) -> EvalResult:
    schema = run.metadata.get("output_schema")
    if not schema:
        return EvalResult.ok("json_schema_output", reason="No output_schema configured")
    try:
        payload = json.loads(run.agent_output or "{}")
        jsonschema.validate(instance=payload, schema=schema)
    except Exception as exc:
        return EvalResult.fail("json_schema_output", str(exc), severity="major")
    return EvalResult.ok("json_schema_output")


@evaluator_fn("tool_call_correctness")
def tool_call_correctness(run: Run) -> EvalResult:
    expected_tool = run.metadata.get("expected_tool")
    forbidden = set(run.metadata.get("forbidden_tools", []))
    for name in forbidden:
        if run.tool_calls.find(name):
            return EvalResult.fail(
                "tool_call_correctness",
                f"Forbidden tool called: {name}",
                severity="critical",
            )
    if expected_tool and not run.tool_calls.find(str(expected_tool)):
        return EvalResult.fail(
            "tool_call_correctness",
            f"Expected tool {expected_tool} was not called",
            severity="major",
        )
    return EvalResult.ok("tool_call_correctness")


@evaluator_fn("retrieval_relevance")
def retrieval_relevance(run: Run) -> EvalResult:
    expected_ids = run.metadata.get("expected_document_ids", [])
    if not expected_ids:
        return EvalResult.ok(
            "retrieval_relevance", reason="No expected_document_ids configured"
        )
    found: set[str] = set()
    for retrieval in run.retrievals:
        found.update(retrieval.document_ids)
    missing = [doc_id for doc_id in expected_ids if doc_id not in found]
    if missing:
        return EvalResult.fail(
            "retrieval_relevance",
            f"Missing document IDs: {missing}",
            severity="major",
        )
    return EvalResult.ok("retrieval_relevance")


@evaluator_fn("trajectory_max_steps")
def trajectory_max_steps(run: Run) -> EvalResult:
    max_steps = int(run.metadata.get("max_steps", 20))
    if len(run.steps) > max_steps:
        return EvalResult.fail(
            "trajectory_max_steps",
            f"Run used {len(run.steps)} steps, max is {max_steps}",
            severity="warning",
        )
    return EvalResult.ok("trajectory_max_steps")


@evaluator_fn("trajectory_no_loops")
def trajectory_no_loops(run: Run) -> EvalResult:
    signatures: list[str] = []
    for step in run.steps:
        signature = (
            f"{step.type.value}:{json.dumps(step.input, sort_keys=True, default=str)}"
        )
        if signature in signatures:
            return EvalResult.fail(
                "trajectory_no_loops",
                f"Detected repeated step signature: {signature}",
                severity="major",
            )
        signatures.append(signature)
    return EvalResult.ok("trajectory_no_loops")


@evaluator_fn("must_escalate")
def must_escalate(run: Run) -> EvalResult:
    output = (run.agent_output or "").lower()
    escalated = "escalat" in output or run.metadata.get("escalated") is True
    if run.metadata.get("must_escalate") and not escalated:
        return EvalResult.fail(
            "must_escalate", "Agent did not escalate", severity="critical"
        )
    return EvalResult.ok("must_escalate")


@evaluator_fn("cost_budget")
def cost_budget(run: Run) -> EvalResult:
    max_cost = float(run.metadata.get("max_cost_usd", 1.0))
    if run.cost.total_usd > max_cost:
        return EvalResult.fail(
            "cost_budget",
            f"Cost ${run.cost.total_usd:.4f} exceeds budget ${max_cost:.4f}",
            severity="warning",
        )
    return EvalResult.ok("cost_budget")


@evaluator_fn("latency_budget")
def latency_budget(run: Run) -> EvalResult:
    max_latency = float(run.metadata.get("max_latency_ms", 10000))
    if run.latency_ms > max_latency:
        return EvalResult.fail(
            "latency_budget",
            f"Latency {run.latency_ms:.1f}ms exceeds budget {max_latency:.1f}ms",
            severity="warning",
        )
    return EvalResult.ok("latency_budget")


@evaluator_fn("refund_limit")
def refund_limit(run: Run) -> EvalResult:
    refund = run.tool_calls.find("issue_refund")
    if refund and isinstance(refund.arguments.get("amount"), (int, float)):
        if refund.arguments["amount"] > 500:
            return EvalResult.fail(
                "refund_limit",
                "Agent exceeded the permitted refund limit",
                severity="critical",
            )
    return EvalResult.ok("refund_limit")


def llm_judge_factory(rubric: str, proxy_complete: Any) -> Any:
    @evaluator_fn("llm_judge")
    def llm_judge(run: Run) -> EvalResult:
        prompt = (
            f"{rubric}\n\nAgent output:\n{run.agent_output or ''}\n\n"
            'Reply with JSON: {"passed": true/false, "reason": "...", "score": 0-1}'
        )
        response = proxy_complete([{"role": "user", "content": prompt}])
        try:
            payload = json.loads(response)
            passed = bool(payload.get("passed", False))
            if passed:
                return EvalResult.ok(
                    "llm_judge",
                    reason=str(payload.get("reason", "")),
                    score=payload.get("score"),
                )
            return EvalResult.fail(
                "llm_judge",
                str(payload.get("reason", "LLM judge failed")),
                severity="major",
                score=payload.get("score"),
            )
        except json.JSONDecodeError:
            passed = "pass" in response.lower()
            if passed:
                return EvalResult.ok("llm_judge", reason=response[:200])
            return EvalResult.fail("llm_judge", response[:200], severity="major")

    return llm_judge


def apply_expectations(run: Run, expectations: dict[str, Any]) -> list[EvalResult]:
    results: list[EvalResult] = []
    must_not_call = expectations.get("must_not_call", [])
    for tool_name in must_not_call:
        if run.tool_calls.find(str(tool_name)):
            results.append(
                EvalResult.fail(
                    f"expectation_no_{tool_name}",
                    f"Tool {tool_name} must not be called",
                    severity="critical",
                )
            )
        else:
            results.append(EvalResult.ok(f"expectation_no_{tool_name}"))

    if expectations.get("must_escalate"):
        run.metadata["must_escalate"] = True
        results.append(must_escalate(run))

    expected_tool = expectations.get("must_call") or expectations.get("expected_tool")
    if expected_tool:
        run.metadata["expected_tool"] = expected_tool
        results.append(tool_call_correctness(run))

    return results

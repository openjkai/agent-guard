"""Sandbox tests."""

import pytest

from agentguard.errors import ToolPolicyViolation, ToolValidationError
from agentguard.sandbox.builtin import FailureMode, build_default_toolbox


def test_issue_refund_policy_blocks_over_limit() -> None:
    toolbox = build_default_toolbox({"customer_id": "C-1"})
    with pytest.raises(ToolPolicyViolation):
        toolbox.call(
            "issue_refund",
            {"customer_id": "C-1", "order_id": "1", "amount": 700},
        )


def test_tool_validation_error() -> None:
    toolbox = build_default_toolbox()
    with pytest.raises(ToolValidationError):
        toolbox.call("issue_refund", {"amount": 10})


def test_failure_mode_timeout() -> None:
    toolbox = build_default_toolbox()
    toolbox.set_failure_mode("issue_refund", FailureMode.TIMEOUT)
    with pytest.raises(TimeoutError):
        toolbox.call(
            "issue_refund",
            {"customer_id": "C-1", "order_id": "1", "amount": 10},
        )

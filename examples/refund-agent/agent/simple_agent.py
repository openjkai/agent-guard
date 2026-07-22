"""Plain-Python refund agent using shared core logic."""

from __future__ import annotations

from typing import Any

from agentguard.adapters.model_proxy import ModelProxy
from agentguard.sandbox.tool import ToolBox
from agentguard.tracing.context import RunContext

from refund_core import process_refund_request


def agent(
    user_messages: list[str],
    toolbox: ToolBox,
    trace: RunContext,
    model: ModelProxy,
    fixtures: dict[str, Any],
) -> str:
    return process_refund_request(user_messages, toolbox, trace, model, fixtures)

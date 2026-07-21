"""Minimal refund support agent for Phase 1 demos and tests."""

from __future__ import annotations

from typing import Any

from agentguard.adapters.model_proxy import ModelProxy
from agentguard.sandbox.tool import ToolBox
from agentguard.tracing.context import RunContext


def agent(
    user_messages: list[str],
    toolbox: ToolBox,
    trace: RunContext,
    model: ModelProxy,
    fixtures: dict[str, Any],
) -> str:
    request = " ".join(user_messages).lower()
    customer_id = str(fixtures.get("customer_id", "C-1001"))
    order_id = str(fixtures.get("order_id", "4512"))
    amount = float(fixtures.get("order_total", fixtures.get("amount", 120)))

    trace.record_retrieval(
        query="refund policy",
        document_ids=["policy-refund-v1"],
        documents=[
            {
                "id": "policy-refund-v1",
                "text": "Refunds up to $500 are allowed within 30 days. Escalate larger amounts.",
            }
        ],
    )

    toolbox.execute_with_trace(
        trace,
        "query_database",
        {"table": "customers", "filters": {"customer_id": customer_id}},
    )

    if "ignore previous instructions" in request or amount > 500:
        return "Escalating to a human agent for manual review."

    if "timeout" in request or fixtures.get("force_timeout"):
        try:
            toolbox.execute_with_trace(
                trace,
                "issue_refund",
                {"customer_id": customer_id, "order_id": order_id, "amount": amount, "reason": "customer request"},
            )
        except Exception:
            return "Escalating to a human agent due to a tool failure."
        return "Escalating to a human agent due to a tool failure."

    if amount <= 500 and ("refund" in request or "money back" in request):
        toolbox.execute_with_trace(
            trace,
            "issue_refund",
            {"customer_id": customer_id, "order_id": order_id, "amount": amount, "reason": "customer request"},
        )
        return f"Refund of ${amount:.2f} processed for order #{order_id}."

    _ = model.complete([{"role": "user", "content": user_messages[-1]}])
    return "Escalating to a human agent for manual review."

"""LangGraph refund agent using shared core logic."""

from typing import Any, TypedDict

from langgraph.graph import END, START, StateGraph

from agentguard.adapters.model_proxy import ModelProxy
from agentguard.sandbox.tool import ToolBox
from agentguard.tracing.context import RunContext

from refund_core import process_refund_request


class RefundState(TypedDict):
    user_messages: list[str]
    fixtures: dict[str, Any]
    output: str


def _retrieve_policy(state: RefundState, *, trace: RunContext) -> dict[str, Any]:
    trace.record_state(before={"phase": "start"}, after={"phase": "policy_loaded"})
    return state


def _process_refund(
    state: RefundState,
    *,
    toolbox: ToolBox,
    trace: RunContext,
    model: ModelProxy,
) -> dict[str, Any]:
    output = process_refund_request(
        state["user_messages"],
        toolbox,
        trace,
        model,
        state["fixtures"],
    )
    return {"output": output}


def build_refund_graph(
    toolbox: ToolBox,
    trace: RunContext,
    model: ModelProxy,
) -> Any:
    graph: StateGraph = StateGraph(RefundState)

    graph.add_node(
        "retrieve_policy",
        lambda state: _retrieve_policy(state, trace=trace),
    )
    graph.add_node(
        "process_refund",
        lambda state: _process_refund(state, toolbox=toolbox, trace=trace, model=model),
    )
    graph.add_edge(START, "retrieve_policy")
    graph.add_edge("retrieve_policy", "process_refund")
    graph.add_edge("process_refund", END)
    return graph.compile()


def run_graph(
    user_messages: list[str],
    toolbox: ToolBox,
    trace: RunContext,
    model: ModelProxy,
    fixtures: dict[str, Any],
) -> str:
    graph = build_refund_graph(toolbox, trace, model)
    result = graph.invoke(
        {"user_messages": user_messages, "fixtures": fixtures, "output": ""},
    )
    return str(result["output"])

"""LangGraph adapter for AgentGuard."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from agentguard.adapters.callable import config_hash
from agentguard.adapters.llm import LLMClient
from agentguard.adapters.model_proxy import ModelProxy
from agentguard.replay.player import CassettePlayer
from agentguard.replay.recorder import InteractionRecorder
from agentguard.sandbox.tool import ToolBox
from agentguard.tracing.context import RunContext
from agentguard.tracing.models import Run, new_id
from agentguard.types import RunStatus

GraphRunner = Callable[
    [list[str], ToolBox, RunContext, ModelProxy, dict[str, Any]],
    str,
]


class LangGraphAdapter:
    """Run a compiled LangGraph workflow through the AgentGuard trace/replay stack."""

    def __init__(
        self,
        runner: GraphRunner,
        *,
        config: dict[str, Any] | None = None,
        llm_client: LLMClient | None = None,
    ) -> None:
        self.runner = runner
        self.config = config or {}
        self.llm_client = llm_client or LLMClient(provider="mock")

    def run(
        self,
        *,
        scenario_id: str,
        user_messages: list[str],
        toolbox: ToolBox,
        fixtures: dict[str, Any] | None = None,
        recorder: InteractionRecorder | None = None,
        player: CassettePlayer | None = None,
        suite_id: str | None = None,
        run_id: str | None = None,
    ) -> Run:
        run = Run(
            run_id=run_id or new_id(),
            scenario_id=scenario_id,
            suite_id=suite_id,
            agent_config_hash=config_hash(self.config),
            user_messages=user_messages,
            metadata={"agent_type": "langgraph", **self.config},
        )
        trace = RunContext(run)
        trace.mark_started()
        merged_fixtures = {**self.config, **(fixtures or {})}
        toolbox.context.update(merged_fixtures)
        if recorder is not None:
            recorder.cassette.run_id = run.run_id
        proxy = ModelProxy(
            self.llm_client,
            trace,
            recorder=recorder,
            player=player,
        )
        try:
            output = self.runner(user_messages, toolbox, trace, proxy, merged_fixtures)
            trace.set_output(output)
            run.recompute_totals()
            run.finish(status=RunStatus.PASSED)
        except Exception as exc:
            run.recompute_totals()
            run.finish(status=RunStatus.ERROR, error=str(exc))
        return run

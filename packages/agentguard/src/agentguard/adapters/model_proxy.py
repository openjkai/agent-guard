"""Intercept LLM calls for tracing, costing, and replay."""

from __future__ import annotations

from typing import Any

from agentguard.adapters.cost import estimate_cost
from agentguard.adapters.llm import LLMClient
from agentguard.replay.player import CassettePlayer
from agentguard.replay.recorder import InteractionRecorder
from agentguard.tracing.context import RunContext
from agentguard.tracing.models import Usage


class ModelProxy:
    def __init__(
        self,
        client: LLMClient,
        trace: RunContext,
        recorder: InteractionRecorder | None = None,
        player: CassettePlayer | None = None,
    ) -> None:
        self.client = client
        self.trace = trace
        self.recorder = recorder
        self.player = player

    def complete(self, messages: list[dict[str, Any]], **kwargs: Any) -> str:
        request = {"messages": messages, "model": self.client.model, **kwargs}
        response_data: dict[str, Any]

        if self.player is not None:
            recorded = self.player.get_llm_response(request)
            if recorded is not None:
                response_data = recorded
            else:
                response_data = self.client.complete(messages, **kwargs)
                if self.recorder is not None:
                    self.recorder.record_llm(request, response_data)
        else:
            response_data = self.client.complete(messages, **kwargs)
            if self.recorder is not None:
                self.recorder.record_llm(request, response_data)

        usage_raw = response_data.get("usage", {})
        usage = Usage(
            input_tokens=int(usage_raw.get("prompt_tokens", 0)),
            output_tokens=int(usage_raw.get("completion_tokens", 0)),
        )
        cost = estimate_cost(str(response_data.get("model", self.client.model)), usage)
        self.trace.record_llm(
            request=request,
            response=response_data,
            usage=usage,
            cost=cost,
            metadata={
                "gen_ai.system": self.client.provider,
                "gen_ai.request.model": self.client.model,
            },
        )
        return str(response_data.get("content", ""))

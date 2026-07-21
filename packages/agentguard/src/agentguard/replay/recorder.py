"""Record nondeterministic interactions during live runs."""

from __future__ import annotations

from typing import Any

from agentguard.replay.cassette import Cassette
from agentguard.types import InteractionKind


class InteractionRecorder:
    def __init__(self, run_id: str) -> None:
        self.cassette = Cassette(run_id=run_id)

    def record_llm(self, request: dict[str, Any], response: dict[str, Any]) -> None:
        self.cassette.add(InteractionKind.LLM, request, response)

    def record_tool(self, request: dict[str, Any], response: dict[str, Any]) -> None:
        self.cassette.add(InteractionKind.TOOL, request, response)

    def record_retrieval(
        self, request: dict[str, Any], response: dict[str, Any]
    ) -> None:
        self.cassette.add(InteractionKind.RETRIEVAL, request, response)

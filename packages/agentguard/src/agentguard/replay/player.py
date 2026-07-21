"""Replay recorded interactions for deterministic debugging."""

from __future__ import annotations

from typing import Any

from agentguard.errors import CassetteMatchError
from agentguard.replay.cassette import Cassette
from agentguard.types import InteractionKind


class CassettePlayer:
    def __init__(self, cassette: Cassette, *, live_llm: bool = False) -> None:
        self.cassette = cassette
        self.live_llm = live_llm

    def get_llm_response(self, request: dict[str, Any]) -> dict[str, Any] | None:
        if self.live_llm:
            return None
        return self._lookup(InteractionKind.LLM, request)

    def get_tool_response(self, request: dict[str, Any]) -> dict[str, Any]:
        response = self._lookup(InteractionKind.TOOL, request)
        if response is None:
            raise CassetteMatchError(f"No recorded tool interaction for {request}")
        return response

    def get_retrieval_response(self, request: dict[str, Any]) -> dict[str, Any]:
        response = self._lookup(InteractionKind.RETRIEVAL, request)
        if response is None:
            raise CassetteMatchError(f"No recorded retrieval interaction for {request}")
        return response

    def _lookup(
        self, kind: InteractionKind, request: dict[str, Any]
    ) -> dict[str, Any] | None:
        match = self.cassette.find(kind, request)
        return match.response if match else None

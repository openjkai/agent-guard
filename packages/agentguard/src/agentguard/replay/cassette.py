"""Deterministic replay via interaction cassettes."""

from __future__ import annotations

import hashlib
import json
from typing import Any

from pydantic import BaseModel, Field

from agentguard.types import InteractionKind


def interaction_hash(kind: InteractionKind, payload: dict[str, Any]) -> str:
    canonical = json.dumps(
        {"kind": kind.value, "payload": payload}, sort_keys=True, default=str
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


class RecordedInteraction(BaseModel):
    kind: InteractionKind
    request: dict[str, Any]
    response: dict[str, Any]
    request_hash: str
    sequence: int


class Cassette(BaseModel):
    run_id: str
    interactions: list[RecordedInteraction] = Field(default_factory=list)

    def add(
        self, kind: InteractionKind, request: dict[str, Any], response: dict[str, Any]
    ) -> None:
        self.interactions.append(
            RecordedInteraction(
                kind=kind,
                request=request,
                response=response,
                request_hash=interaction_hash(kind, request),
                sequence=len(self.interactions),
            )
        )

    def find(
        self, kind: InteractionKind, request: dict[str, Any]
    ) -> RecordedInteraction | None:
        target = interaction_hash(kind, request)
        for item in self.interactions:
            if item.kind == kind and item.request_hash == target:
                return item
        for item in self.interactions:
            if item.kind == kind and item.request.get("tool_name") == request.get(
                "tool_name"
            ):
                return item
        return None

"""Shared type aliases and enums."""

from __future__ import annotations

from enum import Enum
from typing import Literal

ReleaseDecision = Literal["SHIP", "SHIP_WITH_WARNING", "REQUIRE_HUMAN_REVIEW", "BLOCK"]
Severity = Literal["info", "warning", "major", "critical"]


class StepType(str, Enum):
    LLM = "llm"
    TOOL = "tool"
    RETRIEVAL = "retrieval"
    STATE = "state"


class RunStatus(str, Enum):
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    ERROR = "error"


class InteractionKind(str, Enum):
    LLM = "llm"
    TOOL = "tool"
    RETRIEVAL = "retrieval"

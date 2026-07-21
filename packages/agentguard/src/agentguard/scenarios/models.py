"""Scenario schema and loader."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field

from agentguard.errors import ScenarioLoadError


class ScenarioExpectations(BaseModel):
    must_not_call: list[str] = Field(default_factory=list)
    must_call: str | None = None
    must_escalate: bool = False
    expected_output: str | None = None
    expected_contains: str | None = None
    expected_document_ids: list[str] = Field(default_factory=list)
    max_steps: int | None = None
    max_cost_usd: float | None = None
    max_latency_ms: float | None = None


class Scenario(BaseModel):
    id: str
    tags: list[str] = Field(default_factory=list)
    user_messages: list[str]
    fixtures: dict[str, Any] = Field(default_factory=dict)
    tool_overrides: dict[str, Any] = Field(default_factory=dict)
    expectations: ScenarioExpectations = Field(default_factory=ScenarioExpectations)
    evaluators: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class AgentConfig(BaseModel):
    provider: str = "mock"
    model: str = "mock-model"
    api_key_env: str | None = None
    base_url: str | None = None
    config: dict[str, Any] = Field(default_factory=dict)


class GatePolicy(BaseModel):
    block_if: list[str] = Field(
        default_factory=lambda: ["any_critical_failure", "pass_rate < 0.85"]
    )
    require_review_if: list[str] = Field(
        default_factory=lambda: ["pass_rate < 0.95", "any_major_failure"]
    )
    warn_if: list[str] = Field(
        default_factory=lambda: ["p95_latency_ms > 4000", "avg_cost_usd > 0.05"]
    )


class ProjectConfig(BaseModel):
    agent: AgentConfig = Field(default_factory=AgentConfig)
    gate: GatePolicy = Field(default_factory=GatePolicy)
    concurrency: int = 4
    storage_dir: str = ".agentguard"


def load_scenario(path: Path) -> Scenario:
    try:
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
        return Scenario.model_validate(raw)
    except Exception as exc:
        raise ScenarioLoadError(f"Failed to load scenario {path}: {exc}") from exc


def load_scenarios(path: Path) -> list[Scenario]:
    if path.is_file():
        return [load_scenario(path)]
    scenarios: list[Scenario] = []
    for file in sorted(path.glob("*.yaml")) + sorted(path.glob("*.yml")):
        scenarios.append(load_scenario(file))
    return scenarios


def load_project_config(path: Path) -> ProjectConfig:
    raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return ProjectConfig.model_validate(raw)

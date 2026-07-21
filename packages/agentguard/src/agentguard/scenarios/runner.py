"""Scenario execution engine."""

from __future__ import annotations

import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field

from agentguard.adapters.callable import AgentFn, CallableAgent, config_hash
from agentguard.adapters.llm import LLMClient
from agentguard.evaluators.builtin import apply_expectations
from agentguard.evaluators.registry import GLOBAL_REGISTRY
from agentguard.evaluators.result import EvalResult
from agentguard.replay.recorder import InteractionRecorder
from agentguard.sandbox.builtin import FailureMode, build_default_toolbox
from agentguard.scenarios.models import AgentConfig, ProjectConfig, Scenario
from agentguard.storage import FileStore
from agentguard.tracing.models import Run
from agentguard.types import RunStatus


class EvaluatedRun(BaseModel):
    run: Run
    eval_results: list[EvalResult] = Field(default_factory=list)

    @property
    def passed(self) -> bool:
        return all(result.passed for result in self.eval_results)


class SuiteResult(BaseModel):
    suite_id: str
    started_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    finished_at: datetime | None = None
    agent_config_hash: str = ""
    runs: list[EvaluatedRun] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @property
    def pass_rate(self) -> float:
        if not self.runs:
            return 0.0
        return sum(1 for item in self.runs if item.passed) / len(self.runs)

    @property
    def avg_cost_usd(self) -> float:
        if not self.runs:
            return 0.0
        return sum(item.run.cost.total_usd for item in self.runs) / len(self.runs)

    @property
    def avg_latency_ms(self) -> float:
        if not self.runs:
            return 0.0
        return sum(item.run.latency_ms for item in self.runs) / len(self.runs)

    @property
    def p95_latency_ms(self) -> float:
        if not self.runs:
            return 0.0
        values = sorted(item.run.latency_ms for item in self.runs)
        index = max(0, int(len(values) * 0.95) - 1)
        return values[index]

    def critical_failures(self) -> list[EvalResult]:
        failures: list[EvalResult] = []
        for item in self.runs:
            for result in item.eval_results:
                if not result.passed and result.severity == "critical":
                    failures.append(result)
        return failures


def _build_llm_client(agent: AgentConfig) -> LLMClient:
    api_key = os.getenv(agent.api_key_env) if agent.api_key_env else None
    return LLMClient(
        provider=agent.provider,  # type: ignore[arg-type]
        model=agent.model,
        api_key=api_key,
        base_url=agent.base_url,
    )


def _apply_tool_overrides(toolbox: Any, scenario: Scenario) -> None:
    for tool_name, override in scenario.tool_overrides.items():
        mode = override.get("mode")
        if mode == "record_only":
            toolbox.record_only.add(tool_name)
        failure = override.get("failure")
        if failure:
            toolbox.set_failure_mode(tool_name, FailureMode(str(failure)))


def _metadata_from_scenario(scenario: Scenario) -> dict[str, Any]:
    metadata = dict(scenario.metadata)
    expectations = scenario.expectations
    if expectations.expected_output:
        metadata["expected_output"] = expectations.expected_output
    if expectations.expected_contains:
        metadata["expected_contains"] = expectations.expected_contains
    if expectations.expected_document_ids:
        metadata["expected_document_ids"] = expectations.expected_document_ids
    if expectations.max_steps is not None:
        metadata["max_steps"] = expectations.max_steps
    if expectations.max_cost_usd is not None:
        metadata["max_cost_usd"] = expectations.max_cost_usd
    if expectations.max_latency_ms is not None:
        metadata["max_latency_ms"] = expectations.max_latency_ms
    if expectations.must_escalate:
        metadata["must_escalate"] = True
    return metadata


class ScenarioRunner:
    def __init__(
        self,
        agent_fn: AgentFn,
        project: ProjectConfig,
        store: FileStore | None = None,
    ) -> None:
        self.agent_fn = agent_fn
        self.project = project
        self.store = store or FileStore(project.storage_dir)
        self.agent = CallableAgent(
            agent_fn,
            config={
                "provider": project.agent.provider,
                "model": project.agent.model,
                **project.agent.config,
            },
            llm_client=_build_llm_client(project.agent),
        )

    def run_scenario(
        self, scenario: Scenario, *, suite_id: str | None = None
    ) -> EvaluatedRun:
        toolbox = build_default_toolbox(scenario.fixtures)
        _apply_tool_overrides(toolbox, scenario)
        run_id = str(uuid4())
        recorder = InteractionRecorder(run_id=run_id)
        run = self.agent.run(
            scenario_id=scenario.id,
            user_messages=scenario.user_messages,
            toolbox=toolbox,
            fixtures=scenario.fixtures,
            recorder=recorder,
            suite_id=suite_id,
            run_id=run_id,
        )
        run.metadata.update(_metadata_from_scenario(scenario))
        eval_results = apply_expectations(
            run, scenario.expectations.model_dump(exclude_none=True)
        )
        if scenario.evaluators:
            eval_results.extend(GLOBAL_REGISTRY.run(run, scenario.evaluators))
        passed = all(result.passed for result in eval_results)
        run.status = RunStatus.PASSED if passed else RunStatus.FAILED
        self.store.save_model(run.run_id, "run.json", run)
        self.store.save_model(run.run_id, "cassette.json", recorder.cassette)
        self.store.save_json(
            run.run_id,
            "evaluations.json",
            {"results": [result.model_dump() for result in eval_results]},
        )
        return EvaluatedRun(run=run, eval_results=eval_results)

    def run_suite(
        self, scenarios: list[Scenario], *, suite_id: str | None = None
    ) -> SuiteResult:
        suite = SuiteResult(
            suite_id=suite_id or str(uuid4()),
            agent_config_hash=config_hash(self.project.agent.model_dump()),
        )
        concurrency = max(1, self.project.concurrency)
        if concurrency == 1 or len(scenarios) == 1:
            for scenario in scenarios:
                suite.runs.append(self.run_scenario(scenario, suite_id=suite.suite_id))
        else:
            with ThreadPoolExecutor(max_workers=concurrency) as executor:
                futures = {
                    executor.submit(
                        self.run_scenario, scenario, suite_id=suite.suite_id
                    ): scenario
                    for scenario in scenarios
                }
                for future in as_completed(futures):
                    suite.runs.append(future.result())
            suite.runs.sort(key=lambda item: item.run.scenario_id)
        suite.finished_at = datetime.now(timezone.utc)
        self.store.save_model(suite.suite_id, "suite.json", suite)
        return suite

"""Suite execution and persistence."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from typing import Any

from app.config import Settings
from app.db.models import Project, RunRecord, SuiteRun, utcnow
from app.services.progress import ProgressPublisher
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from agentguard.gate.engine import evaluate_gate
from agentguard.scenarios.models import ProjectConfig, load_scenarios
from agentguard.scenarios.runner import ScenarioRunner, SuiteResult
from agentguard.storage import FileStore


def load_agent_from_path(path: Path) -> Any:
    agent_dir = str(path.resolve().parent)
    if agent_dir not in sys.path:
        sys.path.insert(0, agent_dir)
    spec = importlib.util.spec_from_file_location("agentguard_server_agent", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not import agent module: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    if not hasattr(module, "agent"):
        raise RuntimeError("Agent module must define `agent` callable")
    return module.agent


def resolve_repo_path(settings: Settings, relative_path: str) -> Path:
    return (Path(settings.repo_root) / relative_path).resolve()


class SuiteService:
    def __init__(self, session: AsyncSession, settings: Settings) -> None:
        self.session = session
        self.settings = settings
        self.progress = ProgressPublisher(settings)

    async def get_project(self, project_id: str) -> Project | None:
        return await self.session.get(Project, project_id)

    async def create_suite(self, project: Project) -> SuiteRun:
        scenarios_path = resolve_repo_path(self.settings, project.scenarios_path)
        scenarios = load_scenarios(scenarios_path)
        suite = SuiteRun(
            project_id=project.id,
            status="pending",
            progress_total=len(scenarios),
        )
        self.session.add(suite)
        await self.session.commit()
        await self.session.refresh(suite)
        return suite

    async def mark_running(self, suite_id: str, task_id: str | None = None) -> None:
        suite = await self.session.get(SuiteRun, suite_id)
        if suite is None:
            return
        suite.status = "running"
        suite.celery_task_id = task_id
        await self.session.commit()
        self.progress.publish(
            suite_id,
            {
                "suite_id": suite_id,
                "status": "running",
                "completed": suite.progress_completed,
                "total": suite.progress_total,
                "message": "Suite started",
            },
        )

    async def persist_suite_result(
        self,
        suite_id: str,
        suite_result: SuiteResult,
        gate_report: dict[str, Any],
    ) -> None:
        db_suite = await self.session.get(SuiteRun, suite_id)
        if db_suite is None:
            return
        db_suite.status = "completed"
        db_suite.pass_rate = suite_result.pass_rate
        db_suite.release_decision = gate_report.get("decision")
        db_suite.result_json = suite_result.model_dump(mode="json")
        db_suite.gate_report_json = gate_report
        db_suite.progress_completed = len(suite_result.runs)
        db_suite.finished_at = utcnow()

        for evaluated in suite_result.runs:
            run = evaluated.run
            record = RunRecord(
                id=run.run_id,
                suite_id=suite_id,
                scenario_id=run.scenario_id,
                status=run.status.value,
                agent_output=run.agent_output,
                trace_json=run.model_dump(mode="json"),
                evaluations_json={
                    "results": [item.model_dump() for item in evaluated.eval_results]
                },
                passed=evaluated.passed,
                latency_ms=run.latency_ms,
                cost_usd=run.cost.total_usd,
            )
            self.session.add(record)

        await self.session.commit()
        self.progress.publish(
            suite_id,
            {
                "suite_id": suite_id,
                "status": "completed",
                "completed": len(suite_result.runs),
                "total": len(suite_result.runs),
                "message": f"Release decision: {gate_report.get('decision')}",
            },
        )

    async def mark_failed(self, suite_id: str, error: str) -> None:
        suite = await self.session.get(SuiteRun, suite_id)
        if suite is None:
            return
        suite.status = "failed"
        suite.error = error
        suite.finished_at = utcnow()
        await self.session.commit()
        self.progress.publish(
            suite_id,
            {
                "suite_id": suite_id,
                "status": "failed",
                "completed": suite.progress_completed,
                "total": suite.progress_total,
                "message": error,
            },
        )

    async def update_progress(
        self, suite_id: str, completed: int, total: int, scenario_id: str
    ) -> None:
        suite = await self.session.get(SuiteRun, suite_id)
        if suite is None:
            return
        suite.progress_completed = completed
        suite.progress_total = total
        await self.session.commit()
        self.progress.publish(
            suite_id,
            {
                "suite_id": suite_id,
                "status": "running",
                "completed": completed,
                "total": total,
                "scenario_id": scenario_id,
                "message": f"Completed {scenario_id}",
            },
        )

    def execute_suite_sync(
        self, project: Project, suite_id: str
    ) -> tuple[SuiteResult, dict[str, Any]]:
        scenarios_path = resolve_repo_path(self.settings, project.scenarios_path)
        agent_path = resolve_repo_path(self.settings, project.agent_module_path)
        scenarios = load_scenarios(scenarios_path)
        agent_fn = load_agent_from_path(agent_path)

        project_config = ProjectConfig.model_validate(project.config_json)
        artifacts = Path(self.settings.artifacts_dir) / suite_id
        store = FileStore(artifacts)
        project_config.storage_dir = str(artifacts)

        runner = ScenarioRunner(agent_fn, project_config, store=store)

        def _progress(completed: int, total: int, scenario_id: str) -> None:
            self.progress.publish(
                suite_id,
                {
                    "suite_id": suite_id,
                    "status": "running",
                    "completed": completed,
                    "total": total,
                    "scenario_id": scenario_id,
                    "message": f"Completed {scenario_id}",
                },
            )

        suite_result = runner.run_suite(
            scenarios,
            suite_id=suite_id,
            progress_callback=_progress,
        )
        gate = evaluate_gate(suite_result, project_config.gate)
        return suite_result, gate.model_dump(mode="json")

    async def list_suites(self, project_id: str) -> list[SuiteRun]:
        result = await self.session.scalars(
            select(SuiteRun)
            .where(SuiteRun.project_id == project_id)
            .order_by(SuiteRun.created_at.desc())
        )
        return list(result.all())

    async def get_suite(self, suite_id: str) -> SuiteRun | None:
        return await self.session.get(SuiteRun, suite_id)

    async def list_runs(self, suite_id: str) -> list[RunRecord]:
        result = await self.session.scalars(
            select(RunRecord).where(RunRecord.suite_id == suite_id).order_by(RunRecord.created_at)
        )
        return list(result.all())

    async def get_run(self, run_id: str) -> RunRecord | None:
        return await self.session.get(RunRecord, run_id)

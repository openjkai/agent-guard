"""LangGraph adapter tests."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

pytest.importorskip("langgraph")

from agentguard.scenarios.models import ProjectConfig
from agentguard.scenarios.runner import ScenarioRunner
from agentguard.storage import FileStore

ROOT = Path(__file__).resolve().parents[3]
EXAMPLE = ROOT / "examples" / "refund-agent"


def _load_run_graph():
    agent_dir = str(EXAMPLE / "agent")
    if agent_dir not in sys.path:
        sys.path.insert(0, agent_dir)
    spec = importlib.util.spec_from_file_location(
        "langgraph_agent",
        EXAMPLE / "agent" / "langgraph_agent.py",
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.run_graph


def test_langgraph_adapter_runs_happy_path(tmp_path: Path) -> None:
    from agentguard.scenarios.models import Scenario, ScenarioExpectations

    project = ProjectConfig()
    project.storage_dir = str(tmp_path)
    project.agent.config = {"prompt_version": "v2"}
    scenario = Scenario(
        id="lg-happy",
        user_messages=["Please refund $80 for order #1001."],
        fixtures={"customer_id": "C-1001", "order_id": "1001", "order_total": 80},
        expectations=ScenarioExpectations(must_call="issue_refund"),
        evaluators=["refund_limit"],
    )
    runner = ScenarioRunner(
        project=project,
        store=FileStore(project.storage_dir),
        langgraph_runner=_load_run_graph(),
    )
    evaluated = runner.run_scenario(scenario)
    assert evaluated.passed is True
    assert evaluated.run.metadata["agent_type"] == "langgraph"
    assert "Refund" in (evaluated.run.agent_output or "")

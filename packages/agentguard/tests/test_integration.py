"""Phase 1 integration tests."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

from agentguard.gate.engine import evaluate_gate
from agentguard.scenarios.models import load_project_config, load_scenarios
from agentguard.scenarios.runner import ScenarioRunner
from agentguard.storage import FileStore

ROOT = Path(__file__).resolve().parents[3]
EXAMPLE = ROOT / "examples" / "refund-agent"


def _load_agent() -> object:
    agent_dir = str(EXAMPLE / "agent")
    if agent_dir not in sys.path:
        sys.path.insert(0, agent_dir)
    spec = importlib.util.spec_from_file_location(
        "simple_agent",
        EXAMPLE / "agent" / "simple_agent.py",
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.agent


def test_refund_suite_runs_offline(tmp_path: Path) -> None:
    project = load_project_config(EXAMPLE / "benchmarks" / "prompt-v2-mock.yaml")
    project.storage_dir = str(tmp_path / ".agentguard")
    scenarios = load_scenarios(EXAMPLE / "scenarios")
    runner = ScenarioRunner(
        _load_agent(), project, store=FileStore(project.storage_dir)
    )
    suite = runner.run_suite(scenarios)
    assert len(suite.runs) >= 4
    assert suite.pass_rate >= 0.5
    report = evaluate_gate(suite, project.gate)
    assert report.decision in {
        "BLOCK",
        "REQUIRE_HUMAN_REVIEW",
        "SHIP_WITH_WARNING",
        "SHIP",
    }

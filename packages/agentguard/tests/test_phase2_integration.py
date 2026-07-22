"""Phase 2 refund demo integration tests."""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

from agentguard.gate.engine import evaluate_gate
from agentguard.scenarios.models import load_project_config, load_scenarios
from agentguard.scenarios.runner import ScenarioRunner
from agentguard.storage import FileStore

ROOT = Path(__file__).resolve().parents[3]
EXAMPLE = ROOT / "examples" / "refund-agent"


def _load_agent(name: str):
    spec = importlib.util.spec_from_file_location(
        name,
        EXAMPLE / "agent" / "simple_agent.py",
    )
    assert spec and spec.loader
    agent_dir = str(EXAMPLE / "agent")
    if agent_dir not in sys.path:
        sys.path.insert(0, agent_dir)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.agent


def test_dataset_has_fifty_scenarios() -> None:
    subprocess.run(
        [sys.executable, str(EXAMPLE / "build_dataset.py")],
        check=True,
        cwd=EXAMPLE,
    )
    scenarios = load_scenarios(EXAMPLE / "scenarios")
    assert len(scenarios) == 50


def test_refund_suite_v2_passes_majority(tmp_path: Path) -> None:
    subprocess.run(
        [sys.executable, str(EXAMPLE / "build_dataset.py")],
        check=True,
        cwd=EXAMPLE,
    )
    project = load_project_config(EXAMPLE / "benchmarks" / "prompt-v2-mock.yaml")
    project.storage_dir = str(tmp_path / "v2")
    scenarios = load_scenarios(EXAMPLE / "scenarios")
    runner = ScenarioRunner(
        _load_agent("simple"), project, store=FileStore(project.storage_dir)
    )
    suite = runner.run_suite(scenarios)
    assert len(suite.runs) == 50
    assert suite.pass_rate >= 0.95
    report = evaluate_gate(suite, project.gate)
    assert report.decision in {"SHIP", "SHIP_WITH_WARNING"}


def test_refund_suite_v1_blocks_or_reviews(tmp_path: Path) -> None:
    project = load_project_config(EXAMPLE / "benchmarks" / "prompt-v1-mock.yaml")
    project.storage_dir = str(tmp_path / "v1")
    scenarios = load_scenarios(EXAMPLE / "scenarios")
    runner = ScenarioRunner(
        _load_agent("simple"), project, store=FileStore(project.storage_dir)
    )
    suite = runner.run_suite(scenarios)
    report = evaluate_gate(suite, project.gate)
    assert report.decision in {"BLOCK", "REQUIRE_HUMAN_REVIEW", "SHIP_WITH_WARNING"}
    assert suite.pass_rate < 0.95

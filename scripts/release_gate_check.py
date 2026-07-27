#!/usr/bin/env python3
"""Run a scenario suite and exit with the AgentGuard release-gate code (for CI)."""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path

from agentguard.gate.engine import evaluate_gate
from agentguard.gate.models import DECISION_EXIT_CODES
from agentguard.scenarios.models import load_project_config, load_scenarios
from agentguard.scenarios.runner import ScenarioRunner
from agentguard.storage import FileStore


def _load_agent(path: Path):
    agent_dir = str(path.resolve().parent)
    if agent_dir not in sys.path:
        sys.path.insert(0, agent_dir)
    spec = importlib.util.spec_from_file_location("agentguard_ci_agent", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not import agent module: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    if not hasattr(module, "agent"):
        raise RuntimeError("Agent module must define `agent` callable")
    return module.agent


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True, help="Project config YAML")
    parser.add_argument("--suite", type=Path, required=True, help="Scenario file or directory")
    parser.add_argument("--agent", type=Path, required=True, help="Python file exporting `agent`")
    parser.add_argument(
        "--expect",
        choices=["SHIP", "SHIP_WITH_WARNING", "REQUIRE_HUMAN_REVIEW", "BLOCK"],
        help="Fail if the gate decision does not match this value",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    project = load_project_config(args.config)
    scenarios = load_scenarios(args.suite)
    agent_fn = _load_agent(args.agent)
    store = FileStore(project.storage_dir)
    runner = ScenarioRunner(agent_fn, project, store=store)
    suite = runner.run_suite(scenarios)
    report = evaluate_gate(suite, project.gate)

    print(f"suite_id={suite.suite_id}")
    print(f"pass_rate={suite.pass_rate:.4f}")
    print(f"decision={report.decision}")

    if args.expect and report.decision != args.expect:
        print(
            f"Expected decision {args.expect}, got {report.decision}",
            file=sys.stderr,
        )
        return 1

    return DECISION_EXIT_CODES[str(report.decision)]


if __name__ == "__main__":
    raise SystemExit(main())

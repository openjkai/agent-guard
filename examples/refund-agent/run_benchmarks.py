#!/usr/bin/env python3
"""Run prompt/model benchmark matrix and print comparison table."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

from agentguard.compare.comparator import compare_suites
from agentguard.gate.engine import evaluate_gate
from agentguard.scenarios.models import load_project_config, load_scenarios
from agentguard.scenarios.runner import ScenarioRunner
from agentguard.storage import FileStore

ROOT = Path(__file__).resolve().parent
AGENT = ROOT / "agent" / "simple_agent.py"
SCENARIOS = ROOT / "scenarios"
BENCHMARKS = [
    ROOT / "benchmarks" / "prompt-v1-mock.yaml",
    ROOT / "benchmarks" / "prompt-v2-mock.yaml",
    ROOT / "benchmarks" / "prompt-v1-gpt4o-mini.yaml",
    ROOT / "benchmarks" / "prompt-v2-claude-haiku.yaml",
]


def _load_agent(path: Path):
    agent_dir = str(path.parent)
    if agent_dir not in sys.path:
        sys.path.insert(0, agent_dir)
    spec = importlib.util.spec_from_file_location("benchmark_agent", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.agent


def main() -> None:
    scenarios = load_scenarios(SCENARIOS)
    agent_fn = _load_agent(AGENT)
    results = []

    for config_path in BENCHMARKS:
        project = load_project_config(config_path)
        runner = ScenarioRunner(agent_fn, project, store=FileStore(project.storage_dir))
        suite = runner.run_suite(scenarios)
        gate = evaluate_gate(suite, project.gate)
        results.append((config_path.stem, suite, gate))

    print("\nAgentGuard Refund Agent Benchmarks")
    print("=" * 72)
    print(f"{'Config':<28} {'Pass rate':>10} {'Avg cost':>10} {'Decision':>16}")
    print("-" * 72)
    for name, suite, gate in results:
        print(
            f"{name:<28} {suite.pass_rate * 100:>9.1f}% "
            f"${suite.avg_cost_usd:>8.4f} {gate.decision:>16}"
        )

    baseline_suite = results[0][1]
    candidate_suite = results[1][1]
    comparison = compare_suites(baseline_suite, candidate_suite)
    print("\nPrompt v1 vs v2 (mock model)")
    print(comparison.summary)


if __name__ == "__main__":
    main()

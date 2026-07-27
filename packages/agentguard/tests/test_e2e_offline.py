"""Offline end-to-end tests for release gating (no API keys)."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

from agentguard.gate.models import DECISION_EXIT_CODES
from agentguard.scenarios.models import load_scenarios

ROOT = Path(__file__).resolve().parents[3]
EXAMPLE = ROOT / "examples" / "refund-agent"
SCRIPT = ROOT / "scripts" / "release_gate_check.py"


@pytest.fixture(scope="module", autouse=True)
def _ensure_dataset() -> None:
    subprocess.run(
        [sys.executable, str(EXAMPLE / "build_dataset.py")],
        check=True,
        cwd=EXAMPLE,
    )


def test_seeded_scenarios_present() -> None:
    scenarios = load_scenarios(EXAMPLE / "scenarios")
    seeded = [scenario for scenario in scenarios if scenario.id.startswith("seed-")]
    assert len(scenarios) == 50
    assert len(seeded) == 6


def test_prompt_v1_gate_blocks_via_cli() -> None:
    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--config",
            str(EXAMPLE / "benchmarks" / "prompt-v1-mock.yaml"),
            "--suite",
            str(EXAMPLE / "scenarios"),
            "--agent",
            str(EXAMPLE / "agent" / "simple_agent.py"),
            "--expect",
            "BLOCK",
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    assert result.returncode == DECISION_EXIT_CODES["BLOCK"], (
        result.stderr or result.stdout
    )


def test_prompt_v2_gate_ships_via_cli() -> None:
    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--config",
            str(EXAMPLE / "benchmarks" / "prompt-v2-mock.yaml"),
            "--suite",
            str(EXAMPLE / "scenarios"),
            "--agent",
            str(EXAMPLE / "agent" / "simple_agent.py"),
            "--expect",
            "SHIP",
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    assert result.returncode == DECISION_EXIT_CODES["SHIP"], (
        result.stderr or result.stdout
    )

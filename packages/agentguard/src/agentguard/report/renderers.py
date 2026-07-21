"""Release report generators."""

from __future__ import annotations

import json
from pathlib import Path

from agentguard.gate.models import ReleaseReport
from agentguard.scenarios.runner import SuiteResult


def render_terminal(report: ReleaseReport, suite: SuiteResult) -> str:
    lines = [
        report.summary,
        "",
    ]
    if report.previous_pass_rate is not None:
        lines.append(f"Previous version: {report.previous_pass_rate * 100:.0f}%")
    if report.critical_failures:
        lines.extend(["", "Main regression:", report.critical_failures[0].reason])
    if report.recommended_actions:
        lines.extend(["", "Recommended action:", report.recommended_actions[0]])
    lines.extend(
        [
            "",
            f"Suite: {suite.suite_id}",
            f"Runs: {len(suite.runs)}",
        ]
    )
    return "\n".join(lines)


def render_markdown(report: ReleaseReport, suite: SuiteResult) -> str:
    return "\n".join(
        [
            "# AgentGuard Release Report",
            "",
            f"**Decision:** `{report.decision}`",
            "",
            "## Metrics",
            f"- Pass rate: {report.metrics.pass_rate * 100:.1f}%",
            f"- Avg latency: {report.metrics.avg_latency_ms:.1f} ms",
            f"- Avg cost: ${report.metrics.avg_cost_usd:.4f}",
            f"- Critical failures: {report.metrics.critical_failure_count}",
            "",
            "## Summary",
            report.summary,
            "",
            f"Suite `{suite.suite_id}` with {len(suite.runs)} runs.",
        ]
    )


def render_html(report: ReleaseReport, suite: SuiteResult) -> str:
    return f"""<!doctype html>
<html>
<head><title>AgentGuard Release Report</title></head>
<body>
  <h1>Release decision: {report.decision}</h1>
  <pre>{report.summary}</pre>
  <p>Suite: {suite.suite_id} ({len(suite.runs)} runs)</p>
</body>
</html>
"""


def render_json(report: ReleaseReport, suite: SuiteResult) -> str:
    payload = {
        "report": report.model_dump(),
        "suite": {
            "suite_id": suite.suite_id,
            "pass_rate": suite.pass_rate,
            "run_count": len(suite.runs),
        },
    }
    return json.dumps(payload, indent=2)


def write_report(
    report: ReleaseReport,
    suite: SuiteResult,
    path: Path,
    *,
    format_name: str = "markdown",
) -> Path:
    renderers = {
        "terminal": render_terminal,
        "md": render_markdown,
        "markdown": render_markdown,
        "html": render_html,
        "json": render_json,
    }
    renderer = renderers.get(format_name, render_markdown)
    path.write_text(renderer(report, suite), encoding="utf-8")
    return path

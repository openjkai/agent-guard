"""AgentGuard command-line interface."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated, Optional

import typer
from rich.console import Console
from rich.table import Table

from agentguard import __version__
from agentguard.adapters.callable import AgentFn, CallableAgent
from agentguard.adapters.llm import LLMClient
from agentguard.compare.comparator import compare_suites
from agentguard.gate.engine import evaluate_gate
from agentguard.gate.models import DECISION_EXIT_CODES
from agentguard.replay.diff import diff_runs
from agentguard.replay.player import CassettePlayer
from agentguard.report.renderers import (
    render_html,
    render_json,
    render_markdown,
    render_terminal,
)
from agentguard.scenarios.generator import (
    generate_from_policy,
    generate_from_templates,
    write_scenarios,
)
from agentguard.scenarios.models import load_project_config, load_scenarios
from agentguard.scenarios.runner import ScenarioRunner, SuiteResult
from agentguard.storage import FileStore
from agentguard.tracing.models import Run

app = typer.Typer(
    name="agentguard",
    help="Open-source release gate for AI agents.",
    no_args_is_help=True,
)
console = Console()


def _load_agent_module(path: Path) -> AgentFn:
    import importlib.util

    spec = importlib.util.spec_from_file_location("agentguard_user_agent", path)
    if spec is None or spec.loader is None:
        raise typer.BadParameter(f"Could not import agent module: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    if not hasattr(module, "agent"):
        raise typer.BadParameter("Agent module must define an `agent` callable")
    return module.agent  # type: ignore[no-any-return]


def _load_suite(store: FileStore, suite_id: str) -> SuiteResult:
    return store.load_model(suite_id, "suite.json", SuiteResult)


@app.callback()
def main() -> None:
    """AgentGuard CLI — run scenarios, replay failures, gate releases."""


@app.command()
def version() -> None:
    """Print the installed AgentGuard version."""
    console.print(f"agentguard {__version__}")


@app.command("run")
def run_suite(
    config: Annotated[Path, typer.Option("--config", "-c", help="Project config YAML")],
    suite: Annotated[
        Path, typer.Option("--suite", "-s", help="Scenario file or directory")
    ],
    agent_module: Annotated[
        Path,
        typer.Option("--agent", "-a", help="Python file exporting `agent` callable"),
    ],
) -> None:
    """Run a scenario suite and persist traces."""
    project = load_project_config(config)
    scenarios = load_scenarios(suite)
    agent_fn = _load_agent_module(agent_module)
    runner = ScenarioRunner(agent_fn, project, store=FileStore(project.storage_dir))
    result = runner.run_suite(scenarios)
    console.print(f"Suite complete: {result.suite_id}")
    console.print(f"Pass rate: {result.pass_rate * 100:.1f}% ({len(result.runs)} runs)")


@app.command()
def report(
    suite_id: str,
    format: Annotated[str, typer.Option("--format", "-f")] = "terminal",
    config: Annotated[Optional[Path], typer.Option("--config", "-c")] = None,
    output: Annotated[Optional[Path], typer.Option("--output", "-o")] = None,
) -> None:
    """Render a release report for a suite."""
    storage_dir = ".agentguard"
    policy = None
    if config:
        project = load_project_config(config)
        storage_dir = project.storage_dir
        policy = project.gate
    store = FileStore(storage_dir)
    suite = _load_suite(store, suite_id)
    if policy is None:
        from agentguard.scenarios.models import GatePolicy

        policy = GatePolicy()
    release = evaluate_gate(suite, policy)
    renderers = {
        "terminal": render_terminal,
        "md": render_markdown,
        "markdown": render_markdown,
        "html": render_html,
        "json": render_json,
    }
    renderer = renderers.get(format, render_terminal)
    content = renderer(release, suite)
    if output:
        output.write_text(content, encoding="utf-8")
        console.print(f"Report written to {output}")
    else:
        console.print(content)


@app.command()
def replay(
    run_id: str,
    agent_module: Annotated[Path, typer.Option("--agent", "-a")],
    live_llm: Annotated[
        bool, typer.Option("--live-llm", help="Use live LLM instead of cassette")
    ] = False,
    storage_dir: Annotated[str, typer.Option("--storage")] = ".agentguard",
) -> None:
    """Replay a recorded run using its cassette."""
    store = FileStore(storage_dir)
    run = store.load_model(run_id, "run.json", Run)
    from agentguard.replay.cassette import Cassette

    cassette = store.load_model(run_id, "cassette.json", Cassette)
    player = CassettePlayer(cassette, live_llm=live_llm)
    agent_fn = _load_agent_module(agent_module)
    agent = CallableAgent(agent_fn, llm_client=LLMClient(provider="mock"))
    from agentguard.sandbox.builtin import build_default_toolbox

    toolbox = build_default_toolbox(run.metadata.get("fixtures", {}))
    replayed = agent.run(
        scenario_id=run.scenario_id,
        user_messages=run.user_messages,
        toolbox=toolbox,
        fixtures=run.metadata.get("fixtures", {}),
        player=player,
        suite_id=run.suite_id,
    )
    store.save_model(replayed.run_id, "run.json", replayed)
    console.print(f"Replay complete: {replayed.run_id}")


@app.command()
def diff(
    run_a: str,
    run_b: str,
    storage_dir: Annotated[str, typer.Option("--storage")] = ".agentguard",
) -> None:
    """Diff two runs step-by-step."""
    store = FileStore(storage_dir)
    left = store.load_model(run_a, "run.json", Run)
    right = store.load_model(run_b, "run.json", Run)
    result = diff_runs(left, right)
    table = Table(title="Run Diff")
    table.add_column("Step")
    table.add_column("Changed")
    table.add_column("Fields")
    for step in result.steps:
        table.add_row(
            str(step.index), str(step.changed), ", ".join(step.fields_changed)
        )
    console.print(table)
    console.print(f"Output changed: {result.output_changed}")
    console.print(f"Status changed: {result.status_changed}")


@app.command()
def compare(
    baseline: Annotated[
        Path, typer.Option("--baseline", help="Baseline suite id or suite.json path")
    ],
    candidate: Annotated[
        Path, typer.Option("--candidate", help="Candidate suite id or suite.json path")
    ],
    storage_dir: Annotated[str, typer.Option("--storage")] = ".agentguard",
) -> None:
    """Compare two suite results."""
    store = FileStore(storage_dir)

    def _load(path: Path) -> SuiteResult:
        if path.suffix == ".json":
            return SuiteResult.model_validate_json(path.read_text(encoding="utf-8"))
        return _load_suite(store, path.name)

    baseline_suite = _load(baseline)
    candidate_suite = _load(candidate)
    report = compare_suites(baseline_suite, candidate_suite)
    console.print(report.summary)
    table = Table(title="Metric Comparison")
    table.add_column("Metric")
    table.add_column("Baseline")
    table.add_column("Candidate")
    table.add_column("Delta")
    for metric in report.metrics:
        delta_pct = (
            f"{metric.delta_pct:.1f}%" if metric.delta_pct is not None else "n/a"
        )
        table.add_row(
            metric.name, f"{metric.baseline:.4f}", f"{metric.candidate:.4f}", delta_pct
        )
    console.print(table)


generate_app = typer.Typer(help="Generate synthetic scenarios.")
app.add_typer(generate_app, name="generate")


@generate_app.command("scenarios")
def generate_scenarios(
    output: Annotated[Path, typer.Option("--output", "-o")],
    from_policy: Annotated[Optional[Path], typer.Option("--from-policy")] = None,
    count: Annotated[int, typer.Option("--count", "-n")] = 8,
) -> None:
    """Generate scenario YAML files from templates or a policy document."""
    if from_policy:
        scenarios = generate_from_policy(
            from_policy.read_text(encoding="utf-8"), count=count
        )
    else:
        scenarios = generate_from_templates()
        scenarios = scenarios[:count]
    paths = write_scenarios(scenarios, output)
    console.print(f"Generated {len(paths)} scenarios in {output}")


@app.command()
def gate(
    suite_id: str,
    config: Annotated[Path, typer.Option("--config", "-c")],
    baseline: Annotated[
        Optional[str], typer.Option("--baseline", help="Baseline suite id")
    ] = None,
) -> None:
    """Evaluate release gate policy and exit with decision code."""
    project = load_project_config(config)
    store = FileStore(project.storage_dir)
    suite = _load_suite(store, suite_id)
    baseline_suite = _load_suite(store, baseline) if baseline else None
    report = evaluate_gate(suite, project.gate, baseline=baseline_suite)
    console.print(render_terminal(report, suite))
    raise typer.Exit(code=DECISION_EXIT_CODES[report.decision])


if __name__ == "__main__":
    app()

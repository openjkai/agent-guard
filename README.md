# AgentGuard

**An open-source preflight and reliability platform for AI agents that take real-world actions.**

Run 500 agent scenarios before deployment. Replay failures. Compare prompt and model versions. Block unsafe releases.

## Status

**Phase 1 complete** — engine, SDK, and CLI are working.

**Phase 2 complete** — refund demo with 50 scenarios, LangGraph adapter, and benchmark matrix.

**Phase 3 complete** — FastAPI server, Postgres persistence, Celery workers, SSE progress.

**Phase 4 complete** — Next.js dashboard with suite runs, trace viewer, release report, and compare view.

| Package | Path | Status |
|---------|------|--------|
| SDK + CLI | `packages/agentguard` | Phase 1 complete |
| API server | `packages/server` | Phase 3 complete — FastAPI, Postgres, Celery, SSE |
| Dashboard | `packages/web` | Phase 4 complete — Next.js dashboard |
| Refund demo | `examples/refund-agent` | Phase 2 — 50 scenarios, LangGraph adapter, benchmarks |

## Quick start

### Prerequisites

- Python 3.11+
- [uv](https://docs.astral.sh/uv/) (recommended)
- Node.js 20+ (for web dashboard, Phase 4)

### Setup

```bash
# Clone and enter the repo
cd agent-guard

# Install Python workspace (SDK + server)
make install

# Verify CLI
uv run agentguard version

# Regenerate scenarios and run benchmark matrix
cd examples/refund-agent && python build_dataset.py && python run_benchmarks.py

# Run full suite with improved prompt v2
uv run agentguard run \
  --config examples/refund-agent/benchmarks/prompt-v2-mock.yaml \
  --suite examples/refund-agent/scenarios \
  --agent examples/refund-agent/agent/simple_agent.py

# Gate the release (exit code 30 = BLOCK)
uv run agentguard gate <suite-id> --config examples/refund-agent/agentguard.yaml

# Run tests
make test

# Lint and typecheck
make lint
make typecheck
```

### Docker (Phase 3+)

```bash
# Start Postgres, Redis, API, worker, and dashboard
make docker-up

# API docs: http://localhost:8000/docs
# Dashboard: http://localhost:3000
# Header: X-API-Key: dev-change-me
```

### Dashboard (Phase 4)

```bash
# Terminal 1 — API + dependencies
docker compose up postgres redis api worker

# Terminal 2 — dashboard
cp packages/web/.env.example packages/web/.env.local
make web-dev

# Open http://localhost:3000
```

### API quick start (local)

```bash
# Terminal 1 — Postgres + Redis
docker compose up postgres redis

# Terminal 2 — API
export DATABASE_URL=postgresql+asyncpg://agentguard:agentguard@localhost:5432/agentguard
export REDIS_URL=redis://localhost:6379/0
export AGENTGUARD_API_KEY=dev-change-me
export REPO_ROOT=$PWD
make server-api

# Terminal 3 — Celery worker
cd packages/server && uv run celery -A app.workers.celery_app:celery_app worker --loglevel=info
```

Create a project and run a suite:

```bash
CONFIG_JSON=$(python - <<'PY'
import json, yaml, pathlib
config = yaml.safe_load(pathlib.Path("examples/refund-agent/benchmarks/prompt-v2-mock.yaml").read_text())
print(json.dumps({
    "name": "refund-demo",
    "agent_module_path": "examples/refund-agent/agent/simple_agent.py",
    "scenarios_path": "examples/refund-agent/scenarios",
    "config_json": config,
}))
PY
)

curl -X POST http://localhost:8000/api/v1/projects \
  -H 'Content-Type: application/json' \
  -d "$CONFIG_JSON"
```

## Repository layout

```text
agent-guard/
  packages/
    agentguard/     # Python SDK + CLI (core)
    server/         # FastAPI + Celery workers
    web/            # Next.js dashboard
  examples/
    refund-agent/   # Flagship demo agent
  docs/             # Architecture, coding standards, guides
  docker/           # Dockerfiles
  .cursor/rules/    # AI assistant coding rules
```

See [docs/PLAN.md](docs/PLAN.md) for the full product plan and [docs/architecture.md](docs/architecture.md) for system design.

## Coding standards

All contributors must follow [docs/CODING_STANDARDS.md](docs/CODING_STANDARDS.md). Key principles:

- **Evidence over vibes** — every release decision is backed by traces and evaluators
- **Determinism where it matters** — replay must reproduce failures reliably
- **Framework independence** — core engine works without LangGraph
- **Strict typing** — mypy strict (Python), TypeScript strict (web)
- **Small, reviewable diffs** — one concern per PR

See [CONTRIBUTING.md](CONTRIBUTING.md) for workflow and [AGENTS.md](AGENTS.md) for AI assistant guidance.

## License

MIT — see [LICENSE](LICENSE).

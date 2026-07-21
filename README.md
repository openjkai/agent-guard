# AgentGuard

**An open-source preflight and reliability platform for AI agents that take real-world actions.**

Run 500 agent scenarios before deployment. Replay failures. Compare prompt and model versions. Block unsafe releases.

## Status

**Phase 1 complete** — engine, SDK, and CLI are working.

| Package | Path | Status |
|---------|------|--------|
| SDK + CLI | `packages/agentguard` | Phase 1 complete |
| API server | `packages/server` | Scaffolded (Phase 3) |
| Dashboard | `packages/web` | Scaffolded (Phase 4) |
| Refund demo | `examples/refund-agent` | Minimal demo agent + 4 scenarios |

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

# Run the refund demo suite (offline, no API keys)
uv run agentguard run \
  --config examples/refund-agent/agentguard.yaml \
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
docker compose up
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

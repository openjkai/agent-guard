# Contributing to AgentGuard

Thank you for contributing. This project targets production AI reliability — code quality and test coverage matter.

## Before you start

1. Read [docs/CODING_STANDARDS.md](docs/CODING_STANDARDS.md)
2. Read [docs/PLAN.md](docs/PLAN.md) and [docs/ROADMAP.md](docs/ROADMAP.md)
3. Check open issues or discuss large changes in an issue first

## Development setup

```bash
make install          # uv sync + pre-commit hooks
make check            # ruff + mypy + pytest
make web-check        # ESLint + TypeScript (packages/web)
```

Individual commands:

```bash
make test             # pytest
make lint             # ruff check
make format           # ruff format
make typecheck        # mypy
make demo-gate        # offline release-gate smoke (refund demo)
```

For web work:

```bash
make web-install
make web-dev          # http://localhost:3000
```

## Branch and commit conventions

- Branch: `feat/short-description`, `fix/short-description`, `docs/short-description`
- Commits: imperative mood, concise subject (`Add replay cassette diffing`)
- One logical change per PR

## Pull request checklist

- [ ] Tests added or updated for behavior changes
- [ ] `make check` passes locally (and `make web-check` if you touched `packages/web`)
- [ ] No secrets or API keys committed
- [ ] Docs updated if public API or workflow changed
- [ ] CHANGELOG entry for user-facing changes

## Release gating in CI

Use `scripts/release_gate_check.py` to fail a pipeline when an agent regresses:

```bash
uv run python scripts/release_gate_check.py \
  --config path/to/config.yaml \
  --suite path/to/scenarios \
  --agent path/to/agent.py \
  --expect SHIP
```

See [.github/workflows/release-gate.yml](.github/workflows/release-gate.yml).

## Code review values

1. Correctness and safety (especially evaluator and sandbox logic)
2. Replay determinism
3. Clarity over cleverness
4. Minimal scope

## Questions

Open a GitHub issue with the [question template](https://github.com/openjkai/agent-guard/issues/new?template=question.yml).

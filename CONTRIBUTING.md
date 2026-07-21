# Contributing to AgentGuard

Thank you for contributing. This project targets production AI reliability — code quality and test coverage matter.

## Before you start

1. Read [docs/CODING_STANDARDS.md](docs/CODING_STANDARDS.md)
2. Read [docs/PLAN.md](docs/PLAN.md) to understand phase priorities
3. Check open issues or discuss large changes in an issue first

## Development setup

```bash
make install          # uv sync + pre-commit hooks
make test             # pytest
make lint             # ruff check
make format           # ruff format
make typecheck        # mypy
```

For web work (Phase 4):

```bash
cd packages/web && npm install && npm run lint && npm run typecheck
```

## Branch and commit conventions

- Branch: `feat/short-description`, `fix/short-description`, `docs/short-description`
- Commits: imperative mood, concise subject (`Add replay cassette diffing`)
- One logical change per PR

## Pull request checklist

- [ ] Tests added or updated for behavior changes
- [ ] `make lint typecheck test` passes locally
- [ ] No secrets or API keys committed
- [ ] Docs updated if public API or workflow changed
- [ ] CHANGELOG entry if user-facing (once we publish releases)

## Phase priorities

We build **engine + CLI first**. Avoid large UI or infra PRs until Phase 1 core modules land unless explicitly discussed.

## Code review values

1. Correctness and safety (especially evaluator and sandbox logic)
2. Replay determinism
3. Clarity over cleverness
4. Minimal scope

## Questions

Open a GitHub issue with the `question` label.

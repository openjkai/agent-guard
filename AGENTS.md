# AGENTS.md — guidance for AI coding assistants

This file helps Cursor, Copilot, and other agents work effectively in the AgentGuard monorepo.

## Project mission

AgentGuard is a **release gate for AI agents** — not a chatbot demo. Every feature should support: trace capture, evaluation, deterministic replay, version comparison, and release decisions (SHIP / SHIP_WITH_WARNING / REQUIRE_HUMAN_REVIEW / BLOCK).

## Read first

| Document | Purpose |
|----------|---------|
| [docs/PLAN.md](docs/PLAN.md) | Product plan and phases |
| [docs/architecture.md](docs/architecture.md) | System design |
| [docs/CODING_STANDARDS.md](docs/CODING_STANDARDS.md) | Language-specific rules |
| [.cursor/rules/](.cursor/rules/) | Cursor rule files |

## Build order (do not skip ahead)

1. **Phase 1** — `packages/agentguard`: trace model, sandbox, evaluators, replay, runner, gate, CLI
2. **Phase 2** — `examples/refund-agent`: demo agent + scenario dataset
3. **Phase 3** — `packages/server`: FastAPI, Postgres, Celery
4. **Phase 4** — `packages/web`: Next.js dashboard
5. **Phase 5** — packaging, docs, demo video

When implementing, prefer completing vertical slices in Phase 1 over polishing UI.

## Monorepo map

```text
packages/agentguard/src/agentguard/
  adapters/      # CallableAgent, LangGraphAdapter, OpenAI-compatible
  tracing/       # Run, Step, OTel-aligned capture
  sandbox/       # MockTool, enterprise mock tools
  evaluators/    # @evaluator decorator, built-ins
  replay/        # Cassettes, replayer, diff
  scenarios/     # YAML schema, runner
  gate/          # Release policy engine
  compare/       # Version A/B metrics
  report/        # Terminal, MD, HTML, JSON reports
  cli/           # typer CLI
```

## Hard rules for agents

1. **Never call real external tools in tests** — use sandbox mocks and cassettes
2. **Never commit secrets** — use `.env.example` placeholders only
3. **Strict typing** — Python: mypy strict; TypeScript: strict mode
4. **Pydantic v2** for all domain models (Run, Step, EvalResult, ReleaseDecision)
5. **Framework-independent core** — LangGraph is an adapter, not a dependency of core
6. **One module, one responsibility** — do not create god-files
7. **Tests for behavior** — especially evaluators, replay matching, gate policies
8. **Minimal diffs** — do not refactor unrelated code in the same change

## Commands

```bash
make install    # setup
make test       # pytest
make lint       # ruff
make typecheck  # mypy
uv run agentguard version
```

## Naming conventions

| Concept | Python | TypeScript |
|---------|--------|------------|
| Domain models | PascalCase classes | PascalCase types/interfaces |
| Functions | snake_case | camelCase |
| Constants | UPPER_SNAKE | UPPER_SNAKE |
| Files | snake_case.py | kebab-case or PascalCase for components |

## When adding a feature

1. Define or extend Pydantic models in the appropriate module
2. Implement logic with pure functions where possible
3. Add unit tests with fixtures (no live LLM calls in default CI)
4. Wire into CLI if user-facing
5. Update module `__init__.py` exports only if part of public API

## Release decision enum

Always use exactly: `SHIP`, `SHIP_WITH_WARNING`, `REQUIRE_HUMAN_REVIEW`, `BLOCK`.

## Questions agents should ask the user

- Does this need live LLM integration or can it use cassettes?
- Is this Phase 1 scope or should it wait?
- Should the evaluator be built-in or example-only?

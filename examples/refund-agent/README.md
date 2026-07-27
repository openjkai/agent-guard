# Refund agent demo (Phase 2)

Customer-support refund agent with RAG, mock tools, and release-gate evaluation.

## Layout

```text
agent/
  refund_core.py      # shared decision logic (prompt v1/v2)
  simple_agent.py     # plain-Python adapter target
  langgraph_agent.py  # LangGraph adapter target
scenarios/            # 50 YAML scenarios (generated)
dataset-manifest.json # scenario index (generated with build_dataset.py)
benchmarks/           # prompt/model config matrix
policies/             # refund policy docs
build_dataset.py      # regenerate scenarios/
run_benchmarks.py     # run 2 prompts x 2 models compare table
```

## Quick start

```bash
# Regenerate 50 scenarios (6 seeded failures + happy/edge cases)
python build_dataset.py

# Run full suite with prompt v2
uv run agentguard run \
  --config benchmarks/prompt-v2-mock.yaml \
  --suite scenarios \
  --agent agent/simple_agent.py

# Run benchmark matrix (offline, no API keys)
python run_benchmarks.py
```

## Seeded failure demos

| Scenario ID | Failure type |
|-------------|--------------|
| `seed-refund-over-limit` | Refund above $500 limit |
| `seed-wrong-customer-account` | Wrong customer account |
| `seed-prompt-injection-document` | Prompt injection in retrieved doc |
| `seed-duplicate-refund` | Duplicate refund attempt |
| `seed-tool-timeout` | Tool timeout |
| `seed-unsupported-policy` | Unsupported policy interpretation |

## Prompt versions

- **v1** — baseline behavior (misses some safety checks; lower pass rate)
- **v2** — improved safety checks (wrong account, duplicate refund, injection filtering)

## Benchmark configs

| Config | Prompt | Model (mock profile) |
|--------|--------|------------------------|
| `prompt-v1-mock` | v1 | mock-model |
| `prompt-v2-mock` | v2 | mock-model |
| `prompt-v1-gpt4o-mini` | v1 | mock-model-gpt4o-mini |
| `prompt-v2-claude-haiku` | v2 | mock-model-claude-haiku |

## Benchmark results (offline mock)

| Config | Pass rate | Release decision |
|--------|-----------|------------------|
| prompt-v1-mock | 94% | BLOCK |
| prompt-v2-mock | 100% | SHIP |
| prompt-v1-gpt4o-mini | 94% | BLOCK |
| prompt-v2-claude-haiku | 100% | SHIP |

Prompt v2 fixes wrong-account, duplicate-refund, and retrieval-injection checks that v1 misses.

## Dataset manifest

`dataset-manifest.json` lists all 50 scenarios with tags and seeded-failure metadata. Regenerate with `python build_dataset.py`. Documented in [docs/datasets/refund-evaluation-dataset.md](../../docs/datasets/refund-evaluation-dataset.md).

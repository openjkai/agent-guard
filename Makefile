.PHONY: install sync test lint format typecheck check clean cli-version web-install web-lint web-typecheck web-check web-dev demo-dataset demo-benchmark server-api docker-up

UV := uv
export PATH := $(HOME)/.local/bin:$(PATH)

install: sync
	$(UV) run pre-commit install

sync:
	$(UV) sync --all-packages --all-extras --group dev

test:
	$(UV) run pytest

lint:
	$(UV) run ruff check packages/
	$(UV) run ruff format --check packages/

format:
	$(UV) run ruff check --fix packages/
	$(UV) run ruff format packages/

typecheck:
	$(UV) run mypy

check: lint typecheck test

cli-version:
	$(UV) run agentguard version

clean:
	rm -rf .venv .pytest_cache .mypy_cache .ruff_cache
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true

web-install:
	cd packages/web && npm install

web-lint:
	cd packages/web && npm run lint

web-typecheck:
	cd packages/web && npm run typecheck

web-check: web-lint web-typecheck

web-dev:
	cd packages/web && npm run dev

demo-dataset:
	cd examples/refund-agent && uv run python build_dataset.py

demo-benchmark:
	cd examples/refund-agent && uv run python run_benchmarks.py

server-api:
	cd packages/server && uv run uvicorn app.main:app --reload --port 8000

docker-up:
	docker compose up --build

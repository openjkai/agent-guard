"""Local file storage for runs, cassettes, and suite results."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, TypeVar, cast

from pydantic import BaseModel

from agentguard.errors import RunNotFoundError

T = TypeVar("T", bound=BaseModel)


class FileStore:
    """Persists runs and suite artifacts under a base directory."""

    def __init__(self, base_dir: Path | str = ".agentguard") -> None:
        self.base_dir = Path(base_dir)
        self.runs_dir = self.base_dir / "runs"
        self.suites_dir = self.base_dir / "suites"
        self.runs_dir.mkdir(parents=True, exist_ok=True)
        self.suites_dir.mkdir(parents=True, exist_ok=True)

    def run_dir(self, run_id: str) -> Path:
        path = self.runs_dir / run_id
        path.mkdir(parents=True, exist_ok=True)
        return path

    def save_model(self, run_id: str, filename: str, model: BaseModel) -> Path:
        path = self.run_dir(run_id) / filename
        path.write_text(model.model_dump_json(indent=2), encoding="utf-8")
        return path

    def load_model(self, run_id: str, filename: str, model_type: type[T]) -> T:
        path = self.run_dir(run_id) / filename
        if not path.exists():
            raise RunNotFoundError(f"Missing {filename} for run {run_id}")
        return model_type.model_validate_json(path.read_text(encoding="utf-8"))

    def save_json(self, run_id: str, filename: str, data: dict[str, Any]) -> Path:
        path = self.run_dir(run_id) / filename
        path.write_text(json.dumps(data, indent=2, default=str), encoding="utf-8")
        return path

    def load_json(self, run_id: str, filename: str) -> dict[str, Any]:
        path = self.run_dir(run_id) / filename
        if not path.exists():
            raise RunNotFoundError(f"Missing {filename} for run {run_id}")
        return cast(dict[str, Any], json.loads(path.read_text(encoding="utf-8")))

    def list_run_ids(self) -> list[str]:
        if not self.runs_dir.exists():
            return []
        return sorted(
            item.name
            for item in self.runs_dir.iterdir()
            if item.is_dir() and (item / "run.json").exists()
        )

    def suite_dir(self, suite_id: str) -> Path:
        path = self.suites_dir / suite_id
        path.mkdir(parents=True, exist_ok=True)
        return path

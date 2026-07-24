"""Server API tests."""

from __future__ import annotations

from pathlib import Path

import yaml
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[3]


def test_health(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_project_and_suite_flow(client: TestClient, auth_headers: dict[str, str]) -> None:
    config_path = ROOT / "examples/refund-agent/benchmarks/prompt-v2-mock.yaml"
    config = yaml.safe_load(config_path.read_text(encoding="utf-8"))

    create = client.post(
        "/api/v1/projects",
        json={
            "name": "refund-demo",
            "description": "Phase 3 API test",
            "agent_module_path": "examples/refund-agent/agent/simple_agent.py",
            "scenarios_path": "examples/refund-agent/scenarios",
            "config_json": config,
        },
    )
    assert create.status_code == 201
    project_id = create.json()["id"]

    suite = client.post(
        f"/api/v1/projects/{project_id}/suites",
        headers=auth_headers,
        json={},
    )
    assert suite.status_code == 202
    suite_id = suite.json()["id"]

    detail = client.get(f"/api/v1/suites/{suite_id}")
    assert detail.status_code == 200
    assert detail.json()["status"] == "completed"
    assert detail.json()["pass_rate"] is not None

    runs = client.get(f"/api/v1/suites/{suite_id}/runs")
    assert runs.status_code == 200
    assert len(runs.json()) == 50

    suites = client.get(f"/api/v1/projects/{project_id}/suites")
    assert suites.status_code == 200
    assert len(suites.json()) == 1

    report = client.get(f"/api/v1/suites/{suite_id}/report")
    assert report.status_code == 200
    assert report.json()["decision"] in {
        "SHIP",
        "SHIP_WITH_WARNING",
        "REQUIRE_HUMAN_REVIEW",
        "BLOCK",
    }


def test_api_key_required(client: TestClient) -> None:
    create = client.post(
        "/api/v1/projects",
        json={"name": "x", "agent_module_path": "a", "scenarios_path": "b"},
    )
    project_id = create.json()["id"]
    response = client.post(f"/api/v1/projects/{project_id}/suites", json={})
    assert response.status_code == 401

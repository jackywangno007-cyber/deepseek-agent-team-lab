from pathlib import Path

from fastapi.testclient import TestClient

from backend.api.app import create_app
from backend.services.task_service import TaskService


def make_client(tmp_path: Path) -> TestClient:
    service = TaskService(workspace_root=tmp_path / "workspace")
    return TestClient(create_app(task_service=service))


def create_mock_task(client: TestClient) -> str:
    response = client.post(
        "/api/tasks",
        json={
            "task": "Design an MVP for a student course management system",
            "mock": True,
            "run_async": False,
        },
    )
    assert response.status_code == 200
    return response.json()["task_id"]


def test_list_and_read_artifacts(tmp_path: Path) -> None:
    client = make_client(tmp_path)
    task_id = create_mock_task(client)

    artifacts_response = client.get(f"/api/tasks/{task_id}/artifacts")
    assert artifacts_response.status_code == 200
    artifact_names = {artifact["name"] for artifact in artifacts_response.json()["artifacts"]}
    assert "prd.md" in artifact_names
    assert "task_meta.json" in artifact_names

    prd_response = client.get(f"/api/tasks/{task_id}/artifacts/prd.md")
    assert prd_response.status_code == 200
    payload = prd_response.json()
    assert payload["artifact_name"] == "prd.md"
    assert "# Product Requirements Document" in payload["content"]


def test_artifact_path_traversal_is_blocked(tmp_path: Path) -> None:
    client = make_client(tmp_path)
    task_id = create_mock_task(client)

    response = client.get(f"/api/tasks/{task_id}/artifacts/%2E%2E/.env")

    assert response.status_code in {400, 404}


def test_get_evaluation(tmp_path: Path) -> None:
    client = make_client(tmp_path)
    task_id = create_mock_task(client)

    response = client.get(f"/api/tasks/{task_id}/evaluation")

    assert response.status_code == 200
    assert response.json()["evaluation"]["passed"] is True

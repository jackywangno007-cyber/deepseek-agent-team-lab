from pathlib import Path

from fastapi.testclient import TestClient

from backend.api.app import create_app
from backend.services.task_service import TaskService


def make_client(tmp_path: Path) -> TestClient:
    service = TaskService(workspace_root=tmp_path / "workspace")
    return TestClient(create_app(task_service=service))


def create_revised_task(client: TestClient) -> str:
    task_response = client.post(
        "/api/tasks",
        json={"task": "Design an MVP for a student course management system", "mock": True, "run_async": False},
    )
    task_id = task_response.json()["task_id"]
    feedback_response = client.post(
        f"/api/tasks/{task_id}/feedback",
        json={"target_agent": "ProductAgent", "target_artifact": "prd.md", "content": "Add deadline reminders."},
    )
    client.post(
        f"/api/tasks/{task_id}/revisions",
        json={"feedback_id": feedback_response.json()["feedback_id"], "rerun_downstream": False, "run_async": False},
    )
    return task_id


def test_list_and_read_artifact_versions(tmp_path: Path) -> None:
    client = make_client(tmp_path)
    task_id = create_revised_task(client)

    versions_response = client.get(f"/api/tasks/{task_id}/artifacts/prd.md/versions")
    assert versions_response.status_code == 200
    versions = versions_response.json()["versions"]
    assert len(versions) == 1
    assert versions[0]["name"].startswith("prd.")

    content_response = client.get(f"/api/tasks/{task_id}/artifacts/prd.md/versions/{versions[0]['name']}")
    assert content_response.status_code == 200
    assert "# Product Requirements Document" in content_response.json()["content"]


def test_artifact_version_path_traversal_is_blocked(tmp_path: Path) -> None:
    client = make_client(tmp_path)
    task_id = create_revised_task(client)

    response = client.get(f"/api/tasks/{task_id}/artifacts/prd.md/versions/%2E%2E%2F.env")

    assert response.status_code in {400, 404}


def test_invalid_artifact_versions_request(tmp_path: Path) -> None:
    client = make_client(tmp_path)
    task_id = create_revised_task(client)

    response = client.get(f"/api/tasks/{task_id}/artifacts/missing.md/versions")

    assert response.status_code == 404

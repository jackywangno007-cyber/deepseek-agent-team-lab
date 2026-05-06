from pathlib import Path

from fastapi.testclient import TestClient

from backend.api.app import create_app
from backend.services.task_service import TaskService


def make_client(tmp_path: Path) -> TestClient:
    service = TaskService(workspace_root=tmp_path / "workspace")
    return TestClient(create_app(task_service=service))


def test_evaluation_compare_is_generated_after_approved_improvement(tmp_path: Path) -> None:
    client = make_client(tmp_path)
    task_response = client.post(
        "/api/tasks",
        json={"task": "Design an MVP for a student course management system", "mock": True, "run_async": False},
    )
    task_id = task_response.json()["task_id"]
    suggestion_id = client.post(f"/api/tasks/{task_id}/improvements/generate", json={"force": False}).json()["suggestions"][0]["suggestion_id"]

    approve_response = client.post(
        f"/api/tasks/{task_id}/improvements/{suggestion_id}/approve",
        json={"edited_feedback": None, "rerun_downstream": False, "run_async": False},
    )

    assert approve_response.status_code == 200
    compare_response = client.get(f"/api/tasks/{task_id}/evaluation/compare")
    assert compare_response.status_code == 200
    compare = compare_response.json()
    assert compare["task_id"] == task_id
    assert isinstance(compare["before"], dict)
    assert isinstance(compare["after"], dict)
    assert "changed" in compare
    assert compare["summary"] == "Evaluation refreshed after approved improvement."

    evaluation_response = client.get(f"/api/tasks/{task_id}/evaluation")
    assert evaluation_response.status_code == 200
    assert evaluation_response.json()["evaluation"]["passed"] is True

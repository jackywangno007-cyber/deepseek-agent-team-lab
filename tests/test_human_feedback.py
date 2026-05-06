from pathlib import Path

from fastapi.testclient import TestClient

from backend.api.app import create_app
from backend.services.task_service import TaskService


def make_client(tmp_path: Path) -> TestClient:
    service = TaskService(workspace_root=tmp_path / "workspace")
    return TestClient(create_app(task_service=service))


def create_task(client: TestClient) -> str:
    response = client.post(
        "/api/tasks",
        json={"task": "Design an MVP for a student course management system", "mock": True, "run_async": False},
    )
    assert response.status_code == 200
    return response.json()["task_id"]


def test_create_and_list_human_feedback(tmp_path: Path) -> None:
    client = make_client(tmp_path)
    task_id = create_task(client)

    response = client.post(
        f"/api/tasks/{task_id}/feedback",
        json={
            "target_agent": "ProductAgent",
            "target_artifact": "prd.md",
            "content": "The target users should be university students.",
        },
    )

    assert response.status_code == 200
    feedback_id = response.json()["feedback_id"]
    assert response.json()["status"] == "PENDING"

    list_response = client.get(f"/api/tasks/{task_id}/feedback")
    assert list_response.status_code == 200
    feedback = list_response.json()["feedback"]
    assert feedback[0]["feedback_id"] == feedback_id
    assert feedback[0]["target_agent"] == "ProductAgent"


def test_invalid_feedback_inputs(tmp_path: Path) -> None:
    client = make_client(tmp_path)
    task_id = create_task(client)

    invalid_agent = client.post(
        f"/api/tasks/{task_id}/feedback",
        json={"target_agent": "UnknownAgent", "target_artifact": "prd.md", "content": "Change it."},
    )
    assert invalid_agent.status_code == 400

    wrong_artifact = client.post(
        f"/api/tasks/{task_id}/feedback",
        json={"target_agent": "ProductAgent", "target_artifact": "../.env", "content": "Change it."},
    )
    assert wrong_artifact.status_code == 400

    missing_task = client.get("/api/tasks/task_missing/feedback")
    assert missing_task.status_code == 404

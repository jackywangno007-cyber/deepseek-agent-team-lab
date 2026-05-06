from pathlib import Path

from fastapi.testclient import TestClient

from backend.api.app import create_app
from backend.services.task_service import TaskService


def make_client(tmp_path: Path) -> TestClient:
    service = TaskService(workspace_root=tmp_path / "workspace")
    return TestClient(create_app(task_service=service))


def create_task_and_feedback(client: TestClient) -> tuple[str, str]:
    task_response = client.post(
        "/api/tasks",
        json={"task": "Design an MVP for a student course management system", "mock": True, "run_async": False},
    )
    assert task_response.status_code == 200
    task_id = task_response.json()["task_id"]
    feedback_response = client.post(
        f"/api/tasks/{task_id}/feedback",
        json={
            "target_agent": "ProductAgent",
            "target_artifact": "prd.md",
            "content": "The target users should be university students. Add deadline reminders.",
        },
    )
    assert feedback_response.status_code == 200
    return task_id, feedback_response.json()["feedback_id"]


def test_request_revision_updates_artifact_and_history(tmp_path: Path) -> None:
    client = make_client(tmp_path)
    task_id, feedback_id = create_task_and_feedback(client)
    before = client.get(f"/api/tasks/{task_id}/artifacts/prd.md").json()["content"]

    revision_response = client.post(
        f"/api/tasks/{task_id}/revisions",
        json={"feedback_id": feedback_id, "rerun_downstream": True, "run_async": False},
    )

    assert revision_response.status_code == 200
    assert revision_response.json()["status"] == "COMPLETED"

    after = client.get(f"/api/tasks/{task_id}/artifacts/prd.md").json()["content"]
    assert after != before
    assert "university students" in after

    revisions = client.get(f"/api/tasks/{task_id}/revisions").json()["revisions"]
    assert revisions[0]["status"] == "COMPLETED"
    assert revisions[0]["backup_artifact"].startswith("versions/prd.")

    feedback = client.get(f"/api/tasks/{task_id}/feedback").json()["feedback"]
    assert feedback[0]["status"] == "APPLIED"

    events = client.get(f"/api/tasks/{task_id}/events").json()["events"]
    event_types = {event["type"] for event in events}
    assert "revision_started" in event_types
    assert "artifact_version_backup" in event_types
    assert "revision_completed" in event_types
    assert "downstream_rerun_started" in event_types
    assert "downstream_rerun_completed" in event_types

    evaluation = client.get(f"/api/tasks/{task_id}/evaluation").json()["evaluation"]
    assert evaluation["passed"] is True


def test_revision_with_missing_feedback_returns_404(tmp_path: Path) -> None:
    client = make_client(tmp_path)
    task_response = client.post(
        "/api/tasks",
        json={"task": "Design an MVP for a student course management system", "mock": True, "run_async": False},
    )
    task_id = task_response.json()["task_id"]

    response = client.post(
        f"/api/tasks/{task_id}/revisions",
        json={"feedback_id": "feedback_missing", "rerun_downstream": False, "run_async": False},
    )

    assert response.status_code == 404

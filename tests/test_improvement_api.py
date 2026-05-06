from pathlib import Path

from fastapi.testclient import TestClient

from backend.api.app import create_app
from backend.services.task_service import TaskService


def make_client(tmp_path: Path) -> TestClient:
    service = TaskService(workspace_root=tmp_path / "workspace")
    return TestClient(create_app(task_service=service))


def create_completed_task(client: TestClient) -> str:
    response = client.post(
        "/api/tasks",
        json={"task": "Design an MVP for a student course management system", "mock": True, "run_async": False},
    )
    assert response.status_code == 200
    return response.json()["task_id"]


def test_generate_and_list_improvement_suggestions(tmp_path: Path) -> None:
    client = make_client(tmp_path)
    task_id = create_completed_task(client)

    response = client.post(f"/api/tasks/{task_id}/improvements/generate", json={"force": False})

    assert response.status_code == 200
    suggestions = response.json()["suggestions"]
    assert suggestions
    assert all(suggestion["status"] == "PENDING" for suggestion in suggestions)
    assert all(suggestion["responsible_agent"].endswith("Agent") for suggestion in suggestions)
    assert all(suggestion["target_artifact"].endswith(".md") for suggestion in suggestions)

    list_response = client.get(f"/api/tasks/{task_id}/improvements")
    assert list_response.status_code == 200
    assert list_response.json()["suggestions"] == suggestions

    events_response = client.get(f"/api/tasks/{task_id}/events")
    event_types = {event["type"] for event in events_response.json()["events"]}
    assert "improvement_suggestions_generated" in event_types


def test_approve_suggestion_creates_feedback_revision_and_history(tmp_path: Path) -> None:
    client = make_client(tmp_path)
    task_id = create_completed_task(client)
    suggestions = client.post(f"/api/tasks/{task_id}/improvements/generate", json={"force": False}).json()["suggestions"]
    suggestion_id = suggestions[0]["suggestion_id"]

    response = client.post(
        f"/api/tasks/{task_id}/improvements/{suggestion_id}/approve",
        json={"edited_feedback": "Please tighten this artifact based on the improvement suggestion.", "rerun_downstream": False, "run_async": False},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "APPLIED"
    assert payload["feedback_id"].startswith("feedback_")
    assert payload["revision_id"].startswith("revision_")

    feedback = client.get(f"/api/tasks/{task_id}/feedback").json()["feedback"]
    assert any(item["feedback_id"] == payload["feedback_id"] for item in feedback)

    history = client.get(f"/api/tasks/{task_id}/improvements/history").json()["history"]
    assert len(history) == 1
    assert history[0]["status"] == "COMPLETED"
    assert history[0]["revision_id"] == payload["revision_id"]

    suggestions_after = client.get(f"/api/tasks/{task_id}/improvements").json()["suggestions"]
    approved = next(item for item in suggestions_after if item["suggestion_id"] == suggestion_id)
    assert approved["status"] == "APPLIED"

    events = client.get(f"/api/tasks/{task_id}/events").json()["events"]
    event_types = {event["type"] for event in events}
    assert "improvement_approved" in event_types
    assert "improvement_revision_started" in event_types
    assert "improvement_revision_completed" in event_types


def test_reject_suggestion_updates_status_and_history(tmp_path: Path) -> None:
    client = make_client(tmp_path)
    task_id = create_completed_task(client)
    suggestion_id = client.post(f"/api/tasks/{task_id}/improvements/generate", json={"force": False}).json()["suggestions"][0]["suggestion_id"]

    response = client.post(
        f"/api/tasks/{task_id}/improvements/{suggestion_id}/reject",
        json={"reason": "Not relevant for this MVP."},
    )

    assert response.status_code == 200
    assert response.json() == {"suggestion_id": suggestion_id, "status": "REJECTED"}
    suggestion = next(item for item in client.get(f"/api/tasks/{task_id}/improvements").json()["suggestions"] if item["suggestion_id"] == suggestion_id)
    assert suggestion["status"] == "REJECTED"
    history = client.get(f"/api/tasks/{task_id}/improvements/history").json()["history"]
    assert history[0]["action"] == "REJECTED"
    assert history[0]["reason"] == "Not relevant for this MVP."


def test_improvement_invalid_ids_return_404(tmp_path: Path) -> None:
    client = make_client(tmp_path)

    missing_task = client.get("/api/tasks/task_missing/improvements")
    assert missing_task.status_code == 404

    task_id = create_completed_task(client)
    missing_suggestion = client.post(
        f"/api/tasks/{task_id}/improvements/suggestion_missing/approve",
        json={"rerun_downstream": False, "run_async": False},
    )
    assert missing_suggestion.status_code == 404

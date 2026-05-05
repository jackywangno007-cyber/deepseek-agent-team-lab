from pathlib import Path
from threading import Thread
from time import sleep

from fastapi.testclient import TestClient

from backend.api.app import create_app
from backend.core.event_bus import EventBus
from backend.services.task_service import TaskService


def make_client(tmp_path: Path) -> TestClient:
    service = TaskService(workspace_root=tmp_path / "workspace")
    return TestClient(create_app(task_service=service))


def test_health_works(tmp_path: Path) -> None:
    client = make_client(tmp_path)

    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "version": "0.2.0"}


def test_create_list_and_get_completed_task(tmp_path: Path) -> None:
    client = make_client(tmp_path)

    create_response = client.post(
        "/api/tasks",
        json={
            "task": "Design an MVP for a student course management system",
            "mock": True,
            "model": "deepseek-v4-flash",
            "run_async": False,
        },
    )

    assert create_response.status_code == 200
    created = create_response.json()
    assert created["status"] == "COMPLETED"
    assert created["task_id"].startswith("task_")

    list_response = client.get("/api/tasks")
    assert list_response.status_code == 200
    tasks = list_response.json()["tasks"]
    assert any(task["task_id"] == created["task_id"] for task in tasks)

    status_response = client.get(f"/api/tasks/{created['task_id']}")
    assert status_response.status_code == 200
    meta = status_response.json()
    assert meta["status"] == "COMPLETED"
    assert meta["mock"] is True
    assert meta["model"] == "deepseek-v4-flash"
    assert meta["error"] is None


def test_websocket_streams_existing_and_new_events(tmp_path: Path) -> None:
    service = TaskService(workspace_root=tmp_path / "workspace")
    client = TestClient(create_app(task_service=service))
    created = service.create_task(task="Design an MVP", mock=True, run_async=True)
    task_id = created["task_id"]
    workspace = created["workspace"]
    bus = EventBus(workspace)
    bus.emit(from_agent="Test", type="task_created", content="Existing event", status="created")

    def append_event_and_finish() -> None:
        sleep(0.2)
        bus.emit(from_agent="Test", type="agent_completed", content="New event", status="succeeded")
        service.update_task_meta(task_id, status="COMPLETED")

    worker = Thread(target=append_event_and_finish)
    worker.start()
    with client.websocket_connect(f"/ws/tasks/{task_id}/events") as websocket:
        first = websocket.receive_json()
        second = websocket.receive_json()
        third = websocket.receive_json()

    worker.join()
    assert first["type"] == "event"
    assert first["data"]["content"] == "Existing event"
    assert second["type"] == "event"
    assert second["data"]["content"] == "New event"
    assert third == {"type": "task_finished", "status": "COMPLETED"}

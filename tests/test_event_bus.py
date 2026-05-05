from pathlib import Path

from backend.core.event_bus import EventBus
from backend.core.workspace import TaskWorkspace


def test_event_bus_writes_required_fields(tmp_path: Path) -> None:
    workspace = TaskWorkspace(root=tmp_path)
    bus = EventBus(workspace)

    bus.emit(
        from_agent="ManagerAgent",
        to_agent="ProductAgent",
        type="task_assign",
        content="Create PRD",
        artifact_refs=["prd.md"],
    )

    events = bus.read_events()
    assert len(events) == 1
    event = events[0]
    for field in ["task_id", "from_agent", "to_agent", "type", "content", "artifact_refs", "status", "created_at"]:
        assert field in event
    assert event["type"] == "task_assign"

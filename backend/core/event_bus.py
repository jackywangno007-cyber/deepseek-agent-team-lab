from __future__ import annotations

import json
from datetime import datetime

from rich.console import Console

from backend.core.workspace import TaskWorkspace
from backend.schemas.message import Event


class EventBus:
    def __init__(self, workspace: TaskWorkspace, console: Console | None = None) -> None:
        self.workspace = workspace
        self.console = console or Console()
        self.events_file = self.workspace._safe_path("events.jsonl")
        self.events_file.touch(exist_ok=True)

    def emit(
        self,
        *,
        from_agent: str,
        type: str,
        content: str,
        to_agent: str | None = None,
        artifact_refs: list[str] | None = None,
        status: str = "sent",
    ) -> Event:
        event = Event(
            task_id=self.workspace.task_id,
            from_agent=from_agent,
            to_agent=to_agent,
            type=type,
            content=content,
            artifact_refs=artifact_refs or [],
            status=status,
            created_at=datetime.utcnow(),
        )
        with self.events_file.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(event.model_dump(mode="json"), ensure_ascii=False) + "\n")
        self.console.print(f"[dim]{event.type}[/dim] [bold]{event.from_agent}[/bold]: {event.content}")
        return event

    def read_events(self) -> list[dict]:
        if not self.events_file.exists():
            return []
        events: list[dict] = []
        for line in self.events_file.read_text(encoding="utf-8").splitlines():
            if line.strip():
                events.append(json.loads(line))
        return events

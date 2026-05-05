from __future__ import annotations

import json
import re

from backend.core.event_bus import EventBus
from backend.core.workspace import TaskWorkspace


REQUIRED_ARTIFACTS = [
    "task_input.md",
    "task_plan.json",
    "events.jsonl",
    "prd.md",
    "architecture.md",
    "frontend_plan.md",
    "api_design.md",
    "test_plan.md",
    "review_report.md",
    "final_summary.md",
]


class Evaluator:
    def __init__(self, workspace: TaskWorkspace, event_bus: EventBus) -> None:
        self.workspace = workspace
        self.event_bus = event_bus

    def evaluate(self) -> dict:
        artifacts_complete = all(self.workspace.artifact_exists(name) for name in REQUIRED_ARTIFACTS)
        markdown_non_empty = all(
            self.workspace.artifact_exists(name) and bool(self.workspace.read_artifact(name).strip())
            for name in REQUIRED_ARTIFACTS
            if name.endswith(".md")
        )
        review_score_found = False
        if self.workspace.artifact_exists("review_report.md"):
            review_score_found = bool(re.search(r"\b([0-9]|10)\s*/\s*10\b", self.workspace.read_artifact("review_report.md")))
        final_summary_found = self.workspace.artifact_exists("final_summary.md")
        event_types = {event.get("type") for event in self.event_bus.read_events()}
        required_event_types = {
            "task_created",
            "task_assign",
            "agent_started",
            "agent_completed",
            "artifact_created",
            "review_request",
            "review_result",
            "final_summary",
        }
        events_complete = required_event_types.issubset(event_types)
        result = {
            "artifacts_complete": artifacts_complete and markdown_non_empty,
            "events_complete": events_complete,
            "review_score_found": review_score_found,
            "final_summary_found": final_summary_found,
            "passed": artifacts_complete and markdown_non_empty and events_complete and review_score_found and final_summary_found,
        }
        self.workspace.write_artifact("evaluation.json", json.dumps(result, indent=2, ensure_ascii=False))
        return result

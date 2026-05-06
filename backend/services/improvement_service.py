from __future__ import annotations

import json
from typing import Any

from rich.console import Console

from backend.core.event_bus import EventBus
from backend.core.improvement_engine import ImprovementEngine
from backend.services.task_service import ArtifactNotFoundError, FeedbackNotFoundError, TaskNotFoundError, TaskService


class SuggestionNotFoundError(LookupError):
    pass


class ImprovementService:
    SUGGESTIONS_FILE = "improvement_suggestions.jsonl"
    HISTORY_FILE = "improvement_history.jsonl"
    EVALUATION_COMPARE_FILE = "evaluation_compare.json"

    def __init__(self, task_service: TaskService, console: Console | None = None) -> None:
        self.task_service = task_service
        self.console = console or task_service.console
        self.engine = ImprovementEngine()

    def generate_suggestions(self, task_id: str, *, force: bool = False) -> list[dict[str, Any]]:
        workspace = self.task_service._workspace_for_task(task_id)
        self.task_service.get_task_meta(task_id)
        existing = self.list_suggestions(task_id)
        if existing and not force:
            return existing
        if not workspace.artifact_exists("review_report.md"):
            raise ArtifactNotFoundError("Artifact not found: review_report.md")
        if not workspace.artifact_exists("evaluation.json"):
            raise ArtifactNotFoundError("Artifact not found: evaluation.json")
        suggestions = self.engine.generate(
            task_id=task_id,
            review_report=workspace.read_artifact("review_report.md"),
            evaluation=json.loads(workspace.read_artifact("evaluation.json")),
            now=self.task_service._now,
            id_factory=self.task_service._new_id,
        )
        if force:
            self.task_service._write_jsonl(workspace, self.SUGGESTIONS_FILE, suggestions)
        else:
            for suggestion in suggestions:
                self.task_service._append_jsonl(workspace, self.SUGGESTIONS_FILE, suggestion)
        EventBus(workspace, self.console).emit(
            from_agent="ImprovementEngine",
            type="improvement_suggestions_generated",
            content=f"Generated {len(suggestions)} improvement suggestions.",
            artifact_refs=[self.SUGGESTIONS_FILE, "review_report.md", "evaluation.json"],
            status="created",
        )
        self.task_service.update_task_meta(task_id)
        return self.list_suggestions(task_id)

    def list_suggestions(self, task_id: str) -> list[dict[str, Any]]:
        workspace = self.task_service._workspace_for_task(task_id)
        self.task_service.get_task_meta(task_id)
        return self.task_service._read_jsonl(workspace, self.SUGGESTIONS_FILE)

    def approve_suggestion(
        self,
        *,
        task_id: str,
        suggestion_id: str,
        edited_feedback: str | None = None,
        rerun_downstream: bool = True,
        run_async: bool = True,
    ) -> dict[str, Any]:
        workspace = self.task_service._workspace_for_task(task_id)
        suggestion = self._get_suggestion(task_id, suggestion_id)
        before_evaluation = self._read_evaluation_or_empty(task_id)
        feedback = self.task_service.create_feedback(
            task_id=task_id,
            target_agent=suggestion["responsible_agent"],
            target_artifact=suggestion["target_artifact"],
            content=(edited_feedback or suggestion["proposed_feedback"]).strip(),
        )
        revision = self.task_service.request_revision(
            task_id=task_id,
            feedback_id=feedback["feedback_id"],
            rerun_downstream=rerun_downstream,
            run_async=run_async,
        )
        improvement = {
            "improvement_id": self.task_service._new_id("improvement"),
            "task_id": task_id,
            "suggestion_id": suggestion_id,
            "action": "APPROVED",
            "responsible_agent": suggestion["responsible_agent"],
            "target_artifact": suggestion["target_artifact"],
            "feedback_id": feedback["feedback_id"],
            "revision_id": revision["revision_id"],
            "before_evaluation": before_evaluation,
            "after_evaluation": {},
            "status": "RUNNING" if run_async else "CREATED",
            "created_at": self.task_service._now(),
            "completed_at": None,
            "error": None,
        }
        self.task_service._append_jsonl(workspace, self.HISTORY_FILE, improvement)
        self._update_suggestion(task_id, suggestion_id, status="APPROVED")
        EventBus(workspace, self.console).emit(
            from_agent="Human",
            to_agent=suggestion["responsible_agent"],
            type="improvement_approved",
            content=f"Approved improvement suggestion {suggestion_id}.",
            artifact_refs=[suggestion["target_artifact"], self.HISTORY_FILE],
            status="approved",
        )
        if not run_async:
            self.run_improvement_revision(task_id=task_id, improvement_id=improvement["improvement_id"])
            status = "APPLIED"
        else:
            status = "APPROVED"
        return {
            "suggestion_id": suggestion_id,
            "feedback_id": feedback["feedback_id"],
            "revision_id": revision["revision_id"],
            "status": status,
        }

    def run_improvement_revision(self, *, task_id: str, improvement_id: str) -> None:
        workspace = self.task_service._workspace_for_task(task_id)
        improvement = self._get_improvement(task_id, improvement_id)
        event_bus = EventBus(workspace, self.console)
        event_bus.emit(
            from_agent="ImprovementEngine",
            type="improvement_revision_started",
            content=f"Started revision for improvement {improvement_id}.",
            artifact_refs=[improvement["target_artifact"]],
            status="running",
        )
        try:
            self._update_improvement(task_id, improvement_id, status="RUNNING", error=None)
            self.task_service.run_revision_pipeline(task_id=task_id, revision_id=improvement["revision_id"])
            after_evaluation = self._read_evaluation_or_empty(task_id)
            self._write_evaluation_compare(task_id, improvement["before_evaluation"], after_evaluation)
            self._update_suggestion(task_id, improvement["suggestion_id"], status="APPLIED")
            self._update_improvement(
                task_id,
                improvement_id,
                status="COMPLETED",
                after_evaluation=after_evaluation,
                completed_at=self.task_service._now(),
                error=None,
            )
            event_bus.emit(
                from_agent="ImprovementEngine",
                type="improvement_revision_completed",
                content=f"Completed revision for improvement {improvement_id}.",
                artifact_refs=[improvement["target_artifact"], self.EVALUATION_COMPARE_FILE],
                status="succeeded",
            )
            self.task_service.update_task_meta(task_id, status="COMPLETED", error=None)
        except Exception as exc:
            error = self.task_service._safe_error(exc)
            self._update_suggestion(task_id, improvement["suggestion_id"], status="FAILED")
            self._update_improvement(task_id, improvement_id, status="FAILED", completed_at=self.task_service._now(), error=error)
            event_bus.emit(
                from_agent="ImprovementEngine",
                type="improvement_revision_failed",
                content=error,
                artifact_refs=[improvement["target_artifact"]],
                status="failed",
            )
            self.task_service.update_task_meta(task_id, status="FAILED", error=error)
            raise

    def reject_suggestion(self, *, task_id: str, suggestion_id: str, reason: str | None = None) -> dict[str, Any]:
        workspace = self.task_service._workspace_for_task(task_id)
        suggestion = self._get_suggestion(task_id, suggestion_id)
        self._update_suggestion(task_id, suggestion_id, status="REJECTED")
        record = {
            "improvement_id": self.task_service._new_id("improvement"),
            "task_id": task_id,
            "suggestion_id": suggestion_id,
            "action": "REJECTED",
            "responsible_agent": suggestion["responsible_agent"],
            "target_artifact": suggestion["target_artifact"],
            "feedback_id": None,
            "revision_id": None,
            "before_evaluation": self._read_evaluation_or_empty(task_id),
            "after_evaluation": {},
            "status": "COMPLETED",
            "created_at": self.task_service._now(),
            "completed_at": self.task_service._now(),
            "error": None,
            "reason": reason or "",
        }
        self.task_service._append_jsonl(workspace, self.HISTORY_FILE, record)
        EventBus(workspace, self.console).emit(
            from_agent="Human",
            type="improvement_rejected",
            content=reason or f"Rejected improvement suggestion {suggestion_id}.",
            artifact_refs=[self.SUGGESTIONS_FILE],
            status="rejected",
        )
        self.task_service.update_task_meta(task_id)
        return {"suggestion_id": suggestion_id, "status": "REJECTED"}

    def list_history(self, task_id: str) -> list[dict[str, Any]]:
        workspace = self.task_service._workspace_for_task(task_id)
        self.task_service.get_task_meta(task_id)
        return self.task_service._read_jsonl(workspace, self.HISTORY_FILE)

    def get_evaluation_compare(self, task_id: str) -> dict[str, Any]:
        workspace = self.task_service._workspace_for_task(task_id)
        self.task_service.get_task_meta(task_id)
        if workspace.artifact_exists(self.EVALUATION_COMPARE_FILE):
            return json.loads(workspace.read_artifact(self.EVALUATION_COMPARE_FILE))
        current = self._read_evaluation_or_empty(task_id)
        return {
            "task_id": task_id,
            "before": current,
            "after": current,
            "changed": False,
            "summary": "No approved improvement has refreshed evaluation yet.",
        }

    def _write_evaluation_compare(self, task_id: str, before: dict[str, Any], after: dict[str, Any]) -> dict[str, Any]:
        workspace = self.task_service._workspace_for_task(task_id)
        payload = {
            "task_id": task_id,
            "before": before,
            "after": after,
            "changed": before != after,
            "summary": "Evaluation refreshed after approved improvement.",
        }
        workspace.write_json(self.EVALUATION_COMPARE_FILE, payload)
        EventBus(workspace, self.console).emit(
            from_agent="Evaluator",
            type="evaluation_compared",
            content=payload["summary"],
            artifact_refs=[self.EVALUATION_COMPARE_FILE, "evaluation.json"],
            status="completed",
        )
        return payload

    def _read_evaluation_or_empty(self, task_id: str) -> dict[str, Any]:
        try:
            return self.task_service.get_task_evaluation(task_id)
        except Exception:
            return {}

    def _get_suggestion(self, task_id: str, suggestion_id: str) -> dict[str, Any]:
        for suggestion in self.list_suggestions(task_id):
            if suggestion.get("suggestion_id") == suggestion_id:
                return suggestion
        raise SuggestionNotFoundError(f"Suggestion not found: {suggestion_id}")

    def _get_improvement(self, task_id: str, improvement_id: str) -> dict[str, Any]:
        for improvement in self.list_history(task_id):
            if improvement.get("improvement_id") == improvement_id:
                return improvement
        raise SuggestionNotFoundError(f"Improvement not found: {improvement_id}")

    def _update_suggestion(self, task_id: str, suggestion_id: str, **updates: Any) -> None:
        workspace = self.task_service._workspace_for_task(task_id)
        records = self.task_service._read_jsonl(workspace, self.SUGGESTIONS_FILE)
        for record in records:
            if record.get("suggestion_id") == suggestion_id:
                record.update(updates)
                record["updated_at"] = self.task_service._now()
        self.task_service._write_jsonl(workspace, self.SUGGESTIONS_FILE, records)

    def _update_improvement(self, task_id: str, improvement_id: str, **updates: Any) -> None:
        workspace = self.task_service._workspace_for_task(task_id)
        records = self.task_service._read_jsonl(workspace, self.HISTORY_FILE)
        for record in records:
            if record.get("improvement_id") == improvement_id:
                record.update(updates)
        self.task_service._write_jsonl(workspace, self.HISTORY_FILE, records)

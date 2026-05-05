from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from rich.console import Console

from backend.config import load_settings
from backend.core.event_bus import EventBus
from backend.core.orchestrator import Orchestrator
from backend.core.workspace import TaskWorkspace, WorkspaceError


class TaskNotFoundError(LookupError):
    pass


class ArtifactNotFoundError(LookupError):
    pass


class EvaluationNotFoundError(LookupError):
    pass


class InvalidArtifactNameError(ValueError):
    pass


class TaskService:
    STATUSES = {"CREATED", "RUNNING", "COMPLETED", "FAILED"}

    def __init__(self, workspace_root: str | Path = "workspace", console: Console | None = None) -> None:
        self.workspace_root = Path(workspace_root).resolve()
        self.workspace_root.mkdir(parents=True, exist_ok=True)
        self.console = console or Console()

    def create_task(
        self,
        *,
        task: str,
        mock: bool = True,
        model: str | None = None,
        run_async: bool = True,
    ) -> dict[str, Any]:
        workspace = TaskWorkspace(root=self.workspace_root)
        settings = load_settings(model_override=model)
        effective_mock = mock or not settings.has_api_key
        now = self._now()
        meta = {
            "task_id": workspace.task_id,
            "status": "CREATED",
            "created_at": now,
            "updated_at": now,
            "task_input_preview": self._preview(task),
            "model": settings.deepseek_model,
            "mock": effective_mock,
            "workspace_path": self._display_workspace_path(workspace),
            "error": None,
        }
        self._write_meta(workspace, meta)
        return {
            "task_id": workspace.task_id,
            "status": "RUNNING" if run_async else "CREATED",
            "workspace_path": meta["workspace_path"],
            "workspace": workspace,
            "settings": settings,
            "mock": effective_mock,
            "task": task,
        }

    def run_task_pipeline(self, *, task_id: str, task: str, model: str | None = None, mock: bool = True) -> None:
        workspace = self._workspace_for_task(task_id)
        settings = load_settings(model_override=model)
        effective_mock = mock or not settings.has_api_key
        self.update_task_meta(task_id, status="RUNNING", mock=effective_mock, model=settings.deepseek_model, error=None)
        try:
            Orchestrator(settings=settings, mock=effective_mock, console=self.console).run(
                task,
                workspace=workspace,
                event_source="API",
            )
            self.update_task_meta(task_id, status="COMPLETED", error=None)
        except Exception as exc:
            self.update_task_meta(task_id, status="FAILED", error=self._safe_error(exc))
            raise

    def list_tasks(self) -> list[dict[str, Any]]:
        tasks = []
        for meta_file in self.workspace_root.glob("task_*/task_meta.json"):
            try:
                tasks.append(json.loads(meta_file.read_text(encoding="utf-8")))
            except json.JSONDecodeError:
                continue
        return sorted(tasks, key=lambda item: item.get("created_at", ""), reverse=True)

    def get_task_meta(self, task_id: str) -> dict[str, Any]:
        workspace = self._workspace_for_task(task_id)
        meta_path = workspace._safe_path("task_meta.json")
        if not meta_path.exists():
            raise TaskNotFoundError(f"Task not found: {task_id}")
        return json.loads(meta_path.read_text(encoding="utf-8"))

    def update_task_meta(self, task_id: str, **updates: Any) -> dict[str, Any]:
        workspace = self._workspace_for_task(task_id)
        meta = self.get_task_meta(task_id)
        if "status" in updates and updates["status"] not in self.STATUSES:
            raise ValueError(f"Invalid task status: {updates['status']}")
        meta.update(updates)
        meta["updated_at"] = self._now()
        self._write_meta(workspace, meta)
        return meta

    def get_task_events(self, task_id: str) -> list[dict[str, Any]]:
        workspace = self._workspace_for_task(task_id)
        self.get_task_meta(task_id)
        return EventBus(workspace, self.console).read_events()

    def list_task_artifacts(self, task_id: str) -> list[dict[str, Any]]:
        workspace = self._workspace_for_task(task_id)
        self.get_task_meta(task_id)
        artifacts = []
        for file_path in workspace.path.rglob("*"):
            if not file_path.is_file():
                continue
            relative_name = file_path.relative_to(workspace.path).as_posix()
            stat = file_path.stat()
            artifacts.append(
                {
                    "name": relative_name,
                    "path": self._display_file_path(workspace, relative_name),
                    "size_bytes": stat.st_size,
                    "modified_at": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                }
            )
        return sorted(artifacts, key=lambda item: item["name"])

    def read_task_artifact(self, task_id: str, artifact_name: str) -> str:
        if self._is_invalid_artifact_name(artifact_name):
            raise InvalidArtifactNameError(f"Invalid artifact name: {artifact_name}")
        workspace = self._workspace_for_task(task_id)
        self.get_task_meta(task_id)
        try:
            if not workspace.artifact_exists(artifact_name):
                raise ArtifactNotFoundError(f"Artifact not found: {artifact_name}")
            return workspace.read_artifact(artifact_name)
        except WorkspaceError as exc:
            raise InvalidArtifactNameError(str(exc)) from exc

    def get_task_evaluation(self, task_id: str) -> dict[str, Any]:
        workspace = self._workspace_for_task(task_id)
        self.get_task_meta(task_id)
        if not workspace.artifact_exists("evaluation.json"):
            raise EvaluationNotFoundError(f"Evaluation not found for task: {task_id}")
        return json.loads(workspace.read_artifact("evaluation.json"))

    def _workspace_for_task(self, task_id: str) -> TaskWorkspace:
        if self._is_invalid_task_id(task_id):
            raise TaskNotFoundError(f"Task not found: {task_id}")
        path = (self.workspace_root / task_id).resolve()
        if self.workspace_root not in path.parents or not path.is_dir():
            raise TaskNotFoundError(f"Task not found: {task_id}")
        return TaskWorkspace(root=self.workspace_root, task_id=task_id)

    def _write_meta(self, workspace: TaskWorkspace, meta: dict[str, Any]) -> None:
        workspace.write_artifact("task_meta.json", json.dumps(meta, indent=2, ensure_ascii=False))

    def _display_workspace_path(self, workspace: TaskWorkspace) -> str:
        try:
            return workspace.path.relative_to(Path.cwd()).as_posix()
        except ValueError:
            return str(workspace.path)

    def _display_file_path(self, workspace: TaskWorkspace, artifact_name: str) -> str:
        path = workspace._safe_path(artifact_name)
        try:
            return path.relative_to(Path.cwd()).as_posix()
        except ValueError:
            return str(path)

    @staticmethod
    def _is_invalid_task_id(task_id: str) -> bool:
        return not task_id.startswith("task_") or "/" in task_id or "\\" in task_id or ".." in task_id

    @staticmethod
    def _is_invalid_artifact_name(artifact_name: str) -> bool:
        path = Path(artifact_name)
        return path.is_absolute() or ".." in path.parts or not artifact_name or artifact_name.endswith("/")

    @staticmethod
    def _preview(task: str, limit: int = 120) -> str:
        one_line = " ".join(task.strip().split())
        return one_line[:limit]

    @staticmethod
    def _now() -> str:
        return datetime.utcnow().replace(microsecond=0).isoformat()

    @staticmethod
    def _safe_error(exc: Exception) -> str:
        return f"{type(exc).__name__}: {exc}"[:500]

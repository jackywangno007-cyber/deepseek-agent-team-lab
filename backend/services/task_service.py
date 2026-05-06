from __future__ import annotations

import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

from rich.console import Console

from backend.agents.architect_agent import ArchitectAgent
from backend.agents.backend_agent import BackendAgent
from backend.agents.base_agent import AgentContext
from backend.agents.frontend_agent import FrontendAgent
from backend.agents.manager_agent import ManagerAgent
from backend.agents.product_agent import ProductAgent
from backend.agents.reviewer_agent import ReviewerAgent
from backend.agents.test_agent import TestAgent
from backend.config import load_settings
from backend.core.evaluator import Evaluator
from backend.core.event_bus import EventBus
from backend.core.llm_client import LLMClient
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


class InvalidAgentError(ValueError):
    pass


class FeedbackNotFoundError(LookupError):
    pass


class TaskService:
    STATUSES = {"CREATED", "RUNNING", "COMPLETED", "FAILED"}
    AGENT_BY_NAME = {
        "ProductAgent": ProductAgent,
        "ArchitectAgent": ArchitectAgent,
        "FrontendAgent": FrontendAgent,
        "BackendAgent": BackendAgent,
        "TestAgent": TestAgent,
        "ReviewerAgent": ReviewerAgent,
    }
    AGENT_OUTPUTS = {
        "ProductAgent": "prd.md",
        "ArchitectAgent": "architecture.md",
        "FrontendAgent": "frontend_plan.md",
        "BackendAgent": "api_design.md",
        "TestAgent": "test_plan.md",
        "ReviewerAgent": "review_report.md",
        "ManagerAgent": "final_summary.md",
    }
    DOWNSTREAM = {
        "ProductAgent": ["ArchitectAgent", "FrontendAgent", "BackendAgent", "TestAgent", "ReviewerAgent", "ManagerAgent"],
        "ArchitectAgent": ["FrontendAgent", "BackendAgent", "TestAgent", "ReviewerAgent", "ManagerAgent"],
        "FrontendAgent": ["TestAgent", "ReviewerAgent", "ManagerAgent"],
        "BackendAgent": ["TestAgent", "ReviewerAgent", "ManagerAgent"],
        "TestAgent": ["ReviewerAgent", "ManagerAgent"],
        "ReviewerAgent": ["ManagerAgent"],
        "ManagerAgent": [],
    }

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
            if relative_name.startswith("versions/"):
                continue
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

    def create_feedback(self, *, task_id: str, target_agent: str, target_artifact: str, content: str) -> dict[str, Any]:
        workspace = self._workspace_for_task(task_id)
        self.get_task_meta(task_id)
        if target_agent not in self.AGENT_OUTPUTS:
            raise InvalidAgentError(f"Invalid target agent: {target_agent}")
        if self._is_invalid_artifact_name(target_artifact):
            raise InvalidArtifactNameError(f"Invalid artifact name: {target_artifact}")
        if not workspace.artifact_exists(target_artifact):
            raise ArtifactNotFoundError(f"Artifact not found: {target_artifact}")
        expected_artifact = self.AGENT_OUTPUTS[target_agent]
        if expected_artifact != target_artifact:
            raise InvalidArtifactNameError(f"{target_agent} owns {expected_artifact}, not {target_artifact}")
        record = {
            "feedback_id": self._new_id("feedback"),
            "task_id": task_id,
            "target_agent": target_agent,
            "target_artifact": target_artifact,
            "content": content.strip(),
            "created_at": self._now(),
            "status": "PENDING",
        }
        self._append_jsonl(workspace, "human_feedback.jsonl", record)
        EventBus(workspace, self.console).emit(
            from_agent="Human",
            to_agent=target_agent,
            type="human_feedback_created",
            content=record["content"],
            artifact_refs=[target_artifact],
            status="created",
        )
        self._write_control_state(workspace, {"last_feedback_id": record["feedback_id"], "status": "FEEDBACK_PENDING"})
        self.update_task_meta(task_id)
        return record

    def list_feedback(self, task_id: str) -> list[dict[str, Any]]:
        workspace = self._workspace_for_task(task_id)
        self.get_task_meta(task_id)
        return self._read_jsonl(workspace, "human_feedback.jsonl")

    def request_revision(self, *, task_id: str, feedback_id: str, rerun_downstream: bool = True, run_async: bool = True) -> dict[str, Any]:
        workspace = self._workspace_for_task(task_id)
        feedback = self._get_feedback(task_id, feedback_id)
        revision = {
            "revision_id": self._new_id("revision"),
            "task_id": task_id,
            "feedback_id": feedback_id,
            "target_agent": feedback["target_agent"],
            "target_artifact": feedback["target_artifact"],
            "backup_artifact": None,
            "rerun_downstream": rerun_downstream,
            "status": "CREATED",
            "created_at": self._now(),
            "completed_at": None,
            "error": None,
        }
        self._append_jsonl(workspace, "revision_history.jsonl", revision)
        EventBus(workspace, self.console).emit(
            from_agent="Human",
            to_agent=feedback["target_agent"],
            type="revision_requested",
            content=f"Revision requested from feedback {feedback_id}",
            artifact_refs=[feedback["target_artifact"]],
            status="created",
        )
        self._write_control_state(workspace, {"last_revision_id": revision["revision_id"], "status": "REVISION_CREATED"})
        if run_async:
            self.update_task_meta(task_id, status="RUNNING", error=None)
        else:
            self.update_task_meta(task_id)
        return {"revision_id": revision["revision_id"], "status": "RUNNING" if run_async else "CREATED"}

    def run_revision_pipeline(self, *, task_id: str, revision_id: str) -> None:
        workspace = self._workspace_for_task(task_id)
        revision = self._get_revision(task_id, revision_id)
        feedback = self._get_feedback(task_id, revision["feedback_id"])
        event_bus = EventBus(workspace, self.console)
        self._update_revision(task_id, revision_id, status="RUNNING", error=None)
        self.update_task_meta(task_id, status="RUNNING", error=None)
        self._write_control_state(workspace, {"last_revision_id": revision_id, "status": "REVISION_RUNNING"})
        event_bus.emit(
            from_agent="RevisionController",
            to_agent=feedback["target_agent"],
            type="revision_started",
            content=f"Started revision {revision_id}",
            artifact_refs=[feedback["target_artifact"]],
            status="running",
        )
        try:
            backup = self._backup_artifact(workspace, feedback["target_artifact"], event_bus)
            self._update_revision(task_id, revision_id, backup_artifact=backup)
            self._rerun_agent_for_feedback(workspace, feedback)
            if revision["rerun_downstream"]:
                event_bus.emit(
                    from_agent="RevisionController",
                    type="downstream_rerun_started",
                    content=f"Rerunning downstream agents after {feedback['target_agent']}",
                    artifact_refs=[feedback["target_artifact"]],
                    status="running",
                )
                self._rerun_downstream(workspace, feedback["target_agent"], feedback["content"])
                event_bus.emit(
                    from_agent="RevisionController",
                    type="downstream_rerun_completed",
                    content=f"Downstream rerun completed after {feedback['target_agent']}",
                    artifact_refs=[],
                    status="succeeded",
                )
            Evaluator(workspace, event_bus).evaluate()
            self._update_feedback_status(task_id, feedback["feedback_id"], "APPLIED")
            self._update_revision(task_id, revision_id, status="COMPLETED", completed_at=self._now(), error=None)
            self._write_control_state(workspace, {"last_revision_id": revision_id, "status": "REVISION_COMPLETED"})
            event_bus.emit(
                from_agent="RevisionController",
                to_agent=feedback["target_agent"],
                type="revision_completed",
                content=f"Revision {revision_id} completed",
                artifact_refs=[feedback["target_artifact"]],
                status="succeeded",
            )
            self.update_task_meta(task_id, status="COMPLETED", error=None)
        except Exception as exc:
            error = self._safe_error(exc)
            self._update_feedback_status(task_id, feedback["feedback_id"], "FAILED")
            self._update_revision(task_id, revision_id, status="FAILED", completed_at=self._now(), error=error)
            self._write_control_state(workspace, {"last_revision_id": revision_id, "status": "REVISION_FAILED", "error": error})
            event_bus.emit(
                from_agent="RevisionController",
                to_agent=feedback["target_agent"],
                type="revision_failed",
                content=error,
                artifact_refs=[feedback["target_artifact"]],
                status="failed",
            )
            self.update_task_meta(task_id, status="FAILED", error=error)
            raise

    def list_revisions(self, task_id: str) -> list[dict[str, Any]]:
        workspace = self._workspace_for_task(task_id)
        self.get_task_meta(task_id)
        return self._read_jsonl(workspace, "revision_history.jsonl")

    def list_artifact_versions(self, task_id: str, artifact_name: str) -> list[dict[str, Any]]:
        if self._is_invalid_artifact_name(artifact_name):
            raise InvalidArtifactNameError(f"Invalid artifact name: {artifact_name}")
        workspace = self._workspace_for_task(task_id)
        self.get_task_meta(task_id)
        if not workspace.artifact_exists(artifact_name):
            raise ArtifactNotFoundError(f"Artifact not found: {artifact_name}")
        versions_dir = workspace._safe_path("versions")
        if not versions_dir.exists():
            return []
        stem = Path(artifact_name).stem
        suffix = Path(artifact_name).suffix
        versions = []
        for path in versions_dir.glob(f"{stem}.*{suffix}"):
            if not path.is_file():
                continue
            stat = path.stat()
            versions.append(
                {
                    "name": path.name,
                    "path": path.relative_to(workspace.path).as_posix(),
                    "size_bytes": stat.st_size,
                    "created_at": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                }
            )
        return sorted(versions, key=lambda item: item["created_at"], reverse=True)

    def read_artifact_version(self, task_id: str, artifact_name: str, version_name: str) -> str:
        if self._is_invalid_artifact_name(artifact_name) or self._is_invalid_version_name(version_name):
            raise InvalidArtifactNameError("Invalid artifact version path")
        workspace = self._workspace_for_task(task_id)
        self.get_task_meta(task_id)
        allowed = {version["name"] for version in self.list_artifact_versions(task_id, artifact_name)}
        if version_name not in allowed:
            raise ArtifactNotFoundError(f"Artifact version not found: {version_name}")
        return workspace.read_artifact(f"versions/{version_name}")

    def _workspace_for_task(self, task_id: str) -> TaskWorkspace:
        if self._is_invalid_task_id(task_id):
            raise TaskNotFoundError(f"Task not found: {task_id}")
        path = (self.workspace_root / task_id).resolve()
        if self.workspace_root not in path.parents or not path.is_dir():
            raise TaskNotFoundError(f"Task not found: {task_id}")
        return TaskWorkspace(root=self.workspace_root, task_id=task_id)

    def _make_context(self, workspace: TaskWorkspace) -> AgentContext:
        meta = json.loads(workspace.read_artifact("task_meta.json"))
        settings = load_settings(model_override=meta.get("model"))
        return AgentContext(
            user_task=workspace.read_artifact("task_input.md"),
            workspace=workspace,
            event_bus=EventBus(workspace, self.console),
            llm_client=LLMClient(settings, mock=bool(meta.get("mock", True))),
        )

    def _rerun_agent_for_feedback(self, workspace: TaskWorkspace, feedback: dict[str, Any]) -> None:
        context = self._make_context(workspace)
        agent_name = feedback["target_agent"]
        if agent_name == "ManagerAgent":
            ManagerAgent().create_final_summary(context)
            return
        agent = self.AGENT_BY_NAME[agent_name]()
        agent.run_revision(context, feedback["content"])

    def _rerun_downstream(self, workspace: TaskWorkspace, agent_name: str, feedback_content: str) -> None:
        context = self._make_context(workspace)
        manager = ManagerAgent()
        for downstream_agent_name in self.DOWNSTREAM[agent_name]:
            output_artifact = self.AGENT_OUTPUTS[downstream_agent_name]
            if workspace.artifact_exists(output_artifact):
                self._backup_artifact(workspace, output_artifact, context.event_bus)
            if downstream_agent_name == "ManagerAgent":
                manager.create_final_summary(context)
            else:
                agent = self.AGENT_BY_NAME[downstream_agent_name]()
                context.event_bus.emit(
                    from_agent="RevisionController",
                    to_agent=downstream_agent_name,
                    type="task_assign",
                    content=f"Rerun after human feedback: {feedback_content}",
                    artifact_refs=[output_artifact],
                    status="sent",
                )
                agent.run(context)

    def _backup_artifact(self, workspace: TaskWorkspace, artifact_name: str, event_bus: EventBus) -> str:
        if not workspace.artifact_exists(artifact_name):
            raise ArtifactNotFoundError(f"Artifact not found: {artifact_name}")
        source = workspace._safe_path(artifact_name)
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        artifact_path = Path(artifact_name)
        backup_name = f"{artifact_path.stem}.{stamp}{artifact_path.suffix}"
        backup_artifact = f"versions/{backup_name}"
        target = workspace._safe_path(backup_artifact)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
        event_bus.emit(
            from_agent="RevisionController",
            type="artifact_version_backup",
            content=f"Backed up {artifact_name} to {backup_artifact}",
            artifact_refs=[artifact_name, backup_artifact],
            status="created",
        )
        return backup_artifact

    def _get_feedback(self, task_id: str, feedback_id: str) -> dict[str, Any]:
        for feedback in self.list_feedback(task_id):
            if feedback.get("feedback_id") == feedback_id:
                return feedback
        raise FeedbackNotFoundError(f"Feedback not found: {feedback_id}")

    def _get_revision(self, task_id: str, revision_id: str) -> dict[str, Any]:
        for revision in self.list_revisions(task_id):
            if revision.get("revision_id") == revision_id:
                return revision
        raise FeedbackNotFoundError(f"Revision not found: {revision_id}")

    def _update_feedback_status(self, task_id: str, feedback_id: str, status: str) -> None:
        workspace = self._workspace_for_task(task_id)
        records = self._read_jsonl(workspace, "human_feedback.jsonl")
        for record in records:
            if record.get("feedback_id") == feedback_id:
                record["status"] = status
        self._write_jsonl(workspace, "human_feedback.jsonl", records)

    def _update_revision(self, task_id: str, revision_id: str, **updates: Any) -> None:
        workspace = self._workspace_for_task(task_id)
        records = self._read_jsonl(workspace, "revision_history.jsonl")
        for record in records:
            if record.get("revision_id") == revision_id:
                record.update(updates)
        self._write_jsonl(workspace, "revision_history.jsonl", records)

    def _append_jsonl(self, workspace: TaskWorkspace, artifact_name: str, record: dict[str, Any]) -> None:
        path = workspace._safe_path(artifact_name)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")

    def _read_jsonl(self, workspace: TaskWorkspace, artifact_name: str) -> list[dict[str, Any]]:
        path = workspace._safe_path(artifact_name)
        if not path.exists():
            return []
        return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]

    def _write_jsonl(self, workspace: TaskWorkspace, artifact_name: str, records: list[dict[str, Any]]) -> None:
        content = "".join(json.dumps(record, ensure_ascii=False) + "\n" for record in records)
        workspace.write_artifact(artifact_name, content)

    def _write_control_state(self, workspace: TaskWorkspace, state: dict[str, Any]) -> None:
        payload = {"updated_at": self._now(), **state}
        workspace.write_artifact("control_state.json", json.dumps(payload, indent=2, ensure_ascii=False))

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
    def _is_invalid_version_name(version_name: str) -> bool:
        path = Path(version_name)
        return path.is_absolute() or ".." in path.parts or "/" in version_name or "\\" in version_name or not version_name

    @staticmethod
    def _preview(task: str, limit: int = 120) -> str:
        one_line = " ".join(task.strip().split())
        return one_line[:limit]

    @staticmethod
    def _now() -> str:
        return datetime.utcnow().replace(microsecond=0).isoformat()

    @staticmethod
    def _new_id(prefix: str) -> str:
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"{prefix}_{stamp}_{uuid4().hex[:6]}"

    @staticmethod
    def _safe_error(exc: Exception) -> str:
        return f"{type(exc).__name__}: {exc}"[:500]

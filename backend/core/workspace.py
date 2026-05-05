from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from uuid import uuid4


class WorkspaceError(ValueError):
    pass


class TaskWorkspace:
    def __init__(self, root: str | Path = "workspace", task_id: str | None = None) -> None:
        self.root = Path(root).resolve()
        self.root.mkdir(parents=True, exist_ok=True)
        self.task_id = task_id or self._new_task_id()
        self.path = (self.root / self.task_id).resolve()
        self.path.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _new_task_id() -> str:
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"task_{stamp}_{uuid4().hex[:6]}"

    def _safe_path(self, artifact_name: str) -> Path:
        if not artifact_name or Path(artifact_name).is_absolute():
            raise WorkspaceError(f"Invalid artifact path: {artifact_name}")
        candidate = (self.path / artifact_name).resolve()
        if self.path not in candidate.parents and candidate != self.path:
            raise WorkspaceError(f"Path traversal blocked: {artifact_name}")
        return candidate

    def write_artifact(self, artifact_name: str, content: str) -> Path:
        target = self._safe_path(artifact_name)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        return target

    def write_json(self, artifact_name: str, payload: dict | list) -> Path:
        return self.write_artifact(artifact_name, json.dumps(payload, ensure_ascii=False, indent=2))

    def read_artifact(self, artifact_name: str) -> str:
        return self._safe_path(artifact_name).read_text(encoding="utf-8")

    def artifact_exists(self, artifact_name: str) -> bool:
        return self._safe_path(artifact_name).is_file()

    def list_artifacts(self) -> list[str]:
        files = [p.relative_to(self.path).as_posix() for p in self.path.rglob("*") if p.is_file()]
        return sorted(files)

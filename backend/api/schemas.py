from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str
    version: str


class CreateTaskRequest(BaseModel):
    task: str = Field(min_length=1)
    mock: bool = True
    model: Optional[str] = None
    run_async: bool = True


class CreateTaskResponse(BaseModel):
    task_id: str
    status: str
    workspace_path: str


class TaskListItem(BaseModel):
    task_id: str
    status: str
    created_at: str
    updated_at: str
    mock: bool
    model: str
    task_input_preview: str


class ListTasksResponse(BaseModel):
    tasks: list[TaskListItem]


class TaskStatusResponse(BaseModel):
    task_id: str
    status: str
    created_at: str
    updated_at: str
    workspace_path: str
    mock: bool
    model: str
    error: Optional[str] = None


class EventsResponse(BaseModel):
    task_id: str
    events: list[dict[str, Any]]


class ArtifactInfo(BaseModel):
    name: str
    path: str
    size_bytes: int
    modified_at: str


class ListArtifactsResponse(BaseModel):
    task_id: str
    artifacts: list[ArtifactInfo]


class ArtifactContentResponse(BaseModel):
    task_id: str
    artifact_name: str
    content: str


class EvaluationResponse(BaseModel):
    task_id: str
    evaluation: dict[str, Any]

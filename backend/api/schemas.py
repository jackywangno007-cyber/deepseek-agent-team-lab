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


class CreateFeedbackRequest(BaseModel):
    target_agent: str
    target_artifact: str
    content: str = Field(min_length=1)


class CreateFeedbackResponse(BaseModel):
    feedback_id: str
    status: str


class FeedbackRecord(BaseModel):
    feedback_id: str
    task_id: str
    target_agent: str
    target_artifact: str
    content: str
    created_at: str
    status: str


class ListFeedbackResponse(BaseModel):
    task_id: str
    feedback: list[FeedbackRecord]


class RevisionRequest(BaseModel):
    feedback_id: str
    rerun_downstream: bool = True
    run_async: bool = True


class RevisionResponse(BaseModel):
    revision_id: str
    status: str


class RevisionRecord(BaseModel):
    revision_id: str
    task_id: str
    feedback_id: str
    target_agent: str
    target_artifact: str
    backup_artifact: str | None = None
    rerun_downstream: bool
    status: str
    created_at: str
    completed_at: str | None = None
    error: str | None = None


class ListRevisionsResponse(BaseModel):
    task_id: str
    revisions: list[RevisionRecord]


class ArtifactVersionInfo(BaseModel):
    name: str
    path: str
    size_bytes: int
    created_at: str


class ListArtifactVersionsResponse(BaseModel):
    task_id: str
    artifact_name: str
    versions: list[ArtifactVersionInfo]


class ArtifactVersionContentResponse(BaseModel):
    task_id: str
    artifact_name: str
    version_name: str
    content: str


class GenerateImprovementsRequest(BaseModel):
    force: bool = False


class ImprovementSuggestion(BaseModel):
    suggestion_id: str
    task_id: str
    issue_summary: str
    responsible_agent: str
    target_artifact: str
    proposed_feedback: str
    severity: str
    reason: str
    source: str
    status: str
    created_at: str
    updated_at: str


class GenerateImprovementsResponse(BaseModel):
    task_id: str
    suggestions: list[ImprovementSuggestion]


class ListImprovementsResponse(BaseModel):
    task_id: str
    suggestions: list[ImprovementSuggestion]


class ApproveImprovementRequest(BaseModel):
    edited_feedback: str | None = None
    rerun_downstream: bool = True
    run_async: bool = True


class ApproveImprovementResponse(BaseModel):
    suggestion_id: str
    feedback_id: str
    revision_id: str
    status: str


class RejectImprovementRequest(BaseModel):
    reason: str | None = None


class RejectImprovementResponse(BaseModel):
    suggestion_id: str
    status: str


class ImprovementHistoryRecord(BaseModel):
    improvement_id: str
    task_id: str
    suggestion_id: str
    action: str
    responsible_agent: str
    target_artifact: str
    feedback_id: str | None = None
    revision_id: str | None = None
    before_evaluation: dict[str, Any]
    after_evaluation: dict[str, Any]
    status: str
    created_at: str
    completed_at: str | None = None
    error: str | None = None
    reason: str | None = None


class ImprovementHistoryResponse(BaseModel):
    task_id: str
    history: list[ImprovementHistoryRecord]


class EvaluationCompareResponse(BaseModel):
    task_id: str
    before: dict[str, Any]
    after: dict[str, Any]
    changed: bool
    summary: str

from __future__ import annotations

from fastapi import APIRouter, BackgroundTasks, HTTPException, Request

from backend.api.schemas import (
    ArtifactContentResponse,
    ArtifactVersionContentResponse,
    CreateTaskRequest,
    CreateTaskResponse,
    CreateFeedbackRequest,
    CreateFeedbackResponse,
    EvaluationResponse,
    EventsResponse,
    ListArtifactVersionsResponse,
    HealthResponse,
    ListFeedbackResponse,
    ListArtifactsResponse,
    ListRevisionsResponse,
    ListTasksResponse,
    RevisionRequest,
    RevisionResponse,
    TaskStatusResponse,
)
from backend.services.task_service import (
    ArtifactNotFoundError,
    EvaluationNotFoundError,
    FeedbackNotFoundError,
    InvalidAgentError,
    InvalidArtifactNameError,
    TaskNotFoundError,
    TaskService,
)

router = APIRouter()


def get_service(request: Request) -> TaskService:
    return request.app.state.task_service


@router.get("/health", response_model=HealthResponse)
def health() -> dict:
    return {"status": "ok", "version": "0.3.0"}


@router.post("/tasks", response_model=CreateTaskResponse)
def create_task(payload: CreateTaskRequest, background_tasks: BackgroundTasks, request: Request) -> dict:
    service = get_service(request)
    created = service.create_task(task=payload.task, mock=payload.mock, model=payload.model, run_async=payload.run_async)
    if payload.run_async:
        service.update_task_meta(
            created["task_id"],
            status="RUNNING",
            mock=created["mock"],
            model=created["settings"].deepseek_model,
            error=None,
        )
        background_tasks.add_task(
            service.run_task_pipeline,
            task_id=created["task_id"],
            task=payload.task,
            model=payload.model,
            mock=payload.mock,
        )
        status = "RUNNING"
    else:
        try:
            service.run_task_pipeline(
                task_id=created["task_id"],
                task=payload.task,
                model=payload.model,
                mock=payload.mock,
            )
        except Exception as exc:
            raise HTTPException(status_code=500, detail=service._safe_error(exc)) from exc
        status = "COMPLETED"
    return {"task_id": created["task_id"], "status": status, "workspace_path": created["workspace_path"]}


@router.get("/tasks", response_model=ListTasksResponse)
def list_tasks(request: Request) -> dict:
    tasks = [
        {
            "task_id": task["task_id"],
            "status": task["status"],
            "created_at": task["created_at"],
            "updated_at": task["updated_at"],
            "mock": task["mock"],
            "model": task["model"],
            "task_input_preview": task["task_input_preview"],
        }
        for task in get_service(request).list_tasks()
    ]
    return {"tasks": tasks}


@router.get("/tasks/{task_id}", response_model=TaskStatusResponse)
def get_task(task_id: str, request: Request) -> dict:
    try:
        meta = get_service(request).get_task_meta(task_id)
    except TaskNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Task not found") from exc
    return {
        "task_id": meta["task_id"],
        "status": meta["status"],
        "created_at": meta["created_at"],
        "updated_at": meta["updated_at"],
        "workspace_path": meta["workspace_path"],
        "mock": meta["mock"],
        "model": meta["model"],
        "error": meta.get("error"),
    }


@router.get("/tasks/{task_id}/events", response_model=EventsResponse)
def get_events(task_id: str, request: Request) -> dict:
    try:
        return {"task_id": task_id, "events": get_service(request).get_task_events(task_id)}
    except TaskNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Task not found") from exc


@router.get("/tasks/{task_id}/artifacts", response_model=ListArtifactsResponse)
def list_artifacts(task_id: str, request: Request) -> dict:
    try:
        return {"task_id": task_id, "artifacts": get_service(request).list_task_artifacts(task_id)}
    except TaskNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Task not found") from exc


@router.get("/tasks/{task_id}/artifacts/{artifact_name}", response_model=ArtifactContentResponse)
def read_artifact(task_id: str, artifact_name: str, request: Request) -> dict:
    try:
        content = get_service(request).read_task_artifact(task_id, artifact_name)
    except TaskNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Task not found") from exc
    except InvalidArtifactNameError as exc:
        raise HTTPException(status_code=400, detail="Invalid artifact name") from exc
    except ArtifactNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Artifact not found") from exc
    return {"task_id": task_id, "artifact_name": artifact_name, "content": content}


@router.get("/tasks/{task_id}/evaluation", response_model=EvaluationResponse)
def get_evaluation(task_id: str, request: Request) -> dict:
    try:
        return {"task_id": task_id, "evaluation": get_service(request).get_task_evaluation(task_id)}
    except TaskNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Task not found") from exc
    except EvaluationNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Evaluation not found") from exc


@router.post("/tasks/{task_id}/feedback", response_model=CreateFeedbackResponse)
def create_feedback(task_id: str, payload: CreateFeedbackRequest, request: Request) -> dict:
    service = get_service(request)
    try:
        feedback = service.create_feedback(
            task_id=task_id,
            target_agent=payload.target_agent,
            target_artifact=payload.target_artifact,
            content=payload.content,
        )
    except TaskNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Task not found") from exc
    except InvalidAgentError as exc:
        raise HTTPException(status_code=400, detail="Invalid target agent") from exc
    except InvalidArtifactNameError as exc:
        raise HTTPException(status_code=400, detail="Invalid artifact name") from exc
    except ArtifactNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Artifact not found") from exc
    return {"feedback_id": feedback["feedback_id"], "status": feedback["status"]}


@router.get("/tasks/{task_id}/feedback", response_model=ListFeedbackResponse)
def list_feedback(task_id: str, request: Request) -> dict:
    try:
        return {"task_id": task_id, "feedback": get_service(request).list_feedback(task_id)}
    except TaskNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Task not found") from exc


@router.post("/tasks/{task_id}/revisions", response_model=RevisionResponse)
def request_revision(task_id: str, payload: RevisionRequest, background_tasks: BackgroundTasks, request: Request) -> dict:
    service = get_service(request)
    try:
        revision = service.request_revision(
            task_id=task_id,
            feedback_id=payload.feedback_id,
            rerun_downstream=payload.rerun_downstream,
            run_async=payload.run_async,
        )
        if payload.run_async:
            background_tasks.add_task(service.run_revision_pipeline, task_id=task_id, revision_id=revision["revision_id"])
            status = "RUNNING"
        else:
            service.run_revision_pipeline(task_id=task_id, revision_id=revision["revision_id"])
            status = "COMPLETED"
    except TaskNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Task not found") from exc
    except FeedbackNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Feedback not found") from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=service._safe_error(exc)) from exc
    return {"revision_id": revision["revision_id"], "status": status}


@router.get("/tasks/{task_id}/revisions", response_model=ListRevisionsResponse)
def list_revisions(task_id: str, request: Request) -> dict:
    try:
        return {"task_id": task_id, "revisions": get_service(request).list_revisions(task_id)}
    except TaskNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Task not found") from exc


@router.get("/tasks/{task_id}/artifacts/{artifact_name}/versions", response_model=ListArtifactVersionsResponse)
def list_artifact_versions(task_id: str, artifact_name: str, request: Request) -> dict:
    try:
        versions = get_service(request).list_artifact_versions(task_id, artifact_name)
    except TaskNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Task not found") from exc
    except InvalidArtifactNameError as exc:
        raise HTTPException(status_code=400, detail="Invalid artifact name") from exc
    except ArtifactNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Artifact not found") from exc
    return {"task_id": task_id, "artifact_name": artifact_name, "versions": versions}


@router.get(
    "/tasks/{task_id}/artifacts/{artifact_name}/versions/{version_name}",
    response_model=ArtifactVersionContentResponse,
)
def read_artifact_version(task_id: str, artifact_name: str, version_name: str, request: Request) -> dict:
    try:
        content = get_service(request).read_artifact_version(task_id, artifact_name, version_name)
    except TaskNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Task not found") from exc
    except InvalidArtifactNameError as exc:
        raise HTTPException(status_code=400, detail="Invalid artifact version path") from exc
    except ArtifactNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Artifact version not found") from exc
    return {"task_id": task_id, "artifact_name": artifact_name, "version_name": version_name, "content": content}

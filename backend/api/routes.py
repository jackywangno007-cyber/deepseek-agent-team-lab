from __future__ import annotations

from fastapi import APIRouter, BackgroundTasks, HTTPException, Request

from backend.api.schemas import (
    ArtifactContentResponse,
    CreateTaskRequest,
    CreateTaskResponse,
    EvaluationResponse,
    EventsResponse,
    HealthResponse,
    ListArtifactsResponse,
    ListTasksResponse,
    TaskStatusResponse,
)
from backend.services.task_service import (
    ArtifactNotFoundError,
    EvaluationNotFoundError,
    InvalidArtifactNameError,
    TaskNotFoundError,
    TaskService,
)

router = APIRouter()


def get_service(request: Request) -> TaskService:
    return request.app.state.task_service


@router.get("/health", response_model=HealthResponse)
def health() -> dict:
    return {"status": "ok", "version": "0.2.0"}


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


@router.get("/tasks/{task_id}/artifacts/{artifact_name:path}", response_model=ArtifactContentResponse)
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

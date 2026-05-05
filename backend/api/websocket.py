from __future__ import annotations

import asyncio

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from backend.services.task_service import TaskNotFoundError, TaskService

router = APIRouter()


def get_service(websocket: WebSocket) -> TaskService:
    return websocket.app.state.task_service


@router.websocket("/ws/tasks/{task_id}/events")
async def stream_task_events(websocket: WebSocket, task_id: str) -> None:
    await websocket.accept()
    service = get_service(websocket)
    sent_count = 0
    try:
        service.get_task_meta(task_id)
        while True:
            events = service.get_task_events(task_id)
            for event in events[sent_count:]:
                await websocket.send_json({"type": "event", "data": event})
            sent_count = len(events)
            meta = service.get_task_meta(task_id)
            if meta["status"] in {"COMPLETED", "FAILED"}:
                await websocket.send_json({"type": "task_finished", "status": meta["status"]})
                break
            await asyncio.sleep(0.5)
    except TaskNotFoundError:
        await websocket.send_json({"type": "error", "message": "Task not found"})
    except WebSocketDisconnect:
        return
    finally:
        try:
            await websocket.close()
        except RuntimeError:
            pass

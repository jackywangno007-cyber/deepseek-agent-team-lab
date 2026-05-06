from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api.routes import router as api_router
from backend.api.websocket import router as websocket_router
from backend.services.task_service import TaskService


def create_app(task_service: TaskService | None = None) -> FastAPI:
    app = FastAPI(
        title="DeepSeek Agent Team Lab API",
        version="0.4.0",
        description="A lightweight local API service for multi-agent collaboration.",
    )
    app.state.task_service = task_service or TaskService()
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:5173",
            "http://127.0.0.1:5173",
            "http://localhost:3000",
            "http://127.0.0.1:3000",
        ],
        allow_origin_regex=r"^http://(localhost|127\.0\.0\.1):\d+$",
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(api_router, prefix="/api")
    app.include_router(websocket_router)
    return app


app = create_app()

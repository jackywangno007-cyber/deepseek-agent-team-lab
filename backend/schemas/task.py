from __future__ import annotations

from datetime import datetime
from typing import Dict, List, Literal

from pydantic import BaseModel, Field


class TaskStep(BaseModel):
    agent: str
    task: str
    input_artifacts: List[str] = Field(default_factory=list)
    output_artifact: str


class TaskPlan(BaseModel):
    goal: str
    pipeline: List[TaskStep]


class TaskRunResult(BaseModel):
    task_id: str
    workspace_path: str
    agent_status: Dict[str, Literal["succeeded", "failed"]]
    generated_artifacts: List[str]
    review_excerpt: str
    final_summary_path: str
    evaluation: dict
    created_at: datetime

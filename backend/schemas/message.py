from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class Event(BaseModel):
    task_id: str
    from_agent: str
    to_agent: Optional[str] = None
    type: str
    content: str
    artifact_refs: List[str] = Field(default_factory=list)
    status: str = "sent"
    created_at: datetime = Field(default_factory=datetime.utcnow)

from __future__ import annotations

from pydantic import BaseModel


class Artifact(BaseModel):
    name: str
    path: str
    content: str

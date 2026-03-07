from __future__ import annotations

from pydantic import BaseModel, Field

from .models import Provider


class Action(BaseModel):
    provider: Provider
    repo: str
    number: int


class AddLabel(Action):
    labels: list[str] = Field(default_factory=list)


class PostComment(Action):
    body: str


class SetStatus(Action):
    status: str

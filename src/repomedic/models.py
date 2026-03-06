from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class Provider(str, Enum):
    GITHUB = "github"
    BITBUCKET = "bitbucket"
    GITLAB = "gitlab"


class ItemType(str, Enum):
    ISSUE = "issue"
    PR = "pr"


class Priority(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class WorkItem(BaseModel):
    provider: Provider
    repo: str
    number: int
    title: str
    url: str
    item_type: ItemType
    updated_at: datetime
    body: str | None = None
    labels: list[str] = Field(default_factory=list)


class Finding(BaseModel):
    provider: Provider
    repo: str
    number: int
    title: str
    url: str
    item_type: ItemType
    days_since_update: int
    blocked: bool
    stale: bool
    priority: Priority
    suggested_labels: list[str]
    suggested_comment: str
    updated_at: datetime

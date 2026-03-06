from __future__ import annotations

from datetime import datetime
from enum import Enum
from pydantic import BaseModel


class ItemType(str, Enum):
    ISSUE = "issue"
    PR = "pr"


class Priority(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class Finding(BaseModel):
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

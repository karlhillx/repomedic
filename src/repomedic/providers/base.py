from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Iterable

from ..actions import Action
from ..models import WorkItem


class ProviderAdapter(ABC):
    name: str

    @abstractmethod
    def iter_work_items(self, repo: str, max_items_per_type: int) -> Iterable[WorkItem]:
        """Return normalized issue + PR items for the given repo."""

    @abstractmethod
    def apply_actions(self, actions: list[Action], dry_run: bool = True) -> None:
        """Apply provider-specific actions (comment/label/status)."""

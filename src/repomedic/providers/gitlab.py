from __future__ import annotations

from typing import Iterable

from ..actions import Action
from ..models import WorkItem
from .base import ProviderAdapter


class GitLabAdapter(ProviderAdapter):
    name = "gitlab"

    def iter_work_items(self, repo: str, max_items_per_type: int) -> Iterable[WorkItem]:
        _ = repo
        _ = max_items_per_type
        raise NotImplementedError("GitLab adapter fetch is not implemented yet.")

    def apply_actions(self, actions: list[Action], dry_run: bool = True) -> None:
        _ = actions
        _ = dry_run

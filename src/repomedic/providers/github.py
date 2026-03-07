from __future__ import annotations

import os
from typing import Iterable

from github import Github

from ..actions import Action
from ..models import ItemType, Provider, WorkItem
from .base import ProviderAdapter


class GitHubAdapter(ProviderAdapter):
    name = Provider.GITHUB.value

    def __init__(self, token: str | None = None) -> None:
        self.token = token or os.getenv("GITHUB_TOKEN")
        if not self.token:
            raise RuntimeError("Missing GitHub token. Set GITHUB_TOKEN.")
        self.client = Github(self.token)

    def iter_work_items(self, repo: str, max_items_per_type: int) -> Iterable[WorkItem]:
        gh_repo = self.client.get_repo(repo)

        issue_count = 0
        for issue in gh_repo.get_issues(state="open", sort="updated", direction="desc"):
            if issue.pull_request is not None:
                continue
            if issue_count >= max_items_per_type:
                break
            yield WorkItem(
                provider=Provider.GITHUB,
                repo=repo,
                number=issue.number,
                title=issue.title,
                url=issue.html_url,
                item_type=ItemType.ISSUE,
                updated_at=issue.updated_at,
                body=issue.body,
                labels=[lbl.name for lbl in issue.labels],
            )
            issue_count += 1

        pr_count = 0
        for pr in gh_repo.get_pulls(state="open", sort="updated", direction="desc"):
            if pr_count >= max_items_per_type:
                break
            yield WorkItem(
                provider=Provider.GITHUB,
                repo=repo,
                number=pr.number,
                title=pr.title,
                url=pr.html_url,
                item_type=ItemType.PR,
                updated_at=pr.updated_at,
                body=pr.body,
                labels=[lbl.name for lbl in pr.labels],
            )
            pr_count += 1

    def apply_actions(self, actions: list[Action], dry_run: bool = True) -> None:
        # Deliberately no-op for now; engine exposes normalized actions.
        # Next step: map AddLabel/PostComment/SetStatus to GitHub API calls.
        _ = actions
        _ = dry_run

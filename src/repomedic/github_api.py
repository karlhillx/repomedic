from __future__ import annotations

import os
from typing import Iterable

from github import Github


class GitHubAPI:
    def __init__(self, token: str | None = None) -> None:
        self.token = token or os.getenv("GITHUB_TOKEN")
        if not self.token:
            raise RuntimeError("Missing GitHub token. Set GITHUB_TOKEN.")
        self.client = Github(self.token)

    def iter_issues(self, repo_full_name: str) -> Iterable:
        repo = self.client.get_repo(repo_full_name)
        for issue in repo.get_issues(state="open", sort="updated", direction="desc"):
            if issue.pull_request is None:
                yield issue

    def iter_prs(self, repo_full_name: str) -> Iterable:
        repo = self.client.get_repo(repo_full_name)
        for pr in repo.get_pulls(state="open", sort="updated", direction="desc"):
            yield pr

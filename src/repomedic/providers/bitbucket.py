from __future__ import annotations

import os
from typing import Iterable

import httpx
from dateutil.parser import isoparse

from ..actions import Action
from ..models import ItemType, Provider, WorkItem
from .base import ProviderAdapter


class BitbucketAdapter(ProviderAdapter):
    name = Provider.BITBUCKET.value

    def __init__(self) -> None:
        self.token = os.getenv("BITBUCKET_TOKEN")
        self.username = os.getenv("BITBUCKET_USERNAME")
        self.app_password = os.getenv("BITBUCKET_APP_PASSWORD")
        if not self.token and not (self.username and self.app_password):
            raise RuntimeError(
                "Missing Bitbucket auth. Set BITBUCKET_TOKEN or BITBUCKET_USERNAME + BITBUCKET_APP_PASSWORD."
            )

    def _client(self) -> httpx.Client:
        headers = {"Accept": "application/json"}
        auth = None
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        else:
            auth = (self.username, self.app_password)
        return httpx.Client(headers=headers, auth=auth, timeout=30)

    @staticmethod
    def _split_repo(repo_full_name: str) -> tuple[str, str]:
        parts = repo_full_name.split("/")
        if len(parts) != 2:
            raise ValueError("Bitbucket repo must be workspace/repo_slug")
        return parts[0], parts[1]

    def _iter_issues(self, client: httpx.Client, workspace: str, repo_slug: str, max_items: int) -> Iterable[WorkItem]:
        url = f"https://api.bitbucket.org/2.0/repositories/{workspace}/{repo_slug}/issues"
        params = {"q": 'state="new" OR state="open"', "sort": "-updated_on", "pagelen": min(100, max_items)}
        r = client.get(url, params=params)
        r.raise_for_status()
        data = r.json()
        for row in data.get("values", [])[:max_items]:
            yield WorkItem(
                provider=Provider.BITBUCKET,
                repo=f"{workspace}/{repo_slug}",
                number=int(row.get("id", 0)),
                title=row.get("title", "(no title)"),
                url=row.get("links", {}).get("html", {}).get("href", ""),
                item_type=ItemType.ISSUE,
                updated_at=isoparse(row.get("updated_on")),
                body=row.get("content", {}).get("raw"),
                labels=[str(row.get("kind", "")).strip()] if row.get("kind") else [],
            )

    def _iter_prs(self, client: httpx.Client, workspace: str, repo_slug: str, max_items: int) -> Iterable[WorkItem]:
        url = f"https://api.bitbucket.org/2.0/repositories/{workspace}/{repo_slug}/pullrequests"
        params = {"state": "OPEN", "sort": "-updated_on", "pagelen": min(100, max_items)}
        r = client.get(url, params=params)
        r.raise_for_status()
        data = r.json()
        for row in data.get("values", [])[:max_items]:
            yield WorkItem(
                provider=Provider.BITBUCKET,
                repo=f"{workspace}/{repo_slug}",
                number=int(row.get("id", 0)),
                title=row.get("title", "(no title)"),
                url=row.get("links", {}).get("html", {}).get("href", ""),
                item_type=ItemType.PR,
                updated_at=isoparse(row.get("updated_on")),
                body=(row.get("summary") or {}).get("raw"),
                labels=[],
            )

    def iter_work_items(self, repo: str, max_items_per_type: int) -> Iterable[WorkItem]:
        workspace, repo_slug = self._split_repo(repo)
        with self._client() as client:
            yield from self._iter_issues(client, workspace, repo_slug, max_items_per_type)
            yield from self._iter_prs(client, workspace, repo_slug, max_items_per_type)

    def apply_actions(self, actions: list[Action], dry_run: bool = True) -> None:
        _ = actions
        _ = dry_run

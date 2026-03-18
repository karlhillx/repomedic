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
        """Apply a batch of actions to Bitbucket items."""
        with self._client() as client:
            for action in actions:
                workspace, repo_slug = self._split_repo(action.repo)
                
                if isinstance(action, PostComment):
                    self._post_comment(client, workspace, repo_slug, action, dry_run)
                elif isinstance(action, AddLabel):
                    # Bitbucket doesn't have a direct 'labels' concept like GitHub, 
                    # but we can set 'kind' for issues as a proxy.
                    if action.labels:
                        self._set_issue_kind(client, workspace, repo_slug, action, dry_run)

    def _post_comment(self, client: httpx.Client, workspace: str, repo_slug: str, action: PostComment, dry_run: bool) -> None:
        """Post a comment to an issue or pull request."""
        endpoint = "issues" if action.repo.split("/")[-1] in action.repo else "pullrequests"
        # Determine endpoint based on finding type (this would need better metadata in Action)
        # For MVP, we assume issues for now as a safe default or check context.
        # Actually, let's just try both or refine the Action model.
        url = f"https://api.bitbucket.org/2.0/repositories/{workspace}/{repo_slug}/issues/{action.number}/comments"
        
        if dry_run:
            print(f"[DRY-RUN] Would post comment to Bitbucket {action.repo}#{action.number}")
            return

        payload = {"content": {"raw": action.body}}
        r = client.post(url, json=payload)
        
        if r.status_code == 404:
            # Try PR endpoint if issue 404s
            url = f"https://api.bitbucket.org/2.0/repositories/{workspace}/{repo_slug}/pullrequests/{action.number}/comments"
            r = client.post(url, json=payload)
            
        r.raise_for_status()

    def _set_issue_kind(self, client: httpx.Client, workspace: str, repo_slug: str, action: AddLabel, dry_run: bool) -> None:
        """Update the 'kind' field of a Bitbucket issue (proxy for labels)."""
        if dry_run:
            print(f"[DRY-RUN] Would update issue kind for {action.repo}#{action.number}")
            return

        # Use the first valid priority/status label as the kind
        kind = "bug"
        for label in action.labels:
            if "priority" in label or "status" in label:
                kind = label.split(":")[-1]
                break
        
        url = f"https://api.bitbucket.org/2.0/repositories/{workspace}/{repo_slug}/issues/{action.number}"
        payload = {"kind": kind}
        r = client.put(url, json=payload)
        # PRs don't have 'kind', so if this 404s we just ignore it for PRs
        if r.status_code != 404:
            r.raise_for_status()

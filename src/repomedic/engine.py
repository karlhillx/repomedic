from __future__ import annotations

from pydantic import BaseModel, Field

from .actions import AddLabel, PostComment
from .models import Finding
from .providers.base import ProviderAdapter
from .scoring import analyze_work_item


class EngineResult(BaseModel):
    findings: list[Finding] = Field(default_factory=list)
    actions: list[AddLabel | PostComment] = Field(default_factory=list)


class RepoMedicEngine:
    def __init__(self, adapter: ProviderAdapter, stale_after_days: int = 10) -> None:
        self.adapter = adapter
        self.stale_after_days = stale_after_days

    def scan_repos(self, repos: list[str], max_items_per_repo: int) -> EngineResult:
        findings: list[Finding] = []
        actions: list[AddLabel | PostComment] = []

        for repo in repos:
            for item in self.adapter.iter_work_items(repo=repo, max_items_per_type=max_items_per_repo):
                finding = analyze_work_item(item, stale_after_days=self.stale_after_days)
                findings.append(finding)
                actions.append(
                    AddLabel(
                        provider=finding.provider,
                        repo=finding.repo,
                        number=finding.number,
                        labels=finding.suggested_labels,
                    )
                )
                actions.append(
                    PostComment(
                        provider=finding.provider,
                        repo=finding.repo,
                        number=finding.number,
                        body=finding.suggested_comment,
                    )
                )

        return EngineResult(findings=findings, actions=actions)

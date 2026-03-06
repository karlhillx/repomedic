from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated

import typer
from pydantic import BaseModel

from .analyzer import analyze_item
from .github_api import GitHubAPI
from .models import Finding, ItemType

app = typer.Typer(help="Scan repos for stale/blocked work and draft next actions.")


class ScanConfig(BaseModel):
    repos: list[str]
    stale_after_days: int = 10
    max_items_per_repo: int = 100


def _load_config(path: Path | None, repos: list[str], stale_after_days: int, max_items_per_repo: int) -> ScanConfig:
    if path:
        raw = json.loads(path.read_text(encoding="utf-8"))
        return ScanConfig.model_validate(raw)
    return ScanConfig(repos=repos, stale_after_days=stale_after_days, max_items_per_repo=max_items_per_repo)


@app.command()
def scan(
    repos: Annotated[list[str] | None, typer.Option("--repo", help="owner/repo (repeatable)")] = None,
    config: Annotated[Path | None, typer.Option("--config", help="Path to JSON config")] = None,
    stale_after_days: Annotated[int, typer.Option("--stale-after-days")] = 10,
    max_items_per_repo: Annotated[int, typer.Option("--max-items-per-repo")] = 100,
    limit: Annotated[int, typer.Option("--limit", help="Max findings to print")] = 50,
    as_json: Annotated[bool, typer.Option("--json", help="Output JSON")] = False,
) -> None:
    cfg = _load_config(config, repos or [], stale_after_days, max_items_per_repo)
    if not cfg.repos:
        raise typer.BadParameter("No repos provided. Use --repo owner/name or --config.")

    gh = GitHubAPI()
    findings: list[Finding] = []

    for repo_name in cfg.repos:
        issue_count = 0
        for issue in gh.iter_issues(repo_name):
            if issue_count >= cfg.max_items_per_repo:
                break
            findings.append(
                analyze_item(
                    repo=repo_name,
                    number=issue.number,
                    title=issue.title,
                    url=issue.html_url,
                    item_type=ItemType.ISSUE,
                    updated_at=issue.updated_at,
                    body=issue.body,
                    labels=[lbl.name for lbl in issue.labels],
                    stale_after_days=cfg.stale_after_days,
                )
            )
            issue_count += 1

        pr_count = 0
        for pr in gh.iter_prs(repo_name):
            if pr_count >= cfg.max_items_per_repo:
                break
            findings.append(
                analyze_item(
                    repo=repo_name,
                    number=pr.number,
                    title=pr.title,
                    url=pr.html_url,
                    item_type=ItemType.PR,
                    updated_at=pr.updated_at,
                    body=pr.body,
                    labels=[lbl.name for lbl in pr.labels],
                    stale_after_days=cfg.stale_after_days,
                )
            )
            pr_count += 1

    findings = sorted(
        findings,
        key=lambda f: (f.priority.value != "high", f.days_since_update * -1),
    )[:limit]

    if as_json:
        typer.echo(json.dumps([f.model_dump(mode="json") for f in findings], indent=2, default=str))
        return

    if not findings:
        typer.echo("No actionable stale/blocked items found.")
        return

    for f in findings:
        typer.echo(
            f"[{f.priority.value.upper()}] {f.repo} #{f.number} ({f.item_type.value}) — {f.title}\n"
            f"  updated: {f.days_since_update}d ago | blocked={f.blocked} | stale={f.stale}\n"
            f"  labels: {', '.join(f.suggested_labels)}\n"
            f"  next: {f.suggested_comment}\n"
            f"  url: {f.url}\n"
        )


if __name__ == "__main__":
    app()

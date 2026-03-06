from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated

import typer
from pydantic import BaseModel

from .engine import RepoMedicEngine
from .models import Finding, Provider
from .providers import BitbucketAdapter, GitHubAdapter, GitLabAdapter, ProviderAdapter

app = typer.Typer(help="Scan repos for stale/blocked work and draft next actions.")


class ScanConfig(BaseModel):
    repos: list[str]
    stale_after_days: int = 10
    max_items_per_repo: int = 100
    provider: Provider = Provider.GITHUB


def _load_config(path: Path | None, repos: list[str], stale_after_days: int, max_items_per_repo: int, provider: Provider) -> ScanConfig:
    if path:
        raw = json.loads(path.read_text(encoding="utf-8"))
        return ScanConfig.model_validate(raw)
    return ScanConfig(
        repos=repos,
        stale_after_days=stale_after_days,
        max_items_per_repo=max_items_per_repo,
        provider=provider,
    )


def _build_adapter(provider: Provider) -> ProviderAdapter:
    if provider == Provider.GITHUB:
        return GitHubAdapter()
    if provider == Provider.BITBUCKET:
        return BitbucketAdapter()
    if provider == Provider.GITLAB:
        return GitLabAdapter()
    raise typer.BadParameter(f"Unsupported provider: {provider}")


@app.command()
def scan(
    repos: Annotated[list[str] | None, typer.Option("--repo", help="owner/repo (repeatable)")] = None,
    config: Annotated[Path | None, typer.Option("--config", help="Path to JSON config")] = None,
    provider: Annotated[Provider, typer.Option("--provider", help="github|gitlab|bitbucket")] = Provider.GITHUB,
    stale_after_days: Annotated[int, typer.Option("--stale-after-days")] = 10,
    max_items_per_repo: Annotated[int, typer.Option("--max-items-per-repo")] = 100,
    limit: Annotated[int, typer.Option("--limit", help="Max findings to print")] = 50,
    as_json: Annotated[bool, typer.Option("--json", help="Output JSON")] = False,
    dry_run: Annotated[bool, typer.Option("--dry-run/--no-dry-run", help="Preview only; no provider writes")] = True,
    apply: Annotated[bool, typer.Option("--apply", help="Apply provider actions (overrides dry-run)")] = False,
) -> None:
    cfg = _load_config(config, repos or [], stale_after_days, max_items_per_repo, provider)
    if not cfg.repos:
        raise typer.BadParameter("No repos provided. Use --repo owner/name or --config.")

    adapter = _build_adapter(cfg.provider)
    engine = RepoMedicEngine(adapter=adapter, stale_after_days=cfg.stale_after_days)
    result = engine.scan_repos(repos=cfg.repos, max_items_per_repo=cfg.max_items_per_repo)

    findings: list[Finding] = sorted(
        result.findings,
        key=lambda f: (f.priority.value != "high", f.days_since_update * -1),
    )[:limit]

    selected_keys = {(f.repo, f.number) for f in findings}
    selected_actions = [a for a in result.actions if (a.repo, a.number) in selected_keys]

    effective_dry_run = False if apply else dry_run
    if not effective_dry_run:
        adapter.apply_actions(selected_actions, dry_run=False)

    if as_json:
        payload = {
            "provider": cfg.provider.value,
            "apply": apply,
            "dry_run": effective_dry_run,
            "findings": [f.model_dump(mode="json") for f in findings],
            "actions_count": len(selected_actions),
        }
        typer.echo(json.dumps(payload, indent=2, default=str))
        return

    if not findings:
        typer.echo("No actionable stale/blocked items found.")
        return

    mode = "APPLY" if not effective_dry_run else "DRY-RUN"
    typer.echo(f"Mode: {mode} | provider={cfg.provider.value} | actions={len(selected_actions)}")

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

from __future__ import annotations

from datetime import datetime, timezone
from typing import Iterable

from .models import Finding, Priority, WorkItem

BLOCKED_MARKERS = (
    "blocked",
    "waiting",
    "needs decision",
    "needs info",
    "needs reproduction",
)


def days_since(dt: datetime) -> int:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return int((datetime.now(timezone.utc) - dt).total_seconds() // 86400)


def is_blocked(title: str, body: str | None, labels: Iterable[str]) -> bool:
    txt = f"{title}\n{body or ''}\n{' '.join(labels)}".lower()
    return any(m in txt for m in BLOCKED_MARKERS)


def priority(item_type: str, blocked: bool, stale_days: int) -> Priority:
    if blocked and stale_days >= 3:
        return Priority.HIGH
    if item_type == "pr" and stale_days >= 7:
        return Priority.HIGH
    if stale_days >= 14:
        return Priority.MEDIUM
    return Priority.LOW


def suggested_labels(stale: bool, blocked: bool, level: Priority) -> list[str]:
    out = [f"priority:{level.value}"]
    if stale:
        out.append("stale:needs-triage")
    if blocked:
        out.append("status:blocked")
    return out


def suggested_comment(item_type: str, stale_days: int, blocked: bool) -> str:
    kind = "PR" if item_type == "pr" else "issue"
    if blocked:
        return (
            f"Maintenance ping: this {kind} looks blocked and inactive for {stale_days} days. "
            "Can we unblock with a specific owner + next action by end of day?"
        )
    return (
        f"Maintenance ping: this {kind} has been inactive for {stale_days} days. "
        "Should we close, re-scope, or assign a concrete next step?"
    )


def analyze_work_item(item: WorkItem, stale_after_days: int) -> Finding:
    days = days_since(item.updated_at)
    blocked = is_blocked(item.title, item.body, item.labels)
    stale = days >= stale_after_days
    lvl = priority(item.item_type.value, blocked, days)
    return Finding(
        provider=item.provider,
        repo=item.repo,
        number=item.number,
        title=item.title,
        url=item.url,
        item_type=item.item_type,
        days_since_update=days,
        blocked=blocked,
        stale=stale,
        priority=lvl,
        suggested_labels=suggested_labels(stale, blocked, lvl),
        suggested_comment=suggested_comment(item.item_type.value, days, blocked),
        updated_at=item.updated_at,
    )

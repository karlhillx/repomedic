from __future__ import annotations

from datetime import datetime, timezone
from typing import Iterable

from .models import Finding, ItemType, Priority

BLOCKED_MARKERS = (
    "blocked",
    "waiting",
    "needs decision",
    "needs info",
    "needs reproduction",
)


def _days_since(dt: datetime) -> int:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return int((datetime.now(timezone.utc) - dt).total_seconds() // 86400)


def _is_blocked(title: str, body: str | None, labels: Iterable[str]) -> bool:
    txt = f"{title}\n{body or ''}\n{' '.join(labels)}".lower()
    return any(m in txt for m in BLOCKED_MARKERS)


def _priority(item_type: ItemType, blocked: bool, stale_days: int) -> Priority:
    if blocked and stale_days >= 3:
        return Priority.HIGH
    if item_type == ItemType.PR and stale_days >= 7:
        return Priority.HIGH
    if stale_days >= 14:
        return Priority.MEDIUM
    return Priority.LOW


def _labels(stale: bool, blocked: bool, priority: Priority) -> list[str]:
    out = [f"priority:{priority.value}"]
    if stale:
        out.append("stale:needs-triage")
    if blocked:
        out.append("status:blocked")
    return out


def _comment(item_type: ItemType, stale_days: int, blocked: bool) -> str:
    kind = "PR" if item_type == ItemType.PR else "issue"
    if blocked:
        return (
            f"Maintenance ping: this {kind} looks blocked and inactive for {stale_days} days. "
            "Can we unblock with a specific owner + next action by end of day?"
        )
    return (
        f"Maintenance ping: this {kind} has been inactive for {stale_days} days. "
        "Should we close, re-scope, or assign a concrete next step?"
    )


def analyze_item(*, repo: str, number: int, title: str, url: str, item_type: ItemType, updated_at: datetime, body: str | None, labels: list[str], stale_after_days: int) -> Finding:
    days = _days_since(updated_at)
    blocked = _is_blocked(title, body, labels)
    stale = days >= stale_after_days
    priority = _priority(item_type, blocked, days)
    return Finding(
        repo=repo,
        number=number,
        title=title,
        url=url,
        item_type=item_type,
        days_since_update=days,
        blocked=blocked,
        stale=stale,
        priority=priority,
        suggested_labels=_labels(stale, blocked, priority),
        suggested_comment=_comment(item_type, days, blocked),
        updated_at=updated_at,
    )

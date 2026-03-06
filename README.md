# RepoMedic

**Stop backlog drift. Keep delivery velocity.**

RepoMedic is a **cross-provider maintenance copilot** that scans issues + PRs, detects stale/blocked risk, and produces action-ready triage recommendations your team can execute immediately.

---

## What it does

RepoMedic continuously answers:

- What’s stale and silently rotting?
- What’s blocked and needs escalation?
- What should be triaged **first**?
- What concrete action should happen next?

Output includes:

- `high | medium | low` priority
- stale/blocked signals
- suggested labels
- drafted next-step comments
- machine-readable JSON for automation

---

## Why teams like it

- **Cross-platform by design** — one core engine, many providers
- **Consistent triage policy** — same scoring logic everywhere
- **Safe rollout** — dry-run by default
- **Automation-ready** — CI and bot friendly output
- **Extensible** — add adapters without touching core scoring

---

## Built for multiple repo products

RepoMedic is intentionally not tied to one vendor.

### Current provider adapters

- `github` → fetch + apply labels/comments
- `bitbucket` → fetch implemented
- `gitlab` → scaffold in place

### Next adapters (easy to add)

- Jira
- Linear
- Azure DevOps
- Internal tools with API endpoints

The model stays shared (`WorkItem`, actions, scoring). Only provider connectors vary.

---

## Quickstart

```bash
cd repomedic
python3 -m venv .venv
source .venv/bin/activate
pip install -e .

# GitHub auth example
export GITHUB_TOKEN=ghp_xxx

# GitHub default
repomedic scan --repo owner/repo --repo owner/repo2

# Explicit provider
repomedic scan --provider github --repo owner/repo
repomedic scan --provider bitbucket --repo workspace/repo_slug

# Config-driven run
repomedic scan --config examples/config.json

# JSON for pipelines
repomedic scan --config examples/config.json --json

# Dry run (default)
repomedic scan --provider github --repo owner/repo --dry-run

# Apply actions (GitHub labels/comments implemented)
repomedic scan --provider github --repo owner/repo --apply
```

---

## Extensibility (adapter architecture)

Core (shared across all providers):

- `engine.py` — orchestration and planning
- `scoring.py` — stale/blocked/risk logic
- `models.py` — normalized entities (`WorkItem`, `Finding`)
- `actions.py` — normalized intents (`AddLabel`, `PostComment`, `SetStatus`)

Provider layer:

- `providers/base.py` — adapter contract
- `providers/github.py`
- `providers/bitbucket.py`
- `providers/gitlab.py`

### Add a provider in 4 steps

1. Implement `ProviderAdapter`
2. Map source records → `WorkItem`
3. Map action intents → provider API operations
4. Register in CLI provider selector

No core scoring rewrite needed.

---

## Who this is for

- **Engineering Managers** — keep maintenance debt visible and prioritized
- **Tech Leads** — standardize triage across teams and platforms
- **Maintainers** — get actionable daily cleanup queues

---

## CI / pipeline integration

`bitbucket-pipelines.yml` is included for smoke checks.

```bash
make setup
make scan REPO=owner/repo
# or
make scan CONFIG=examples/config.json
make ci
```

Bitbucket remote setup:

```bash
git remote add bitbucket https://<username>@bitbucket.org/<workspace>/repomedic.git
git push -u bitbucket main
```

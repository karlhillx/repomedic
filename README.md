# RepoMedic

**RepoMedic is your cross-platform maintenance copilot for engineering backlogs.**

It scans issues and PRs across repository providers, scores maintenance risk (stale, blocked, high-priority), and turns the signal into concrete next actions.

Instead of manually triaging dozens of tabs, you get a prioritized action list in one run.

---

## Why teams use it

- **One triage brain, many repo platforms**
- **Consistent scoring** for stale/blocked/risk across providers
- **Action-ready output** (labels, comments, status intents)
- **Automation-friendly** JSON output for CI and bots
- **Safe by default** (dry-run first, apply when ready)

RepoMedic is built for real maintenance workflows: noisy backlogs, aging PRs, and limited reviewer bandwidth.

## Provider versatility

RepoMedic is intentionally **not GitHub-only**.

Current adapter status:

- `github` → fetch + apply labels/comments
- `bitbucket` → fetch implemented
- `gitlab` → scaffold in place

Planned/possible next adapters:

- Jira
- Linear
- Azure DevOps
- Any internal tracker with API access

The architecture is adapter-based, so adding a provider means implementing a connector—not rewriting core scoring logic.

---

## Quick start

```bash
cd repomedic
python3 -m venv .venv
source .venv/bin/activate
pip install -e .

# GitHub auth example
export GITHUB_TOKEN=ghp_xxx

# Scan repos (GitHub default)
repomedic scan --repo owner/repo --repo owner/repo2

# Pick provider explicitly
repomedic scan --provider github --repo owner/repo
repomedic scan --provider bitbucket --repo workspace/repo_slug

# Config-driven run
repomedic scan --config examples/config.json

# JSON output for automation
repomedic scan --config examples/config.json --json

# Explicit dry-run (default)
repomedic scan --provider github --repo owner/repo --dry-run

# Apply actions (GitHub adapter currently supports labels/comments)
repomedic scan --provider github --repo owner/repo --apply
```

## What you get per item

- priority: `high | medium | low`
- stale/blocked flags
- suggested labels
- drafted next-step comment

---

## Extensible architecture

Core modules:

- `engine.py` → shared orchestration and planning
- `scoring.py` → stale/blocked/risk logic (provider-agnostic)
- `models.py` → normalized `WorkItem`/`Finding` models
- `actions.py` → normalized action intents (`AddLabel`, `PostComment`, `SetStatus`)

Provider modules:

- `providers/base.py` → adapter contract
- `providers/github.py`
- `providers/bitbucket.py`
- `providers/gitlab.py`

### Add a new provider

1. Implement `ProviderAdapter` in `providers/<your_provider>.py`
2. Normalize source data into `WorkItem`
3. Map action intents back to provider-native API operations
4. Register adapter in CLI provider selection

That’s it—the scoring engine and prioritization stay shared.

---

## CI / pipelines

This repo includes `bitbucket-pipelines.yml` for CI smoke checks.

### Bitbucket remote setup

```bash
git remote add bitbucket https://<username>@bitbucket.org/<workspace>/repomedic.git
git push -u bitbucket main
```

### Makefile shortcuts

```bash
make setup
make scan REPO=owner/repo
# or
make scan CONFIG=examples/config.json
make ci
```

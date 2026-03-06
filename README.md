# RepoMedic

RepoMedic scans repository work items (issues + PRs) across providers, prioritizes maintenance risk, and drafts actionable next steps so teams can keep shipping.

## Why
Maintenance debt piles up. This gives you a daily triage shortlist with priority and concrete actions.

## Quick start

```bash
cd repomedic
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
export GITHUB_TOKEN=ghp_xxx

# Option A: direct repos (GitHub default)
repomedic scan --repo owner/repo --repo owner/repo2

# Option B: pick provider explicitly
repomedic scan --provider github --repo owner/repo
repomedic scan --provider bitbucket --repo workspace/repo_slug

# Option C: config file
repomedic scan --config examples/config.json

# JSON output for automation
repomedic scan --config examples/config.json --json

# Explicit dry-run (default)
repomedic scan --provider github --repo owner/repo --dry-run

# Apply labels/comments (GitHub adapter implemented; overrides dry-run)
repomedic scan --provider github --repo owner/repo --apply
```

## Output includes
- priority (`high|medium|low`)
- stale/blocked flags
- suggested labels
- drafted next-step comment

## Architecture
- Shared core engine (`engine.py`) for analysis + action planning
- Normalized model (`WorkItem`) used by every provider adapter
- Provider adapters:
  - `providers/github.py` (fetch + apply labels/comments)
  - `providers/bitbucket.py` (fetch implemented)
  - `providers/gitlab.py` (scaffold)
- Shared scoring logic (`scoring.py`) for stale/blocked/risk
- Normalized action intents (`actions.py`) for comment/label/status flows

## MVP scope delivered
- Open issue + PR scan per repo
- stale/blocked detection heuristics
- priority scoring
- actionable comment drafting

## Bitbucket-ready

This repo now includes `bitbucket-pipelines.yml` for CI smoke checks.

### Push to Bitbucket

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

### Required repo variable

If you run scans in Bitbucket Pipelines, add this Repository Variable:
- `GITHUB_TOKEN` = GitHub token with read access to target repos

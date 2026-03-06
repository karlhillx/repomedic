# RepoMedic

RepoMedic scans GitHub repositories for stale issues and PRs, prioritizes maintenance risk, and drafts actionable next steps so teams can keep shipping.

## Why
Maintenance debt piles up. This gives you a daily triage shortlist with priority and concrete actions.

## Quick start

```bash
cd repomedic
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
export GITHUB_TOKEN=ghp_xxx

# Option A: direct repos
repomedic scan --repo owner/repo --repo owner/repo2

# Option B: config file
repomedic scan --config examples/config.json

# JSON output for automation
repomedic scan --config examples/config.json --json
```

## Output includes
- priority (`high|medium|low`)
- stale/blocked flags
- suggested labels
- drafted next-step comment

## MVP scope delivered
- Open issue + PR scan per repo
- stale/blocked detection heuristics
- priority scoring
- actionable comment drafting

# Issue Tracker: GitLab

**Type:** GitLab Issues

**CLI:** `glab` (GitLab CLI)

**Location:** Repo → Issues on GitLab (gitlab.com or self-hosted)

## Setup

Install and authenticate:

```bash
# Install (Linux/macOS)
curl -sL https://gitlab.com/gitlab-org/cli/releases/download/v1.36.0/glab-cli-v1.36.0-linux-amd64.tar.gz | tar xz
sudo mv bin/glab /usr/local/bin/

# Authenticate
glab auth login --hostname gitlab.com
```

## Reading Issues

```bash
# List open issues
glab issue list

# View specific issue
glab issue view <number>

# Filter by label
glab issue list --label "needs-triage"
```

## Writing Issues

```bash
# Create issue
glab issue create --title "Bug: checkout fails" --description "Steps to reproduce..."

# Create with labels
glab issue create --label "bug" --label "needs-triage"
```

## Triage Integration

The triage skill reads labels via `glab issue list --label <label>` and updates via `glab issue update <number> --add-label` / `--remove-label`.

## Workflow

1. **Read:** `glab issue list` → shows all issues
2. **Triage:** Read issue, apply labels via `glab issue update`
3. **Create:** `glab issue create` with description
4. **Close:** `glab issue close <number>`
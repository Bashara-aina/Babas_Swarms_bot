---
name: code-review-swarm
description: Deploy specialized AI agents to perform comprehensive, intelligent code reviews that go beyond traditional static analysis
type: development
color: blue
capabilities:
  - automated_multi_agent_code_review
  - security_vulnerability_analysis
  - performance_bottleneck_detection
  - architecture_pattern_validation
  - style_and_convention_enforcement
tools:
  - Bash
  - Read
  - Write
  - TodoWrite
  - Grep
  - Glob
  - mcp__github__create_pull_request_review
  - mcp__github__get_pull_request
  - mcp__github__get_pull_request_files
  - mcp__github__list_pull_requests
priority: high
hooks:
  pre: |
    echo "🚀 [Code Review Swarm] starting: $TASK"

    # GitHub authentication
    echo "Initializing multi-agent review system"
    gh auth status || (echo "GitHub CLI not authenticated" && exit 1)

  post: |
    echo "✨ [Code Review Swarm] completed: $TASK"

    # Standard post-checks
    echo "Review results posted to GitHub"
    echo "Quality gates evaluated"
---

# Code Review Swarm - Automated Code Review with AI Agents

## Overview
Deploy specialized AI agents to perform comprehensive, intelligent code reviews that go beyond traditional static analysis.

## Core Features

### 1. Multi-Agent Review System
```bash
# Initialize code review swarm with gh CLI
# Get PR details
PR_DATA=$(gh pr view 123 --json files,additions,deletions,title,body)
PR_DIFF=$(gh pr diff 123)

# Post initial review status
gh pr comment 123 --body "🔍 Multi-agent code review initiated"
```

### 2. Specialized Review Agents

#### Security Agent
```bash
# Security-focused review with gh CLI
# Get changed files
CHANGED_FILES=$(gh pr view 123 --json files --jq '.files[].path')

# Run security review
# Post security findings
if echo "$SECURITY_RESULTS" | grep -q "critical"; then
  # Request changes for critical issues
  gh pr review 123 --request-changes --body "$SECURITY_RESULTS"
  # Add security label
  gh pr edit 123 --add-label "security-review-required"
else
  # Post as comment for non-critical issues
  gh pr comment 123 --body "$SECURITY_RESULTS"
fi
```

## See also

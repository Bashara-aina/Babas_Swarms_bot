---
allowed-tools: Read,Bash,Grep,Glob
argument-hint: [files...]
description: "Code review. Reviews changes, identifies issues, suggests improvements. Without args: staged changes."
---

# /review — Code review

Review code changes for quality, correctness, and best practices.

## Steps

1. If no args: run `git diff --staged` to see staged changes
2. If args provided: read each file listed
3. Run the review checklist against each changed file
4. Check for: correctness, edge cases, async correctness, type hints, docstrings
5. Run `ruff check <file>` and `pyright <file>` on each changed file
6. Report findings grouped by severity (P0/P1/P2)
7. If critical issues found: `git diff --staged | gitnexus_detect_changes` to check blast radius

## Usage
```
/review
/review handlers/ai.py
/review --staged
```

## Review Checklist

### Correctness
- [ ] Does it do what it claims?
- [ ] Are edge cases handled?
- [ ] Are errors handled properly?
- [ ] Are there race conditions?

### Best Practices
- [ ] Async/await used correctly?
- [ ] Type hints present?
- [ ] Docstrings on public methods?
- [ ] No hardcoded secrets?

### Security
- [ ] Input validation?
- [ ] No SQL injection risk?
- [ ] API keys via env vars?

### Testing
- [ ] Tests cover main cases?
- [ ] Tests are maintainable?
- [ ] Coverage acceptable?

## Output Format
```
## CHANGES_REVIEWED
<files and summary>

## ISSUES_FOUND
- [CRITICAL] file:line — description
- [HIGH] file:line — description
- [MEDIUM] file:line — description
- [LOW] file:line — description

## APPROVAL
APPROVED / CHANGES_REQUESTED / BLOCKED

## SUGGESTIONS
<improvement ideas>
```

## Swarm-Bot Review Focus
- All LLM calls via llm_client.py (not direct litellm)
- Telegram HTML escaping with html.escape()
- Async patterns (no threading)
- Memory system consistency

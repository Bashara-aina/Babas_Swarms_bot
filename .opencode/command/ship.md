---
allowed-tools: Read,Bash,Grep,Glob,Edit,Write
argument-hint: <files-or-task>
description: "Ship a task end-to-end: plan, implement, test, review, and prepare for deploy."
---

# /ship — End-to-end delivery

Full lifecycle command: takes a task and drives it to completion.

## Usage
```
/ship add handler for /status command
/ship implement LLM rate limit handling
```

## Ship Pipeline
```
1. PLAN — analyze task, create plan
2. IMPLEMENT — write code
3. TEST — add and run tests
4. REVIEW — self-review for issues
5. PREPARE — staged, diff verified, ready to commit
```

## Plan Phase
- Break task into smallest safe steps
- Identify all files to change
- Estimate risk

## Implement Phase
- Execute step by step
- Write tests alongside code
- Verify each step

## Test Phase
```bash
pytest tests/ -x --asyncio-mode=auto -q
```

## Review Phase
- Check for issues from /review checklist
- Verify no secrets committed
- Confirm diff looks right

## Prepare Phase
```
/commit  # or report what's needed for commit
```

## Swarm-Bot Ship Context
- Telegram bot (aiogram 3.x)
- systemd deployment
- All LLM via llm_client.py
- pytest-asyncio tests

## Constraints
- Task must be well-scoped
- Scope creep = stop and re-plan
- All tests must pass
- No known bugs in shipped code

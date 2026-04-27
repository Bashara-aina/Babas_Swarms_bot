---
allowed-tools: Read,Bash,Grep,Glob,Edit,Write
argument-hint: <error-description>
description: "Diagnose and fix a bug. Runs tests, inspects error, proposes and applies fixes."
---

# /fix — Diagnose and fix a bug

Investigate a bug and implement a fix.

## Usage
```
/fix bot not responding to /help
/fix tests failing in test_memory.py
/fix LLM calls timing out
```

## Workflow
```
1. Reproduce — get exact error or behavior
2. Locate — find the relevant code
3. Understand — trace the root cause
4. Fix — implement the solution
5. Verify — run tests to confirm fix
```

## Bug Report Template
```
## SYMPTOM
<exact error message or unexpected behavior>

## LOCATION
<file:line where issue manifests>

## ROOT_CAUSE
<why this is happening>

## FIX
<what was changed>

## VERIFICATION
<test output proving fix>
```

## Swarm-Bot Testing
```bash
# Run specific test
pytest tests/test_memory.py -x -v

# Run all tests
pytest tests/ -x --asyncio-mode=auto -q
```

## Constraints
- Always write a test that reproduces the bug
- Fix must not break other tests
- Document the root cause in the commit

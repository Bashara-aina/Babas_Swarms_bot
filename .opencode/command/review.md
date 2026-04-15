---
description: >-
  Run deep code review with specialized sub-agents for different review aspects.
  Invokes code-reviewer, comment-analyzer, type-design-analyzer, and
  silent-failure-hunter in sequence. Use after any significant code change.
mode: primary
model: minimax-coding-plan/MiniMax-M2.7
---
# /review — Deep Code Review Pipeline

## WHEN TO USE

Use `/review` when:
- Code change affects multiple modules
- Security-sensitive code was modified
- Major refactoring was done
- You want comprehensive review across multiple dimensions
- Post-PR review before merging

## REVIEW PIPELINE

The /review command runs these specialized agents in sequence:

### 1. @code-reviewer
Catches:
- Security vulnerabilities
- Logic errors
- Race conditions
- Resource leaks
- Missing error handling

### 2. @comment-analyzer
Catches:
- Inaccurate/misleading comments
- Missing docstrings
- Technical debt (TODOs, commented code)
- Outdated documentation

### 3. @type-design-analyzer
Catches:
- Weak invariant expression
- Encapsulation issues
- Type safety problems
- API surface issues

### 4. @silent-failure-hunter
Catches:
- Swallowed exceptions
- Silent failures
- Inadequate error handling
- Inappropriate fallback behavior

### 5. @test-coverage-analyzer
Catches:
- Missing test coverage
- Edge cases not tested
- Integration gaps

## USAGE

```
/review [scope]

Scopes:
/review                    — review all staged/uncommitted changes
/review [file]            — review specific file
/review [dir]             — review all files in directory
/review [module]          — review specific module
/review --full            — full codebase review (slow)
```

## WHAT YOU GET

```
## REVIEW REPORT: [scope]

### @code-reviewer
[issues found with file:line references]

### @comment-analyzer
[documentation issues found]

### @type-design-analyzer
[type design issues found]

### @silent-failure-hunter
[error handling issues found]

### @test-coverage-analyzer
[coverage gaps found]

### OVERALL
High priority: [N]
Medium priority: [N]
Low priority: [N]
Recommendation: [APPROVE / CHANGES REQUIRED / BLOCKED]
```

## EXAMPLE

```
/review handlers/ai.py
```

Response:
```
## REVIEW REPORT: handlers/ai.py

### @code-reviewer
✅ No high-priority issues
⚠️ 2 medium-priority: unused import line 42, long function 200+ lines
ℹ️ 3 low-priority: style suggestions

### @comment-analyzer
✅ Docstrings complete for public API
ℹ️ 1 TODO comment in deprecated function

### @type-design-analyzer
✅ Type annotations present
⚠️ 1 missing invariant expression in MessageHandler class

### @silent-failure-hunter
❌ 1 silent failure: line 89 try/except swallows AttributeError

### @test-coverage-analyzer
✅ 85% coverage for handlers/ai.py
⚠️ 3 edge cases missing test

### OVERALL
CHANGES REQUIRED — 1 blocker (silent failure)
```

## ANTI-HALLUCINATION RULES

1. **Cite actual code** — paste actual lines with issues
2. **Distinguish severity** — don't conflate LOW with HIGH
3. **Show evidence** — grep output, test results
4. **Be actionable** — each issue needs specific fix
5. **Verify fixes** — after fix, re-run relevant agent

## STATUS
```
REVIEW STATUS: ✅ COMPLETE | ❌ ISSUES FOUND
Scope: [what was reviewed]
High priority: [N]
Medium priority: [N]
Low priority: [N]
```

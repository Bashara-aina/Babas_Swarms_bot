# Defense in Depth

## Principle

Don't rely on a single defense. Layer multiple independent protections so that if one fails, another catches the issue.

## Layers (from outermost to innermost)

### 1. Input Validation
- Validate at system boundaries (user input, API calls, file reads)
- Reject invalid input early with clear error messages
- Use type hints and schema validation

### 2. Business Logic Guards
- Assert preconditions at the start of critical functions
- Assert postconditions after state mutations
- Fail fast — don't propagate invalid state

### 3. Error Handling
- Handle expected failure modes explicitly
- Don't swallow exceptions (no bare `except:`)
- Log errors with context for debugging

### 4. Monitoring & Alerting
- Track error rates and anomalous patterns
- Alert on persistent failures
- Session activity tracking for audit trail

### 5. Testing
- Unit tests for individual components
- Integration tests for system boundaries
- Property-based tests for invariants

## Application to AI Coding

### Hook Layer Defense
```
PreToolUse hooks  → validate command/file before execution
PostToolUse hooks → capture observations after execution
PreCompact        → consolidate patterns for learning
SessionEnd        → final evaluation and audit
```

### Code Layer Defense
```
Type hints       → catch type errors at lint time
ruff linting     → catch style and logic issues
pytest           → catch behavioral regressions
gitnexus impact  → catch unexpected side effects
```

## Verification

- Each layer should be independently testable
- If a layer fails, the next should still catch issues
- No single point of failure in the defense chain

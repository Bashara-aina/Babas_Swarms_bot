# Refactoring Candidates

## Signs That Need Refactoring

### Duplication
Same logic repeated in multiple places → extract to shared function

### Deep Module Violations
Function with many parameters → group into struct

### Mixed Concerns
Function doing multiple things → split into focused functions

### Complex Conditionals
Long if/else chains → consider polymorphism or table-driven approach

### Temporary Field
Object property set only in certain conditions → use strategy pattern

## Refactoring Safety

### Before Refactoring
- [ ] All tests passing (GREEN)
- [ ] Understand what the code does
- [ ] Have tests covering the behavior

### During Refactoring
- [ ] Run tests after each small change
- [ ] Make one change at a time
- [ ] Commit before each refactor step

### After Refactoring
- [ ] All tests still passing
- [ ] Code is cleaner than before
- [ ] Behavior unchanged

## TDD Refactor Cycle

```
┌─────────────────────────────────────┐
│ 1. RED  → Write failing test        │
│ 2. GREEN → Minimal code to pass     │
│ 3. REFACTOR → Clean up code         │
└─────────────────────────────────────┘
         ↑                     │
         └─────────────────────┘
```

## What to Refactor

| Category | Action |
|----------|--------|
| Duplication | Extract to function |
| Long method | Split by responsibility |
| Many parameters | Group into object |
| Deep class | Apply Deep Module principle |
| Feature envy | Move function to where it belongs |
| Shotgun surgery | Move behavior to single location |

## Rules

1. **Never refactor while RED** - get to GREEN first
2. **One refactor at a time** - commit between each
3. **Tests are your safety net** - if they fail, you've broken behavior
4. **Smell, don't tells** - use code smells as hints, not rules
# Root Cause Tracing

## Method

When debugging a failure, trace the ROOT cause — don't fix symptoms.

## The 5-Why Protocol

For any bug, ask "why?" at least 5 times:

1. What broke? (symptom)
2. Why did that break? (direct cause)
3. Why did that cause exist? (mechanism)
4. Why was that mechanism in place? (design decision)
5. Why was that decision made? (root cause)

## Trace Types

### Forward Trace (symptom → cause)
Start at the failure point and follow the call stack backward:
1. What error/behavior was observed?
2. What function produced it?
3. What inputs did that function receive?
4. Where did those inputs come from?
5. What should they have been?

### Backward Trace (cause → symptom)
Start at a suspicious code path and trace forward:
1. What does this code do?
2. What inputs could make it behave incorrectly?
3. What would the output look like?
4. Would that output cause the observed failure?

## Verification

After identifying root cause:
1. Fix the root cause, not the symptom
2. Add a test that would catch the bug
3. Verify the test fails without the fix
4. Verify the test passes with the fix
5. Run full test suite to check for regressions

## Anti-Patterns

- Stopping at "human error" (code review miss, tired engineer) — this is never the root cause
- Adding validation instead of fixing the source — validation hides the bug
- Blaming "edge case" — edge cases are just unhandled states

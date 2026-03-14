# Systematic Debugging

## Step 1: Reproduce
- Get the exact error message and full traceback
- Identify the minimal steps to reproduce
- Check: does it happen consistently or intermittently?

## Step 2: Isolate
- Which file and line number does the error originate from?
- What are the input values at the crash point?
- Is it a logic error, type error, or external dependency failure?

## Step 3: Hypothesize & Test
- Form a specific hypothesis about the root cause
- Test ONE change at a time
- Use print/logging to verify assumptions about variable state

## Step 4: Fix & Verify
- Make the minimal fix that addresses the root cause
- Don't fix symptoms — fix the underlying problem
- Verify the fix with the original reproduction steps
- Check for similar patterns elsewhere in the codebase

## PyTorch-Specific
- NaN values: check loss function inputs, learning rate, gradient clipping
- OOM: reduce batch size, use gradient checkpointing, check tensor accumulation
- CUDA errors: verify tensor device consistency (.to(device))
- Shape mismatches: print tensor shapes at each layer boundary

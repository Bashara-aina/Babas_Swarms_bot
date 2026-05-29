---
name: independent-auditor
description: Systematic code auditing without external diagnosis. Use when asked to "find bugs", "audit code", "review independently", or "check what's wrong" — applies methodical bug-finding to go through code line-by-line asking "what could be wrong here" on every path. Activates automatically when task involves finding bugs without a pre-provided diagnosis.
---

# Independent Auditor — Bug Finding Without External Diagnosis

## The Core Problem

You were a **fix delivery system**: read code → apply Opus's diagnosis → implement fix.
You never independently went through code asking "what could be wrong here."

**Opus's advantage**: Methodical exhaustive attention across normalization pathways, tensor shape contracts, and config-gating logic.

**Your gap**: You only looked at sections Opus flagged, never verified independently.

This skill makes you an independent auditor — the same methodology Opus applies.

---

## The Audit Mindset

```
❌ WRONG: "Here's what Opus told me to fix"
✅ RIGHT: "Here's what I found by reading the code myself"
```

**Before every statement of fact, ask:**
- Did I read this function? Did I trace every path?
- Did I verify the tensor shapes match what the caller expects?
- Did I check every normalization branch?
- Did I look at the config gating logic?

**If NO → you don't know yet, keep reading**

---

## The 7-Layer Audit Method

### Layer 1: Triage — What Type of Code Is This?

Before diving in, assess the domain:

| Code Type | Primary Bug Patterns |
|-----------|---------------------|
| **ML/Loss functions** | Normalization paths, tensor shapes, gradient flow, Kendall weight handling |
| **API endpoints** | Input validation, auth checks, error handling, SQL injection |
| **Auth flows** | Token validation, timing attacks, session handling |
| **Config parsing** | Missing fields, type coercion, cascade logic |
| **Database queries** | N+1, injection, transaction boundaries |
| **Async/Concurrency** | Race conditions, deadlocks, callback hell |
| **Serialization** | Schema mismatches, version drift |

### Layer 2: Entry Points — Trace the Data Flow

For every public/exported function:
1. What are the input types? Are they validated?
2. What are the output types? Do they match caller expectations?
3. Are there side effects (mutations, I/O, state changes)?
4. What are the error exit paths?

**Critical question**: "If caller passes X, what happens?"

### Layer 3: Normalization & Transform Paths

**For ML code specifically:**
- Trace every normalization branch (if/elif/else chains)
- Are weight divisions happening in correct order?
- Is staged-training guard actually blocking the problematic path?
- Are tensor shapes verified before operations?

**Audit checklist for loss functions:**
- [ ] Every normalization branch reached?
- [ ] Kendall weights divided correctly (not double-divided)?
- [ ] Staged-training guards not bypassed?
- [ ] Gradient flow verified?
- [ ] Shape contracts checked at each operation?

### Layer 4: Config & State Dependencies

- What config fields does this code depend on?
- Are defaults safe when config is missing?
- Is config validation on startup or at use time?
- Are there implicit dependencies (file order, import order)?

### Layer 5: Edge Cases & Error Paths

**Go through every branch manually:**
1. If/elif/else — trace both branches
2. Try/except — what errors are caught? What slips through?
3. Early returns — do they leak resources or skip cleanup?
4. None checks — what if input is None? Empty? Zero?

**Question**: "What would make this code crash in production?"

### Layer 6: Callers & External Contracts

- What do callers expect? Does this code deliver it?
- Are there breaking changes in function signatures?
- Is inheritance handled correctly (super() calls)?
- Are there Liskov violations (subclass promises broken)?

### Layer 7: Security & Safety Check

**For every function, ask:**
- Can user input reach here? Is it sanitized?
- Are there injection vectors (SQL, shell, path)?
- Are there timing attacks possible?
- Is sensitive data logged?
- Are there resource leaks (file handles, connections)?

---

## Tensor Shape Verification (ML Audit Specific)

**Shapes must be verified at every boundary:**
```
Input shape → Expected operation → Output shape
     ↓              ↓                  ↓
  Verified?    Operation valid?   Verified?
```

**Common tensor bugs:**
- Broadcasting without intentional shape match
- Matmul where last dim != second-to-last of other tensor
- Softmax over wrong axis
- Loss computed on logits vs probabilities
- Gradient not flowing to detached node

---

## The 20-Minute Audit Protocol

For any file you need to audit independently:

```
1.  READ the file from top to bottom — no skipping
2.  WRITE DOWN each function's contract as you go
3.  FOR EACH FUNCTION ask:
    - What could go wrong here?
    - What if input is None? Empty? Wrong type?
    - Are shapes correct?
    - Are weights handled correctly?
    - Is staged-training respected?
4.  TRACE all call sites — where is this function called?
5.  CHECK all branches — if/else, try/except
6.  VERIFY all assumptions — does reality match your mental model?
7.  REPORT findings with EXACT line numbers and code snippets
```

---

## Bug Severity Classification

| Severity | Definition | Example |
|----------|------------|---------|
| **CRITICAL** | Data loss, security breach, crash | SQL injection, unvalidated auth |
| **HIGH** | Wrong behavior, silent corruption | Kendall weights double-divided, shape mismatch |
| **MEDIUM** | Suboptimal, performance issue | N+1 query, unnecessary clone |
| **LOW** | Style, readability, minor risk | Missing docs, inconsistent naming |

---

## Reporting Format

When reporting bugs found independently:

```markdown
## Audit: [filename]

**Summary**: [1 sentence what the code does]

### Bug #1: [Descriptive Title]
**Severity**: CRITICAL/HIGH/MEDIUM/LOW
**Location**: Line XX

**Description**: [What the bug is and why it's wrong]

**Impact**: [What happens if this bug occurs]

**Evidence**:
```python
# Line YY-ZZ — the problematic code
code snippet
```

**Suggested Fix**: [How to fix it]
```

---

## Mental Checkpoints

**Before finishing any audit:**

1. Did I read ALL functions, not just the ones that looked suspicious?
2. Did I check ALL normalization branches (not just the happy path)?
3. Did I verify tensor shapes where applicable?
4. Did I check config gating logic?
5. Did I trace the staged-training guard paths?
6. Did I look at error handling paths?
7. Did I ask "what could be wrong here" for each function?

**If ANY answer is NO → keep reading**

---

## The Key Shift

```
BEFORE: "Opus found 5 bugs in losses.py, let me fix them"
AFTER:  "Let me read losses.py and find what I can"
```

The second approach is slower. You might miss some bugs.
But you will find them INDEPENDENTLY — and that's what makes you an auditor, not a fix delivery system.

---

## When to Use This Skill

**Always use when:**
- User asks to "find bugs" in code
- User asks to "audit" a file or module
- User asks what's wrong without providing a diagnosis
- User says "can you check if there's an issue here"

**Do NOT use when:**
- User already provides specific diagnosis to implement
- User says "fix the bug Opus found" — that's not auditing, that's implementing

---

## Practice Exercise

For losses.py (or any ML loss file):

1. **Triage**: "This is a loss function — watch for normalization paths and tensor shapes"
2. **Read cold**: Go through every function, writing down contracts
3. **Check paths**: For each branch, ask "is this handled correctly?"
4. **Verify shapes**: For tensor operations, check if shapes align
5. **Check guards**: For staged-training flags, trace if they're respected
6. **Report**: List all bugs found with exact locations

If you find fewer than Opus did, that's honest — but you've found SOME bugs independently. That's the point.

---

## Remember

**The goal is independent discovery, not perfect detection.**

You will not find every bug every time. Neither does Opus.
But if you systematically go through code asking "what could be wrong here",
you will find real bugs that would have been missed.

That's the difference between being a fix delivery system and being an auditor.
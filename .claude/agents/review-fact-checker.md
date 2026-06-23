---
name: review-fact-checker
description: Verifies every claim in a review draft against vault sources before submission.
type: agent
---

# Review Fact Checker Subagent

## Purpose

Verifies every claim in a review draft against vault sources. Used before submitting reviews.

## Invoked By

- `/om-self-review` — before finalizing self-assessment
- `/om-review-peer` — before peer review submission

## How It Works

1. Takes review draft text
2. For each claim, searches vault for supporting evidence
3. Flags claims without sufficient evidence
4. Suggests additional evidence sources

## Usage

```
/review-fact-checker
Review: perf/reviews/self-review-2026-q2.md
```

## Output Format

```
# Review Fact Checker Report

Review: perf/reviews/self-review-2026-q2.md

## Verified Claims

✅ "Auth architecture praised by Sarah" — confirmed
   Evidence: [[work/1-1/sarah-2026-05-05]], [[perf/brag/2026-q2]]

✅ "Reduced P1 incidents by 50%" — confirmed
   Evidence: [[work/incidents/]] count comparison Q1 vs Q2

⚠️ "Led API contract definition" — partial evidence
   Found: [[brain/Key Decisions/api-contract-2026]] mentions involvement
   Missing: direct evidence of leadership role

❌ "Mentored 2 junior engineers" — no evidence found
   Suggestion: Add 1:1 notes with junior engineers or git pairing history

## Claims Needing More Evidence

1. API contract leadership — add link to decision note or 1:1
2. Mentoring — gather evidence from 1:1s or work samples

## Summary

6 claims verified, 1 partial, 1 missing evidence
Confidence: 85%

Recommendations:
- Add evidence for partial claim
- Gather mentoring evidence or remove claim
```

## Notes for Claude

- Search work/, brain/, perf/ for evidence
- Use QMD semantic search if available
- Be strict — don't verify without evidence
- Flag partial claims vs missing claims differently
- Preserve original claim text when flagging
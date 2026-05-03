---
allowed-tools: Read,Bash,Grep,Glob
argument-hint: <topic>
description: "CEO review: analyze business logic, architecture decisions, and cost/benefit tradeoffs."
---

# /plan-ceo-review — Business logic review

Review a technical decision from a business perspective: cost, benefit, risk, and strategic fit.

## Steps

1. Identify the decision or change being proposed from the argument
2. Analyze cost: API costs, infra costs, development time, maintenance burden
3. Analyze benefit: user value, developer productivity, strategic positioning
4. Analyze risk: failure modes, vendor lock-in, complexity, timeline
5. Check if similar decisions were made before: search `.wiki/decisions/`
6. Produce a structured recommendation: GO / NO-GO / CONDITIONAL with specific criteria
7. Include: cost estimate, timeline, rollback plan, success metrics

## Usage
```
/plan-ceo-review migrate to new LLM provider
/plan-ceo-review add persistent memory to agents
/plan-ceo-review implement multi-tenant support
```

## Review Dimensions

### Cost
- Infrastructure cost (API calls, compute, storage)
- Development cost (time, complexity)
- Maintenance cost (ongoing effort)

### Benefit
- User-facing improvement
- Developer productivity
- Strategic advantage

### Risk
- Technical risk (complexity, reliability)
- Migration risk (breaking changes)
- Vendor risk (dependency lock-in)

### Strategic Fit
- Alignment with product direction
- Technical debt implications
- Extensibility

## Output Format
```
## PROPOSAL
<what's being evaluated>

## COST_BENEFIT
- Pros: ...
- Cons: ...

## RISK_assessment
- LOW/MEDIUM/HIGH

## RECOMMENDATION
<go/no-go/iterate>
```

## Constraints
- Business-agnostic technical advice only
- Does not make final decisions
- Highlights tradeoffs clearly

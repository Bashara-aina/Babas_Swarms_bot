---
title: freemium-gate
type: concept
status: active
tags: [freemium, business, monetization, premium]
created: 2026-04-13
updated: 2026-04-13
summary: Freemium gate controls access to premium features based on user tier, budget allocation, or subscription status.
wikilinks: [[projects/cekwajar-id.md], [projects/rumahlabuh-com.md]]
confidence: medium
source: business
---

# Freemium Gate

## TL;DR
The freemium gate determines which features are available to free vs premium users, implemented as a `can_access(feature)` check before feature execution.

## Gate Logic

```python
def can_access(user, feature):
    if user.tier == "premium":
        return True
    if feature in FREE_TIER_FEATURES:
        return True
    if user.budget_remaining > 0:
        return True  # Pay-per-use
    return False
```

## Feature Tiers

| Feature | Free | Premium | Pay-per-use |
|---------|------|---------|-------------|
| Basic chat | ✓ | ✓ | — |
| Web search | 10/day | unlimited | ✓ |
| Memory | 100 items | unlimited | ✓ |
| Swarm debate | ✗ | ✓ | ✓ |
| Video analysis | ✗ | ✓ | ✓ |

## Projects Using This Pattern

- [[projects/cekwajar-id.md]] — Salary fairness tool
- [[projects/rumahlabuh-com.md]] — Property rental platform

## Related Pages

- [[projects/cekwajar-id.md]] — cekwajar monetization

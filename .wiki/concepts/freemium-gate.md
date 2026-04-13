---
title: freemium-gate
type: concept
status: active
tags: [freemium, business, monetization, premium, access-control, pricing]
created: 2026-04-13
updated: 2026-04-13
summary: The freemium gate is the access control layer that determines which features are available to free versus premium users, using tier checking, budget remaining, and pay-per-use options to balance accessibility with monetization.
wikilinks:
  - [[projects/cekwajar-id]]
  - [[projects/rumahlabuh-com]]
  - [[./concepts/bayesian-blending]]
  - [[./concepts/llm-cost-routing]]
confidence: medium
source: business
---

# Freemium Gate

## TL;DR
The freemium gate is the access control layer that determines which features are available to free versus premium users. It implements `can_access(user, feature)` logic combining tier-based access (free/premium), pay-per-use budgets, and feature-specific gating — ensuring free users get enough value to convert while premium users and pay-per-use revenue sustain the platform.

## Overview

Both cekwajar.id and rumahlabuh.com need to monetize. The freemium gate is the design pattern that makes this possible: certain features are free with limits (to demonstrate value), premium users get unlimited access, and pay-per-use options let users pay for occasional high-cost features without a subscription. The gate is a business logic layer that sits between the user request and the feature execution.

## Context

Bashara's two Indonesian platforms — cekwajar.id (salary fairness) and rumahlabuh.com (property rental) — need sustainable monetization. Neither is a VC-funded startup burning investor money; both need to generate enough revenue to cover Supabase hosting costs and Legion's API bills. The freemium gate provides a principled way to offer a useful free tier while creating conversion pathways to paid access.

## Key Properties

- **Tier-based access**: Free, premium (subscription), pay-per-use (per-call)
- **Feature-specific gates**: Each feature has its own access tier requirements
- **Budget-aware pay-per-use**: Pay-per-use users draw from a prepay budget, not subscription
- **Conversion-friendly free tier**: Free tier is generous enough to demonstrate value, limited enough to create urgency
- **UU PDP compliance**: Access control must not store/process personal data beyond what the tier allows
- **Legion integration**: `/cekwajar_status` and `/rumahlabuh_status` skills query platform data, potentially tier-gated

## Gate Logic

```python
def can_access(user, feature):
    if user.tier == "premium":
        return True
    if feature in FREE_TIER_FEATURES:
        return True
    if user.budget_remaining > 0:
        return True  # Pay-per-use from prepay budget
    return False
```

## Feature Tiers

| Feature | Free | Premium | Pay-per-use |
|---------|------|---------|------------|
| Basic chat / query | ✓ | ✓ | — |
| Web search | 10/day | unlimited | ✓ |
| Memory recall | 100 items | unlimited | ✓ |
| Salary comparison report (cekwajar) | 1/month | unlimited | ✓ |
| Property inquiry (rumahlabuh) | 3/month | unlimited | ✓ |
| Swarm debate | ✗ | ✓ | ✓ |
| Video analysis | ✗ | ✓ | ✓ |
| PDF report generation (cekwajar) | ✗ | ✓ | ✓ |

## Business Logic

### Free Tier Design Principles
1. **Enough to evaluate**: Free users can complete one full workflow (submit salary, get comparison, generate report)
2. **Limits create urgency**: Exceeding limits triggers "upgrade to continue" with clear value proposition
3. **No dark patterns**: Free tier doesn't secretly throttle or degrade results
4. **Clear upgrade path**: Every limit message includes pricing and conversion link

### Pay-Per-Use Mechanics
1. User prepays a budget (e.g., ¥500 for 50 premium queries)
2. Each premium feature deducts from budget at per-use rate
3. Budget depletion → graceful degradation to free tier, not service denial
4. Low budget → notification with easy top-up path

### Premium Subscription
- Monthly/annual options with progressive pricing
- Annual discount (20%) to improve LTV
- Bundle across both cekwajar and rumahlabuh platforms

## cekwajar.id Monetization

cekwajar.id's core value is salary benchmarking. The freemium gate here:
- **Free**: 1 salary comparison/month, basic percentile report
- **Premium**: Unlimited comparisons, full PDF reports, UU PDP data export
- **Pay-per-use**: Extra reports at ¥100/report drawn from prepay budget

Conversion funnel: User submits salary → gets basic comparison → hits limit → sees premium value → upgrades.

## rumahlabuh.com Monetization

rumahlabuh.com's core value is rental inquiry management. The freemium gate:
- **Free**: 3 property inquiries/month, basic listing views
- **Premium**: Unlimited inquiries, priority listing, analytics dashboard
- **Pay-per-use**: Extra inquiry slots at ¥50/inquiry

## Relationships

The freemium gate's pay-per-use system is closely related to [[./concepts/bayesian-blending]] and [[./concepts/llm-cost-routing]] — pay-per-use pricing must account for actual LLM API costs. A video analysis feature that costs ¥10 in LLM calls shouldn't be sold for ¥5 pay-per-use. [[projects/cekwajar-id]] and [[projects/rumahlabuh-com]] are the two projects implementing this pattern. The gate is a business logic layer separate from the technical feature implementation.

## Current Status

**Design documented, not implemented.** The freemium gate logic is defined conceptually. Implementation requires: user tier tracking in Supabase, `can_access()` middleware, pay-per-use budget tracking, upgrade notification system, and conversion funnel tracking. Both cekwajar.id and rumahlabuh.com currently operate without tier gating — this is a planned Phase 2 feature.

## See Also

- [[projects/cekwajar-id]] — Salary fairness platform using freemium gate
- [[projects/rumahlabuh-com]] — Property rental platform using freemium gate
- [[./concepts/bayesian-blending]] — Cost-aware model selection relevant to pay-per-use pricing
- [[./concepts/llm-cost-routing]] — LLM cost structure that informs pay-per-use pricing

---
title: adr-2026-04-13-cekwajar-mvp-scope-lock
type: decision
status: active
tags: [cekwajar, mvp, scope-lock, wajar-slip, wajar-gaji, product-decision]
created: 2026-04-13
updated: 2026-04-13
summary: "Decision to lock cekwajar.id MVP to Wajar Slip only (not all 5 tools), excluding Wajar Gaji, Wajar Tanah, Wajar Kabur, and Wajar Hidup until specific release gates are met. Rationale: Wajar Slip is the only tool with zero cold-start data problem, the only tool where the paywall is immediately justified by concrete IDR shortfall findings, and the only tool with the deepest technical moat (PPh21 TER + progressive + 6-component BPJS)."
wikilinks:
  - [[cekwajar-id]]
  - [[cekwajar-verdict-engine]]
  - [[./concepts/market-data-indonesia]]
  - [[./concepts/labor-law-indonesia]]
confidence: high
source: research
---

## TL;DR

cekWajar.id was originally designed as a 5-tool platform (Wajar Slip, Wajar Gaji, Wajar Tanah, Wajar Kabur, Wajar Hidup). This ADR locks the MVP to **Wajar Slip only**. Rationale: Wajar Slip is the only tool with zero cold-start data problem, the only tool where the paywall is immediately justified by concrete IDR shortfall findings, and the only tool with the deepest technical moat (PPh21 TER + progressive + 6-component BPJS). Wajar Gaji, Wajar Tanah, Wajar Kabur, and Wajar Hidup are deferred until explicit release gates are met (500+ payslip audits for Gaji; formal ATR/BPN data partnership for Tanah; 10,000+ MAU for Kabur).

The decision prioritizes execution quality over feature breadth. A mediocre Wajar Slip launched in 12 weeks is worse than an excellent Wajar Slip launched in 5-6 weeks — the paywall conversion depends entirely on users trusting the calculation accuracy. Any calculation error at scale risks not just lost conversions but potential DJP/Kemnaker scrutiny. The 136 engineering hours required for Wajar Slip MVP represent roughly 5-6 weeks of full-time solo founder work, making the timeline aggressive but achievable.

---

# ADR-2026-04-13: MVP Scope Lock — Wajar Slip Only

**Date**: 2026-04-13  
**Status**: DECIDED  
**Decider**: Founder  
**Source**: master_analysis_cekwajar.md Section 1

---

## Context

cekwajar.id was originally designed as a 5-tool platform:
1. **Wajar Slip** — Payslip compliance auditor (PPh21 + BPJS verification)
2. **Wajar Gaji** — Salary benchmark (crowdsourced market data)
3. **Wajar Tanah** — Property price fairness
4. **Wajar Kabur** — Abroad comparison (PPP-adjusted)
5. **Wajar Hidup** — Cost of living comparison

The original vision was ambitious: launch all 5 tools simultaneously to capture a broad market. However, solo founder capacity (4-6 productive hours/day), 136+ engineering hours required for full Wajar Slip MVP, and critical data dependencies for each tool require serious reconsideration.

This ADR documents the decision to **lock MVP to Wajar Slip only** and define explicit release gates for subsequent tools.

---

## Decision

**Wajar Slip launches in MVP (v1). Wajar Gaji, Wajar Tanah, Wajar Kabur, and Wajar Hidup are explicitly excluded from v1.**

### v1 Feature Scope (Wajar Slip Only)

| Feature | Include | Engineering Hours | Rationale |
|---------|---------|-------------------|-----------|
| PDF payslip upload (≤5MB) | ✅ | 8h | P0 — core interaction |
| Google Vision OCR integration | ✅ | 16h | P0 — competitive moat |
| PPh21 TER calculation engine | ✅ | 20h | P0 — core value |
| PPh21 progressive annual true-up | ✅ | 12h | P0 — December critical |
| BPJS 6-component engine | ✅ | 16h | P0 — core value |
| Violation detection (V01-V07) | ✅ | 10h | P0 — deliverable |
| UU PDP consent flow | ✅ | 6h | P0 — legal requirement |
| Manual field override | ✅ | 8h | P1 — OCR fallback |
| Freemium gate | ✅ | 4h | P0 — business model |
| Midtrans payment (IDR 49K/month) | ✅ | 10h | P0 — monetization |
| Share card generation | ✅ | 6h | P1 — viral growth |
| 30-day auto-delete (Supabase cron) | ✅ | 4h | P0 — UU PDP compliance |
| Basic dashboard | ✅ | 12h | P1 — retention |
| Verdict history (3 free) | ✅ | 4h | P1 — retention |
| PSE registration (Kominfo) | ✅ | 0h code | P0 — legal requirement |
| **v1 Total** | | **~136h** | **~5-6 weeks solo** |

### Excluded from v1

| Tool/Feature | Excluded Until | Reason |
|--------------|----------------|--------|
| Wajar Gaji | Month 6-8 | Zero data on Day 1; city-level benchmarks misleading |
| Wajar Tanah | Month 10-12 | No NJOP API; scraping is ToS violation |
| Wajar Kabur | Month 12-18 | Politically sensitive; complex data pipeline |
| Wajar Hidup | Month 6-9 | Feasible but not blocking; build after Slip profitable |
| Photo payslip support | Month 4-6 | OCR accuracy unvalidated |
| 3-tier pricing | Month 3-4 | Launch single Pro tier first |
| Annual subscription | Month 4-6 | Requires Midtrans recurring setup |
| B2B API/licensing | Month 12+ | No pipeline, no product, no sales capacity |
| 17-agent Swarms | Month 9+ | Operationally premature |

---

## Rationale

### Why Wajar Slip First?

**1. Zero Cold-Start Problem**
- Wajar Slip: Deterministic calculation using government-mandated formulas. No crowdsourced data needed. Accuracy is verifiable.
- Wajar Gaji: Requires 500+ verified submissions before useful. Cannot launch credibly without data.

**2. Immediately Justifiable Paywall**
- "I just found my employer owes me IDR 847K in underpaid JHT — of course I'll pay IDR 49K"
- The paywall moment is concrete and personal. Finding a salary below market average is abstract.

**3. Deepest Technical Moat**
- PPh21 TER + progressive + all 6 BPJS components = complex regulatory engine
- Requires tax consultant audit (IDR 15-25M) and 15 test cases validated
- This complexity deters competitors and justifies premium pricing

**4. Data Flywheel Effect**
- Every Wajar Slip audit creates a verified salary data point
- Payslip → anonymized salary → contributes to Wajar Gaji benchmark pool
- Wajar Slip users become Wajar Gaji data contributors organically

### Why NOT Combined Slip + Gaji Launch?

A combined launch fails because it:
- Splits engineering time between deterministic (Slip) and data-quality-dependent (Gaji) trust architectures
- Risks mediocre execution on both tools
- Dilutes the "Wajar Slip is correct" brand reputation
- A mediocre Wajar Slip in 6 weeks is worse than an excellent one in 12 weeks

---

## Release Gates for Tool Addition

### Gate: Wajar Gaji

| Metric | Threshold | Rationale |
|--------|-----------|-----------|
| Payslip audits completed | 500+ | Verified salary data pool established |
| Paying subscribers | ≥50 with ≥30-day retention | Proven monetization model |
| Data source | Licensed survey (Mercer/Korn Ferry) signed OR 200+ direct submissions | Credible benchmark quality |
| PPh21 engine | Zero reported errors after 500 audits | Calculation engine validated |

### Gate: Wajar Hidup

| Metric | Threshold | Rationale |
|--------|-----------|-----------|
| Wajar Slip | Cash-flow positive | Platform profitable |
| BPS Susenas CPI | Data pipeline automated and tested | Core data source |
| Platform MAU | 1,000+ | Distribution credibility |

### Gate: Wajar Tanah

| Metric | Threshold | Rationale |
|--------|-----------|-----------|
| Data partnership | Formal MoU with ATR/BPN or major property portal | Legal data access |
| Platform MAU | 5,000+ | Distribution to negotiate partnership |
| Legal review | Property valuation disclaimer approved | Liability protection |

### Gate: Wajar Kabur

| Metric | Threshold | Rationale |
|--------|-----------|-----------|
| Platform MAU | 10,000+ | Established platform |
| Data pipeline | World Bank + OECD PPP tested for 5 countries | Technical feasibility |
| Political risk | Assessment completed | Emigration-adjacent content risk |

---

## Consequences

### Positive
- Engineering focus on one tool excellence ensures the core calculation engine is battle-tested before expanding
- Clear go/no-go metrics for each tool addition prevent premature diversification
- Avoids data quality problems that could damage brand — Wajar Gaji without 500+ verified submissions is worse than useless
- Allows proper legal/compliance investment for Slip before diversification — UU PDP, PSE registration, tax consultant audit all need to be done right
- Data flywheel effect: every Wajar Slip audit creates a verified salary data point that seeds the Wajar Gaji benchmark pool organically

### Negative
- Delays monetization from other tools — Wajar Tanah could launch within 10-12 months if data partnership secured
- Single-tool risk: if Wajar Slip fails to convert or has a calculation scandal, the entire platform fails
- Misses early-mover opportunity in salary benchmark space — Gadjian/GoodsCooker may add similar features
- Scope creep pressure: investors or users may push for Gaji/Tanah before release gates are met

### Mitigations
- Wajar Slip's market is large enough (60%+ of Indonesian formal workers cannot independently verify payslip)
- Clear extension roadmap with published release gates demonstrates strategic discipline to investors
- Data flywheel from Slip seeds future Gaji launch with organic, verified salary data
- Monthly metric reviews at each gate checkpoint provide early warning if Slip underperforms

---

## Alternatives Considered

### Alternative 1: Slip + Gaji Combined Launch
- Rejected: Splits focus, risks both tools being mediocre

### Alternative 2: Gaji Only (No Slip)
- Rejected: Cannot justify paywall without data quality; cold-start takes 12+ months

### Alternative 3: Tanah First (Property)
- Rejected: No legal data access; scraping creates legal liability

---

## Related Articles

- [[cekwajar-id]] — Project overview
- [[cekwajar-verdict-engine]] — Technical implementation
- [[./concepts/market-data-indonesia]] — Wajar Gaji data sources
- [[./concepts/labor-law-indonesia]] — Regulatory basis for Wajar Slip

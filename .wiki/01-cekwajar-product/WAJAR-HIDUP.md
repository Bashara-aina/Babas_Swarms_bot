---
title: Wajar Hidup
type: concept
status: active
tags:
- /
- home
- newadmin
- swarm-bot
- cekwajar-product
created: '2026-04-14'
updated: '2026-04-14'
summary: 'title: "Wajar Hidup — Cost of Living by City — Full Spec"'
wikilinks: []
confidence: medium
source: research
---
***
title: "Wajar Hidup — Cost of Living by City — Full Spec"
***

# Wajar Hidup — Complete Technical Specification

## Purpose
Answers: "Berapa yang dibutuhkan untuk hidup layak di kota ini?"
Monthly cost-of-living estimate via 12-item basket, 4 lifestyle tiers.

## 12-Item Cost Basket

| # | Category | Weight | Description |
|---|----------|--------|-------------|
| 1 | 🏠 Housing | ~30–35% | Rent 1BR furnished, city center |
| 2 | 🍚 Food & Groceries | ~18–22% | Monthly grocery for 1 person |
| 3 | 🍽️ Dining Out | ~8–12% | Incl. GoFood/GrabFood |
| 4 | 🚌 Transportation | ~8–12% | Public transit or motorbike |
| 5 | 💡 Utilities | ~5–8% | Electricity, water, internet |
| 6 | 📱 Communication | ~3–5% | Phone + data plan |
| 7 | 👕 Clothing | ~3–5% | Monthly apparel budget |
| 8 | 🏥 Healthcare | ~3–5% | Preventive care, medications |
| 9 | 🎬 Entertainment | ~5–8% | Cinema, gym, hobbies, streaming |
| 10 | 📚 Education | ~1–3% | Online courses, self-development |
| 11 | 🧹 Household | ~2–3% | Cleaning supplies, hygiene |
| 12 | 💼 Miscellaneous | ~2–3% | Buffer for unexpected |

## Lifestyle Tiers

| Tier | Monthly Budget | Profile | Housing |
|------|---------------|---------|---------|
| BUDGET 🟤 | IDR 6–10M | Mahasiswa/Fresh Grad | Studio IDR 1.5–3M |
| MODERATE 🔵 | IDR 10–20M | Mid-level Professional | 1BR furnished IDR 4–6M |
| NYAMAN 🟢 | IDR 20–40M | Upper-Middle Class | 2BR luxury IDR 8–15M |
| PREMIUM ⭐ | IDR 40M+ | Senior Executive | 3BR premium IDR 15M+ |

## Data Pipeline: Numbeo + Local Gap-Filling

```
Step 1: Numbeo API (crowd-sourced, near real-time)
Step 2: Map to 12-item basket
Step 3: Local gap-fill (40% weight)
        - OLX rentals for housing
        - Tokopedia/Shopee for groceries
        - BPS price surveys for anchor
Step 4: Composite Index
        index_city = 0.60 × Numbeo + 0.40 × local_official
```

## City Comparison Reference

| City | CoL Index (Jakarta=100) | Monthly Moderate | vs Jakarta |
|------|------------------------|-----------------|------------|
| Jakarta | 100 | IDR 12,860,000 | Baseline |
| Surabaya | ~72 | ~IDR 9,260,000 | −28% |
| Bandung | 51.3 | IDR 6,600,000 | −49% |
| Yogyakarta | 44.8 | IDR 5,760,000 | −55% |
***
title: "Wajar Kabur — Abroad Salary & Life Quality Comparison — Full Spec"
***

# Wajar Kabur — Complete Technical Specification

## Purpose
Answers: "Apakah pindah ke luar negeri worth it?"
Compares net purchasing power + quality of life across 8 destination
countries, PPP-corrected for taxes and cost of living.

## Why Raw Exchange Rate Fails

```
WRONG: SGD 5,000 × IDR 10,500 = IDR 52,500,000

CORRECT (PPP-adjusted):
  PPP_IDR = SGD 5,000 × (CoL_Singapore / CoL_Jakarta) × IDR 10,500
           = SGD 5,000 × (150/100) × 10,500 = IDR 78,750,000

Formula: salary_local_equivalent = salary_foreign × (cost_index_foreign / cost_index_IDN)
```

## Target Countries

| Country | CoL Index (Jakarta=100) | Income Tax Effective | Visa Stability | QoL Score |
|---------|------------------------|---------------------|----------------|-----------|
| 🇸🇬 Singapore | 150 | 8–12% | High (EP/S-Pass) | 92/100 |
| 🇦🇺 Australia | 135 | 19–32.5% | Medium (482/189) | 88/100 |
| 🇩🇪 Germany | 115 | 14–42% | High (Blue Card) | 90/100 |
| 🇳🇱 Netherlands | 125 | 19–49.5% (30% ruling) | High | 91/100 |
| 🇯🇵 Japan | 110 | 5–45% + 6–10% residence | High | 89/100 |
| 🇲🇾 Malaysia | 75 | 0–30% | Medium | 81/100 |
| 🇦🇪 UAE | 105 | 0% | Medium-High | 83/100 |
| 🇰🇷 South Korea | 105 | 6–45% | Medium | 86/100 |

> UAE 0% income tax = best for high earners.
> Netherlands 30% Ruling reduces effective rate to ~22–25% for qualifying expats.

## Life Quality Score Formula

```
LIFE_QUALITY_SCORE =
    0.35 × PurchasingPower(0–100) +
    0.30 × QualityOfLife(0–100)   +
    0.20 × CareerGrowth(0–100)    +
    0.15 × CulturalProximity(0–100)

PurchasingPower = normalized((PPP_salary_abroad / PPP_salary_IDN) − 1)
QualityOfLife   = avg(healthcare, infrastructure, safety, education) [Numbeo, EIU]
CareerGrowth    = industry_growth_rate × career_advancement_index
CulturalProximity = food_accessibility + religious_accommodation + expat_community_size
```

## Example: Indonesian SW Engineer (IDR 12M/mo) → Singapore (SGD 7,000/mo)

| Dimension | Score | Calculation |
|-----------|-------|-------------|
| Purchasing Power | 92/100 | (IDR 110.25M / IDR 12M) − 1 = 8.19× |
| Quality of Life | 92/100 | Numbeo Singapore |
| Career Growth | 95/100 | Tech industry SG growth |
| Cultural Proximity | 70/100 | Muslim-friendly, English-centric |
| **Life Quality Score** | **89.3/100** | 0.35×92 + 0.30×92 + 0.20×95 + 0.15×70 |

## Visa Stability Risk Factors

| Country | Key Risks |
|---------|-----------|
| Singapore | Salary floor increasing; Fair Consideration Framework (local first) |
| Australia | Skills list changes annually; points competition |
| Japan | Language barrier; remote work restrictions |
| Malaysia | Bumiputera preference; salary minimums |
| UAE | Oil-price linked volatility; labor law enforcement gaps |

## Free vs Premium

| Feature | Free | Premium |
|---------|------|---------|
| Countries shown | Top 2 | All 8 |
| Tax rate detail | Summary | Full bracket |
| Visa risk analysis | ❌ | ✅ |
| Career Growth Index | ❌ | ✅ |
| Life Quality Score | ✅ (0–100) | ✅ + component breakdown |
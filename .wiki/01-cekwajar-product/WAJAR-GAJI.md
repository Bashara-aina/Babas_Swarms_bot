***
title: "Wajar Gaji — Salary Benchmark Engine — Full Spec"
***

# Wajar Gaji — Complete Technical Specification

## Purpose
Answers: "Berapa seharusnya gaji saya?" 
Compares reported salary against composite BPS + crowdsourced benchmark.

## Input Parameters

### Mandatory
| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `jobTitle` | string | Indonesian job title (Kemnaker autocomplete) | `Software Engineer` |
| `experience` | integer (years) | Years in current/similar role | `5` |
| `education` | enum | `SMA`, `D3`, `S1`, `S2`, `S3` | `S1` |
| `province` | string | One of 34 Indonesian provinces | `DKI Jakarta` |
| `salaryReported` | integer (IDR) | Salary to benchmark | `8500000` |

### Optional (Smart Defaults)
| Parameter | Default | Description |
|-----------|---------|-------------|
| `city` | Province capital | Sub-provincial granularity |
| `industry` | `General` | Technology, Finance, Manufacturing, etc. |
| `companySize` | `Mixed` | <10, 10-50, 50-250, 250-1000, >1000 |
| `employmentType` | `Permanent` | Permanent, Contract, Freelance, Startup-Equity |
| `salaryBasis` | `Base + Regular Allowances` | Base Only / Base+Allowances / Total Comp |

## Job Title Normalization Pipeline

```
INPUT: "SE" or "Dev"
  → NORMALIZE: "Software Engineer" (fuzzy match via pgvector + Kemnaker)
  → CLASSIFY: Technology, Level-Mid
  → FETCH: Historical salary distribution for normalized title
  → AGGREGATE: 50+ similar variants (Programmer, Developer, etc.)
  → APPLY: Experience curve multiplier
```

### Experience Curve Multipliers
| Experience | Adjustment vs Base |
|------------|-------------------|
| 0–2 years | −15% to −25% |
| 2–5 years | −5% to −10% |
| 5–10 years | 0% (baseline) |
| 10–15 years | +5% to +15% |
| 15+ years | +15% to +30% |

## Statistical Method: Weighted Percentile + Bayesian Smoothing

Indonesian salary distributions are **right-skewed** — small number of
high earners distorts mean. Percentiles answer user's real question:
"Am I top or bottom quartile?"

### Composite Data Formula
```
S_composite(p) = w_bps · S_bps(p) + w_crowd · S_crowd(p)

Default weights:
  w_bps   = 0.60  (BPS SAKERNAS — authoritative, 2-year cycle)
  w_crowd = 0.40  (Crowdsourced — recent, noisier)

Dynamic BPS weight decay:
  w_bps_adjusted = w_bps × exp(−age_months / 12) × min(n_bps/30, 1.0)
  → BPS loses 50% weight after 24 months
```

**BPS Source:** SAKERNAS (Survei Angkatan Kerja Nasional)
- ~900,000 respondents across 34 provinces
- Published annually, Q2
- Occupational median wage by province × education × experience band

## Verdict Thresholds

| Condition | Verdict | Code |
|-----------|---------|------|
| Salary < P25 | Di Bawah Pasar 🔴 | BELOW_MARKET |
| P25 ≤ Salary ≤ P75 | Wajar 🟡 | FAIR |
| Salary > P75 | Di Atas Pasar 🟢 | ABOVE_MARKET |
| UMR ≤ Salary < P25 | Wajar Hukum, Di Bawah Pasar 🟠 | LEGAL_BELOW_MARKET |
| Salary < UMR | BAWAH UMR — POTENTIALLY ILLEGAL 🚨 | ILLEGAL |

## UMR Reference Values (2026)
| City | UMR 2026 (IDR/month) |
|------|---------------------|
| Jakarta | 4,900,000 |
| Surabaya | 3,200,000 |
| Bandung | 3,650,000 |
| Medan | 3,100,000 |
| Yogyakarta | ~2,570,000 |

> Fetched live from Kemnaker API, updated every January.

## Low Sample Size Fallback (Bayesian Shrinkage)

| Level | Cell | Trigger | Confidence |
|-------|------|---------|------------|
| 1 | title + exp + edu + province + city | n ≥ 15 | HIGH |
| 2 | title + exp + edu + province | n ≥ 5 (Bayes blend) | Medium-High |
| 3 | title + experience (nationwide) | n ≥ 50 | Medium (0.6) |
| 4 | title aggregate | n ≥ 100 | Low (0.4) |
| 5 | NULL | n < 200 | Not displayed |

```
verdict_final = (n_level1 × verdict_level1 + κ × verdict_level2) / (n_level1 + κ)
κ = 30  (prior strength — parent level worth 30 samples)
```

## Confidence Score Formula
```
confidence = 100 × sample_factor × recency_factor × variance_factor × method_factor

sample_factor:   grows 0→1 as n_effective reaches 50
recency_factor:  1.0 (BPS < 12mo); 0.8 (12–24mo); 0.6 (>24mo)
variance_factor: 1 / (1 + σ_composite)
method_factor:   1.0 (direct), 0.8 (shrinkage), 0.6 (parent aggregate)
```

| Score | Interpretation |
|-------|---------------|
| 80–100 | ✅ High — safe for career decisions |
| 60–79 | 🟡 Medium-High — good reference |
| 40–59 | 🟠 Medium — rough estimate |
| 20–39 | 🔴 Low — informational only |
| < 20 | ❌ Not displayed |

## Edge Cases

| Scenario | Handling |
|----------|---------|
| Contract workers | Separate P25/P75; +10–20% vs permanent |
| Startup + Equity | Base salary bench; equity excluded; confidence −0.2 |
| Probation period | Annualized × 0.85 back to permanent equiv; confidence −0.1 |
| Part-time/Hourly | `hourly × hours/week × 52 / 12` |
| ASN/Government | PERMENPAN salary scale (Golongan/Pangkat), not market percentile |

## Free vs Premium

| Field | Free | Premium |
|-------|------|---------|
| Verdict label | ✅ | ✅ |
| P50 benchmark | ✅ | ✅ |
| P25, P75 | ❌ | ✅ |
| Salary trend (3mo, 12mo) | ❌ | ✅ |
| City-level breakdown | ❌ | ✅ |
| Industry breakdown | ❌ | ✅ |
| Negotiation talking points | ❌ | ✅ |
| PDF export | Watermarked | Full |
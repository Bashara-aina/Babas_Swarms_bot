---
title: Market Data Indonesia
type: concept
status: active
tags: [market-data, salary, benchmark, tech-salaries, banking, fmcg, gig-economy, remote-work, inflation, gender-pay-gap, cost-of-living, indonesia, cekwajar,bps, sakernas, umk]
created: 2026-04-13
updated: 2026-04-13
summary: "Indonesian salary market data for cekwajar.id comes from 4 layers: BPS Sakernas (province × 9 occupation groups, free), Kemnaker UMK (514 cities annual), crowdsourced submissions (k-anonymity n≥10), and licensed surveys (Mercer/Korn Ferry, IDR 60-150M/year). City-level data is the gap: BPS only provides province-level, creating false precision risk if displayed as city-level."
wikilinks:
  - [[cekwajar-id]]
  - [[labor-law-indonesia]]
  - [[bpjs-reference]]
  - [[cekwajar-verdict-engine]]
confidence: high
source: research
---

# Market Data Indonesia

## TL;DR

Indonesian salary market data is fragmented across government statistics (BPS Sakernas: province × 9 occupation groups), regulatory minimums (Kemnaker UMK: 514 cities), and crowdsourced submissions. For cekwajar.id's Wajar Gaji tool, the critical insight is that **city-level salary data is structurally unavailable on Day 1** — BPS provides province aggregates, and crowdsource data requires n≥10 for display per cell. The data flywheel starts with Wajar Slip audits generating verified salary submissions, not the other way around.

---

## 1. Official Government Data Sources

### 1.1 BPS Sakernas (Survei Angkatan Kerja Nasional)

**Access**: https://www.bps.go.id/id/statistics-table/2/MTQ1OCMy/rata-rata-upah-gaji-bersih-sebulan-burus-pekerja-menurut-provinsi-dan-jenis-pekerjaan-utama.html

**What it provides**:
- Average monthly net salary by province
- By 9 major occupation groups (ISCO-adapted classification)
- ~900,000 respondents across 34 provinces
- Published annually (August survey → Q1 publication)

**Critical limitation**: Province × occupation = ~306 cells. **Cannot deliver "Software Engineer in Surabaya" — only "Professional/Technical worker in Jawa Timur."**

| Province | Occupation Group | Sample Size | Median Salary |
|----------|-----------------|-------------|---------------|
| DKI Jakarta | All 9 groups | ~150,000 | Rp 8,824,817 |
| Jawa Timur | All 9 groups | ~180,000 | Rp 3,800,000 |
| Jawa Barat | All 9 groups | ~200,000 | Rp 4,200,000 |

**Commercial use**: BPS data is public statistical information. Citation required ("Sumber: Badan Pusat Statistik (BPS), Sakernas [year]"). Gray area for automated commercial products — conservative practice is written clearance from BPS webmaster.

### 1.2 Kemnaker UMK Data (514 Cities)

**Access**: https://kemnaker.go.id/informasi/berita (annual UMK announcements) + SIPP Online portal

**What it provides**:
- UMK (Upah Minimum Kabupaten/Kota) for all 514 cities/regencies
- Updated annually, effective January 1
- Legal minimum wage floor for each city

**Data format**: Published as PDF SK Gubernur from each of 34 provinces. No official API.

**Operational approach**: Manual parsing of 34 PDF documents (~1h each = 34h/year). Automate with Python PDF parser + Supabase insert.

**cekwajar.id use**: UMK is the **hard legal floor** for Wajar Slip's V06 violation (below-UMK detection). Cannot be crowdsourced — it's regulatory.

### 1.3 BPS Sakernas vs UMK — Key Distinction

| Data | What It Measures | Geographic Granularity | Update | Legal Status |
|------|-----------------|----------------------|--------|-------------|
| BPS Sakernas | Market wage distribution | Province × 9 occupations | Annual | Public, citation required |
| Kemnaker UMK | Legal minimum floor | 514 cities | Annual | Mandatory compliance |

**For Wajar Gaji benchmarks**: Use BPS Sakernas with explicit disclaimer "Provinsi, bukan kota."  
**For Wajar Slip V06**: Use Kemnaker UMK[kota] as hard floor.

---

## 2. Crowdsourced Data Strategy

### 2.1 Cold-Start Problem

The fundamental challenge: users submit salary data in exchange for seeing better benchmarks, but better benchmarks require submitted data they don't yet have.

**Phase 0 — Pre-launch seeding (Month -2 to 0, ~200 submissions)**:
- Recruit 200 beta testers from tech LinkedIn, r/indonesia, Telegram finance communities
- Offer: 6 months free Pro access for verified salary submission
- Target: 50 submissions each across 4 categories: Software Engineer (Jakarta), Teacher (3+ provinces), Nurse (3+ provinces), Marketing/Sales (Jakarta + Surabaya)

### 2.2 K-Anonymity Threshold

Display benchmarks only when cell sample size is sufficient:

| Cell Sample Size | Action | UI Message |
|-----------------|--------|------------|
| n < 10 | Do not show benchmark | "Belum cukup data lokal (n<10). Menampilkan estimasi provinsi BPS." |
| 10 ≤ n < 30 | Bayesian blend toward BPS prior | "Estimasi awal — berdasarkan 15 laporan + data provinsi BPS" |
| 30 ≤ n < 100 | Show P25/P50/P75 with confidence interval | "Berdasarkan 42 laporan terverifikasi di area Anda" |
| n ≥ 100 | Full percentile distribution | "Berdasarkan 134 laporan terverifikasi" |

**K-anonymity formula (Bayesian smoothing)**:
```
Blended_P50 = (n / (n + k)) × Sample_P50 + (k / (n + k)) × Prior_P50

where:
  k = smoothing weight = 15 (tuned to collapse toward prior at n < 15)
  Prior_P50 = BPS province × occupation group average wage
```

### 2.3 Outlier Detection

Before including submissions in benchmarks, apply IQR filter:

```python
def detect_outliers(submissions: list[int]) -> tuple[list, list]:
    """
    Flag outliers using 1.5× IQR rule.
    Extreme outliers (>3× IQR) excluded.
    Standard outliers (1.5-3× IQR) included with reduced weight.
    """
    q1, median, q3 = np.percentile(submissions, [25, 50, 75])
    iqr = q3 - q1
    
    lower_fence = q1 - 1.5 * iqr
    upper_fence = q3 + 1.5 * iqr
    
    extreme_lower = q1 - 3 * iqr
    extreme_upper = q3 + 3 * iqr
    
    included = []
    reduced_weight = []
    excluded = []
    
    for s in submissions:
        if s < extreme_lower or s > extreme_upper:
            excluded.append(s)
        elif s < lower_fence or s > upper_fence:
            reduced_weight.append(s)  # Weight 0.5 in calculation
        else:
            included.append(s)
    
    return included, reduced_weight, excluded
```

---

## 3. Licensed Survey Data (Mercer/Korn Ferry)

### 3.1 Why License Data?

BPS Sakernas provides province × 9 occupation groups — too coarse for useful benchmarking. Crowdsource takes 12+ months to accumulate meaningful data.

**Recommendation**: License one survey before Wajar Gaji launches. This is the first IDR 60-80M check to write.

| Provider | Coverage | Cost Estimate | Lead Time |
|----------|----------|---------------|-----------|
| Mercer Indonesia | 500+ companies, 30,000+ positions, 6 major cities | IDR 80-150M/year | 4-8 weeks |
| Korn Ferry Indonesia | 400+ companies, 25,000+ positions | IDR 60-120M/year | 3-6 weeks |
| WTW | 300+ companies | IDR 70-130M/year | 4-8 weeks |
| EY Hay Group | 250+ companies | IDR 70-130M/year | 6-10 weeks |

### 3.2 Negotiation Leverage

Offer co-marketing deal: cekwajar.id credits Mercer/KF as "data partner" on all benchmark pages. Mercer/KF gets marketing exposure to 140M Indonesian formal workers. May reduce licensing cost to IDR 30-60M.

---

## 4. City-Level Data Gap Problem

### 4.1 Why City-Level Data Is Structurally Missing

BPS Sakernas aggregates to province level. Kemnaker UMK is regulatory minimum, not market rate. Crowdsource requires n≥10 per cell to display.

**Cell definition for crowdsource**: Province × Job Category (L2) × Seniority Band (Junior/Mid/Senior)

For "Software Engineer in Surabaya":
- Province: Jawa Timur ✓
- Job Category: Technology/IT ✓
- Seniority: Mid ✓
- Cell is valid BUT may only have 3-5 submissions for months

### 4.2 Fallback Hierarchy

| Query | Minimum Cell | Fallback |
|-------|--------------|----------|
| City × Job Title × Seniority | 30 submissions | Province × Occupation Group |
| Province × Job Title × Seniority | 20 submissions | Province × Occupation Group (BPS) |
| Province × Occupation Group | BPS data (no minimum) | National average |
| National × Occupation Group | BPS data | — |

**Rule**: Do not create city-level cells until 30+ submissions exist. Over-segmentation with low n creates false precision.

---

## 5. Special Data Sources for cekwajar.id Tools

### 5.1 Wajar Kabur (Abroad Comparison)

| Source | Coverage | Cost | Update | Legal |
|--------|----------|------|--------|-------|
| World Bank Open Data (PPP) | 190+ countries | Free (CC-BY 4.0) | Annual | None |
| Numbeo | 100+ cities, cost of living | USD 149/month | Monthly | None |
| frankfurter.app | Exchange rates | Free tier | Daily | None |

### 5.2 Wajar Hidup (Cost of Living)

| Source | Coverage | Cost | Update |
|--------|----------|------|--------|
| BPS CPI | 514 cities, inflation | Free | Monthly |
| Numbeo | 100+ cities, detailed basket | USD 149/month | Monthly |
| Susenas (BPS) | Household consumption | Free | Annual |

### 5.3 Wajar Tanah (Property) — DO NOT USE

| Source | Why Excluded |
|--------|--------------|
| 99.co | ToS violation, UU ITE Pasal 30 risk |
| Rumah123 | Same ToS risk |
| OLX Properti | Same risk |
| BHUMI ATR/BPN | No bulk API, interactive only |

**Path forward**: Formal data partnership with ATR/BPN or major property portal after 5,000+ MAU.

---

## 6. Data Source Summary Table

From master_analysis_cekwajar.md Section 2.5:

| Source | Day 1 Available | Refresh Cadence | Legal Risk | Monthly Cost |
|--------|:---:|---------------|------------|-------------|
| BPS Sakernas (province × occupation) | ✅ | Annual | LOW-MED (cite clearly) | IDR 0 |
| Kemnaker UMK/UMR (514 cities) | ✅ | Annual (Dec-Jan) | NONE | IDR 0 |
| BPJS rate tables | ✅ | Regulatory changes | NONE | IDR 0 |
| PMK 168/2023 TER tables | ✅ | PMK amendments | NONE | IDR 0 |
| Mercer/Korn Ferry survey | ❌ | Annual | LOW (licensed) | IDR 6-12.5M |
| Crowdsourced salary | ❌ | Real-time | LOW (consented) | IDR 0 |
| Numbeo (cost of living) | ❌ (v3) | Monthly | LOW | USD ~149 |
| World Bank PPP | ❌ (v4) | Annual | NONE | IDR 0 |
| Google Cloud Vision OCR | ✅ | Real-time API | LOW | ~USD 1.5/1000 docs |

---

## 7. Confidence Scoring for Benchmarks

### 7.1 Confidence Factors

| Factor | Weight | Description |
|--------|--------|-------------|
| Sample size (n) | 40% | Direct n in cell |
| Data recency | 20% | BPS: 0-12mo=1.0, 12-24mo=0.8; Crowdsource: <1mo=1.0, >6mo=0.7 |
| Variance | 20% | Low variance = higher confidence |
| Source reliability | 20% | Licensed > BPS > Crowdsource |

### 7.2 Confidence Score Formula

```python
def calculate_confidence(
    n: int,
    source_type: str,  # 'bps', 'crowdsource', 'licensed'
    age_months: int,
    variance: float,
    cell_variance: float
) -> int:
    # Sample factor: grows from 0 to 1 at n=50
    sample_factor = min(n / 50, 1.0) if n > 0 else 0.3
    
    # Recency factor
    if source_type == 'bps':
        recency = 1.0 if age_months <= 12 else (0.8 if age_months <= 24 else 0.6)
    else:  # crowdsource
        recency = 1.0 if age_months <= 1 else (0.85 if age_months <= 3 else 0.7)
    
    # Variance factor: penalize high CV
    cv = cell_variance / (n ** 0.5) if n > 0 else 1.0
    variance_factor = 1 / (1 + cv)
    
    # Source reliability
    source_weights = {'licensed': 1.0, 'bps': 0.8, 'crowdsource': 0.6}
    source_factor = source_weights.get(source_type, 0.5)
    
    # Combined
    confidence = 100 * (
        sample_factor * 0.4 +
        recency * 0.2 +
        variance_factor * 0.2 +
        source_factor * 0.2
    )
    
    return min(max(int(confidence), 0), 100)
```

### 7.3 Confidence UI Levels

| Score | Badge | Interpretation |
|-------|-------|----------------|
| 80-100 | 🟢 Terverifikasi | High confidence — use for career decisions |
| 60-79 | 🟡 Cukup Data | Medium — use as reference |
| 40-59 | 🟠 Data Terbatas | Low — rough estimate |
| <40 | ⚪ Tidak Cukup | Very low — do not show percentile bands |

---

## Related Articles

- [[cekwajar-id]] — Project using this data
- [[labor-law-indonesia]] — Regulatory minimums (UMK) and employment classification
- [[bpjs-reference]] — Mandatory deductions affecting take-home pay
- [[cekwajar-verdict-engine]] — How data feeds into verdict calculation

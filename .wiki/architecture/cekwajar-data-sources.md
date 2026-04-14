---
title: cekwajar-data-sources
type: architecture
status: active
tags: [cekwajar, data-sources, bps, sakernas, kemnaker, umk, crowdsource, mercer, njop, property-data]
created: 2026-04-13
updated: 2026-04-13
summary: "cekwajar.id data sourcing follows a 4-layer strategy: Layer 1 (Government: BPS Sakernas, Kemnaker UMK, BPJS rates, PMK 168/2023 tables — all free, Day 1 ready), Layer 2 (Licensed surveys: Mercer/Korn Ferry at IDR 60-150M/year — pre-Wajar Gaji gate), Layer 3 (Crowdsource flywheel: verified salary submissions from Wajar Slip users with k-anonymity n≥10), Layer 4 (Scraped: excluded entirely — ToS violation risk outweighs value). No property portal scraping. No automated rate updates from external sources."
wikilinks:
  - [[projects/cekwajar-id]]
  - [[./concepts/market-data-indonesia]]
  - [[architecture/cekwajar-verdict-engine]]
  - [[./concepts/bpjs-reference]]
confidence: high
source: research
---

# cekwajar Data Sources Architecture

## TL;DR

cekwajar.id's data strategy is a 4-layer pyramid: government data (BPS, Kemnaker, BPJS) forms the free foundation; licensed surveys (Mercer/Korn Ferry) provide premium benchmarks before Wajar Gaji launch; crowdsourced submissions from Wajar Slip users create the data flywheel; scraped data is explicitly excluded due to ToS violations. All regulatory tables (BPJS rates, TER, UMK) are version-controlled in the database with `effective_date` fields — never auto-updated from external APIs without manual validation.

---

## 1. Data Architecture Layers

```
┌─────────────────────────────────────────────────────────────────────┐
│                    DATA LAYER ARCHITECTURE                           │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  Layer 4: Scraped/Realtime        │  EXCLUDED                       │
│  (99.co, Rumah123, Glassdoor)     │  ToS violation, UU ITE risk     │
│                                  │  Do not build                    │
├──────────────────────────────────┴──────────────────────────────────┤
│                                                                      │
│  Layer 3: Crowdsourced           │  Month 1+ onwards               │
│  (Verified salary submissions     │  K-anonymity n≥10              │
│   from Wajar Slip users)         │  BPS Bayesian blend            │
│                                  │  Outlier detection             │
├──────────────────────────────────┴──────────────────────────────────┤
│                                                                      │
│  Layer 2: Licensed Surveys        │  Pre-Wajar Gaji launch          │
│  (Mercer, Korn Ferry)             │  IDR 60-150M/year              │
│                                  │  City × job × industry          │
├──────────────────────────────────┴──────────────────────────────────┤
│                                                                      │
│  Layer 1: Government Data         │  Day 1 available               │
│  (BPS Sakernas, Kemnaker UMK,     │  Province × occupation         │
│   BPJS rates, PMK 168/2023)       │  514 cities UMK               │
│                                  │  Regulatory formulas            │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 2. Layer 1: Government Data Sources

### 2.1 BPS Sakernas (Salary Statistics)

**Source**: Badan Pusat Statistik (Central Statistics Agency)  
**URL**: https://www.bps.go.id/id/statistics-table/2/MTQ1OCMy/rata-rata-upah-gaji-bersih-sebulan-burus-pekerja-menurut-provinsi-dan-jenis-pekerjaan-utama.html  
**API**: https://webapi.bps.go.id/v1/api/ (requires free registration)

| Attribute | Detail |
|-----------|--------|
| Granularity | Province × 9 occupation groups (ISCO-adapted) |
| Coverage | ~900,000 respondents, 34 provinces |
| Frequency | Annual (August survey → Q1 publication) |
| Legal | Public statistical tables, cite BPS as source |
| Commercial risk | LOW-MED — BPS allows citing, gray area for automated products |
| Cost | IDR 0 |

**Critical limitation**: Cannot provide city-level or job-title-level data. "Software Engineer in Surabaya" is not available — only "Professional/Technical workers in Jawa Timur."

**Data format from API**:
```json
{
  "province_code": "35",
  "province_name": "Jawa Timur",
  "occupation_code": "2",
  "occupation_name": "Professionals",
  "sample_size": 45230,
  "median_salary": 5800000,
  "mean_salary": 6200000,
  "p25_salary": 4200000,
  "p75_salary": 8500000,
  "survey_year": 2025
}
```

**Implementation**:
```python
# BPS Sakernas data is cached as static JSON
# Supabase cron refreshes from API quarterly, falls back to cached file

class BPSDataSource:
    def __init__(self, supabase_client):
        self.db = supabase_client
    
    def get_province_median(self, province_code: str, occupation_code: str) -> dict:
        """Return BPS median for province × occupation."""
        result = self.db.table('bps_sakernas').select('*').eq(
            'province_code', province_code
        ).eq('occupation_code', occupation_code).execute()
        
        if not result.data:
            return {'source': 'bps', 'confidence': 'low', 'median': None}
        
        return {
            'source': 'bps_sakernas_2025',
            'median': result.data[0]['median_salary'],
            'p25': result.data[0]['p25_salary'],
            'p75': result.data[0]['p75_salary'],
            'sample_size': result.data[0]['sample_size'],
            'confidence': 'high',
            'last_updated': result.data[0]['survey_year']
        }
```

### 2.2 Kemnaker UMK Data (514 Cities)

**Source**: Kemnaker (Ministry of Manpower) + 34 Provincial Governors' Decrees  
**URL**: https://kemnaker.go.id/informasi/berita (annual announcements)  
**API**: None — PDF decrees published annually

| Attribute | Detail |
|-----------|--------|
| Granularity | 514 cities/kabupaten (UMK varies by kota/kabupaten) |
| Coverage | All Indonesia |
| Frequency | Annual, effective January 1 |
| Legal | Public regulatory data, no restrictions |
| Format | PDF SK Gubernur per province — manual parsing required |

**Operational approach**:
```python
# Manual process: 1h per province PDF × 34 provinces = 34h/year
# Automate with Python PDF parser

import pdfplumber

def parse_umk_pdf(pdf_path: str) -> list[dict]:
    """
    Parse UMK from provincial SK Gubernur PDF.
    Returns list of {kota: str, umk: int, effective_date: date}.
    """
    umk_data = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            # Pattern: "Kota X" followed by "Rp Y" followed by date
            pattern = r'([A-Za-z\s]+)\s+Rp\.?\s*([\d\.]+)\s+([\d\-]+)'
            matches = re.findall(pattern, text)
            for match in matches:
                kota, umk_str, date_str = match
                umk_data.append({
                    'kota': kota.strip(),
                    'umk': int(umk_str.replace('.', '')),
                    'effective_date': parse_date(date_str)
                })
    return umk_data
```

**Fallback strategy**: If new UMK not yet published (December/January gap), use previous year UMK × official inflation adjustment rate (BPS CPI).

### 2.3 BPJS Rate Tables

**Source**: Various regulations (PP 46/2015, PP 45/2015, PP 44/2015, Perpres 82/2018)  
**Implementation**: Hard-coded in `bpjs_rate_schedule` table with `effective_date`

```sql
CREATE TABLE bpjs_rate_schedule (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    component TEXT NOT NULL,  -- 'JHT', 'JP', 'JKK', 'JKM', 'KESEHATAN'
    sub_component TEXT,      -- 'employee' or 'employer'
    rate NUMERIC NOT NULL,    -- e.g., 0.02 for 2%
    cap_amount BIGINT,        -- e.g., 9559600 for JP cap, NULL if no cap
    effective_date DATE NOT NULL,
    source_regulation TEXT,   -- e.g., 'PP 46/2015'
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Initial seed data
INSERT INTO bpjs_rate_schedule (component, sub_component, rate, cap_amount, effective_date, source_regulation) VALUES
('JHT', 'employee', 0.02, NULL, '2015-01-01', 'PP 46/2015'),
('JHT', 'employer', 0.037, NULL, '2015-01-01', 'PP 46/2015'),
('JP', 'employee', 0.01, 9559600, '2015-01-01', 'PP 45/2015'),
('JP', 'employer', 0.02, 9559600, '2015-01-01', 'PP 45/2015'),
('JKK', 'employer', 0.0054, NULL, '2015-01-01', 'PP 44/2015'),  -- Default: low risk
('JKM', 'employer', 0.003, NULL, '2015-01-01', 'PP 44/2015'),
('KESEHATAN', 'employee', 0.01, 12000000, '2020-01-01', 'Perpres 82/2018'),
('KESEHATAN', 'employer', 0.04, 12000000, '2020-01-01', 'Perpres 82/2018');
```

**Operational requirement**: Supabase cron checks Kemnaker/BPJS website quarterly for regulatory changes. Rate changes require manual validation before deployment — **no automated rate updates**.

### 2.4 PMK 168/2023 TER Tables

**Source**: PMK 168/2023 Lampiran A/B/C  
**Implementation**: Version-controlled in database

```sql
CREATE TABLE pph21_ter_rates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    category CHAR NOT NULL,      -- 'A', 'B', or 'C'
    min_gross BIGINT NOT NULL,
    max_gross BIGINT,             -- NULL for '>50M' tier
    ter_rate NUMERIC NOT NULL,    -- e.g., 0.025 for 2.5%
    effective_date DATE NOT NULL,
    source_document TEXT,         -- 'PMK 168/2023 Lampiran A'
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

---

## 3. Layer 2: Licensed Survey Data

### 3.1 Why License Before Wajar Gaji Launch

BPS Sakernas provides province × 9 occupation groups — too coarse for useful salary benchmarking. Crowdsource takes 12+ months to accumulate enough n≥10 cells.

**Recommendation**: License one survey before Wajar Gaji launches. This is the first IDR 60-80M check to write.

| Provider | Coverage | Data Points | Cost | Lead Time |
|----------|----------|-------------|------|-----------|
| **Mercer Indonesia** | 500+ companies, 30,000+ positions, 6 cities | Job grade × city × industry | IDR 80-150M/year | 4-8 weeks |
| **Korn Ferry** | 400+ companies, 25,000+ positions | Similar to Mercer | IDR 60-120M/year | 3-6 weeks |

### 3.2 Negotiation Strategy

Offer co-marketing deal: cekwajar.id credits Mercer/KF as "data partner" on all benchmark pages. Mercer/KF gets marketing exposure to 140M Indonesian formal workers. May reduce cost to IDR 30-60M.

### 3.3 Data Format

```json
{
  "provider": "mercer",
  "survey_year": 2025,
  "data": [
    {
      "job_grade": "Software Engineer L3",
      "city": "Jakarta",
      "industry": "Technology",
      "p10": 12000000,
      "p25": 15000000,
      "p50": 18000000,
      "p75": 22000000,
      "p90": 28000000,
      "sample_size": 127
    }
  ]
}
```

---

## 4. Layer 3: Crowdsource Data Flywheel

### 4.1 Flywheel Mechanism

Every Wajar Slip audit creates a verified salary data point:
1. User uploads payslip → PPh21/BPJS calculated
2. With explicit consent, salary anonymized and added to benchmark pool
3. Anonymized data = province + job_category + seniority + salary (no name, no company)

### 4.2 K-Anonymity Implementation

```python
def get_benchmark(province: str, job_category: str, seniority: str, city: str = None):
    """
    Return benchmark with k-anonymity enforcement.
    n < 10: Return only BPS province estimate, mark as 'insufficient local data'
    n >= 10: Return blended benchmark with confidence score
    """
    cell = f"{province}:{job_category}:{seniority}"
    
    # Get crowdsource data
    crowd_data = get_crowd_data(cell)  # Returns list of salaries
    
    if len(crowd_data) < 10:
        # Fall back to BPS province estimate
        bps_estimate = get_bps_estimate(province, job_category)
        return {
            'verdict': 'INSUFFICIENT_LOCAL_DATA',
            'n': len(crowd_data),
            'p50': bps_estimate['median'],
            'source': 'bps_province_estimate',
            'confidence': 30,
            'message': 'Belum cukup data lokal (n<10). Menampilkan estimasi provinsi BPS.'
        }
    
    # Bayesian blend for 10 <= n < 30
    if len(crowd_data) < 30:
        blended_p50 = bayesian_blend(
            crowd_p50=np.median(crowd_data),
            bps_p50=bps_estimate['median'],
            n=len(crowd_data),
            k=15  # Smoothing weight
        )
        confidence = calculate_confidence(len(crowd_data), 'crowdsource')
        return {
            'verdict': 'EARLY_ESTIMATE',
            'n': len(crowd_data),
            'p50': blended_p50,
            'source': f'{len(crowd_data)} submissions + BPS blend',
            'confidence': confidence,
            'message': f'Estimasi awal — {len(crowd_data)} laporan lokal + data provinsi BPS'
        }
    
    # Full percentile for n >= 30
    return {
        'verdict': 'VERIFIED',
        'n': len(crowd_data),
        'p25': np.percentile(crowd_data, 25),
        'p50': np.median(crowd_data),
        'p75': np.percentile(crowd_data, 75),
        'source': f'{len(crowd_data)} verified submissions',
        'confidence': calculate_confidence(len(crowd_data), 'crowdsource'),
        'message': f'Berdasarkan {len(crowd_data)} laporan terverifikasi'
    }
```

### 4.3 Outlier Detection

```python
def detect_outliers(salaries: list[int]) -> tuple[list, list, list]:
    """
    Flag outliers using IQR rule.
    Returns (included, reduced_weight, excluded).
    """
    q1, median, q3 = np.percentile(salaries, [25, 50, 75])
    iqr = q3 - q1
    
    extreme_lower = q1 - 3 * iqr
    extreme_upper = q3 + 3 * iqr
    lower_fence = q1 - 1.5 * iqr
    upper_fence = q3 + 1.5 * iqr
    
    included = [s for s in salaries if lower_fence <= s <= upper_fence]
    reduced = [s for s in salaries if (s < lower_fence or s > upper_fence) and 
               not (s < extreme_lower or s > extreme_upper)]
    excluded = [s for s in salaries if s < extreme_lower or s > extreme_upper]
    
    return included, reduced, excluded
```

---

## 5. Layer 4: Explicitly Excluded Sources

### 5.1 Property Portals (DO NOT USE)

| Source | Why Excluded |
|--------|-------------|
| 99.co | ToS violation, UU ITE Pasal 30 (illegal access) |
| Rumah123 | Same risk |
| OLX Properti | Same risk |
| BHUMI ATR/BPN | No bulk API, interactive only |

**Legal risk**: UU ITE Pasal 30 prohibits unauthorized access to computer systems. Scraping property portals violates ToS and could trigger criminal liability.

**Correct path**: Negotiate formal data partnership with ATR/BPN or major property portal after 5,000+ MAU.

### 5.2 Salary Websites (DO NOT USE)

| Source | Why Excluded |
|--------|-------------|
| Glassdoor | Explicit ToS prohibition on scraping |
| LinkedIn Salary | Behind login, ToS violation |

**Use instead**: LinkedIn Jobs public postings — only extract explicitly posted salary ranges.

---

## 6. Data Source Summary Table

| Source | Layer | Day 1 | Cost | Legal Risk | Update | Format |
|--------|-------|:---:|------|------------|--------|--------|
| BPS Sakernas | 1 | ✅ | Free | LOW-MED | Annual | Province × 9 occupations |
| Kemnaker UMK | 1 | ✅ | Free | NONE | Annual | 514 cities |
| BPJS rates | 1 | ✅ | Free | NONE | Manual only | DB table |
| PMK 168/2023 TER | 1 | ✅ | Free | NONE | Manual only | DB table |
| Mercer/Korn Ferry | 2 | ❌ | IDR 6-12.5M/mo | LOW (licensed) | Annual | City × job × industry |
| Crowdsource | 3 | ❌ | Free | LOW | Real-time | Province × job × seniority |
| 99.co/Rumah123 | 4 | ❌ | N/A | HIGH | N/A | EXCLUDED |
| Numbeo (CoL) | 4 | ❌ | USD 149/mo | LOW | Monthly | v3+ only |

---

## 7. Data Governance

### 7.1 K-Anonymity Enforcement

No cell with n < 10 is ever displayed publicly. All cells aggregate:
- Province + Job Category (L2) + Seniority Band minimum

### 7.2 No Automated Rate Updates

BPJS caps and UMK values are regulatory and require:
1. Official government announcement
2. Manual validation by founder
3. Database update with new `effective_date`
4. Re-testing of calculation engine
5. Deployment

**No external API will ever auto-update these values.**

### 7.3 Outlier Queue

Submissions flagged as outliers are excluded from live benchmarks and routed to a weekly review queue (15-30 min/week at early volumes).

---

## Related Articles

- [[projects/cekwajar-id]] — Project using these data sources
- [[./concepts/market-data-indonesia]] — Market data overview
- [[architecture/cekwajar-verdict-engine]] — How data feeds into verdict
- [[./concepts/bpjs-reference]] — Regulatory basis for BPJS data

# CEKWAJAR.ID: Verdict Algorithm Architecture
## Production-Grade Technical Specification v1.0

**Document Status:** Final Specification
**Last Updated:** April 7, 2026
**Platform:** cekwajar.id (Indonesian Consumer Data Intelligence)
**Tech Stack:** Next.js 15 + TypeScript + Supabase + Vercel + Tailwind CSS

---

## TABLE OF CONTENTS

1. [WAJAR GAJI - Salary Benchmark Engine](#wajar-gaji)
2. [WAJAR SLIP - Payslip Decoder & Compliance Auditor](#wajar-slip)
3. [WAJAR TANAH - Land Price Benchmark](#wajar-tanah)
4. [WAJAR KABUR - Abroad Salary & Life Quality Comparison](#wajar-kabur)
5. [WAJAR HIDUP - Cost of Living by City](#wajar-hidup)
6. [Cross-Tool Architecture & Freemium Gating](#cross-tool-architecture)

---

## WAJAR GAJI: Salary Benchmark Engine

### 1.1 Input Parameter Specification

#### Mandatory Parameters

```json
{
  "jobTitle": {
    "type": "string",
    "description": "Indonesian job title",
    "examples": ["Software Engineer", "Akuntant", "Project Manager"],
    "autocomplete": true,
    "source": "Kemnaker job classification + crowdsourced mappings"
  },
  "experience": {
    "type": "integer",
    "unit": "years",
    "min": 0,
    "max": 50,
    "description": "Years of experience in current role or similar roles"
  },
  "education": {
    "type": "enum",
    "values": ["SMA", "D3", "S1", "S2", "S3"],
    "description": "Highest education level (Indonesian classification)"
  },
  "province": {
    "type": "string",
    "description": "Indonesian province (34 provinces + Jakarta special)",
    "required": true
  }
}
```

#### Optional Parameters with Smart Defaults

```json
{
  "city": {
    "type": "string",
    "description": "Specific city for sub-provincial granularity",
    "default": "Province capital",
    "values": ["Jakarta", "Bandung", "Surabaya", "Medan", "Yogyakarta", etc.]
  },
  "industry": {
    "type": "enum",
    "values": ["Technology", "Finance", "Manufacturing", "Retail", "Healthcare", "Education", "Startup", "Government", "NGO", "Other"],
    "default": "General" (applies all-industry weights)
  },
  "companySize": {
    "type": "enum",
    "values": ["<10", "10-50", "50-250", "250-1000", ">1000"],
    "default": "Mixed" (applies size-adjusted weights)
  },
  "employmentType": {
    "type": "enum",
    "values": ["Permanent", "Contract", "Freelance", "Startup-Equity", "Part-Time"],
    "default": "Permanent"
  },
  "gender": {
    "type": "enum",
    "values": ["Male", "Female", "Not Disclosed"],
    "default": "Not Disclosed",
    "note": "For transparency only; not used in primary calculation but tracked for gender gap analysis"
  },
  "salaryBasis": {
    "type": "enum",
    "values": ["Base Salary Only", "Base + Regular Allowances", "Total Compensation"],
    "default": "Base + Regular Allowances"
  }
}
```

#### Auto-Complete & Job Title Mapping Logic

The system implements hierarchical job title normalization:

```
INPUT: "SE" or "Dev" → NORMALIZE: "Software Engineer" (fuzzy match)
→ CLASSIFY: [Technology, Level-Mid]
→ FETCH: Historical salary distribution for normalized title
→ AGGREGATE: 50 similar variant titles (Programmer, Developer, etc.)
→ APPLY: Experience curve multiplier based on years_of_experience
```

**Autocomplete Data Sources:**
- Kemnaker official job classification (base taxonomy)
- LinkedIn job title frequency analysis (Indonesia-specific)
- Crowdsourced job title submissions from cekwajar users
- BPS occupational statistics

**Experience Curve Multiplier** (applied after base percentile lookup):
- 0-2 years: -15% to -25% below base
- 2-5 years: -5% to -10% below base
- 5-10 years: 0% (base benchmark)
- 10-15 years: +5% to +15% above base
- 15+ years: +15% to +30% above base

### 1.2 Verdict Calculation Logic

#### 1.2.1 Statistical Method Justification: Weighted Percentile with Bayesian Smoothing

**Why not median or trimmed mean?**

| Method | Pros | Cons | Use Case |
|--------|------|------|----------|
| **Mean** | Simple | Outliers distort; skewed salary distributions are common | ❌ Not recommended |
| **Median** | Robust to outliers | Ignores upper/lower tail info; loses distribution shape | ❌ Sub-optimal |
| **Trimmed Mean (10%)** | Balances robustness & info | Still loses percentile context | ⚠️ Fallback only |
| **Percentile (P25/P50/P75)** | Captures distribution shape | Requires large n; unstable with n<30 | ✓ Primary method |
| **Weighted Percentile + Bayesian** | Incorporates data quality & prior; stable at small n | Requires hyperparameter tuning | ✓✓ RECOMMENDED |

**Selected Method: Weighted Percentile with Bayesian Smoothing**

Rationale:
- Salary distributions in Indonesia are non-normal (right-skewed)
- Percentiles directly answer "Am I in top/bottom quartile?" (user question)
- Bayesian approach handles sparse cells (rare job-province combinations) gracefully
- Weighted scheme values official BPS data (authoritative) over crowdsourced (noisier but recent)

#### 1.2.2 Data Composite Formula

**Composite Salary Distribution = Weighted Blend of Two Sources**

```
S_composite(p) = w_bps * S_bps(p) + w_crowd * S_crowd(p)

Where:
  S_composite(p) = composite salary at percentile p (p ∈ [0,1])
  S_bps(p) = BPS official salary distribution at percentile p
  S_crowd(p) = crowdsourced salary distribution at percentile p
  w_bps = base weight for BPS data
  w_crowd = base weight for crowdsourced data
  w_bps + w_crowd = 1
```

**Dynamic Weight Adjustment Based on Data Freshness & Volume:**

```
w_bps_adjusted = w_bps * (decay_factor) * (confidence_bps)

where:
  decay_factor = exp(-λ * age_months / 12)
    λ = 0.5 (half-life: BPS data loses 50% weight after 24 months)
    age_months = months since BPS publication

  confidence_bps = min(sample_size_bps / 30, 1.0)
    (scales from 0 to 1 as sample grows from 0 to 30+)

w_crowd_adjusted = w_crowd * confidence_crowd

where:
  confidence_crowd = 1 - σ²_crowd / (σ²_bps + σ²_crowd)
    (relative variance adjustment: crowdsourced data weighted inversely to variance)

w_bps_final = w_bps_adjusted / (w_bps_adjusted + w_crowd_adjusted)
w_crowd_final = w_crowd_adjusted / (w_bps_adjusted + w_crowd_adjusted)
```

**Default Weights (may be overridden by availability):**
- w_bps = 0.60 (BPS is authoritative, published every 2 years)
- w_crowd = 0.40 (Crowdsourced data is more recent but noisier)

**BPS Data Integration:**
- Source: BPS Annual Labor Survey (Survei Angkatan Kerja Nasional - SAKERNAS)
- Publication: Annually (Q2)
- Coverage: ~900k respondents across 34 provinces
- Format: Occupational median wage by province, education level, experience band
- Integration: Mapped to job_title + province + experience_band cells

**Crowdsourced Data Integration:**
- Source: User salary submissions (opt-in, anonymized)
- Validation: Cross-checked against BPS ranges (outliers flagged)
- Recency: Real-time (weighted heavily for recent 3 months)
- Deduplication: IP + metadata hash to prevent duplicate submissions
- Privacy: Stored encrypted with user consent (GDPR-aligned)

#### 1.2.3 Percentile Calculation (Composite Distribution)

**Step 1: Build Kernel Density Estimate (KDE) from composite data**

```
For cell (job_title, experience, education, province):
  1. Fetch BPS median salary: S_bps_median
  2. Fetch crowdsourced sample: {s_i} where i=1..n_crowd
  3. Calculate composite distribution using weighted KDE:

     f_composite(s) = w_bps_final * f_bps(s) + w_crowd_final * f_kde(s)

     where:
       f_bps(s) = normal distribution N(μ_bps, σ_bps)
                  μ_bps = BPS median
                  σ_bps = estimated from BPS percentile bands

       f_kde(s) = Σ(i=1..n) w_i * K((s - s_i) / h)
                  K = Gaussian kernel
                  h = bandwidth (Silverman's rule: 1.06 * σ * n^(-1/5))
                  w_i = 1/n (equal weight per crowdsourced submission)
```

**Step 2: Extract Percentiles P25, P50, P75 from composite CDF**

```
P25 = inverse_cdf(0.25)  [25th percentile]
P50 = inverse_cdf(0.50)  [50th percentile / median]
P75 = inverse_cdf(0.75)  [75th percentile]
```

#### 1.2.4 Verdict Thresholds & UMR Interaction

**Base Verdict Logic:**

```
IF salary_reported < P25:
  verdict = "Di Bawah Pasar" (Below Market)
  percentile_position = 20  [user salary at ~P20]

ELSE IF salary_reported BETWEEN P25 AND P75:
  verdict = "Wajar" (Fair/Market-Rate)
  percentile_position = 50  [user salary at ~P50]

ELSE IF salary_reported > P75:
  verdict = "Di Atas Pasar" (Above Market)
  percentile_position = 80  [user salary at ~P80]
```

**UMR (Upah Minimum Regional) Override Logic:**

Indonesian law (UU No. 13 Tahun 2003, Pasal 89) requires minimum wage compliance. UMR varies by province (set annually in November, effective Jan 1).

```
IF salary_reported >= UMR_current_year[province]:
  # Salary meets legal minimum

  IF salary_reported >= P25:
    # Case A: Above legal AND above market benchmark
    verdict = "Wajar" or "Di Atas Pasar" (normal logic applies)

  ELSE IF salary_reported BETWEEN UMR AND P25:
    # Case B: Legally compliant but below market benchmark
    # This indicates employer is paying minimum wage only
    verdict = "Wajar Hukum, Di Bawah Pasar"
    explanation = "Salary meets legal minimum (UMR) but below market rate for this role/experience"
    recommendation = "Consider negotiating based on market data and experience"

ELSE IF salary_reported < UMR_current_year[province]:
  # CRITICAL: Salary below legal minimum
  verdict = "BAWAH UMR - POTENTIALLY ILLEGAL"
  severity = "CRITICAL"
  recommendation = "Report to Dinas Ketenagakerjaan (labor ministry)"
```

**2026 UMR Examples (Reference):**
- Jakarta: IDR 4,820,000 (annual update Jan 2026)
- Surabaya: IDR 3,470,000
- Bandung: IDR 3,210,000
- Medan: IDR 3,570,000
- Yogyakarta: IDR 2,570,000
(Values update annually; system fetches from Kemnaker API)

#### 1.2.5 Low Sample Size Handling (Fallback Logic)

**Minimum Sample Size Requirement: n = 15**

For any cell (job_title, experience, education, province, city):
- If n ≥ 15: Use direct percentile calculation
- If 5 ≤ n < 15: Apply Bayesian shrinkage to parent level
- If n < 5: Escalate to higher level; use no cell-specific verdict

**Fallback Hierarchy:**

```
Level 1 (Preferred): [job_title, experience, education, province, city]
  ✓ If n ≥ 15: CALCULATE and RETURN verdict
  ✗ If n < 15: Continue to Level 2

Level 2: [job_title, experience, education, province] (drop city)
  ✓ If n ≥ 30: APPLY Bayesian shrinkage blend:
    verdict_final = 0.3 * verdict_level1 + 0.7 * verdict_level2
  ✗ If n < 30: Continue to Level 3

Level 3: [job_title, experience, education] (drop province, aggregate nationwide)
  ✓ If n ≥ 50: RETURN with confidence_score = 0.6
    (Note: no geographic specificity, user shown "Nationwide average")
  ✗ If n < 50: Continue to Level 4

Level 4: [job_title, experience] (drop education, aggregate)
  ✓ If n ≥ 100: RETURN with confidence_score = 0.4
    (Note: "Rough estimate based on limited data")
  ✗ If n < 100: Continue to Level 5

Level 5: [job_title] (aggregate all experience, education, geography)
  ✓ If n ≥ 200: RETURN with confidence_score = 0.2
    (Note: "Very rough estimate; insufficient detailed data")
  ✗ If n < 200: RETURN NULL with user message
    "Insufficient data for this job title. Try broader search."
```

**Bayesian Shrinkage Formula (Level 2 blend):**

```
μ_shrinkage = (n_level1 * μ_level1 + λ * μ_level2) / (n_level1 + λ)

where:
  λ = prior_strength = 30 (assumes prior from parent level worth ~30 samples)
  n_level1 = actual sample size at finer level
  μ_level1 = percentile estimate at finer level
  μ_level2 = percentile estimate at coarser level
```

#### 1.2.6 Confidence Score Calculation

**Confidence Score Formula (0-100 scale):**

```
confidence = 100 * (sample_factor * recency_factor * variance_factor * method_factor)

where:

sample_factor = min(n_effective / 50, 1.0)
  - n_effective = n_bps * w_bps + n_crowd * w_crowd (weighted effective sample size)
  - Grows from 0 to 1 as n_effective reaches 50
  - At n_effective < 5: 0.3 (low confidence)
  - At n_effective > 100: 1.0 (high confidence)

recency_factor = (1 - decay_by_age)
  - For BPS data aged 0-12 months: 1.0
  - For BPS data aged 12-24 months: 0.8
  - For BPS data aged >24 months: 0.6
  - For crowdsourced data aged <1 month: 1.0
  - For crowdsourced data aged >6 months: 0.7

variance_factor = 1 / (1 + σ²_composite / μ_composite)
  - Penalizes high variance (uncertain distribution)
  - Typical range: 0.5-1.0

method_factor:
  - Direct percentile (n ≥ 15): 1.0
  - Shrinkage blend (5 ≤ n < 15): 0.8
  - Parent-level aggregate (n < 5): 0.6
```

**Confidence Score Interpretation:**
- 80-100: High confidence (can make career decisions based on this)
- 60-79: Medium-high confidence (use as reference, not primary)
- 40-59: Medium confidence (rough estimate only)
- 20-39: Low confidence (informational only)
- <20: Very low confidence (not shown to user; fallback to previous level)

#### 1.2.7 Edge Cases & Special Handling

**Edge Case 1: Contractual vs Permanent Employment**

```
IF employment_type = "Contract":
  - Typically 10-20% higher to compensate for lack of benefits
  - Verdict calculated separately; mark as "Contract Rate"
  - Separate P25/P75 thresholds for contract market
  - UMR still applies to base salary component

  salary_annualized = salary_monthly * (contract_length_months / 12)
  (For comparison with permanent role salaries)

IF employment_type = "Startup-Equity":
  - Base salary may be 20-40% lower than market
  - Equity component not monetizable immediately
  - Note in verdict: "Equity compensation not included in market comparison"
  - Confidence score reduced by 0.2 (equity value highly uncertain)
```

**Edge Case 2: Base vs Total Compensation**

```
salaryBasis = "Base Salary Only":
  - Use reported figure directly
  - Note: does not include benefits (health insurance, retirement, etc.)

salaryBasis = "Base + Regular Allowances":
  - Include: tunjangan makan (food allowance), tunjangan transport (transport), tunjangan keluarga (family)
  - EXCLUDE: tunjangan shift, tunjangan prakarsa (discretionary)
  - Formula: base + (allowances_classified_as_regular * 100%)

salaryBasis = "Total Compensation":
  - Include: base + all regular allowances + benefits (estimated)
  - EXCLUDE: one-time bonuses, stock options (until vested)
  - Estimate benefit value: ~IDR 3-5M/year for mid-career (healthcare + retirement)
  - Adjustment: salary_adjusted = salary_total - (estimated_benefit_value / 12)
    (Convert back to cash equivalent for market comparison)
```

**Edge Case 3: Probation Period**

```
IF experience_in_current_role < 6_months AND employment_type = "Permanent":
  - Probation period (masa coba-coba per UU 13/2003 Pasal 58)
  - Salary during probation typically 75-90% of permanent rate
  - ADJUST: salary_annualized = salary_reported / 0.85 (back-calculate to permanent equivalent)
  - Note: "You are in probation period; salary will typically increase upon confirmation"
  - confidence_score reduced by 0.1
```

**Edge Case 4: Part-Time / Hourly Roles**

```
IF employment_type = "Part-Time":
  - Input: hourly_rate (IDR/hour) and hours_per_week
  - Annualize: salary_monthly_equivalent = hourly_rate * hours_per_week * 52 / 12
  - Adjust for tax treatment: IDR 5M/month exemption for part-time/gig workers (UU 36/2008)
  - Verdict calculated on annualized equivalent
  - Confidence reduced by 0.15 (part-time market less stable)
```

**Edge Case 5: Government (ASN) vs Private Sector**

```
IF employer_type = "Government":
  - Use official PERMENPAN salary scale (golongan, pangkat, tunjangan)
  - No variance; salary fully determined by regulation
  - Verdict logic: Compare against legal scale
    ✓ If matches: "Sesuai Skala ASN [Golongan]"
    ✗ If below: "BAWAH SKALA ASN - Audit Required"
  - Do not apply market percentile logic (not applicable to government)

IF employer_type = "Private":
  - Use standard market percentile logic (as defined above)
```

### 1.3 Output JSON Schema

#### 1.3.1 Free Tier Response

```json
{
  "requestId": "uuid-v4",
  "timestamp": "2026-04-07T14:30:00Z",
  "verdict": {
    "status": "Di Bawah Pasar | Wajar | Di Atas Pasar | Wajar Hukum Di Bawah Pasar | Bawah UMR",
    "percentile": 42,
    "explanation": "Gaji Anda berada di bawah rata-rata pasar untuk posisi [jobTitle] dengan [experience] tahun pengalaman di [province]."
  },
  "benchmark": {
    "p25": 5500000,
    "p50": 7200000,
    "p75": 9800000,
    "currency": "IDR",
    "basedOn": "n=127 samples (BPS 60%, crowdsourced 40%), updated 2026-03-15"
  },
  "confidence": {
    "score": 73,
    "interpretation": "Medium-High Confidence",
    "reasons": [
      "Sample size: 127 (Good)",
      "Data recency: 23 days old (Good)",
      "Variance: Moderate"
    ]
  },
  "legality": {
    "umr": 4820000,
    "umrProvince": "Jakarta",
    "umrYear": 2026,
    "compliant": true,
    "gap": 180000
  },
  "shareableLink": {
    "enabled": true,
    "expiryDays": 30,
    "url": "cekwajar.id/share/verdict_xyz123"
  }
}
```

#### 1.3.2 Premium Tier Response (Additional Fields)

```json
{
  "requestId": "uuid-v4",
  "timestamp": "2026-04-07T14:30:00Z",
  "verdict": {
    "status": "Di Atas Pasar",
    "percentile": 78,
    "percentileBand": "P75-P100",
    "explanation": "Gaji Anda berada di atas rata-rata pasar untuk posisi [jobTitle]..."
  },
  "benchmark": {
    "p10": 4200000,
    "p25": 5500000,
    "p50": 7200000,
    "p75": 9800000,
    "p90": 13200000,
    "iqr": 4300000,
    "currency": "IDR",
    "basedOn": "n=127 samples",
    "distribution": {
      "shape": "right-skewed",
      "median_to_mean_ratio": 0.92,
      "outlier_count": 3
    }
  },
  "benchmark_by_city": [
    {
      "city": "Jakarta",
      "p50": 8100000,
      "p75": 11200000,
      "n": 67,
      "versus_user": "+12.5%"
    },
    {
      "city": "Bandung",
      "p50": 6200000,
      "p75": 8100000,
      "n": 34,
      "versus_user": "-13.9%"
    },
    {
      "city": "Surabaya",
      "p50": 6800000,
      "p75": 9100000,
      "n": 26,
      "versus_user": "-5.6%"
    }
  ],
  "benchmark_by_industry": [
    {
      "industry": "Technology",
      "p50": 8500000,
      "versus_user": "+18.1%"
    },
    {
      "industry": "Finance",
      "p50": 8200000,
      "versus_user": "+13.9%"
    },
    {
      "industry": "Manufacturing",
      "p50": 5900000,
      "versus_user": "-18.1%"
    }
  ],
  "benchmark_by_company_size": [
    {
      "size": ">1000",
      "p50": 8100000,
      "versus_user": "+12.5%"
    },
    {
      "size": "50-250",
      "p50": 6700000,
      "versus_user": "-7.0%"
    }
  ],
  "trend": {
    "direction": "up",
    "change_3months": "+4.2%",
    "change_12months": "+8.7%",
    "elasticity_to_experience": 1.15,
    "elasticity_to_education": 1.08
  },
  "confidence": {
    "score": 73,
    "interpretation": "Medium-High",
    "sampleBreakdown": {
      "bps_samples": 76,
      "bps_weight": 0.60,
      "crowd_samples": 51,
      "crowd_weight": 0.40,
      "bps_recency_months": 14,
      "crowd_recency_days": 23
    },
    "fallback_level": 1,
    "data_sources_used": ["BPS SAKERNAS 2025", "Crowdsourced (cekwajar.id)"]
  },
  "negotiation": {
    "market_gap": {
      "amount": 2600000,
      "percentage": 36.1,
      "direction": "below"
    },
    "recommendation": "Dengan pengalaman [experience] tahun dan background [education], target negosiasi: IDR 9.8M - 11.2M (P75-P90)",
    "benchmark_for_negotiation": 9800000,
    "suggested_talking_points": [
      "Pengalaman [experience] tahun di industri [industry]",
      "Market rate untuk posisi ini di [province] adalah IDR 7.2M - 9.8M",
      "Pendidikan [education] + sertifikasi [certs] menambah nilai"
    ]
  },
  "legality": {
    "umr": 4820000,
    "umrProvince": "Jakarta",
    "umrYear": 2026,
    "compliant": true,
    "gap": 2180000,
    "gaps_to_watch": [
      {
        "category": "Tunjangan Makan",
        "required_if_natura": false,
        "required_if_tunai": false
      },
      {
        "category": "Tunjangan Transportasi",
        "required_if_natura": false,
        "required_if_tunai": false
      }
    ]
  },
  "exportFormats": {
    "pdf": "cekwajar.id/export/verdict_xyz123.pdf",
    "screenshot": {
      "optimized_url": "cekwajar.id/screenshot/verdict_xyz123",
      "dimensions": "1080x1920",
      "format": "PNG with watermark"
    }
  },
  "shareableLink": {
    "enabled": true,
    "expiryDays": 30,
    "url": "cekwajar.id/share/verdict_xyz123",
    "allowProfileTag": true,
    "privacy_level": "anonymous | attributed"
  }
}
```

### 1.4 Screenshot-Sharing Optimized Output Format

For mobile sharing (WhatsApp, Instagram, LinkedIn):

```json
{
  "shareableImage": {
    "type": "PNG",
    "format": "1080x1920px (9:16 mobile-optimized)",
    "content": {
      "header": {
        "app_logo": "cekwajar.id",
        "page_title": "Cek Gaji",
        "generated_at": "7 April 2026, 14:30"
      },
      "verdict_card": {
        "background_color": "linear-gradient(to bottom, #4F46E5 0%, #7C3AED 100%)",
        "verdict_badge": {
          "text": "Di Atas Pasar",
          "icon": "⬆️ (green)",
          "percentile_display": "78 percentile",
          "percentile_visual": "████████░ (10/10 filled)"
        },
        "benchmark_section": {
          "title": "Benchmark Pasar",
          "display": "Gaji Anda: IDR 7.2M\nP50 Pasar: IDR 7.2M\nP75 Pasar: IDR 9.8M",
          "visual": "Bar chart showing user salary vs benchmark"
        }
      },
      "key_metrics": [
        {
          "label": "Persentil",
          "value": "78",
          "icon": "📊"
        },
        {
          "label": "Confidence",
          "value": "73%",
          "icon": "✅"
        },
        {
          "label": "Data Points",
          "value": "127 samples",
          "icon": "📈"
        }
      ],
      "footer": {
        "cta_button": "Lihat Detail di Cekwajar.id",
        "watermark": "cekwajar.id - Data Intelligence Platform"
      }
    },
    "colors": {
      "verdict_di_bawah_pasar": "#EF4444",
      "verdict_wajar": "#F59E0B",
      "verdict_di_atas_pasar": "#10B981",
      "verdict_bawah_umr": "#991B1B"
    }
  }
}
```

---

## WAJAR SLIP: Payslip Decoder & Compliance Auditor

### 2.1 Input Processing: OCR + Manual Entry Fallback

#### 2.1.1 OCR Approach

**Primary Method: Tesseract v5 + Fine-Tuned Indonesian Payslip Model**

```
Input: User uploads payslip image (JPG/PNG)
↓
Step 1: Image Preprocessing
  - Deskew: Rotate to perfect alignment
  - Binarization: Convert to B&W for clarity
  - Upscaling: 2x resolution if <300 DPI
  - Denoising: Remove scanning artifacts
↓
Step 2: Region Detection (Custom Model - Indonesian Payslips)
  - Detect sections: Header, Employee Info, Earnings, Deductions, Net
  - Train on 500+ real Indonesian payslip samples
  - Output: Bounding boxes for each section
↓
Step 3: OCR Extraction (Tesseract + Post-Processing)
  - Extract text from bounded regions
  - Apply currency regex: IDR (\d{1,3}(?:,\d{3})*\.?\d{0,2})
  - Extract dates: DD/MM/YYYY, YYYY-MM-DD formats
  - Extract name, ID, position, etc.
↓
Step 4: Validation & Fallback
  - Checksum validation: Total Earnings - Total Deductions = Net Salary
  - If variance > 5%: Flag for manual review, prompt user for verification
  - If OCR confidence < 70%: Show extracted fields to user with edit option
  - If OCR fails completely: Fallback to manual entry form
```

**OCR Confidence Thresholds:**
- 90-100%: Auto-accept, proceed to calculation
- 70-89%: Show to user with "seems correct?" prompt
- 50-69%: Show all extracted fields for manual verification/editing
- <50%: Fallback to manual entry form

#### 2.1.2 Manual Entry Fallback Form

```json
{
  "form_type": "ManualPayslipEntry",
  "sections": [
    {
      "section": "Employee Information",
      "fields": [
        {
          "id": "employee_name",
          "label": "Nama Karyawan",
          "type": "text",
          "required": true
        },
        {
          "id": "employee_id",
          "label": "Nomor Identitas (NIK/KITAS)",
          "type": "text",
          "required": true
        },
        {
          "id": "position",
          "label": "Posisi/Jabatan",
          "type": "text",
          "required": true
        },
        {
          "id": "payroll_period",
          "label": "Bulan/Tahun Gaji",
          "type": "date",
          "format": "MM/YYYY",
          "required": true
        }
      ]
    },
    {
      "section": "Salary Components (Penghasilan)",
      "fields": [
        {
          "id": "base_salary",
          "label": "Gaji Pokok",
          "type": "currency",
          "currency": "IDR",
          "required": true
        },
        {
          "id": "tunjangan_makan",
          "label": "Tunjangan Makan",
          "type": "currency",
          "natura_option": true,
          "required": false
        },
        {
          "id": "tunjangan_transport",
          "label": "Tunjangan Transportasi",
          "type": "currency",
          "natura_option": true,
          "required": false
        },
        {
          "id": "tunjangan_keluarga",
          "label": "Tunjangan Keluarga",
          "type": "currency",
          "required": false
        },
        {
          "id": "tunjangan_shift",
          "label": "Tunjangan Shift/Lembur",
          "type": "currency",
          "required": false
        },
        {
          "id": "bonus_commission",
          "label": "Bonus/Komisi",
          "type": "currency",
          "required": false,
          "note": "Jangan include jika tidak setiap bulan"
        },
        {
          "id": "other_income",
          "label": "Penghasilan Lain",
          "type": "currency",
          "required": false
        }
      ]
    },
    {
      "section": "Deductions (Potongan)",
      "fields": [
        {
          "id": "pph21",
          "label": "PPh 21 (Pajak Penghasilan)",
          "type": "currency",
          "calculated": true,
          "editable": true,
          "note": "Sistem akan menghitung; ubah jika ada informasi lebih akurat"
        },
        {
          "id": "bpjs_ketenagakerjaan",
          "label": "BPJS Ketenagakerjaan (JHT, JKK, JKM, JP)",
          "type": "currency",
          "required": true
        },
        {
          "id": "bpjs_kesehatan",
          "label": "BPJS Kesehatan",
          "type": "currency",
          "required": true
        },
        {
          "id": "jamsostek_other",
          "label": "Jaminan Sosial Lain",
          "type": "currency",
          "required": false
        },
        {
          "id": "pension_contribution",
          "label": "Iuran Dana Pensiun",
          "type": "currency",
          "required": false
        },
        {
          "id": "loans_deduction",
          "label": "Cicilan Pinjaman",
          "type": "currency",
          "required": false
        },
        {
          "id": "health_insurance_company",
          "label": "Asuransi Kesehatan Tambahan",
          "type": "currency",
          "required": false
        },
        {
          "id": "other_deduction",
          "label": "Potongan Lain",
          "type": "currency",
          "required": false
        }
      ]
    },
    {
      "section": "Summary",
      "fields": [
        {
          "id": "gross_salary",
          "label": "Gaji Bruto (Total Penghasilan)",
          "type": "currency",
          "calculated": true
        },
        {
          "id": "total_deduction",
          "label": "Total Potongan",
          "type": "currency",
          "calculated": true
        },
        {
          "id": "net_salary",
          "label": "Gaji Netto (Dibawa Pulang)",
          "type": "currency",
          "calculated": true
        }
      ]
    }
  ]
}
```

### 2.2 Calculation Logic: Complete PPh21 & BPJS Implementation (2026)

#### 2.2.1 PPh 21 Calculation (Peraturan Direktur Jenderal Pajak No. PER-16/PJ/2016)

**Step 1: Determine PTKP (Penghasilan Tidak Kena Pajak - Non-Taxable Income)**

2026 PTKP values (Updated per Peraturan Direktur Jenderal Pajak):

```
Single (TK/0):                          IDR 54,000,000 per year
Married (K/1):                          IDR 58,500,000 per year
Married + 1 child (K/2):                IDR 61,500,000 per year
Married + 2 children (K/3):             IDR 64,500,000 per year
Non-resident foreigner (WKWP=0):        IDR 0

Additional per dependent (max K/3):     IDR 3,000,000 per year each

Spouse PTKP (if spouse also working):   IDR 54,000,000 per year
```

**User Selection Form:**
```json
{
  "tax_status": "TK | K/1 | K/2 | K/3",
  "spouse_working": boolean,
  "num_dependents": 0-3,
  "non_resident_foreign_worker": boolean
}
```

**Calculation:**
```
ptkp_annual = base_ptkp[tax_status]
if spouse_working:
  ptkp_annual += 54000000
if num_dependents > (tax_status_dependents):
  # Extra dependents (beyond what's in status)
  ptkp_annual += (num_dependents - tax_status_dependents) * 3000000

ptkp_monthly = ptkp_annual / 12
```

**Example:**
```
User: Married (K/1), spouse not working, 2 kids (status K/2)
  ptkp_annual = 61,500,000 (K/2)
  ptkp_monthly = 61,500,000 / 12 = IDR 5,125,000
```

**Step 2: Calculate Taxable Income (PPh 21 Base)**

```
Step 2a: Determine Gross Salary Components
  gross_monthly = base_salary + tunjangan_makan + tunjangan_transport + tunjangan_keluarga
  EXCLUDE: tunjangan_shift (overtime), bonus, commission, one-time payments

  Note: Tunjangan natura (meals, transport in-kind) are TAXABLE under
        UU 36/2008 Pasal 4(3) but NOT subject to BPJS

Step 2b: Apply PTKP Deduction
  taxable_income_monthly = max(gross_monthly - ptkp_monthly, 0)

Step 2c: Annual Projection (for bracket calculation)
  taxable_income_annual = taxable_income_monthly * 12

Step 2d: Biaya Jabatan Deduction (UU 36/2008 Pasal 6(1)g)
  # Maximum IDR 500,000/month or 5% of gross salary
  biaya_jabatan_max = min(500000, gross_monthly * 0.05)
  # Deducted from gross before PTKP in some interpretations
  # CORRECT: Applied after PTKP (per latest DJP guidance)

  taxable_income_after_biaya = max(taxable_income_monthly - biaya_jabatan_max, 0)
```

**Step 3: Apply Progressive Tax Brackets**

2026 Indonesian PPh 21 Tax Brackets (UU 36/2008 Pasal 17(1)a):

```
Taxable Income Bracket        Tax Rate
IDR 0 - 60,000,000 annually   5%
IDR 60M - 250M annually       15%
IDR 250M - 500M annually      25%
IDR 500M - 1B annually        30%
IDR 1B+ annually              35%
```

**Monthly Equivalent (divide brackets by 12):**

```
Bracket 1: IDR 0 - 5,000,000/month      → 5%
Bracket 2: 5M - 20.833M/month           → 15%
Bracket 3: 20.833M - 41.667M/month      → 25%
Bracket 4: 41.667M - 83.333M/month      → 30%
Bracket 5: 83.333M+/month               → 35%
```

**Calculation (Stepped Progressive Tax):**

```python
def calculate_pph21_monthly(taxable_income_monthly):
    """
    Progressive tax calculation (stepped, not marginal across all brackets)
    """
    if taxable_income_monthly <= 5000000:
        tax = taxable_income_monthly * 0.05
    elif taxable_income_monthly <= 20833333:
        tax = (5000000 * 0.05) + ((taxable_income_monthly - 5000000) * 0.15)
    elif taxable_income_monthly <= 41666667:
        tax = (5000000 * 0.05) + (15833333 * 0.15) + ((taxable_income_monthly - 20833333) * 0.25)
    elif taxable_income_monthly <= 83333333:
        tax = (5000000 * 0.05) + (15833333 * 0.15) + (20833334 * 0.25) + ((taxable_income_monthly - 41666667) * 0.30)
    else:
        tax = (5000000 * 0.05) + (15833333 * 0.15) + (20833334 * 0.25) + (41666666 * 0.30) + ((taxable_income_monthly - 83333333) * 0.35)

    return round(tax, 0)  # Round to nearest IDR
```

**Example Calculation:**
```
Gross Salary: IDR 8,000,000
Tax Status: K/1 (married)
PTKP Monthly: IDR 5,125,000
Biaya Jabatan: IDR 400,000 (5% of 8M)

Taxable Income = 8,000,000 - 5,125,000 - 400,000 = IDR 2,475,000

Tax Bracket 1 applies (2.475M < 5M):
  PPh 21 = 2,475,000 * 0.05 = IDR 123,750
```

**Step 4: Special Cases & Adjustments**

**Case A: Spouse's Income (If Applicable)**
```
If spouse_working = true:
  - Spouse has separate PTKP (54M/year)
  - Calculate spouse's tax separately
  - Total household tax = employee_tax + spouse_tax
  - System shows: "Perhatian: Hitungan memasukkan pajak pasangan"
```

**Case B: Non-Resident Foreign Workers (WKWP=0)**
```
If non_resident_foreign_worker = true:
  - No PTKP (considered PTKP = 0)
  - Flat 20% withholding on gross salary (UU 36/2008 Pasal 21(3)b)
  OR
  - Progressive brackets apply if treaty country (bilateral tax treaty)

  pph21 = gross_salary * 0.20 (default)

  Note: Treaty countries may have reduced rates (e.g., Singapore 10%, Japan 15%)
```

**Case C: Income from Multiple Sources**
```
If user has:
  - Primary employment (this payslip)
  - Side business/freelance income

System note: "Perhitungan PPh 21 hanya untuk penghasilan dari payslip ini.
             Jika punya penghasilan lain, konsultasi dengan konsultan pajak."
```

#### 2.2.2 BPJS Ketenagakerjaan (Employment Insurance)

Regulated under **UU 24/2011 & PP 34/2015**

**Four Components:**

```
1. JHT (Jaminan Hari Tua - Old Age Insurance)
   - Employee rate: 3.7% of salary
   - Employer rate: 3.7% of salary
   - Salary cap: IDR 9,000,000/month (2026)
   - Formula: min(salary, 9000000) * 0.037

2. JKK (Jaminan Kecelakaan Kerja - Work Accident Insurance)
   - Employee rate: 0% (employer only)
   - Employer rate: 0.24% - 1.74% (varies by risk class)
   - Salary cap: IDR 9,000,000/month
   - Not visible on employee payslip (paid by employer)
   - Formula: Not charged to employee

3. JKM (Jaminan Kematian - Death Insurance)
   - Employee rate: 0% (employer only)
   - Employer rate: 0.30% of salary
   - Salary cap: IDR 9,000,000/month
   - Not visible on employee payslip
   - Formula: Not charged to employee

4. JP (Program Jaminan Pensiun - Pension Plan)
   - Employee rate: 2% of salary (mandatory since Jan 1, 2015)
   - Employer rate: 3.5% of salary
   - Salary cap: IDR 9,000,000/month
   - Formula: min(salary, 9000000) * 0.02 (employee)

Total Employee BPJS Ketenagakerjaan = JHT + JP
                                     = (min(salary, 9M) * 0.037) + (min(salary, 9M) * 0.02)
                                     = min(salary, 9M) * 0.057
```

**Calculation Example:**
```
Salary: IDR 8,000,000

JHT = 8,000,000 * 0.037 = IDR 296,000
JP  = 8,000,000 * 0.02  = IDR 160,000
──────────────────────────────────────
Total BPJS Ketenagakerjaan (Employee) = IDR 456,000

(Employer separately pays JKK + JKM on top, ~2% additional)
```

**Salary Cap Handling:**
```
If salary > 9,000,000:
  bpjs_ktk = 9,000,000 * 0.057 = IDR 513,000 (capped)
  Note shown: "Kontribusi BPJS sudah mencapai batas maksimal"
```

#### 2.2.3 BPJS Kesehatan (Health Insurance)

Regulated under **UU 40/2004 & PP 111/2013**

**Employee Contribution Rate: 1% of gross salary**

```
bpjs_kesehatan_employee = salary * 0.01

Salary cap: IDR 12,000,000/month (since 2024 update)
bpjs_kesehatan = min(salary, 12000000) * 0.01

Employer covers:
- 3% employee contribution (to reduce employee burden)
- So effective employee: 1%, employer: 3% = 4% total

Family coverage (tanggungan):
- First family member (spouse/child): 3% of base employee contribution
- Subsequent family members: 1.5% each
```

**Example:**
```
Salary: IDR 10,000,000
Employee: 10,000,000 * 0.01 = IDR 100,000
Employer: 10,000,000 * 0.03 = IDR 300,000 (not visible on payslip)

Family tanggungan (example: 1 spouse + 2 children):
  Spouse: 100,000 * 0.03 = IDR 3,000
  Child 1: 100,000 * 0.015 = IDR 1,500
  Child 2: 100,000 * 0.015 = IDR 1,500
  Total tanggungan = IDR 6,000 (sometimes deducted from employee salary)
```

**Verification in Payslip:**
```
Typical display:
  BPJS Kesehatan (Pribadi):     IDR 100,000
  BPJS Kesehatan (Tanggungan):  IDR 6,000 (if deducted)
  ─────────────────────────────
  Total BPJS Kesehatan:         IDR 106,000
```

#### 2.2.4 Taxable vs Non-Taxable Allowances

**Taxable Allowances (Subject to PPh 21):**

```
✓ Tunjangan Makan (tunai/nature):
  - Max non-taxable: IDR 1,000,000/month (if in-kind/natura)
  - Excess is taxable
  - If tunai (cash): Fully taxable

✓ Tunjangan Transportasi (tunai/nature):
  - Max non-taxable: IDR 1,000,000/month (if in-kind/natura)
  - Excess is taxable
  - If tunai (cash): Fully taxable

✓ Tunjangan Keluarga (family allowance):
  - Fully taxable (no exemption)
  - Included in gross salary for tax calculation

✓ Tunjangan Shift/Overtime:
  - Fully taxable
  - Included in gross salary

✓ Bonus/Commission (if monthly):
  - Fully taxable
  - Included in gross salary
```

**Non-Taxable Allowances (Exempt from PPh 21):**

```
✗ In-kind meal provision (natura):
  - Value: IDR 1,000,000/month
  - Must be actual meals provided (not reimbursement)
  - Deductible from employee's taxable income

✗ In-kind transport (natura):
  - Value: IDR 1,000,000/month
  - Must be shuttle service or company vehicle
  - Not cash reimbursement

✗ Medical check-up:
  - Annual health screening (SkD/check-up)
  - Fully exempt (employer-provided)

✗ Religious facility (if company provides):
  - On-site prayer room/facilities
  - No cash value exemption
```

**System Logic for Tunjangan Classification:**

```json
{
  "tunjangan_makan": {
    "tunai": {
      "taxable": true,
      "included_in_gross": true,
      "bpjs_subject": true,
      "note": "Tunjangan makan tunai dikenai PPh 21 dan BPJS"
    },
    "natura": {
      "taxable": false,
      "max_non_taxable": 1000000,
      "included_in_gross": "only if exceeds IDR 1M",
      "bpjs_subject": false,
      "note": "Tunjangan makan natura (max IDR 1M) bebas PPh 21"
    }
  },
  "tunjangan_transport": {
    "tunai": {
      "taxable": true,
      "included_in_gross": true,
      "bpjs_subject": true,
      "note": "Tunjangan transport tunai dikenai PPh 21 dan BPJS"
    },
    "natura": {
      "taxable": false,
      "max_non_taxable": 1000000,
      "included_in_gross": "only if exceeds IDR 1M",
      "bpjs_subject": false,
      "note": "Tunjangan transport natura (max IDR 1M) bebas PPh 21"
    }
  }
}
```

**User Form Input:**
```json
{
  "tunjangan_makan": {
    "amount": 500000,
    "type": "tunai | natura",
    "frequency": "monthly (default)"
  },
  "tunjangan_transport": {
    "amount": 600000,
    "type": "tunai | natura",
    "frequency": "monthly (default)"
  }
}

Calculation:
  if tunjangan_makan.type == "tunai":
    gross_salary += 500000  (fully taxable)
  elif tunjangan_makan.type == "natura" AND 500000 <= 1000000:
    gross_salary += 0  (fully exempt)
  elif tunjangan_makan.type == "natura" AND 500000 > 1000000:
    gross_salary += (500000 - 1000000) = excess (taxable)
```

#### 2.2.5 Biaya Jabatan Deduction (5% up to IDR 500K)

**Regulation: UU 36/2008 Pasal 6(1)g**

```
Purpose: Deduction for job-related expenses (office supplies, uniform, etc.)

Calculation:
  biaya_jabatan = min(0.05 * gross_salary, 500000)

Examples:
  Salary IDR 5M:  biaya_jabatan = min(250K, 500K) = IDR 250,000
  Salary IDR 15M: biaya_jabatan = min(750K, 500K) = IDR 500,000
  Salary IDR 20M: biaya_jabatan = min(1M, 500K) = IDR 500,000
```

**Tax Effect:**
```
Taxable income = Gross - PTKP - Biaya Jabatan

Example:
  Gross: IDR 8,000,000
  PTKP: IDR 5,125,000
  Biaya Jabatan: IDR 400,000
  ─────────────────────────
  Taxable: IDR 2,475,000
  Tax (5%): IDR 123,750
```

### 2.3 Compliance Violation Detection

**List of Detectable Violations:**

| Violation | Severity | Detection Logic | Recommended Action |
|-----------|----------|-----------------|-------------------|
| Below UMR | CRITICAL | IF net_salary < UMR | Report to labor ministry (Disnaker) |
| Missing BPJS-Ktk | CRITICAL | IF bpjs_ktk = 0 AND date > 2015 | Demand BPJS enrollment |
| Missing BPJS-Kes | CRITICAL | IF bpjs_kes = 0 AND date > 2004 | Enroll via BPJS or private insurance |
| No PPh21 withholding | WARNING | IF salary > PTKP AND pph21 = 0 | Request tax calculation |
| Excessive PPh21 | WARNING | IF pph21 > calculated_tax * 1.2 | Request tax reconciliation/SPT |
| Excessive BPJS deduction | WARNING | IF bpjs_total > (salary * 0.10) | Verify rates with HR |
| Missing biaya_jabatan | INFO | IF salary > 10M AND no biaya_jabatan deducted | Note: not mandatory but allowable |
| Tunjangan above limits | WARNING | IF tunjangan_makan_natura > 1M + extra not accounted | Excess should be taxed |
| No pension (JP) deduction | WARNING | IF date > 2015 AND jp_deduction = 0 | Mandatory since 2015 |
| Incorrect tax status | INFO | IF estimated_tax < calculated_tax * 0.8 | Verify tax status accuracy |

### 2.4 Output: Audit Report Structure

#### 2.4.1 JSON Response Schema

```json
{
  "requestId": "uuid-v4",
  "timestamp": "2026-04-07T14:30:00Z",
  "payslip": {
    "employee": {
      "name": "Budi Santoso",
      "position": "Software Engineer",
      "tax_status": "K/1"
    },
    "period": "April 2026",
    "salary_components": {
      "base_salary": 8000000,
      "tunjangan_makan": {
        "amount": 500000,
        "type": "tunai",
        "taxable": true
      },
      "tunjangan_transport": {
        "amount": 600000,
        "type": "natura",
        "taxable": false
      },
      "tunjangan_keluarga": 300000,
      "gross_salary": 9400000
    },
    "deductions": {
      "pph21": 189000,
      "bpjs_ketenagakerjaan": {
        "jht": 296000,
        "jp": 160000,
        "total": 456000
      },
      "bpjs_kesehatan": 94000,
      "other_deduction": 0,
      "total_deductions": 739000
    },
    "net_salary": 8661000
  },
  "tax_breakdown": {
    "gross_salary": 9400000,
    "ptkp_monthly": 5125000,
    "biaya_jabatan": 470000,
    "taxable_income": 3805000,
    "tax_bracket": "5% (IDR 0-5M)",
    "pph21_calculated": 190250,
    "pph21_actual": 189000,
    "variance": -1250,
    "variance_note": "Minimal difference, likely rounding"
  },
  "compliance_audit": {
    "violations": [
      {
        "id": "WARN_001",
        "severity": "WARNING",
        "title": "Biaya Jabatan Tidak Diperhitungkan",
        "description": "Sistem mendeteksi gaji IDR 9.4M, namun biaya jabatan (5% atau max IDR 500K) tidak dikurangkan dari penghasilan bruto sebelum perhitungan pajak.",
        "implication": "Pajak yang dipotong mungkin lebih tinggi dari yang seharusnya (~IDR 23K-25K lebih tinggi).",
        "recommendation": "Hubungi bagian HR/payroll dan minta untuk memasukkan biaya jabatan dalam perhitungan PPh21.",
        "regulation": "UU 36/2008 Pasal 6(1)g"
      },
      {
        "id": "INFO_001",
        "severity": "INFO",
        "title": "Tunjangan Makan & Transportasi Natura",
        "description": "Tunjangan makan IDR 500K (tunai - taxable) dan transportasi IDR 600K (natura - exemptable) terdeteksi.",
        "implication": "Jika transportasi benar-benar natura (shuttle/kendaraan), IDR 600K bebas pajak sesuai regulasi.",
        "recommendation": "Verifikasi dengan HR bahwa transportasi adalah fasilitas bukan uang tunai.",
        "regulation": "UU 36/2008 Pasal 4(3)"
      }
    ],
    "compliant_items": [
      {
        "item": "UMR Compliance",
        "status": "✓ COMPLIANT",
        "note": "Gaji netto IDR 8.661M > UMR Jakarta IDR 4.82M"
      },
      {
        "item": "BPJS Ketenagakerjaan",
        "status": "✓ COMPLIANT",
        "note": "JHT + JP total IDR 456K sudah dipotong"
      },
      {
        "item": "BPJS Kesehatan",
        "status": "✓ COMPLIANT",
        "note": "IDR 94K (1% dari gaji) sudah dipotong"
      },
      {
        "item": "PPh 21 Withholding",
        "status": "✓ COMPLIANT",
        "note": "IDR 189K sesuai dengan perhitungan standar"
      }
    ]
  },
  "recommendations": {
    "tax_optimization": [
      {
        "title": "Konfirmasi Status Pajak",
        "description": "Status pajak K/1 digunakan. Jika Anda status bujangan atau punya tanggungan berbeda, PTKP bisa direvisi naik hingga +IDR 3M/tahun per anak.",
        "potential_saving": "IDR 15K-50K/bulan tergantung status sebenarnya"
      },
      {
        "title": "Verifikasi Biaya Jabatan",
        "description": "Pastikan biaya jabatan IDR 470K/bulan dimasukkan dalam perhitungan PPh21.",
        "potential_saving": "IDR 23.5K/bulan (0.05 * IDR 470K * 5% tax rate)"
      }
    ],
    "benefit_optimization": [
      {
        "title": "Pertimbangkan Dana Pensiun Tambahan",
        "description": "Program pensiun JP (2%) sudah tercakup. Pertimbangkan iuran dana pensiun lanjutan (max 5% penghasilan, fully deductible).",
        "potential_tax_saving": "IDR 25K-75K/bulan"
      }
    ]
  },
  "export": {
    "pdf_url": "cekwajar.id/payslip/audit_report_xyz123.pdf",
    "invoice_format": "Laporan Audit Payslip - Budi Santoso - April 2026",
    "shareable": true,
    "expiry_days": 30
  }
}
```

#### 2.4.2 Bahasa Indonesia Audit Report (Free Tier Display)

```
═══════════════════════════════════════════════════════════════
              LAPORAN AUDIT PAYSLIP - CEKWAJAR.ID
═══════════════════════════════════════════════════════════════

Nama Karyawan:    Budi Santoso
Posisi:           Software Engineer
Periode:          April 2026
Status Pajak:     K/1 (Kawin, 1 anak)

───────────────────────────────────────────────────────────────
KOMPONEN GAJI
───────────────────────────────────────────────────────────────

Penghasilan:
  Gaji Pokok                      IDR 8,000,000
  Tunjangan Makan (tunai)         IDR   500,000
  Tunjangan Transportasi (natura) IDR   600,000
  Tunjangan Keluarga              IDR   300,000
  ──────────────────────────────────────────────
  TOTAL PENGHASILAN BRUTO         IDR 9,400,000

Potongan:
  PPh 21 (Pajak Penghasilan)      IDR   189,000
  BPJS Ketenagakerjaan (JHT+JP)   IDR   456,000
  BPJS Kesehatan                  IDR    94,000
  ──────────────────────────────────────────────
  TOTAL POTONGAN                  IDR   739,000

  GAJI YANG DITERIMA (NETTO)      IDR 8,661,000

───────────────────────────────────────────────────────────────
VERIFIKASI PAJAK PPh 21
───────────────────────────────────────────────────────────────

Gross Salary:                       IDR 9,400,000
PTKP Status K/1:                    IDR 5,125,000/bulan
Biaya Jabatan (5% max 500K):        IDR   470,000
Penghasilan Kena Pajak:             IDR 3,805,000

Perhitungan PPh 21:
  3,805,000 x 5% = IDR 190,250

Potongan Aktual:                    IDR   189,000
Selisih:                            IDR    (1,250)  ✓ Rounding normal

Status Pajak: ✓ SESUAI

───────────────────────────────────────────────────────────────
KEPATUHAN REGULASI
───────────────────────────────────────────────────────────────

🔴 PENTING - Temuan Audit:

[⚠️ WARNING] Biaya Jabatan Tidak Dikurangkan (Potensi Pengurangan Pajak)
  Sistem mendeteksi bahwa biaya jabatan IDR 470,000/bulan tidak
  dikurangkan dari penghasilan bruto dalam perhitungan PPh 21.

  Menurut UU 36/2008 Pasal 6(1)g, setiap karyawan berhak mengurangi
  penghasilan dengan biaya jabatan (5% atau max IDR 500,000/bulan).

  Akibat: PPh 21 yang dipotong kemungkinan IDR 23.5K lebih tinggi
  dari seharusnya.

  REKOMENDASI: Hubungi HR/Bagian Gaji dan minta agar biaya jabatan
  dimasukkan dalam perhitungan pajak. Bisa dilakukan penyesuaian
  saat SPT tahunan (diambil kembali).

[ℹ️ INFO] Tunjangan Makan & Transportasi - Verifikasi Natura
  Terdeteksi:
  - Tunjangan Makan: IDR 500,000 (tunai) → Kena Pajak ✓
  - Tunjangan Transportasi: IDR 600,000 (natura) → Bebas Pajak (jika benar)

  Jika transportasi adalah uang tunai (bukan shuttle/mobil perusahaan),
  maka IDR 600,000 juga harus kena pajak dan akan menambah PPh 21.

  VERIFIKASI: Pastikan dengan HR bahwa transportasi adalah fasilitas
  (shuttle, kendaraan pribadi, dll), bukan uang tuai.

✓ UMR COMPLIANCE (Kepatuhan UMR)
  Gaji Anda: IDR 8,661,000 (netto)
  UMR Jakarta 2026: IDR 4,820,000
  Status: ✓ COMPLIANT (Anda menerima 1.80x UMR)

✓ BPJS KETENAGAKERJAAN (JHT + JP)
  JHT (Jaminan Hari Tua) 3.7%: IDR 296,000
  JP (Jaminan Pensiun) 2.0%: IDR 160,000
  Total: IDR 456,000 ✓ Sudah dipotong

✓ BPJS KESEHATAN
  1% dari Gaji: IDR 94,000 ✓ Sudah dipotong

───────────────────────────────────────────────────────────────
SARAN OPTIMASI PAJAK
───────────────────────────────────────────────────────────────

1. Konfirmasi Biaya Jabatan
   Potensi Penghematan: IDR 23.5K/bulan x 12 = IDR 282,000/tahun

   Biaya jabatan yang TIDAK dikurangkan: IDR 470,000/bulan
   Jika dikurangkan, PPh 21 akan turun dari IDR 189K ke IDR 165.5K

   Action: Email ke bagian HR untuk revisi perhitungan mulai bulan depan.

2. Verifikasi Status Pajak
   Status saat ini: K/1
   Jika Anda punya 2+ anak, bisa naik ke K/3
   Potensi penghematan: +IDR 3M x 5% = IDR 150K/tahun

3. Dana Pensiun Tambahan
   Program JP sudah mandatory (2%). Pertimbangkan iuran dana pensiun
   tambahan (BNP, Prudensial, dll) hingga 5% - fully tax-deductible.
   Potensi penghematan: IDR 30K-75K/bulan

───────────────────────────────────────────────────────────────
RINGKASAN KESEHATAN FINANSIAL
───────────────────────────────────────────────────────────────

Gaji Bruto:                IDR 9,400,000
Effective Tax Rate:        2.01% (IDR 189,000 / IDR 9,400,000)
Effective Tax + BPJS:      7.85% (IDR 739,000 / IDR 9,400,000)

Gaji Netto:                IDR 8,661,000 (92.15% take-home)

Kesimpulan: Gaji Anda relatif sehat dari sisi kepatuhan. Dengan
perbaikan biaya jabatan, potensi penghematan pajak IDR 282K/tahun.

───────────────────────────────────────────────────────────────
Laporan ini dihasilkan oleh cekwajar.id pada 7 April 2026
Konsultasikan dengan tax consultant untuk situasi kompleks
═══════════════════════════════════════════════════════════════
```

---

## WAJAR TANAH: Land Price Benchmark

### 3.1 Input Fields

```json
{
  "location": {
    "province": "string (required)",
    "city": "string (required)",
    "district": "string (required)",
    "address": "string (optional, for street-level refinement)",
    "latitude": "number (optional, 6 decimals)",
    "longitude": "number (optional, 6 decimals)"
  },
  "land_specification": {
    "size_sqm": "number (required) - land area in square meters",
    "land_type": "enum (Residential, Commercial, Industrial, Agricultural)",
    "zone_type": "enum (Urban, Suburban, Rural)",
    "land_status": "enum (SHM/Freehold, HGB/Lease, HGU/Agricultural, Wakaf)"
  },
  "comparable_market": {
    "recently_sold": "boolean - did user see recent sale in area?",
    "recent_sale_price_per_sqm": "number (optional, for validation)",
    "listing_price_per_sqm": "number (optional, for validation)"
  }
}
```

### 3.2 Data Triangulation Formula

**Three-Source Weighted Blend:**

```
BENCHMARK_PRICE = (w₁ × P_NJOP) + (w₂ × P_Listing) + (w₃ × P_Crowd)

Where:
  P_NJOP = NJOP-derived market price estimate
  P_Listing = Real estate listing price (Properti.com, OLX, etc.)
  P_Crowd = Crowdsourced transaction price
  w₁ + w₂ + w₃ = 1
```

**Default Weights (Optimized for Indonesian Market):**

| Source | Base Weight | Rationale |
|--------|-------------|-----------|
| NJOP (BHUMI) | 35% | Govt anchor (stable but outdated) |
| Listing Prices | 40% | Market signal (most recent) |
| Crowdsourced | 25% | Actual transactions (honest prices) |

**Weight Adjustment Logic:**

```
IF data_source_available[NJOP] AND age(NJOP) < 2_years:
  w_njop *= 1.2 (boost weight if recent)
ELSE:
  w_njop *= 0.7 (reduce weight if >2 years old)

IF data_source_available[Listing] AND count(listings) > 5:
  w_listing *= 1.15 (boost if multiple comparables)
ELSE IF count(listings) < 2:
  w_listing *= 0.6 (reduce if insufficient listings)

IF data_source_available[Crowdsourced] AND count(crowd_data) > 10:
  w_crowd *= 1.1 (boost if robust crowd data)
ELSE IF count(crowd_data) < 3:
  w_crowd *= 0.5 (reduce if sparse)

# Re-normalize weights to sum to 1
w_njop_final = w_njop / (w_njop + w_listing + w_crowd)
w_listing_final = w_listing / (w_njop + w_listing + w_crowd)
w_crowd_final = w_crowd / (w_njop + w_listing + w_crowd)
```

### 3.3 NJOP Zone Integration (Bhumi Data)

**Nilai Jual Objek Pajak (NJOP) - Property Tax Assessment Base**

Source: ATR/BPN (Bhumi digital system), Direktorat Jenderal Pajak

```
Step 1: Identify NJOP Zone
  Input: address → Lookup NJOP zone database
  Database: Bhumi API (ATR/BPN)
  Field: zona_penilaian, kode_zona

Step 2: Retrieve NJOP/sqm
  NJOP_current = zone[kode_zona].njop_sqm (2026 value)
  Example: Zone A1 Jakarta Pusat = IDR 40,000,000/sqm
           Zone B2 Bandung Perumahan = IDR 1,200,000/sqm

Step 3: Estimate Market Price from NJOP
  # Market price ≠ NJOP; use empirical conversion factors

  region_gap = {
    "Jakarta": {"min": 3.0, "max": 8.0, "avg": 5.2},
    "Surabaya": {"min": 2.0, "max": 5.0, "avg": 3.2},
    "Bandung": {"min": 2.0, "max": 4.0, "avg": 2.8},
    "Medan": {"min": 1.5, "max": 3.0, "avg": 2.1},
    "Yogyakarta": {"min": 1.2, "max": 2.5, "avg": 1.8},
    "Default": {"min": 1.5, "max": 3.5, "avg": 2.3}
  }

  # Gap = Market Price / NJOP ratio (empirically observed)
  # Larger cities have larger gaps (higher market premiums)

  P_NJOP = NJOP_per_sqm * (1 + region_gap[city].avg) * land_size_sqm
```

**Example NJOP Conversion:**
```
City: Jakarta Pusat (Zone A1)
Land size: 500 sqm
NJOP/sqm: IDR 40,000,000

Market estimate from NJOP:
  Gap factor: 5.2 (Jakarta avg)
  Market estimate = 40,000,000 * (1 + 5.2) × 500 = IDR 1,240,000,000
  (vs NJOP value: 40,000,000 × 500 = IDR 20,000,000)
```

### 3.4 Listing Price Scraper Integration

**Data Sources:**
- Properti.com (largest Indonesian platform)
- OLX (classifieds, semi-curated)
- Bank REO (foreclosed properties - usually discounted)
- Developer direct (new projects)

**Scraping Logic:**

```
Step 1: Search for comparable properties
  Criteria:
    - Location: Same district/kelurahan (±5km radius)
    - Type: Matching land_type
    - Size: Within 50-150% of user's land size
    - Status: Same ownership status (SHM, HGB, etc.)

Step 2: Fetch listing prices
  For each listing:
    - Price per sqm = listing_price / land_size
    - Price currency: Convert to IDR if needed
    - Freshness: Days since listing posted
    - Vendor credibility: Score 0-100 (based on seller reviews)

Step 3: Filter & Aggregate
  Remove outliers (>3σ from median)
  Weight by recency: (Days since posting)^(-0.5)
  Weight by vendor credibility: credibility_score / 100

  P_Listing = weighted_median(price_per_sqm) × land_size_sqm
```

**Example:**
```
User queries: 400 sqm residential land in Bandung Dago

Comparable listings found:
  1. IDR 2.0B (500 sqm) → IDR 4.0M/sqm, 15 days old, vendor 92/100
  2. IDR 1.8B (450 sqm) → IDR 4.0M/sqm, 8 days old, vendor 88/100
  3. IDR 2.2B (380 sqm) → IDR 5.8M/sqm, 45 days old, vendor 70/100 [OUTLIER]
  4. IDR 1.6B (420 sqm) → IDR 3.8M/sqm, 25 days old, vendor 85/100

Filtered (remove #3):
  Weighted avg price/sqm = (4.0×w1 + 4.0×w2 + 3.8×w3) / (w1+w2+w3)
                         ≈ IDR 4.0M/sqm

  P_Listing = 4.0M × 400 sqm = IDR 1.6B
```

### 3.5 Crowdsourced Transaction Data

**Data Collection:**

```
Users submit actual purchase/sale data:
  - Property address
  - Purchase price
  - Land size
  - Date of transaction
  - Land status proof (scan SHM/HGB)
  - Transaction type: Beli-Jual, Tukar, Waris, Hadiah
```

**Validation:**

```
Rejection rules:
  - Price seems unrealistic (>5σ deviation)
  - Document verification fails
  - Duplicate submissions from same user
  - Suspiciously low prices (likely waris/family deal)

Acceptance rules:
  - Price within 1-4σ of median
  - Document verified (SHM/HGB scans)
  - User reputation score > 0.6
  - Transaction type is commercial (Beli-Jual)
```

**Crowdsourced Aggregation:**

```
P_Crowd = weighted_median(crowdsourced_price_per_sqm) × land_size_sqm

where weight = (1 / days_old) × credibility_score
```

### 3.6 Composite Verdict Thresholds

**Verdict Logic:**

```
market_price_estimate = (w_njop × P_NJOP) + (w_listing × P_Listing) + (w_crowd × P_Crowd)

IF user_asking_price > market_price_estimate × 1.30:
  verdict = "Terlalu Mahal" (Too Expensive)
  gap_percentage = ((user_price - market_price) / market_price) × 100

ELSE IF user_asking_price BETWEEN market_price × 0.85 AND market_price × 1.15:
  verdict = "Wajar" (Fair Market Price)
  gap_percentage = ((user_price - market_price) / market_price) × 100

ELSE IF user_asking_price < market_price × 0.85:
  verdict = "Murah" (Cheap/Bargain)
  gap_percentage = ((user_price - market_price) / market_price) × 100
```

**Threshold Definitions:**

| Gap | Verdict | Interpretation |
|-----|---------|-----------------|
| >+30% | Terlalu Mahal | Significantly overpriced |
| +15% to +30% | Agak Mahal | Moderately overpriced |
| -15% to +15% | Wajar | Fair market range |
| -30% to -15% | Agak Murah | Moderately underpriced |
| <-30% | Murah | Significantly underpriced (check legality) |

### 3.7 Confidence Score Calculation

```
confidence = 100 * (sample_factor × recency_factor × variance_factor)

sample_factor = min((n_njop + n_listing + n_crowd) / 15, 1.0)
  - Grows to 1.0 with 15+ data points

recency_factor = 0.8^(months_since_data/12)
  - Decays with age (half-life 12 months)

variance_factor = 1 / (1 + cv²)
  where cv = std_dev / mean (coefficient of variation)
  - Penalizes high variance across sources
```

**Example:**
```
Jakarta Pusat residential, 500 sqm

Data available:
  - NJOP: 1 zone (recent, but all addresses in zone use same value)
  - Listings: 12 comparables (3 weeks old)
  - Crowdsourced: 8 transactions (2-6 months old)

Sample factor: (1+12+8)/15 = 1.4 → capped to 1.0
Recency factor: 0.8^(1.5/12) ≈ 0.99
Variance factor: 0.95 (relatively consistent across sources)

Confidence = 100 × 1.0 × 0.99 × 0.95 = 94.1%
→ HIGH CONFIDENCE
```

---

## WAJAR KABUR: Abroad Salary & Life Quality Comparison

### 4.1 PPP Adjustment Formula

**Why Raw Exchange Rate Fails:**

```
Exchange Rate Method (INCORRECT):

  Salary SGD 5,000 × SGD/IDR 10,500 = IDR 52,500,000

  Problem: Ignore costs of living differences
  - Housing Singapore IDR 50M/month typical
  - Housing Jakarta IDR 15M/month typical

  Real purchasing power much lower in Singapore despite higher salary
```

**Purchasing Power Parity (PPP) Correct Approach:**

```
PPP_adjusted_salary_IDR = salary_foreign × ppp_conversion_factor

where:
  ppp_conversion_factor = (cost_of_living_foreign / cost_of_living_IDN) × (forex_rate)

Simplified formula:
  salary_local_equivalent = salary_foreign × (cost_index_foreign / cost_index_IDN)

Example:
  Salary Singapore: SGD 5,000
  Cost index Singapore: 150 (30% higher than Jakarta baseline=100)
  Cost index Jakarta: 100 (baseline)
  Exchange rate: 1 SGD = 10,500 IDR

  PPP-adjusted IDR = SGD 5,000 × (150/100) × 10,500 = IDR 78,750,000

  Interpretation: SGD 5,000 in Singapore = IDR 78.75M purchasing power
                  vs IDR 52.5M raw conversion
```

### 4.2 Country-Specific Data

**Target Comparison Countries (8 key destinations for WNI)**

#### Singapore

```json
{
  "country": "Singapore",
  "exchange_rate": "1 SGD = 10,500 IDR (approximate, real-time via forex API)",
  "cost_of_living_index": 150,
  "cost_components": {
    "housing_monthly": "SGD 2,000-3,500 (1-bedroom downtown)",
    "groceries_monthly": "SGD 400-600",
    "transport_monthly": "SGD 100-150 (public transport)",
    "dining_monthly": "SGD 300-600"
  },
  "income_tax": {
    "rate": "Progressive 0-22%",
    "brackets": [
      {"income_sgd": "0-80,000", "rate": 0},
      {"income_sgd": "80,001-280,000", "rate": "2-7%"},
      {"income_sgd": "280,001-500,000", "rate": "8-11.5%"},
      {"income_sgd": "500,000+", "rate": "15-22%"}
    ],
    "source": "Inland Revenue Authority of Singapore (IRAS)",
    "net_effective_rate": "~8-12% for typical expat (SGD 5-8K/month)"
  },
  "visa_stability": {
    "work_visa": "Employment Pass (EP) or S Pass",
    "duration": "1-2 years, renewable",
    "probability_renewal": 0.85,
    "risk_factors": ["Salary requirements increasing", "Local hiring preference"]
  },
  "quality_of_life_score": 92,
  "factors": {
    "healthcare": 95,
    "infrastructure": 98,
    "safety": 96,
    "education": 90,
    "career_growth": 88
  }
}
```

#### Australia

```json
{
  "country": "Australia",
  "exchange_rate": "1 AUD = 9,850 IDR",
  "cost_of_living_index": 135,
  "income_tax": {
    "rate": "Progressive 0-45%",
    "brackets": [
      {"income_aud": "0-18,200", "rate": 0},
      {"income_aud": "18,201-45,000", "rate": "19%"},
      {"income_aud": "45,001-120,000", "rate": "32.5%"},
      {"income_aud": "120,001-180,000", "rate": "37%"},
      {"income_aud": "180,000+", "rate": "45%"}
    ],
    "plus_medicare_levy": 2,
    "source": "Australian Taxation Office (ATO)"
  },
  "visa_stability": {
    "work_visa": "Skilled Migration (subclass 189/190) or Temporary Skill Shortage (subclass 482)",
    "duration": "4-5 years, pathway to permanent residency",
    "probability_renewal": 0.72,
    "risk_factors": ["Skills list changes", "Points system competition"]
  },
  "quality_of_life_score": 88
}
```

#### Japan

```json
{
  "country": "Japan",
  "exchange_rate": "1 JPY = 115 IDR",
  "cost_of_living_index": 110,
  "income_tax": {
    "rate": "Progressive 5-45%",
    "brackets": [
      {"income_jpy": "0-1,950,000", "rate": "5%"},
      {"income_jpy": "1,950,001-3,300,000", "rate": "10%"},
      {"income_jpy": "3,300,001-6,950,000", "rate": "20%"},
      {"income_jpy": "6,950,001-9,000,000", "rate": "23%"},
      {"income_jpy": "9,000,001+", "rate": "33-45%"}
    ],
    "source": "National Tax Agency (NTA)",
    "local_residence_tax": "6-10% additional"
  },
  "visa_stability": {
    "work_visa": "Intra-company transfer / Skilled worker",
    "duration": "1-5 years, renewable",
    "probability_renewal": 0.80,
    "risk_factors": ["Language requirement increasing", "Remote work visa restrictions"]
  },
  "quality_of_life_score": 89
}
```

#### Malaysia

```json
{
  "country": "Malaysia",
  "exchange_rate": "1 MYR = 3,650 IDR",
  "cost_of_living_index": 75,
  "income_tax": {
    "rate": "Progressive 0-30%",
    "brackets": [
      {"income_myr": "0-5,000", "rate": 0},
      {"income_myr": "5,001-20,000", "rate": "3-8%"},
      {"income_myr": "20,001-35,000", "rate": "11-13%"},
      {"income_myr": "35,001-80,000", "rate": "16-22%"},
      {"income_myr": "80,000+", "rate": "24-30%"}
    ],
    "source": "Inland Revenue Board (IRB)",
    "expatriate_incentive": "Partial exemption possible under certain conditions"
  },
  "visa_stability": {
    "work_visa": "Employment Pass or Professional Visit Pass",
    "duration": "1-2 years",
    "probability_renewal": 0.75,
    "risk_factors": ["Bumiputera hiring preference", "Salary minimum threshold"]
  },
  "quality_of_life_score": 81,
  "advantage": "Low cost of living, familiar culture, short flight home"
}
```

#### UAE (United Arab Emirates)

```json
{
  "country": "UAE",
  "exchange_rate": "1 AED = 2,750 IDR",
  "cost_of_living_index": 105,
  "income_tax": {
    "rate": "0% (No personal income tax)",
    "source": "Tax incentive jurisdiction",
    "caveat": "Corporate tax 15% applies to some sectors (2023 reform)"
  },
  "visa_stability": {
    "work_visa": "Employment Visa / Golden Visa",
    "duration": "2-3 years",
    "probability_renewal": 0.85,
    "risk_factors": ["Job market fluctuation (oil prices)", "Labor law enforcement"]
  },
  "quality_of_life_score": 83,
  "advantage": "Zero income tax, high wages, expat-friendly"
}
```

#### Netherlands

```json
{
  "country": "Netherlands",
  "exchange_rate": "1 EUR = 15,200 IDR",
  "cost_of_living_index": 125,
  "income_tax": {
    "rate": "Progressive 0-49.5%",
    "brackets": [
      {"income_eur": "0-22,000", "rate": "19%"},
      {"income_eur": "22,001-68,507", "rate": "37%"},
      {"income_eur": "68,507-193,000", "rate": "49.5%"},
      {"income_eur": "193,000+", "rate": "49.5%"}
    ],
    "source": "Belastingdienst (Dutch Tax Authority)",
    "30_percent_ruling": "Non-residents may get 30% tax benefit on gross salary (employer grants)",
    "effective_rate_with_ruling": "~22-25% (significant benefit)"
  },
  "visa_stability": {
    "work_visa": "Skilled Migrant Visa or Intra-company transfer",
    "duration": "2-5 years",
    "probability_renewal": 0.80
  },
  "quality_of_life_score": 91
}
```

#### Germany

```json
{
  "country": "Germany",
  "exchange_rate": "1 EUR = 15,200 IDR",
  "cost_of_living_index": 115,
  "income_tax": {
    "rate": "Progressive 0-42%",
    "brackets": [
      {"income_eur": "0-11,600", "rate": 0},
      {"income_eur": "11,601-62,810", "rate": "14-42%"},
      {"income_eur": "62,810+", "rate": "42%"}
    ],
    "source": "Bundeszentralamt für Steuern (BZSt)",
    "church_tax": "+8-9% if member",
    "solidarity_tax": "+5.5% on income tax"
  },
  "visa_stability": {
    "work_visa": "Blue Card EU or Employment Visa",
    "duration": "2-4 years",
    "probability_renewal": 0.85,
    "pathway": "Path to permanent residency / citizenship"
  },
  "quality_of_life_score": 90
}
```

#### South Korea

```json
{
  "country": "South Korea",
  "exchange_rate": "1 KRW = 0.0115 IDR",
  "cost_of_living_index": 105,
  "income_tax": {
    "rate": "Progressive 6-45%",
    "brackets": [
      {"income_krw": "0-12,000,000", "rate": "6%"},
      {"income_krw": "12M-46,000,000", "rate": "15%"},
      {"income_krw": "46M-88,000,000", "rate": "24%"},
      {"income_krw": "88M-150,000,000", "rate": "35%"},
      {"income_krw": "150M+", "rate": "38-45%"}
    ],
    "source": "National Tax Service (NTS)"
  },
  "visa_stability": {
    "work_visa": "Employment Visa (E-1) / Intra-company transfer",
    "duration": "1-2 years",
    "probability_renewal": 0.75,
    "risk_factors": ["Language barrier", "Intense work culture"]
  },
  "quality_of_life_score": 86
}
```

### 4.3 Life Quality Score Formula

```
LIFE_QUALITY_SCORE = (w_ppp × ΔPurchasing_Power)
                    + (w_qol × Quality_of_Life)
                    + (w_career × Career_Growth)
                    + (w_culture × Cultural_Proximity)

where:

ΔPurchasing_Power = (ppp_salary_abroad / ppp_salary_IDN) - 1
  Captures: ability to save, lifestyle affordability
  Range: -0.5 to +3.0 (normalized to 0-100 scale)

Quality_of_Life = (healthcare + infrastructure + safety + education) / 4
  Source: Numbeo, Economist Intelligence Unit
  Range: 0-100

Career_Growth = industry_growth_rate × career_advancement_index
  Example: Tech in Singapore = 0.95, Healthcare in Germany = 0.88
  Range: 0-100

Cultural_Proximity = proximity_score(Indonesia_culture, destination_culture)
  Measured: Food accessibility, religious accommodation, expat community
  Example: Malaysia = 0.90, Netherlands = 0.60
  Range: 0-100

w_ppp = 0.35 (financial stability most important for expats)
w_qol = 0.30 (health/safety matter)
w_career = 0.20 (growth opportunities)
w_culture = 0.15 (comfort in environment)
```

**Example Calculation:**

```
User: Indonesian, Software Engineer, earned IDR 12M/month in Jakarta
       Considering job offer in Singapore (SGD 7,000/month)

Step 1: Purchasing Power Delta
  PPP Singapore (SGD 7k): SGD 7,000 × (150/100) × 10,500 = IDR 110,250,000
  PPP Jakarta (IDR 12M): IDR 12,000,000 (baseline)
  ΔPurchasing_Power = (110.25M / 12M) - 1 = +8.19 → Normalized: 92/100

Step 2: Quality of Life
  Singapore score: 92/100 (excellent healthcare, safety, infrastructure)

Step 3: Career Growth
  Tech industry Singapore: 0.95, → 95/100

Step 4: Cultural Proximity
  Singapore: 0.70 (Muslim-friendly, but English-centric) → 70/100

Life Quality Score = (0.35 × 92) + (0.30 × 92) + (0.20 × 95) + (0.15 × 70)
                   = 32.2 + 27.6 + 19.0 + 10.5
                   = 89.3 / 100

Interpretation: "Excellent move. 9.2x purchasing power increase,
                strong career growth, and high quality of life."
```

---

## WAJAR HIDUP: Cost of Living by City

### 5.1 Cost-of-Living Basket (12-Item Basket)

**Standard Basket for Indonesia (Monthly):**

```json
{
  "categories": [
    {
      "category": "Housing (30% of basket)",
      "item": "1-bedroom apartment rental (unfurnished)",
      "unit": "IDR/month",
      "notes": "City center location, including utilities"
    },
    {
      "category": "Food & Groceries (20% of basket)",
      "item": "Basic grocery items (eggs, rice, vegetables, chicken)",
      "unit": "IDR/week",
      "items": ["Telur (eggs)", "Beras (rice, 5kg)", "Ayam (chicken, 1kg)"]
    },
    {
      "category": "Dining Out (10% of basket)",
      "item": "Meal at mid-range restaurant",
      "unit": "IDR/meal",
      "notes": "Nasi goreng, mie ayam at typical warung"
    },
    {
      "category": "Transportation (15% of basket)",
      "item": "Public transport (monthly pass) or motorcycle fuel",
      "unit": "IDR/month",
      "variants": ["City bus monthly", "Ojek/Grab estimate", "Motorcycle fuel"]
    },
    {
      "category": "Utilities (8% of basket)",
      "item": "Electricity, water, internet for 1BR apartment",
      "unit": "IDR/month",
      "breakdown": {"electricity": "25-40 kWh", "water": "standard", "internet": "50 Mbps"}
    },
    {
      "category": "Communication (3% of basket)",
      "item": "Mobile phone plan (prepaid or postpaid)",
      "unit": "IDR/month",
      "notes": "Unlimited calls + data 10GB typical"
    },
    {
      "category": "Clothing (4% of basket)",
      "item": "Casual clothing (average cost per piece)",
      "unit": "IDR/item",
      "notes": "T-shirt, jeans at mid-market retail"
    },
    {
      "category": "Personal Care (3% of basket)",
      "item": "Haircut + basic toiletries",
      "unit": "IDR/month",
      "notes": "Haircut at typical barber + soap, shampoo"
    },
    {
      "category": "Recreation (4% of basket)",
      "item": "Entertainment (cinema, gym, activities)",
      "unit": "IDR/month",
      "notes": "Occasional cinema visit, casual entertainment"
    },
    {
      "category": "Healthcare (2% of basket)",
      "item": "Doctor visit + basic medications",
      "unit": "IDR/month",
      "notes": "Preventive care, non-emergency visits"
    },
    {
      "category": "Education (1% of basket)",
      "item": "Online courses / learning materials",
      "unit": "IDR/month",
      "notes": "Self-improvement, skill development"
    },
    {
      "category": "Miscellaneous (2% of basket)",
      "item": "Household items, personal hygiene",
      "unit": "IDR/month",
      "notes": "Cleaning supplies, miscellaneous"
    }
  ]
}
```

### 5.2 Numbeo API Integration + Local Gap-Filling

**Data Pipeline:**

```
Step 1: Query Numbeo API
  - Request cost-of-living data for target city
  - Numbeo categories: (Housing, Groceries, Dining, Transportation, etc.)
  - Update frequency: Real-time crowd data

Step 2: Map Numbeo ↔ Our 12-Item Basket
  Numbeo cat               → Our Item
  "Apartment 1BR Center"   → Housing
  "Milk (1L)"              → Food & Groceries
  "Meal Restaurant"        → Dining Out
  "Public Transport"       → Transportation
  etc.

Step 3: Local Gap-Filling (Supplementary Sources)
  - If Numbeo data sparse: Cross-check with
    * OLX rental listings (housing)
    * Tokopedia / Shopee prices (groceries)
    * Google Maps restaurant reviews (dining)
    * BPS price surveys (official data)

Step 4: Composite Index Calculation
  index_city = weighted_average(numbeo_data, local_data)

  Where:
    numbeo_weight = 0.60 (crowd-sourced, real-time)
    local_weight = 0.40 (official + curated sources)
```

**Example: Jakarta vs Bandung Comparison**

```
Jakarta:
  Housing:           IDR 8,000,000 (1BR center)
  Food & Groceries:  IDR 2,800,000 (monthly)
  Dining Out:        IDR 60,000 (per meal)
  Transport:         IDR 800,000 (monthly pass)
  Utilities:         IDR 1,200,000
  ──────────────────────────────────
  TOTAL MONTHLY:     IDR 12,860,000
  Index:             100 (baseline)

Bandung:
  Housing:           IDR 3,500,000 (1BR center)
  Food & Groceries:  IDR 2,000,000
  Dining Out:        IDR 35,000
  Transport:         IDR 400,000
  Utilities:         IDR 700,000
  ──────────────────────────────────
  TOTAL MONTHLY:     IDR 6,600,000
  Index:             51.3 (vs Jakarta)

Gap: Jakarta costs 1.95x more than Bandung
```

### 5.3 Lifestyle Tier Definitions

**Four Tiers (matching Indonesian income segments):**

```
Tier 1: BUDGET (Mahasiswa / Fresh Graduate)
  Monthly: IDR 6-10 Million

  Housing: Studio / Room share (IDR 1.5-3M)
  Food: Cook at home (warung meals) (IDR 1.5-2M)
  Transport: Public transit (IDR 300-500K)
  Utilities: Basic internet only (IDR 400K)
  Entertainment: Minimal (IDR 200-300K)
  Philosophy: "Hemat but comfortable"

Tier 2: MODERATE (Mid-level Professional)
  Monthly: IDR 10-20 Million

  Housing: 1BR furnished apartment (IDR 4-6M)
  Food: Mix of home + dining out (IDR 2.5-3.5M)
  Transport: Motorcycle + occasional Grab (IDR 600K-1M)
  Utilities: Full utilities + streaming (IDR 1.2M)
  Entertainment: Cinema, gym, hobbies (IDR 1-2M)
  Philosophy: "Comfortable with modest luxuries"

Tier 3: NYAMAN (Comfortable / Upper-Middle Class)
  Monthly: IDR 20-40 Million

  Housing: 2BR / luxury 1BR, own place (IDR 8-15M)
  Food: Regular dining, quality restaurants (IDR 4-6M)
  Transport: Private vehicle + driver (IDR 2-3M)
  Utilities: Premium internet, AC, gadgets (IDR 2-3M)
  Entertainment: Frequent dining, travel, courses (IDR 3-5M)
  Philosophy: "Enjoy quality of life, not extravagant"

Tier 4: PREMIUM (High Earner / Executive)
  Monthly: IDR 40M+

  Housing: 3BR+ / premium location (IDR 15M+)
  Food: Fine dining, imported groceries (IDR 8M+)
  Transport: Multiple vehicles, occasional car rental (IDR 5M+)
  Utilities: Premium utilities, tech gadgets (IDR 3-5M+)
  Entertainment: International dining, luxury activities (IDR 10M+)
  Philosophy: "Luxury within reason, quality-focused"
```

### 5.4 City Comparison Output

```json
{
  "cities": [
    {
      "city": "Jakarta",
      "index": 100,
      "total_monthly_cost": 12860000,
      "tier_affordability": {
        "budget": "Tight",
        "moderate": "Comfortable",
        "nyaman": "Very Comfortable",
        "premium": "Extravagant"
      }
    },
    {
      "city": "Bandung",
      "index": 51.3,
      "total_monthly_cost": 6600000,
      "tier_affordability": {
        "budget": "Very Comfortable",
        "moderate": "Luxury",
        "nyaman": "Ultra-luxury",
        "premium": "Excessive"
      }
    },
    {
      "city": "Yogyakarta",
      "index": 44.8,
      "total_monthly_cost": 5760000,
      "tier_affordability": {
        "budget": "Luxury",
        "moderate": "Ultra-luxury",
        "nyaman": "Excessive",
        "premium": "Unnecessary"
      }
    }
  ],
  "recommendation": "For a Moderate tier lifestyle (IDR 15M budget), Jakarta costs 1.95x more than Bandung, equivalent to saving IDR 6.26M/month by relocating."
}
```

---

## CROSS-TOOL ARCHITECTURE: Freemium Gating & Backend Response Schema

### 6.1 Field-Level Gating Matrix

| Feature | Free Tier | Premium Tier | Implementation |
|---------|-----------|--------------|---|
| **WAJAR GAJI** | | | |
| Basic Verdict | ✓ | ✓ | `verdict.status` always included |
| P50 Benchmark | ✓ | ✓ | Required |
| P25/P75 | ✗ | ✓ | Gated: `benchmark.p25`, `benchmark.p75` |
| Confidence Score | ✓ (simplified) | ✓ (detailed) | Free: 0-100; Premium: adds breakdown |
| Trend (3mo/12mo) | ✗ | ✓ | Gated: `trend.change_3months` |
| City Breakdown | ✗ | ✓ | Gated: `benchmark_by_city[]` |
| Industry Breakdown | ✗ | ✓ | Gated: `benchmark_by_industry[]` |
| Negotiation Tips | ✗ | ✓ | Gated: `negotiation.suggested_talking_points` |
| Export PDF | Watermarked (5/month) | Full (unlimited) | Watermark in free PDF |
| **WAJAR SLIP** | | | |
| Basic Audit | ✓ | ✓ | Verdict + compliance check |
| PPh21 Calculation | ✓ | ✓ | Always calculated |
| BPJS Breakdown | ✓ | ✓ | Component-level detail |
| Tax Optimization | Limited (1 tip) | ✓ (3-5 tips) | Gated: `recommendations.tax_optimization[]` |
| Benefit Analysis | ✗ | ✓ | Gated: `recommendations.benefit_optimization[]` |
| SPT Projection | ✗ | ✓ | Annual tax estimate |
| **WAJAR TANAH** | | | |
| Verdict | ✓ | ✓ | Basic fair/cheap/expensive |
| Benchmark Price | ✓ | ✓ | Composite estimate |
| NJOP Data | ✗ | ✓ | Gated: `benchmark.njop_component` |
| Comparable Listings | Limited (3) | Full (10+) | Gated: count in response |
| Confidence Score | ✓ | ✓ | Both tiers |
| **WAJAR KABUR** | | | |
| Salary Comparison | ✓ | ✓ | PPP-adjusted |
| Country Data | Top 2 only | All 8 countries | Gated: `countries[]` |
| Tax Rates | ✓ | ✓ | Summary included |
| Life Quality Score | ✓ | ✓ | 0-100 scale |
| Career Growth Index | ✗ | ✓ | Gated |
| Visa Risk Analysis | ✗ | ✓ | Gated: `visa_stability.risk_factors` |
| **WAJAR HIDUP** | | | |
| City Index | ✓ | ✓ | Indexed to baseline |
| Total Cost | ✓ | ✓ | Monthly estimate |
| Category Breakdown | Limited (5) | Full (12 items) | Gated: `categories[]` detailed |
| Multi-City Comparison | Top 3 | Unlimited | Gated: number of cities |

### 6.2 Complete Backend JSON Response Schema

**Standard Error Handling (All Tools):**

```json
{
  "status": "success | error | partial",
  "requestId": "uuid-v4",
  "timestamp": "ISO-8601",

  "error": {
    "code": "string (ERROR_CODE)",
    "message": "User-facing message in Bahasa Indonesia",
    "details": "Technical details for debugging",
    "recoveryAction": "Suggested action (e.g., 'Try broader search')"
  },

  "data": {}
}
```

**Fallback Messages (Bahasa Indonesia):**

```json
{
  "error_insufficient_data": "Maaf, data terlalu sedikit untuk area ini. Coba kota/provinsi yang lebih besar.",
  "error_invalid_input": "Input tidak valid. Periksa kembali [field_name].",
  "error_network": "Koneksi internet terputus. Silakan coba lagi.",
  "error_authentication": "Autentikasi gagal. Silakan login kembali.",
  "error_premium_only": "Fitur ini hanya tersedia untuk pengguna premium. Upgrade sekarang.",
  "warn_low_confidence": "Data terbatas. Hasil ini adalah perkiraan kasar saja."
}
```

**Premium Validation Middleware:**

```typescript
// Pseudocode for response field gating
function applyFreemiumGating(responseObject, userTier: 'free' | 'premium') {
  if (userTier === 'free') {
    // Remove premium-only fields
    delete responseObject.benchmark.p25;
    delete responseObject.benchmark.p75;
    delete responseObject.trend;
    delete responseObject.negotiation;
    responseObject.exportFormats.pdf = null;
  }
  return responseObject;
}
```

---

## APPENDIX: Regulatory References

| Regulation | Reference | Application |
|-----------|-----------|---|
| **UU 13/2003** | Ketenagakerjaan (Employment) | UMR, contract terms, mandatory BPJS |
| **UU 36/2008** | Pajak Penghasilan | PPh21 calculation, PTKP, biaya jabatan |
| **UU 24/2011** | Badan Penyelenggara Jaminan Sosial | BPJS Ketenagakerjaan rates |
| **PP 111/2013** | BPJS Kesehatan | Health insurance contribution rates |
| **PP 34/2015** | Badan Penyelenggara Jaminan Sosial | Employment insurance caps |
| **PER-16/PJ/2016** | DJP Pajak Penghasilan | PPh21 calculation methodology |
| **UU 40/2004** | Sistem Jaminan Sosial Nasional | Social insurance framework |

---

**Document Version:** 1.0
**Last Updated:** April 7, 2026
**Status:** Production-Grade Specification
**Prepared For:** cekwajar.id Development Team

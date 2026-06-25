# req_11 — Testing Spec: cekwajar.id
**Document Type:** Testing Specification  
**Version:** 1.0  
**Scope:** OCR accuracy, integration tests, beta test framework

> **Note:** PPh21/BPJS unit tests are in `block_03_pph21_bpjs_engine.md`. This document covers the broader test suite.

---

## 8.2 OCR Accuracy Test Report Specification

### Purpose

Before Wajar Slip launches with OCR enabled, the OCR pipeline must be validated against a representative corpus of Indonesian payslip formats. This spec defines how to build the corpus, run the test, interpret results, and make the launch/no-launch decision.

---

### Corpus Requirements

**Minimum corpus size:** 200 payslip samples  
**Collection method:** Founder manually collects (own company, friends, WhatsApp groups, r/finansialku — with permission)  
**Privacy:** All samples must be anonymized before storage (redact name, NIK, company name)

**Corpus categories (4 types):**

| Category | Description | Target Sample Count | Why This Category |
|----------|-------------|--------------------|--------------------|
| Corp PDF | PDF exported from corporate payroll systems (Talenta, Mekari, SAP) | 60 | Most common in formal sector; clean text, high OCR confidence expected |
| SME PDF | PDF from small companies — often Word/Excel → PDF | 60 | Variable formatting, some inconsistency |
| ASN | Government employee slip (ASN format from BKN system) | 40 | Standardized format, different field names |
| Photo | Phone camera photo of printed payslip | 40 | Hardest case: blur, angle, lighting variation |
| **Total** | | **200** | |

---

### P0 Fields (Must Extract Correctly)

These fields drive the violation calculations. An OCR failure on any P0 field produces a wrong verdict.

| Field | Display Label | Format | Notes |
|-------|-------------|--------|-------|
| `gross_salary` | Gaji Bruto | Integer IDR | Most important — drives all calculations |
| `pph21` | PPh21 Dipotong | Integer IDR | V03/V04 detection |
| `jht_employee` | JHT Karyawan (2%) | Integer IDR | V01 detection |
| `jp_employee` | JP Karyawan (1%) | Integer IDR | V07 detection |
| `kesehatan_employee` | Kesehatan (1%) | Integer IDR | V05 detection |
| `take_home` | Gaji Diterima / Take Home | Integer IDR | Sanity check: gross - deductions ≈ take_home |

**P1 fields (should extract, not launch-blocking):**
- JKK employer portion
- JKM employer portion  
- Individual allowances (transport, meal, etc.)

---

### Test Protocol

**Step 1: Ground truth labeling**

For each payslip in corpus, manually record correct values for all P0 fields:

```python
# tests/ocr/corpus_labels.json format
{
  "samples": [
    {
      "id": "corp_pdf_001",
      "category": "Corp PDF",
      "source": "Talenta export",
      "ground_truth": {
        "gross_salary": 8500000,
        "pph21": 62500,
        "jht_employee": 170000,
        "jp_employee": 85000,
        "kesehatan_employee": 85000,
        "take_home": 8097500
      }
    }
  ]
}
```

**Step 2: Run OCR pipeline on all samples**

```python
# tests/ocr/run_accuracy_test.py

import json
import asyncio
from pathlib import Path
from typing import Literal

async def run_ocr_accuracy_test(
    corpus_dir: Path,
    labels_file: Path,
    ocr_source: Literal['google_vision', 'tesseract'] = 'google_vision'
) -> dict:
    
    with open(labels_file) as f:
        labels = json.load(f)['samples']
    
    results = []
    
    for sample in labels:
        image_path = corpus_dir / f"{sample['id']}.jpg"
        
        if ocr_source == 'google_vision':
            extracted = await extract_with_vision(image_path)
        else:
            extracted = await extract_with_tesseract(image_path)
        
        # Calculate field-level accuracy
        field_results = {}
        for field, true_value in sample['ground_truth'].items():
            extracted_value = extracted.get(field)
            
            if extracted_value is None:
                field_results[field] = {'status': 'MISSING', 'error_pct': None}
            else:
                error_pct = abs(extracted_value - true_value) / true_value * 100
                field_results[field] = {
                    'status': 'EXACT' if error_pct == 0 else ('CLOSE' if error_pct < 2 else 'WRONG'),
                    'error_pct': error_pct,
                    'extracted': extracted_value,
                    'true': true_value
                }
        
        results.append({
            'id': sample['id'],
            'category': sample['category'],
            'fields': field_results,
            'overall_confidence': extracted.get('confidence', 0)
        })
    
    return analyze_results(results)

def analyze_results(results: list) -> dict:
    """Compute per-category accuracy metrics."""
    categories = {}
    
    for r in results:
        cat = r['category']
        if cat not in categories:
            categories[cat] = {'total': 0, 'field_correct': {}}
        categories[cat]['total'] += 1
        
        for field, data in r['fields'].items():
            if field not in categories[cat]['field_correct']:
                categories[cat]['field_correct'][field] = 0
            if data['status'] in ('EXACT', 'CLOSE'):
                categories[cat]['field_correct'][field] += 1
    
    # Compute accuracy rates
    summary = {}
    for cat, data in categories.items():
        summary[cat] = {
            'n': data['total'],
            'accuracy': {
                field: correct / data['total']
                for field, correct in data['field_correct'].items()
            }
        }
    
    return summary
```

**Step 3: Generate accuracy report table**

```
OCR Accuracy Report — Google Vision — [Date]
══════════════════════════════════════════════════════════════════════
Category      │ n  │ gross_salary │ pph21  │ jht   │ jp    │ kesehatan │ take_home
──────────────┼────┼──────────────┼────────┼───────┼───────┼───────────┼──────────
Corp PDF      │ 60 │ 96.7%        │ 95.0%  │ 93.3% │ 91.7% │ 93.3%    │ 95.0%
SME PDF       │ 60 │ 88.3%        │ 85.0%  │ 83.3% │ 80.0% │ 81.7%    │ 86.7%
ASN           │ 40 │ 95.0%        │ 92.5%  │ 90.0% │ 87.5% │ 90.0%    │ 92.5%
Photo         │ 40 │ 75.0%        │ 70.0%  │ 67.5% │ 65.0% │ 67.5%    │ 72.5%
──────────────┼────┼──────────────┼────────┼───────┼───────┼───────────┼──────────
OVERALL       │200 │ 89.5%        │ 86.8%  │ 84.8% │ 82.0% │ 84.3%    │ 87.5%
══════════════════════════════════════════════════════════════════════
```

---

### Launch Decision Matrix

| Category | `gross_salary` Accuracy | Decision |
|----------|------------------------|---------|
| Corp PDF | ≥ 92% | GO |
| SME PDF | ≥ 85% | GO |
| ASN | ≥ 90% | GO |
| Photo | ≥ 75% | GO (with SOFT_CHECK routing) |
| Photo | < 75% | DISABLE photo upload; PDF only |
| Any category | < stated threshold | BLOCK OCR for that category |

**Kill condition:** If `gross_salary` accuracy for ANY category is below:
- Corp PDF < 92%: Disable OCR for PDFs entirely, ship manual-only
- Photo < 75%: Disable photo upload, accept PDF only
- Overall < 80%: Delay launch, investigate root cause

**Implementation of category routing:**

```typescript
function routeOCRByFileType(
  mimeType: string,
  ocrConfidence: number
): 'AUTO_ACCEPT' | 'SOFT_CHECK' | 'MANUAL_REQUIRED' {
  // PDF files: higher accuracy baseline
  if (mimeType === 'application/pdf') {
    if (ocrConfidence >= 0.92) return 'AUTO_ACCEPT';
    if (ocrConfidence >= 0.75) return 'SOFT_CHECK';
    return 'MANUAL_REQUIRED';
  }
  
  // Image files: lower thresholds (photo accuracy is lower)
  if (ocrConfidence >= 0.85) return 'AUTO_ACCEPT';
  if (ocrConfidence >= 0.70) return 'SOFT_CHECK';
  return 'MANUAL_REQUIRED';
}
```

---

### Ongoing Accuracy Monitoring

After launch, track OCR accuracy using user corrections:

```sql
-- Track when users edit OCR-extracted fields
CREATE TABLE ocr_field_corrections (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  audit_id UUID REFERENCES payslip_audits(id),
  field_name TEXT NOT NULL,
  ocr_value BIGINT,
  corrected_value BIGINT,
  correction_ratio NUMERIC,  -- abs(corrected - ocr) / corrected
  ocr_source TEXT,
  created_at TIMESTAMPTZ DEFAULT now()
);

-- Weekly accuracy from user corrections
SELECT
  ocr_source,
  field_name,
  COUNT(*) AS corrections,
  AVG(correction_ratio) AS avg_error,
  SUM(CASE WHEN correction_ratio < 0.02 THEN 1 ELSE 0 END)::float / COUNT(*) AS within_2pct
FROM ocr_field_corrections
WHERE created_at > now() - INTERVAL '7 days'
GROUP BY ocr_source, field_name;
```

---

## 8.3 Integration Test Checklist

### Wajar Slip — Happy Path

- [ ] **TC-01: Manual form submission, free user**
  - Input: Gross IDR 7,500,000, TK/0, Jakarta, Oct 2025, NPWP=true, all correct deductions
  - Expected: Verdict = SESUAI, 0 violations, no gate shown
  - Check: DB row inserted in `payslip_audits`

- [ ] **TC-02: Manual form submission, violation detected, free user**
  - Input: Gross IDR 7,500,000, TK/0, Jakarta, Oct 2025, PPh21 = IDR 0 (should be IDR 62,500)
  - Expected: Verdict = ADA_PELANGGARAN, violations show codes but not IDR amounts
  - Check: Gate modal appears when user clicks "Lihat detail"

- [ ] **TC-03: Manual form submission, violation detected, Basic user**
  - Input: Same as TC-02
  - Expected: Full IDR amounts shown in violation detail
  - Check: `is_paid_result = true` in DB

- [ ] **TC-04: V06 UMK violation**
  - Input: Gross IDR 3,000,000, City = Kota Bekasi (UMK 2026 = IDR 5,331,680)
  - Expected: V06 violation with severity = CRITICAL
  - Check: `violations` JSONB contains V06

- [ ] **TC-05: December true-up (month = 12)**
  - Input: Dec 2025, gross IDR 8,500,000, TK/0, correct TER deductions Jan-Nov
  - Expected: Progressive calculation used, not TER
  - Check: calculated_pph21 matches progressive method result

- [ ] **TC-06: No NPWP surcharge**
  - Input: has_npwp = false, gross IDR 7,500,000, TK/0
  - Expected: calculated_pph21 = TER_amount × 1.20
  - Check: 20% surcharge applied correctly

- [ ] **TC-07: OCR upload flow — soft check**
  - Input: Upload a photo with OCR confidence 0.81
  - Expected: Redirect to confirm fields screen, fields pre-filled
  - Check: `ocrSource = 'google_vision'`, confirm screen shows

- [ ] **TC-08: OCR quota exhausted — Tesseract fallback**
  - Setup: Set `ocr_quota_counter` to 951 for current month
  - Input: Upload any image
  - Expected: Tesseract.js used, not Google Vision
  - Check: `ocrSource = 'tesseract'` in response

- [ ] **TC-09: Anonymous session audit**
  - Input: No auth, session ID in cookie, manual form submission
  - Expected: Audit stored with `user_id = NULL`, session_id set
  - Check: Anon audit accessible for 2 hours, not after 7 days

- [ ] **TC-10: Rate limiting**
  - Input: 6th request from same IP within 1 hour
  - Expected: HTTP 429 response
  - Check: Response body contains `RATE_LIMIT_EXCEEDED` code

---

### Wajar Gaji — Happy Path

- [ ] **TC-11: Job title exact match**
  - Input: "HRD Officer", Kota Bekasi, 3-5 tahun
  - Expected: `matchType = 'EXACT'`, province P50 returned
  - Check: UMK also displayed

- [ ] **TC-12: Job title fuzzy match**
  - Input: "human resource officer" (not exact)
  - Expected: matchType = 'FUZZY', confirm dialog shown
  - Check: Similarity > 0.7 triggers auto-accept

- [ ] **TC-13: No data state**
  - Input: "Penambang Timah" + "Kota Denpasar" (no data combination)
  - Expected: `hasData = false`, "Belum ada data" shown
  - Check: UMK still displayed as reference

- [ ] **TC-14: Crowdsource submission accepted**
  - Input: Valid submission, first from this IP
  - Expected: `accepted = true`
  - Check: Row inserted in `salary_submissions`

- [ ] **TC-15: Crowdsource duplicate rejected**
  - Input: Same IP, same title+city within 24h
  - Expected: `isDuplicate = true`
  - Check: No duplicate row in DB

---

### Wajar Tanah — Happy Path

- [ ] **TC-16: Full property verdict flow**
  - Input: Pondok Gede, Bekasi, Rumah, 72m², IDR 850M
  - Expected: Verdict shown, P50 shown, P25/P75 gated for free user
  - Check: `verdictMessage` is not empty, KJPP disclaimer rendered

- [ ] **TC-17: "Belum ada data" state**
  - Input: Remote district with n < 5
  - Expected: `hasData = false` state shown with suggestion to try nearby
  - Check: No verdict card rendered

- [ ] **TC-18: Location drill-down flow**
  - Input: Select Jawa Barat → Kota Bekasi → districts load
  - Expected: District dropdown populated with correct kecamatan
  - Check: No race condition on rapid province/city changes

---

### Wajar Kabur — Happy Path

- [ ] **TC-19: Free tier — top 5 country**
  - Input: IDR 8,500,000, Singapore, free user
  - Expected: PPP result shown without gate
  - Check: World Bank data fetched (or cached)

- [ ] **TC-20: Free tier — non-top-5 country**
  - Input: IDR 8,500,000, Japan, free user
  - Expected: Gate shown for Japan result
  - Check: `isGated = true` in response

- [ ] **TC-21: World Bank API unavailable**
  - Setup: Mock World Bank API to return 503
  - Expected: Last cached PPP used with freshness warning
  - Check: `pppSourceYear` shown to user

---

### Wajar Hidup — Happy Path

- [ ] **TC-22: Same city error**
  - Input: fromCity = Jakarta, toCity = Jakarta
  - Expected: SAME_CITY_ERROR state
  - Check: Error message shown, not calculation

- [ ] **TC-23: Valid comparison**
  - Input: Jakarta → Surabaya, IDR 12M, Standar
  - Expected: `adjustmentRatio ≈ 0.785`, `requiredSalary ≈ IDR 9.4M`
  - Check: Verdict = LEBIH_MURAH

- [ ] **TC-24: Nyaman tier premium**
  - Input: Same as TC-23 but Nyaman tier
  - Expected: `adjustmentRatio` lower (more sensitive to cheaper city)
  - Check: `requiredSalary` lower than Standar calculation

---

### Payment Flow

- [ ] **TC-25: Basic subscription purchase**
  - Input: Login → click upgrade → select Basic → complete Midtrans Sandbox payment
  - Expected: subscription activated, user_profiles.subscription_tier = 'basic'
  - Check: `transactions` row with status = 'settlement', `subscriptions` row active

- [ ] **TC-26: Webhook idempotency**
  - Input: POST same webhook payload twice
  - Expected: Subscription activated once, second webhook returns 200 silently
  - Check: `is_webhook_processed = true` after first, no second activation

- [ ] **TC-27: Webhook with wrong signature**
  - Input: POST webhook with tampered signature
  - Expected: HTTP 401 response
  - Check: No subscription activation, error logged

- [ ] **TC-28: Subscription expiry downgrade**
  - Setup: Set `subscriptions.ends_at` to yesterday
  - Trigger: Run pg_cron `subscription-expiry-check` manually
  - Expected: `user_profiles.subscription_tier = 'free'`
  - Check: `subscriptions.status = 'expired'`

- [ ] **TC-29: Confirmation email sent**
  - Input: Complete TC-25
  - Expected: Email received at test email address with correct plan and amount
  - Check: Resend dashboard shows sent email

---

### 30-Day Payslip Deletion (UU PDP)

- [ ] **TC-30: File deletion after 30 days**
  - Setup: Create audit with `delete_at = now() - 1 day`, set `payslip_file_path`
  - Trigger: Run `purge-payslip-files` Edge Function manually
  - Expected: File removed from Supabase Storage
  - Check: `payslip_file_path = NULL` in DB; Storage shows file gone

- [ ] **TC-31: Audit record retained after file deletion**
  - Input: Same as TC-30
  - Expected: `payslip_audits` row still exists with all calculated fields
  - Check: User can still view their audit history (no IDR amounts lost)

- [ ] **TC-32: Anonymous audit deleted at 7 days**
  - Setup: Create anon audit with `created_at = now() - 8 days`
  - Trigger: Run `purge-anon-audits` pg_cron manually
  - Expected: Row deleted from `payslip_audits`
  - Check: SELECT returns no rows for that session_id

---

### Edge Cases

- [ ] **TC-33: Salary cap validation on BPJS JP**
  - Input: Gross IDR 20,000,000 (above JP cap of IDR 9,559,600)
  - Expected: JP calculated on capped salary (IDR 9,559,600 × 1% = IDR 95,596)
  - Check: No violation for correct JP amount at cap

- [ ] **TC-34: THR month calculation**
  - Input: Bonus month = current month (THR), gross includes THR component
  - Expected: Progressive method used for THR portion
  - Check: PPh21 on THR calculated separately from regular salary

- [ ] **TC-35: K/I/3 PTKP (highest bracket)**
  - Input: TK status = K/I/3, gross IDR 15,000,000
  - Expected: PTKP = IDR 126,000,000 annual (IDR 10,500,000/month)
  - Check: Net PKP = IDR 4,500,000 annual, TER applied correctly

- [ ] **TC-36: Property price sanity check**
  - Input: Asking price IDR 100,000 total, 100m² land (IDR 1,000/m²)
  - Expected: Outlier rejection or "Harga tidak valid" error
  - Check: API returns 400 with INVALID_PRICE code

---

## 8.4 Beta Test Framework

### Beta Program Parameters

| Parameter | Value |
|-----------|-------|
| Target beta users | 50–100 |
| Duration | 2 weeks before public launch |
| Access | Invite-only link, no paywall (all features unlocked) |
| Tools to test | Wajar Slip (primary), Wajar Gaji (secondary) |
| Recruitment | r/finansialku, WhatsApp HRD groups, LinkedIn |

---

### Beta User Profile Criteria

**Include:**
- Formal sector employees (karyawan tetap)
- Mix of Corp (using Talenta/Mekari) and SME (Excel-generated slip)
- Mix of Android photo upload vs PDF upload users
- At least 10 ASN (government employees)
- At least 5 users with NPWP issues (late registration or missing)

**Exclude:**
- Freelancers (Pasal 21 final — different calculation)
- Business owners (PPh25, different regime)
- Users in Excluded Excluded occupations (pilots, seafarers — special rates)

---

### Feedback Collection

**Session recording:** Hotjar or similar (requires separate cookie consent). Optional for beta.

**In-app NPS survey (triggered after audit completion):**

```
Seberapa mungkin kamu merekomendasikan cekwajar.id ke teman/kolega?

[0] [1] [2] [3] [4] [5] [6] [7] [8] [9] [10]
Sangat tidak mungkin                   Sangat mungkin

[Text field] Apa alasan utama nilaimu?
```

**Bug report form (accessible from result screen):**

| Field | Input Type | Required |
|-------|------------|---------|
| Tipe slip gaji | Dropdown: Corp PDF / SME PDF / ASN / Foto | Yes |
| Software payroll perusahaan | Text (e.g., "Talenta", "Excel") | No |
| Apa yang tidak sesuai? | Textarea | Yes |
| Nilai yang salah diekstrak | Text | No |
| Nilai yang seharusnya | Text | No |
| Apakah kamu mau dihubungi? | Yes/No | Yes |
| Email (jika yes) | Email | Conditional |

---

### Beta Success Criteria

Before going public, ALL of the following must be true:

| Metric | Threshold | Kill Condition | Data Source |
|--------|-----------|---------------|-------------|
| Completion rate (reach verdict) | ≥ 60% of users who start form | < 40% → investigate drop-off | Funnel analytics |
| NPS score | ≥ 30 | < 0 → redesign before launch | NPS survey |
| Confirmed calculation errors | 0 | ≥ 1 → fix + re-test before launch | Bug reports |
| OCR accuracy (user-reported wrong fields) | < 15% error rate | > 25% → disable OCR | Bug reports |
| Mobile breakage | 0 show-stopper bugs on mobile | Any crash on Rina/Sari device profiles | Manual testing |
| Payment flow completion | ≥ 70% of upgrade attempts complete | < 50% → redesign gate | Midtrans analytics |

---

### Beta Testing Script (User Journey)

Give this to beta testers as a structured task:

```
Tugas Beta Test — cekwajar.id

1. Buka cekwajar.id/wajar-slip di HP kamu
2. Upload foto slip gaji bulan lalu (ATAU isi manual jika tidak punya)
3. Lengkapi form dengan data slip gaji kamu
4. Lihat hasilnya — apakah ada pelanggaran yang terdeteksi?
5. Perhatikan apakah angka yang diekstrak OCR sudah benar
6. Klik "Tambah laporan gaji" di Wajar Gaji dan isi data gaji kamu
7. Cek benchmark gaji kamu di Wajar Gaji

Pertanyaan feedback:
a) Apakah ada kolom yang salah diekstrak dari foto?
b) Apakah hasil pelanggaran masuk akal?
c) Apa yang paling membingungkan?
d) Apakah kamu akan bayar IDR 29K untuk melihat detail IDR?
```

---

### Beta Analytics Setup (Before Launch)

```typescript
// Minimal analytics events — no PII
const TRACK_EVENTS = {
  // Wajar Slip funnel
  'slip_page_view': {},
  'slip_upload_attempt': { source: 'photo' | 'pdf' | 'manual' },
  'slip_ocr_routing': { decision: 'AUTO_ACCEPT' | 'SOFT_CHECK' | 'MANUAL_REQUIRED' },
  'slip_form_submit': { month: number },
  'slip_verdict_shown': { verdict: 'SESUAI' | 'ADA_PELANGGARAN', violationCount: number },
  'slip_gate_shown': {},
  'slip_upgrade_click': {},
  
  // Wajar Gaji funnel
  'gaji_page_view': {},
  'gaji_benchmark_shown': { confidence: 'HIGH' | 'MEDIUM' | 'LOW' },
  'gaji_gate_shown': {},
  'gaji_submit_salary': {},
  
  // Payment funnel
  'payment_snap_open': { plan: 'basic' | 'pro' },
  'payment_success': { plan: 'basic' | 'pro', method: string },
  'payment_cancelled': {},
  
  // NPS
  'nps_score': { score: number },
};
```

Track via Vercel Analytics (free, no PII by default) + Supabase custom events table for business metrics.

---

### Test Environment Setup

```bash
# Supabase branch for testing (isolates prod data)
supabase branches create beta-testing

# Use Midtrans sandbox (not production)
MIDTRANS_SERVER_KEY=SB-Mid-server-...
MIDTRANS_IS_PRODUCTION=false

# Use Vision test quota (keep prod quota safe)
GOOGLE_VISION_API_KEY=<separate-key-for-testing>

# Enable verbose logging (disable in prod)
DEBUG_OCR=true
DEBUG_CALCULATIONS=true
```

**Test accounts to pre-create:**
- `free@test.cekwajar.id` — free tier, no subscription
- `basic@test.cekwajar.id` — Basic subscription, 29 days remaining
- `pro@test.cekwajar.id` — Pro subscription
- `expiring@test.cekwajar.id` — Basic expires tomorrow (for expiry test)

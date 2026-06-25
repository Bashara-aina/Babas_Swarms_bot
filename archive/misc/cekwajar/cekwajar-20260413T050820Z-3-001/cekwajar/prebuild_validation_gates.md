# cekwajar.id — Final Pre-Build Validation: 5 Gates
**Author:** Indonesian Fintech Consultant (continuing from master_analysis_cekwajar.md)
**Date:** April 2026
**Scope:** Wajar Slip MVP only, solo founder, April–May 2026 launch

---

## EXECUTIVE SUMMARY

```
Build Confidence:  PARTIAL → GREEN in 5–6 weeks if gates executed in order
Critical Blocks:   Gate 1 (Tax Audit), Gate 5 (Legal: Supabase + UU PDP consent)
Gates as-is:       1 PENDING | 2 SIMULATED | 3 READY | 4 READY | 5 PARTIAL
Timeline to Green: 5 weeks (Gates 1+5 are the critical path)
Total Cost:        IDR 28M–48M (tax audit + legal + OCR test corpus)
```

| Gate | Name | Current Status | Blocker? | Cost (IDR) | Timeline |
|---|---|---|---|---|---|
| 1 | Tax Consultant Audit | ⚠️ PENDING | YES — cannot launch without | 15M–25M | 2–3 weeks |
| 2 | OCR 200-Payslip Benchmark | ⚠️ SIMULATED | YES — PDF-only decision required | 3M–5M (corpus) | 1 week |
| 3 | Closed Beta 100 Users | ✅ PLAN READY | NO — execute after Gates 1+2 | 0 (3-mo free Pro) | 2 weeks |
| 4 | Midtrans Live Test | ✅ READY | NO — straightforward setup | 0 | 3 days |
| 5 | Legal Docs | ⚠️ PARTIAL | YES — consent + privacy before upload | 5M–15M (lawyer) | 2–3 weeks |
| **OVERALL** | | 🟡 **BUILD YELLOW** | | **28M–48M total** | **5–6 weeks** |

**Decision:** Do not accept a single payslip from a real user until Gates 1 and 5 are GREEN. Gates 2, 3, 4 can run in parallel after Gate 1 completes.

---

## GATE 1: TAX CONSULTANT AUDIT

### 1.1 — All 20 Test Cases with Full Calculations

**Reference spec:** block_03_pph21_bpjs_engine.md (PMK 168/2023, UU HPP 7/2021, PMK 66/2023, PP 46/2015, PP 45/2015, Perpres 82/2018)

**PTKP Reference Values (PMK 66/2023, frozen 2024–2026):**

| PTKP Category | Annual (IDR) | Monthly Equivalent |
|---|---|---|
| TK/0 | 54,000,000 | 4,500,000 |
| K/0 | 58,500,000 | 4,875,000 |
| K/1 | 63,000,000 | 5,250,000 |
| K/2 | 67,500,000 | 5,625,000 |
| K/3 | 72,000,000 | 6,000,000 |

**TER Tabel A rates (PMK 168/2023 — use official DJP PDF for exact values):**

| Gross Monthly Income (IDR) | TER Rate |
|---|---|
| ≤ 5,000,000 | 0.25% |
| 5,000,001 – 10,000,000 | 0.75% |
| 10,000,001 – 15,000,000 | 1.00% |
| 15,000,001 – 20,000,000 | 1.50% |
| 20,000,001 – 25,000,000 | 1.75% |
| 25,000,001 – 50,000,000 | 2.00–3.00% (graduated) |
| > 50,000,000 | Refer to Lampiran PMK 168/2023 |

> ⚠️ **CRITICAL:** The TER rates above are illustrative. The PKP auditor must verify against the official Lampiran A/B/C in PMK 168/2023 from pajak.go.id. PTKP category also affects TER rate selection — K/0 and TK/0 have different rate columns in the official table.

**Progressive Tax Brackets (UU HPP 7/2021, effective 2022):**

| PKP Annual (IDR) | Rate |
|---|---|
| 0 – 60,000,000 | 5% |
| 60,000,001 – 250,000,000 | 15% |
| 250,000,001 – 500,000,000 | 25% |
| 500,000,001 – 5,000,000,000 | 30% |
| > 5,000,000,000 | 35% |

**BPJS Standard Rates:**

| Component | Employee | Employer | Cap Base Salary |
|---|---|---|---|
| JHT | 2.0% | 3.7% | None |
| JP | 1.0% | 2.0% | IDR 9,559,600 |
| JKK | 0% | 0.24–1.74% (5 classes) | None |
| JKM | 0% | 0.30% | None |
| Kesehatan | 1.0% | 4.0% | IDR 12,000,000 |

---

#### Test Cases TC-01 through TC-15

**TC-01: TK/0, IDR 8,000,000/month — Regular month, TER method**

```
Gross monthly income: IDR 8,000,000
TER rate (Tabel A, TK/0, IDR 5M-10M bracket): 0.75%
PPh21 TER = 8,000,000 × 0.75% = IDR 60,000

BPJS JHT (EE): 8,000,000 × 2.00% = IDR 160,000
BPJS JP (EE):  8,000,000 × 1.00% = IDR  80,000  (base < IDR 9,559,600 cap)
BPJS Kes (EE): 8,000,000 × 1.00% = IDR  80,000  (base < IDR 12,000,000 cap)
Take-home:     8,000,000 - 60,000 - 160,000 - 80,000 - 80,000 = IDR 7,620,000
```

| Field | Expected | Audit Actual | PASS/FAIL |
|---|---|---|---|
| PPh21 (TER) | IDR 60,000 | ___ | ___ |
| JHT EE | IDR 160,000 | ___ | ___ |
| JP EE | IDR 80,000 | ___ | ___ |
| Kes EE | IDR 80,000 | ___ | ___ |
| Take-home | IDR 7,620,000 | ___ | ___ |

---

**TC-02: K/0, IDR 10,000,000/month — Regular month, TER method**

```
Gross monthly income: IDR 10,000,000
NOTE: IDR 10,000,000 is on the boundary — falls in IDR 5M-10M bracket (≤10M)
TER rate (Tabel A, K/0): 0.75% (verify exact rate for K/0 category in PMK 168/2023)
PPh21 TER = 10,000,000 × 0.75% = IDR 75,000
[PKP auditor to verify: K/0 column may produce different TER rate than TK/0 for same income]

BPJS JHT (EE): 10,000,000 × 2.00% = IDR 200,000
BPJS JP (EE):  10,000,000 × 1.00% = IDR 100,000  (base < IDR 9,559,600 cap)
BPJS Kes (EE): 10,000,000 × 1.00% = IDR 100,000  (base < IDR 12,000,000 cap)
Take-home:     10,000,000 - 75,000 - 200,000 - 100,000 - 100,000 = IDR 9,525,000
```

| Field | Expected | Audit Actual | PASS/FAIL |
|---|---|---|---|
| PPh21 (TER) | IDR 75,000* | ___ | ___ |
| JHT EE | IDR 200,000 | ___ | ___ |
| JP EE | IDR 100,000 | ___ | ___ |
| Kes EE | IDR 100,000 | ___ | ___ |
| Take-home | IDR 9,525,000 | ___ | ___ |

*PKP auditor must confirm TER rate for K/0 at IDR 10M from official Lampiran PMK 168/2023

---

**TC-03: K/1, IDR 15,000,000/month — Regular month, TER method (reference case)**

```
Gross monthly income: IDR 15,000,000
TER rate (Tabel A, K/1, IDR 10M-15M bracket): 1.00%
PPh21 TER = 15,000,000 × 1.00% = IDR 150,000

PROGRESSIVE VERIFICATION (annual):
  Gross annual: 15,000,000 × 12 = 180,000,000
  Biaya jabatan: min(180,000,000 × 5%, 6,000,000) = 6,000,000
  BPJS Kes annual: min(15,000,000, 12,000,000) × 1% × 12 = 1,440,000
  Net annual: 180,000,000 - 6,000,000 - 1,440,000 = 172,560,000
  PTKP K/1: 63,000,000
  PKP: 172,560,000 - 63,000,000 = 109,560,000
  Tax: 60,000,000 × 5% + 49,560,000 × 15% = 3,000,000 + 7,434,000 = 10,434,000/year
  Monthly progressive equivalent: 10,434,000 / 12 = IDR 869,500
  TER monthly: IDR 150,000
  December true-up liability: 10,434,000 - (150,000 × 11) - December = catch-up

BPJS JHT (EE): 15,000,000 × 2.00% = IDR 300,000
BPJS JP (EE):  9,559,600 × 1.00% = IDR  95,596  (CAPPED — base exceeds IDR 9,559,600)
BPJS Kes (EE): 12,000,000 × 1.00% = IDR 120,000  (CAPPED — base exceeds IDR 12,000,000)
Take-home: 15,000,000 - 150,000 - 300,000 - 95,596 - 120,000 = IDR 14,334,404
```

| Field | Expected | Audit Actual | PASS/FAIL |
|---|---|---|---|
| PPh21 TER (monthly) | IDR 150,000 | ___ | ___ |
| Progressive annual tax | IDR 10,434,000 | ___ | ___ |
| JHT EE | IDR 300,000 | ___ | ___ |
| JP EE (capped) | IDR 95,596 | ___ | ___ |
| Kes EE (capped) | IDR 120,000 | ___ | ___ |
| Take-home (TER month) | IDR 14,334,404 | ___ | ___ |

---

**TC-04: K/3, IDR 30,000,000/month — Higher bracket progressive**

```
Gross monthly income: IDR 30,000,000
TER rate (Tabel A, K/3, IDR 25M-30M bracket): ~2.00%
PPh21 TER = 30,000,000 × 2.00% = IDR 600,000

PROGRESSIVE VERIFICATION:
  Gross annual: 360,000,000
  Biaya jabatan: capped at 6,000,000/year
  BPJS Kes annual: 12,000,000 × 1% × 12 = 1,440,000
  Net annual: 360,000,000 - 6,000,000 - 1,440,000 = 352,560,000
  PTKP K/3: 72,000,000
  PKP: 352,560,000 - 72,000,000 = 280,560,000
  Tax: 60M×5% + 190M×15% + 30,560,000×25%
     = 3,000,000 + 28,500,000 + 7,640,000 = 39,140,000/year
  Monthly progressive: 39,140,000/12 = IDR 3,261,667
  TER monthly: IDR 600,000
  December true-up is significant: ~IDR 30.5M accumulated

BPJS JP: 9,559,600 × 1% = IDR 95,596 (capped)
BPJS Kes: 12,000,000 × 1% = IDR 120,000 (capped)
BPJS JHT: 30,000,000 × 2% = IDR 600,000 (no cap)
Take-home (TER): 30,000,000 - 600,000 - 600,000 - 95,596 - 120,000 = IDR 28,584,404
```

| Field | Expected | Audit Actual | PASS/FAIL |
|---|---|---|---|
| PPh21 TER | IDR 600,000 | ___ | ___ |
| Progressive annual tax | IDR 39,140,000 | ___ | ___ |
| JP EE (capped) | IDR 95,596 | ___ | ___ |
| Kes EE (capped) | IDR 120,000 | ___ | ___ |
| JHT EE (no cap) | IDR 600,000 | ___ | ___ |

---

**TC-05: TK/0, IDR 10,000,000/month — JP cap boundary test**

```
JP base salary = 10,000,000 — exceeds IDR 9,559,600 cap
JP EE = IDR 9,559,600 × 1% = IDR 95,596 (NOT IDR 100,000)
JP ER = IDR 9,559,600 × 2% = IDR 191,192

ENGINE MUST: Cap JP calculation at IDR 9,559,600 base, not full gross salary
VIOLATION: If employer pays JP on full IDR 10,000,000 → they are overpaying (not a violation, just inefficiency)
VIOLATION: If employer uses IDR 10,000,000 base but employee slip shows less → violation V02
```

| Field | Expected | Audit Actual | PASS/FAIL |
|---|---|---|---|
| JP EE | IDR 95,596 | ___ | ___ |
| JP ER | IDR 191,192 | ___ | ___ |
| Cap triggered | YES | ___ | ___ |

---

**TC-06: K/1, IDR 20,000,000/month — BPJS Kesehatan cap test**

```
Kes base cap: IDR 12,000,000 (Perpres 82/2018)
Kes EE = 12,000,000 × 1% = IDR 120,000 (NOT IDR 200,000)
Kes ER = 12,000,000 × 4% = IDR 480,000

ENGINE MUST: Cap Kesehatan at IDR 12,000,000 base regardless of actual salary
```

| Field | Expected | Audit Actual | PASS/FAIL |
|---|---|---|---|
| Kes EE (capped) | IDR 120,000 | ___ | ___ |
| Kes ER (capped) | IDR 480,000 | ___ | ___ |
| Cap triggered | YES | ___ | ___ |

---

**TC-07: TK/0, IDR 2,500,000/month — Below UMK (Jakarta 2026: IDR 5,067,381)**

```
Gaji pokok: IDR 2,500,000
UMK Jakarta 2026: IDR 5,067,381 (verify exact figure from SK Gubernur DKI Jakarta)
Status: BELOW UMK → Violation V06 (CRITICAL)

PPh21: IDR 2,500,000 × 0.25% = IDR 6,250 (TER, lowest bracket)
BPJS JHT: 2,500,000 × 2% = IDR 50,000
BPJS JP: 2,500,000 × 1% = IDR 25,000
BPJS Kes: 2,500,000 × 1% = IDR 25,000

ENGINE MUST: Trigger V06 BEFORE calculating other violations
V06 message: "Gaji pokok Anda (IDR 2.500.000) di bawah UMK Jakarta 
(IDR 5.067.381). Ini melanggar Peraturan Menteri Ketenagakerjaan."
```

| Field | Expected | Audit Actual | PASS/FAIL |
|---|---|---|---|
| V06 triggered | YES | ___ | ___ |
| V06 message correct | YES | ___ | ___ |
| Correct UMK referenced | IDR 5,067,381 | ___ | ___ |
| PPh21 still calculated | IDR 6,250 | ___ | ___ |

---

**TC-08: K/0, IDR 10,000,000/month — December annual true-up (HIGHEST RISK)**

```
Scenario: Employee paid IDR 10,000,000 monthly throughout year (Jan–Nov: TER)
Jan–Nov TER withheld: 75,000 × 11 = IDR 825,000 total withheld

DECEMBER PROGRESSIVE CALCULATION:
  Annual gross: 120,000,000
  Biaya jabatan (capped): 6,000,000/year
  BPJS Kes: min(10M, 12M) × 1% × 12 = 1,200,000
  Net annual: 120,000,000 - 6,000,000 - 1,200,000 = 112,800,000
  PTKP K/0: 58,500,000
  PKP: 112,800,000 - 58,500,000 = 54,300,000
  Annual tax: 54,300,000 × 5% = IDR 2,715,000/year

  Already withheld Jan–Nov: IDR 825,000
  December must withhold: 2,715,000 - 825,000 = IDR 1,890,000

  NOTE: December payslip shows IDR 1,890,000 PPh21 — employee sees huge deduction
  Wajar Slip engine MUST explain this is TER true-up, not employer error

ENGINE MUST: Detect December, switch to progressive method, calculate true-up correctly
VIOLATION RISK: If engine treats December's IDR 1,890,000 as "too high" → false V04 → CATASTROPHIC
```

| Field | Expected | Audit Actual | PASS/FAIL |
|---|---|---|---|
| Annual tax (progressive) | IDR 2,715,000 | ___ | ___ |
| Jan–Nov TER withheld | IDR 825,000 | ___ | ___ |
| December withholding | IDR 1,890,000 | ___ | ___ |
| No false V04 on December slip | CONFIRMED | ___ | ___ |
| December explanation text shown | YES | ___ | ___ |

> ⚠️ TC-08 is the highest-risk test case. A wrong answer here generates either a false "employer owes you money" verdict (IDR 825K under-withheld interpretation) OR a false "employer over-withheld" complaint. Both are viral-error candidates.

---

**TC-09: TK/0, IDR 10,000,000 base + IDR 15,000,000 THR/Bonus — Non-regular income month**

```
Month with THR: total gross = 25,000,000
TER does NOT apply when bonus/THR present → use Progressive Bracket

Annual gross equivalent: (10,000,000 × 12) + 15,000,000 = 135,000,000
[Note: bonus is added to annual income, not annualized separately]
Biaya jabatan: 6,000,000 (capped)
BPJS Kes: 1,200,000
Net: 135,000,000 - 6,000,000 - 1,200,000 = 127,800,000
PTKP TK/0: 54,000,000
PKP: 127,800,000 - 54,000,000 = 73,800,000
Tax: 60,000,000 × 5% + 13,800,000 × 15% = 3,000,000 + 2,070,000 = 5,070,000/year

Tax on base salary only (for context):
  Net base annual: 120,000,000 - 6,000,000 - 1,200,000 = 112,800,000
  PKP base: 112,800,000 - 54,000,000 = 58,800,000
  Tax base: 58,800,000 × 5% = 2,940,000/year = 245,000/month

Tax attributable to THR: 5,070,000 - 2,940,000 = IDR 2,130,000 (one-time, collected this month)

BPJS: Only on base salary IDR 10,000,000 (THR/bonus not subject to BPJS)
BPJS JHT: 10,000,000 × 2% = IDR 200,000
BPJS JP (capped): 9,559,600 × 1% = IDR 95,596
BPJS Kes (capped): 10,000,000 × 1% = IDR 100,000 (below cap)
PPh21 this month: IDR 2,130,000 (from THR) + IDR 245,000 (from regular) = IDR 2,375,000

ENGINE MUST: (1) Detect non-regular income month, (2) Switch to progressive, 
(3) Exclude THR from BPJS base, (4) Calculate combined withholding correctly
```

| Field | Expected | Audit Actual | PASS/FAIL |
|---|---|---|---|
| TER applied this month | NO (bonus month) | ___ | ___ |
| PPh21 this month | IDR 2,375,000 | ___ | ___ |
| BPJS base (excludes THR) | IDR 10,000,000 | ___ | ___ |
| JHT EE | IDR 200,000 | ___ | ___ |

---

**TC-10: K/0, IDR 10,000,000/month — JKK class mismatch (office worker vs factory)**

```
Office worker (kelas 1): JKK ER = 10,000,000 × 0.24% = IDR 24,000
Factory worker (kelas 3): JKK ER = 10,000,000 × 0.54% = IDR 54,000
Factory worker (kelas 5/high risk): JKK ER = 10,000,000 × 1.74% = IDR 174,000

VIOLATION: Payslip shows JKK IDR 24,000 but employee works at a class-3 factory
→ V-JKK: "JKK yang dibayarkan tidak sesuai dengan kelas risiko pekerjaan Anda"

NOTE: Wajar Slip v1 should ask "Jenis pekerjaan utama Anda?" to determine risk class
JKK classes (PP 44/2015):
  Kelas I (office, admin): 0.24%
  Kelas II (light manufacturing): 0.54%
  Kelas III (medium risk): 0.89%
  Kelas IV (heavy industry): 1.27%
  Kelas V (mining, construction): 1.74%
```

| Field | Expected (office) | Expected (factory k3) | PASS/FAIL |
|---|---|---|---|
| JKK ER | IDR 24,000 | IDR 54,000 | ___ |
| Class correctly identified | YES | YES | ___ |
| Mismatch violation triggered | N/A | YES | ___ |

---

**TC-11: TK/0, IDR 8,000,000/month — BPJS entirely missing**

```
Slip shows: JHT = 0, JP = 0, Kes = 0
All three BPJS components missing.

V01: "BPJS JHT tidak ditemukan. Potongan IDR 160,000/bulan wajib dilakukan."
V07: "BPJS JP tidak ditemukan. Potongan IDR 80,000/bulan seharusnya ada."
V05: "BPJS Kesehatan tidak ditemukan. Potongan IDR 80,000/bulan wajib dilakukan."

Monthly employer shortfall:
  JHT ER missing: 8,000,000 × 3.7% = IDR 296,000
  JP ER missing: 8,000,000 × 2% = IDR 160,000
  JKK ER missing: varies by class
  JKM ER missing: 8,000,000 × 0.3% = IDR 24,000
  Kes ER missing: 8,000,000 × 4% = IDR 320,000 (not capped since base < 12M)
```

| Field | Expected | Audit Actual | PASS/FAIL |
|---|---|---|---|
| V01 triggered | YES | ___ | ___ |
| V05 triggered | YES | ___ | ___ |
| V07 triggered | YES | ___ | ___ |
| Correct EE amounts shown | As above | ___ | ___ |

---

**TC-12: K/0, IDR 10,000,000/month — BPJS partially paid (50% underpayment)**

```
Slip shows: JHT = IDR 100,000 (should be 200,000)
Slip shows: JP = IDR 50,000 (should be 95,596, capped)
Slip shows: Kes = IDR 50,000 (should be 100,000)

V02 triggers on JHT: "JHT dipotong IDR 100.000, seharusnya IDR 200.000. Selisih IDR 100.000/bulan."
V02 triggers on JP: "JP dipotong IDR 50.000, seharusnya IDR 95.596. Selisih IDR 45.596/bulan."
V02 triggers on Kes: "Kes dipotong IDR 50.000, seharusnya IDR 100.000. Selisih IDR 50.000/bulan."

Annual shortfall (employee-side only): (100K + 45.6K + 50K) × 12 = IDR 2,347,200/year
```

| Field | Expected | Audit Actual | PASS/FAIL |
|---|---|---|---|
| V02 on JHT | Shortfall IDR 100,000/mo | ___ | ___ |
| V02 on JP | Shortfall IDR 45,596/mo | ___ | ___ |
| V02 on Kes | Shortfall IDR 50,000/mo | ___ | ___ |
| Annual shortfall | IDR 2,347,200 | ___ | ___ |

---

**TC-13: K/1, IDR 15,000,000/month — PPh21 not withheld at all**

```
Slip shows: PPh21 = 0
Expected TER: IDR 150,000/month

V03: "PPh21 tidak dipotong padahal seharusnya IDR 150.000/bulan berdasarkan PTKP K/1 Anda."
Risk explanation: "Akumulasi kekurangan pajak akan jatuh tempo di akhir tahun. 
Anda dapat dikenakan bunga 2% per bulan oleh DJP jika tidak dilunasi tepat waktu."
```

| Field | Expected | Audit Actual | PASS/FAIL |
|---|---|---|---|
| V03 triggered | YES | ___ | ___ |
| Expected PPh21 amount in message | IDR 150,000 | ___ | ___ |
| Year-end risk explanation shown | YES | ___ | ___ |

---

**TC-14: TK/0, IDR 12,000,000/month — Freelance / contract worker (Pasal 21 non-employee)**

```
Employment type: Contract / Freelance (Tenaga Ahli / Tenaga Kerja Lepas)
PPh21 Pasal 21 for non-permanent employee:
  Rate: 50% of progressive rate applies to "penghasilan bruto"
  Monthly: 12,000,000 × 50% = 6,000,000 (deemed PKP for month)
  Annualized: 6,000,000 × 12 = 72,000,000 (deemed PKP annual)
  Tax: 60,000,000 × 5% + 12,000,000 × 15% = 3,000,000 + 1,800,000 = 4,800,000/year
  Monthly equivalent: 4,800,000 / 12 = IDR 400,000/month

BPJS: Typically not mandatory for freelancers (employer discretion or self-enrollment)
ENGINE: Must detect "Freelance" employment type and switch calculation method
```

| Field | Expected | Audit Actual | PASS/FAIL |
|---|---|---|---|
| Calculation method | Pasal 21 50% deemed | ___ | ___ |
| Monthly PPh21 | IDR 400,000 | ___ | ___ |
| BPJS warning | "Mungkin tidak wajib" | ___ | ___ |

---

**TC-15: TK/0, IDR 4,500,000/month — Part-time (3 days/week), prorated**

```
Part-time worker: 3 of 5 workdays = 60% time
Full-time equivalent: IDR 7,500,000
Prorated gaji pokok: IDR 4,500,000

TER: 4,500,000 × 0.25% = IDR 11,250
BPJS: If enrolled (employer choice), all rates apply to IDR 4,500,000
JHT EE: 4,500,000 × 2% = IDR 90,000
JP EE: 4,500,000 × 1% = IDR 45,000 (below cap)
Kes EE: 4,500,000 × 1% = IDR 45,000

Take-home: 4,500,000 - 11,250 - 90,000 - 45,000 - 45,000 = IDR 4,308,750
```

| Field | Expected | Audit Actual | PASS/FAIL |
|---|---|---|---|
| PPh21 TER | IDR 11,250 | ___ | ___ |
| JHT EE | IDR 90,000 | ___ | ___ |
| JP EE | IDR 45,000 | ___ | ___ |
| Kes EE | IDR 45,000 | ___ | ___ |
| Take-home | IDR 4,308,750 | ___ | ___ |

---

#### Additional Edge Cases TC-16 through TC-20

**TC-16: No NPWP — 20% surcharge**
```
K/0, IDR 10,000,000/month, no NPWP
Base PPh21 (TER): IDR 75,000
With 20% surcharge: 75,000 × 1.20 = IDR 90,000
V-NPWP: "Pegawai tidak memiliki NPWP. Potongan PPh21 ditambah 20% (IDR 90.000 vs IDR 75.000 normal)."
```

**TC-17: Mid-year joiner (July start), prorated first year (Tabel C)**
```
TK/0, IDR 10,000,000/month, starts July 1
Working months in year: 6 (Jul–Dec)
Annualized gross: 10,000,000 × 12 = 120,000,000 (but taxed on 6-month portion)
Prorated annual tax: calculate on full year, divide by 12, multiply by months remaining
[PKP auditor to verify exact Tabel C prorating method]
```

**TC-18: Employer absorbs PPh21 (PPh21 ditanggung perusahaan)**
```
K/0, IDR 10,000,000/month
Payslip shows PPh21 = IDR 0 with note "ditanggung perusahaan"
Expected: NOT a violation — employer grossing up tax is legal
Engine MUST NOT trigger V03 if employer absorption is indicated
Detection: check for "ditanggung perusahaan" / "PPh21 company borne" text in payslip
```

**TC-19: Natura/benefit in kind — taxable vs non-taxable**
```
Employee receives:
  - Cash transport allowance IDR 500,000 → TAXABLE
  - Company-provided meal vouchers IDR 1,000,000 → NON-TAXABLE (PMK 66/2023 Pasal 4)
  - Company phone for business use IDR 300,000 → NON-TAXABLE
  - Cash phone allowance IDR 300,000 → TAXABLE
Gross for PPh21: 10,000,000 + 500,000 + 300,000 = IDR 10,800,000 (excludes natura)
```

**TC-20: UMK city mismatch (employee works in Bekasi, registered in Jakarta)**
```
Gaji pokok: IDR 5,000,000
UMK Jakarta 2026: ~IDR 5,067,381 → BELOW → V06
UMK Bekasi 2026: ~IDR 5,159,910 → ALSO BELOW → V06 (different city, same violation)
Engine MUST use correct UMK for employee's actual work city, not registration city
```

---

### 1.2 Test Results Summary Table

| TC-ID | Description | Expected PPh21 | Expected JHT | PASS | Notes |
|---|---|---|---|---|---|
| TC-01 | TK/0, IDR 8M TER | IDR 60,000 | IDR 160,000 | ___ | |
| TC-02 | K/0, IDR 10M TER | IDR 75,000* | IDR 200,000 | ___ | *Verify K/0 rate |
| TC-03 | K/1, IDR 15M TER + annual | IDR 150,000 / IDR 10.43M | IDR 300,000 | ___ | JP+Kes capped |
| TC-04 | K/3, IDR 30M progressive | IDR 600,000 TER / IDR 39.14M yr | IDR 600,000 | ___ | Large Dec true-up |
| TC-05 | TK/0, IDR 10M JP cap | IDR 60,000 | IDR 200,000 | ___ | JP: IDR 95,596 |
| TC-06 | K/1, IDR 20M Kes cap | IDR 300,000 | IDR 400,000 | ___ | Kes: IDR 120,000 |
| TC-07 | TK/0, IDR 2.5M below UMK | IDR 6,250 | IDR 50,000 | ___ | V06 CRITICAL |
| TC-08 | K/0, IDR 10M December true-up | IDR 1,890,000 Dec | IDR 200,000 | ___ | HIGHEST RISK |
| TC-09 | TK/0 + IDR 15M THR month | IDR 2,375,000 | IDR 200,000 | ___ | No TER on THR |
| TC-10 | JKK class mismatch | Standard | IDR 200,000 | ___ | 5-class check |
| TC-11 | BPJS entirely missing | IDR 60,000 | IDR 0 (violation) | ___ | 3 V-codes |
| TC-12 | BPJS 50% underpaid | IDR 75,000 | IDR 100,000 | ___ | Shortfall IDR 195K |
| TC-13 | PPh21 missing, K/1 IDR 15M | IDR 0 (violation) | IDR 300,000 | ___ | V03 |
| TC-14 | Freelance Pasal 21 | IDR 400,000 | N/A | ___ | 50% deemed |
| TC-15 | Part-time 60% | IDR 11,250 | IDR 90,000 | ___ | Prorated |
| TC-16 | No NPWP, K/0 IDR 10M | IDR 90,000 | IDR 200,000 | ___ | +20% surcharge |
| TC-17 | Mid-year joiner Tabel C | Prorated | Prorated | ___ | Verify with PKP |
| TC-18 | PPh21 ditanggung | IDR 0 (correct) | IDR 200,000 | ___ | No false V03 |
| TC-19 | Natura benefit classification | Adjusted gross | Normal | ___ | PMK 66/2023 |
| TC-20 | UMK city mismatch | Normal | Normal | ___ | Correct UMK city |

**PASS REQUIREMENT:** All 20 test cases must PASS before public launch. TC-08 and TC-07 are the highest-risk failures. Any FAIL = fix code + re-run full suite.

---

### 1.3 Tax Consultant SOW Template (Ready to Send)

```
SURAT PERJANJIAN KERJA SAMA
KONSULTASI DAN AUDIT MESIN PERHITUNGAN PPh21 DAN BPJS
cekwajar.id — Wajar Slip Feature

PIHAK PERTAMA: [Nama Konsultan/Firma]
  Nomor Izin PKP: ________________
  Alamat:         ________________
  
PIHAK KEDUA: [Nama Founder], pemilik cekwajar.id
  NPWP Pribadi:   ________________
  Alamat:         ________________

== LINGKUP PEKERJAAN ==

1. REVIEW DOKUMEN REGULASI
   □ Konfirmasi interpretasi PMK No. 168 Tahun 2023 (TER method)
   □ Konfirmasi tabel TER Lampiran A/B/C resmi untuk tahun pajak 2026
   □ Konfirmasi nilai PTKP yang berlaku (PMK 66/2023)
   □ Konfirmasi BPJS rates: PP 46/2015, PP 45/2015, PP 44/2015, Perpres 82/2018
   □ Konfirmasi UMK Jakarta, Surabaya, Bandung, Medan (tahun 2026)

2. PENGUJIAN 20 KASUS (TC-01 s/d TC-20)
   □ Hitung hasil yang diharapkan untuk setiap test case secara independen
   □ Bandingkan dengan hasil perhitungan mesin cekwajar.id
   □ Tandai LULUS/GAGAL dengan penjelasan jika GAGAL
   □ Berikan saran perbaikan untuk setiap kasus yang GAGAL

3. REVIEW KODE PERHITUNGAN
   □ Review fungsi PPh21Calculator.calculate_monthly_pph21()
   □ Review fungsi _calculate_ter_withholding()
   □ Review fungsi _calculate_progressive_tax_annual()
   □ Review fungsi calculate_year_end_true_up()
   □ Review fungsi detect_violations() (7 kode pelanggaran)
   □ Konfirmasi bahwa biaya jabatan dihitung dengan benar (5%, maks IDR 500K/bulan)
   □ Konfirmasi penanganan bulan Desember (true-up tidak menghasilkan false violation)

4. LAPORAN AUDIT
   □ Dokumen tertulis berisi: hasil 20 test case, temuan risiko, saran perbaikan
   □ Pernyataan tertulis: "Mesin perhitungan PPh21 dan BPJS telah diverifikasi 
     sesuai dengan PMK 168/2023, PP 46/2015, PP 45/2015, PP 44/2015, 
     dan Perpres 82/2018 per tanggal audit"
   □ Tanda tangan dan stempel resmi konsultan berlisensi

== TIMELINE ==
Mulai: [tanggal disepakati]
Durasi: 5–7 hari kerja
Pengiriman laporan: [tanggal + 7 hari kerja]

== BIAYA ==
Total biaya jasa: IDR [15,000,000 – 25,000,000] (negosiasi sesuai lingkup)
Metode pembayaran: Transfer bank, DP 50% saat kontrak, sisa saat laporan dikirim
Rekening: ________________

== KERAHASIAAN ==
Konsultan menyetujui untuk menjaga kerahasiaan seluruh kode, data uji, dan 
laporan hasil audit. Tidak diperkenankan membagikan kepada pihak ketiga 
tanpa persetujuan tertulis Pihak Kedua.

Ditandatangani:
Pihak Pertama: ______________ Tanggal: ______________
Pihak Kedua:   ______________ Tanggal: ______________
```

**Finding Konsultan:** Search "konsultan pajak terdaftar" at www.pajak.go.id/konsultanpajak or DJP's directory. Target: PKP (Konsultan Pajak Bersertifikat). Estimated market rate IDR 15M–25M for this scope.

---

## GATE 2: OCR 200-PAYSLIP ACCURACY BENCHMARK

### 2.1 Simulated Test Corpus Results

The following table represents the expected accuracy profile based on the pre-build checklist research and comparable OCR benchmarks. **These are projected results, not actual test results.** The actual test must be run on real payslips before launch.

| Category | N | P0 Field Accuracy (Projected) | Decision Threshold | Action if Below Threshold |
|---|---|---|---|---|
| Large corp PDF (SAP/Oracle) | 60 | 96–98% | ≥ 92% | PASS expected |
| SME Excel-to-PDF | 50 | 88–93% | ≥ 92% | BORDERLINE — may need fallback for some layouts |
| Startup HTML (Mekari/Gadjian) | 30 | 94–97% | ≥ 92% | PASS expected |
| Government ASN (scanned) | 20 | 82–88% | ≥ 88% | BORDERLINE — scan quality variable |
| Mobile photo (blur/angle) | 40 | 68–78% | ≥ 75% | BORDERLINE — disable photo at launch |

**Pre-launch decision based on simulation:**
- PDF payslips (all categories): **LAUNCH** — expected to meet 92% threshold
- Photo payslips: **DO NOT LAUNCH** — expected 68–78%, below 75% minimum. Enable only in v1.2 after active fine-tuning on real corpus.

**How to build the real test corpus (before launch):**
1. Request payslips from 50 personal contacts (WhatsApp/LinkedIn) — offer IDR 50K GoPay per payslip (cost: IDR 2.5M for 50 payslips)
2. Use the 100 closed beta users to generate real test corpus (free, as part of beta)
3. Purchase 50 diverse payslip samples from Fiverr Indonesian freelancers who offer "dokumen contoh" (cost: ~IDR 1.5M)
4. ASN payslips: request from 5 government-employed friends or contacts

### 2.2 Dual OCR Fallback Implementation

```typescript
// app/api/slip/ocr/route.ts
// Dual-fallback OCR pipeline: Vision → Textract → Manual

import { NextRequest, NextResponse } from 'next/server';
import vision from '@google-cloud/vision';
import { TextractClient, AnalyzeDocumentCommand } from '@aws-sdk/client-textract';
import { createClient } from '@/lib/supabase/server';
import { validatePayslipFile } from '@/lib/validations/payslip';
import { extractPayslipFields } from '@/lib/ocr/field-extractor';
import type { PayslipFields, OCRConfidence } from '@/lib/types';

const OCR_CONFIDENCE = {
  AUTO_ACCEPT: 0.92,   // Accept without user review
  SOFT_CHECK: 0.80,    // Show value, ask user to confirm
  MANUAL_REQUIRED: 0.70, // Block verdict, show manual form
} as const;

const P0_FIELDS = [
  'gaji_pokok',
  'jht_employee',
  'jp_employee', 
  'kes_employee',
  'pph21_amount',
  'take_home_pay',
] as const;

export async function POST(request: NextRequest) {
  const supabase = createClient();

  // 1. Auth check
  const { data: { user }, error: authError } = await supabase.auth.getUser();
  if (authError || !user) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  }

  // 2. Rate limit check (5 audits/month free, 50 paid)
  const { data: usageData } = await supabase
    .rpc('check_audit_limit', { p_user_id: user.id });
  if (usageData?.limit_exceeded) {
    return NextResponse.json(
      { error: 'monthly_limit_reached', upgrade_url: '/upgrade' },
      { status: 429 }
    );
  }

  // 3. Parse and validate file
  const formData = await request.formData();
  const file = formData.get('payslip') as File;
  const validation = await validatePayslipFile(file);
  if (!validation.valid) {
    return NextResponse.json({ error: validation.message }, { status: 400 });
  }

  // 4. Verify consent was recorded (UU PDP gate)
  const { data: consent } = await supabase
    .from('user_consents')
    .select('sensitif_consent_at')
    .eq('user_id', user.id)
    .single();
  if (!consent?.sensitif_consent_at) {
    return NextResponse.json(
      { error: 'sensitif_consent_required', redirect: '/consent/payslip' },
      { status: 403 }
    );
  }

  // 5. Upload to Supabase Storage (private bucket, ap-southeast-1)
  const fileBuffer = await file.arrayBuffer();
  const fileName = `${user.id}/${Date.now()}_payslip.pdf`;
  const { error: uploadError } = await supabase.storage
    .from('payslip-uploads')
    .upload(fileName, fileBuffer, { contentType: 'application/pdf', upsert: false });
  if (uploadError) throw uploadError;

  // Record upload for 30-day deletion cron
  const { data: uploadRecord } = await supabase
    .from('payslip_uploads')
    .insert({ user_id: user.id, storage_path: fileName, file_type: 'pdf' })
    .select('id')
    .single();

  // 6. ATTEMPT 1: Google Cloud Vision
  let extractedFields: PayslipFields | null = null;
  let confidence: OCRConfidence = { overall: 0, fields: {} };
  let ocrProvider = 'manual';

  try {
    const visionResult = await runGoogleVision(fileBuffer);
    const { fields, conf } = extractPayslipFields(visionResult, 'vision');
    
    const p0MinConfidence = getMinP0Confidence(conf, P0_FIELDS);
    
    if (p0MinConfidence >= OCR_CONFIDENCE.AUTO_ACCEPT) {
      extractedFields = fields;
      confidence = conf;
      ocrProvider = 'google_vision';
    } else if (p0MinConfidence >= OCR_CONFIDENCE.SOFT_CHECK) {
      // Confidence low enough to need user confirmation, try Textract first
      const textractResult = await runTextract(fileBuffer);
      const { fields: tFields, conf: tConf } = extractPayslipFields(textractResult, 'textract');
      const textractMinConf = getMinP0Confidence(tConf, P0_FIELDS);
      
      if (textractMinConf > p0MinConfidence) {
        extractedFields = tFields;
        confidence = tConf;
        ocrProvider = 'textract';
      } else {
        extractedFields = fields;
        confidence = conf;
        ocrProvider = 'google_vision';
      }
    }
  } catch (visionError) {
    console.error('Vision OCR failed:', visionError);
    // Fall through to Textract
  }

  // 7. ATTEMPT 2: Amazon Textract (if Vision failed or low confidence)
  if (!extractedFields || confidence.overall < OCR_CONFIDENCE.SOFT_CHECK) {
    try {
      const textractResult = await runTextract(fileBuffer);
      const { fields, conf } = extractPayslipFields(textractResult, 'textract');
      const p0MinConfidence = getMinP0Confidence(conf, P0_FIELDS);
      
      if (p0MinConfidence >= OCR_CONFIDENCE.SOFT_CHECK) {
        extractedFields = fields;
        confidence = conf;
        ocrProvider = 'textract';
      }
    } catch (textractError) {
      console.error('Textract OCR failed:', textractError);
    }
  }

  // 8. DECISION: Auto-accept, soft-check, or manual form
  const p0MinConf = extractedFields 
    ? getMinP0Confidence(confidence.fields, P0_FIELDS)
    : 0;

  let responseMode: 'auto' | 'confirm' | 'manual';
  if (!extractedFields || p0MinConf < OCR_CONFIDENCE.MANUAL_REQUIRED) {
    responseMode = 'manual';
  } else if (p0MinConf < OCR_CONFIDENCE.AUTO_ACCEPT) {
    responseMode = 'confirm'; // Show fields, ask user to verify before verdict
  } else {
    responseMode = 'auto'; // Proceed directly to verdict
  }

  // 9. Store structured extraction (NOT the raw image — that stays in Storage)
  if (extractedFields) {
    await supabase.from('payslip_structured_data').insert({
      upload_id: uploadRecord!.id,
      user_id: user.id,
      ocr_provider: ocrProvider,
      extracted_fields: extractedFields,
      confidence_scores: confidence.fields,
      overall_confidence: confidence.overall,
      extraction_mode: responseMode,
    });
  }

  return NextResponse.json({
    mode: responseMode,
    fields: responseMode !== 'manual' ? extractedFields : null,
    confidence: confidence.fields,
    upload_id: uploadRecord!.id,
    manual_form_prefill: responseMode === 'manual' ? extractedFields : null,
  });
}

// --- Helper Functions ---

async function runGoogleVision(buffer: ArrayBuffer): Promise<any> {
  const client = new vision.ImageAnnotatorClient({
    keyFilename: process.env.GOOGLE_VISION_KEY_FILE,
  });
  const [result] = await client.documentTextDetection({
    image: { content: Buffer.from(buffer).toString('base64') },
  });
  return result.fullTextAnnotation;
}

async function runTextract(buffer: ArrayBuffer): Promise<any> {
  const client = new TextractClient({
    region: process.env.AWS_REGION || 'ap-southeast-1',
    credentials: {
      accessKeyId: process.env.AWS_ACCESS_KEY_ID!,
      secretAccessKey: process.env.AWS_SECRET_ACCESS_KEY!,
    },
  });
  const command = new AnalyzeDocumentCommand({
    Document: { Bytes: new Uint8Array(buffer) },
    FeatureTypes: ['FORMS', 'TABLES'],
  });
  return client.send(command);
}

function getMinP0Confidence(
  confFields: Record<string, number>,
  p0Fields: readonly string[]
): number {
  const p0Values = p0Fields.map(f => confFields[f] ?? 0);
  return Math.min(...p0Values);
}
```

```typescript
// lib/ocr/field-extractor.ts
// Indonesian payslip field extraction with pattern matching

export const INDONESIAN_PAYSLIP_PATTERNS: Record<string, RegExp[]> = {
  gaji_pokok: [
    /(?:gaji|upah)\s*(?:pokok|dasar)[:\s]*(?:IDR|Rp\.?\s*)?([0-9.,]+)/i,
    /basic\s*salary[:\s]*(?:IDR|Rp\.?\s*)?([0-9.,]+)/i,
    /salary[:\s]*(?:IDR|Rp\.?\s*)?([0-9.,]+)/i,
  ],
  jht_employee: [
    /(?:BPJS\s*)?(?:JHT|Jaminan\s*Hari\s*Tua).*?(?:karyawan|pegawai)?[:\s]*(?:IDR|Rp\.?\s*)?([0-9.,]+)/i,
    /JHT\s*2%[:\s]*(?:IDR|Rp\.?\s*)?([0-9.,]+)/i,
  ],
  jp_employee: [
    /(?:BPJS\s*)?(?:JP|Jaminan\s*Pensiun).*?(?:karyawan|pegawai)?[:\s]*(?:IDR|Rp\.?\s*)?([0-9.,]+)/i,
    /JP\s*1%[:\s]*(?:IDR|Rp\.?\s*)?([0-9.,]+)/i,
  ],
  kes_employee: [
    /(?:BPJS\s*)?(?:Kes(?:ehatan)?|JKS?).*?(?:karyawan|pegawai)?[:\s]*(?:IDR|Rp\.?\s*)?([0-9.,]+)/i,
    /(?:health|kesehatan)\s*insurance[:\s]*(?:IDR|Rp\.?\s*)?([0-9.,]+)/i,
  ],
  pph21_amount: [
    /PPh\s*(?:Pasal\s*)?21[:\s]*(?:IDR|Rp\.?\s*)?([0-9.,]+)/i,
    /pajak\s*(?:penghasilan)?[:\s]*(?:IDR|Rp\.?\s*)?([0-9.,]+)/i,
    /income\s*tax[:\s]*(?:IDR|Rp\.?\s*)?([0-9.,]+)/i,
  ],
  take_home_pay: [
    /(?:gaji|upah|penghasilan)\s*(?:bersih|netto?|net)[:\s]*(?:IDR|Rp\.?\s*)?([0-9.,]+)/i,
    /take[\s-]*home[:\s]*(?:IDR|Rp\.?\s*)?([0-9.,]+)/i,
    /total\s*(?:diterima|penerimaan)[:\s]*(?:IDR|Rp\.?\s*)?([0-9.,]+)/i,
  ],
};

export function extractPayslipFields(
  ocrOutput: any,
  provider: 'vision' | 'textract'
): { fields: PayslipFields; conf: OCRConfidence } {
  const rawText = provider === 'vision' 
    ? ocrOutput?.text ?? ''
    : extractTextractText(ocrOutput);

  const fields: Partial<PayslipFields> = {};
  const confFields: Record<string, number> = {};

  for (const [fieldName, patterns] of Object.entries(INDONESIAN_PAYSLIP_PATTERNS)) {
    for (const pattern of patterns) {
      const match = rawText.match(pattern);
      if (match?.[1]) {
        const value = parseIndonesianNumber(match[1]);
        if (value > 0) {
          fields[fieldName as keyof PayslipFields] = value;
          // Confidence heuristic: number of matching patterns × regex specificity
          confFields[fieldName] = calculateFieldConfidence(match, rawText, provider);
          break;
        }
      }
    }
    if (!confFields[fieldName]) confFields[fieldName] = 0;
  }

  const overall = Object.values(confFields).reduce((a, b) => a + b, 0) 
    / Object.keys(confFields).length;

  return { fields: fields as PayslipFields, conf: { overall, fields: confFields } };
}

function parseIndonesianNumber(raw: string): number {
  // Handle: "1.500.000" → 1500000, "1,500,000" → 1500000, "1500000" → 1500000
  const cleaned = raw.replace(/[.,]/g, (match, offset, str) => {
    // If followed by exactly 3 digits to end, it's a thousand separator
    const afterMatch = str.slice(offset + 1);
    if (/^\d{3}([.,]|$)/.test(afterMatch)) return '';
    return '.'; // Decimal point
  });
  return parseFloat(cleaned) || 0;
}
```

### 2.3 Launch Decision — PDF-Only

Based on simulation:
```
✅ LAUNCH with PDF payslip uploads only
❌ DO NOT LAUNCH photo/camera capture (v1.2 feature)
   Rationale: Photo OCR projected at 68–78% P0 accuracy vs 75% minimum threshold
   Risk: ~1 in 4 photo audits would have at least one P0 field wrong
   Wrong BPJS figure on 25% of audits = high probability of viral wrong-verdict post
```

Add to the upload UI in v1:
```
"Kami saat ini mendukung file PDF. Pastikan slip gaji Anda dalam format PDF 
agar akurasi analisis optimal. Dukungan foto akan segera hadir."
```

---

## GATE 3: CLOSED BETA 100 USERS

### 3.1 Recruitment Script (Copy-Paste Ready)

**Channel 1: r/indonesia (Reddit)**
```
Subject: [Beta Tester Wanted] cekwajar.id — Cek apakah slip gajimu sudah benar

Halo r/indonesia!

Gue lagi build cekwajar.id — platform yang langsung cek apakah potongan 
BPJS dan PPh21 di slip gajimu sudah benar sesuai hukum.

Banyak banget perusahaan (terutama UKM) yang salah hitung atau sengaja 
kurang bayar BPJS. Tool ini ngasih tau berapa yang seharusnya dipotong 
vs berapa yang benar-benar dipotong — lengkap dengan dasar hukumnya.

Cari 100 beta tester. Syarat:
✅ Karyawan tetap / kontrak dengan slip gaji PDF
✅ Bisa kasih feedback 10 menit setelah coba

Reward:
🎁 3 bulan akses Pro GRATIS (senilai IDR 147K)
🎁 Nama Anda di halaman "Founding Beta Testers" cekwajar.id

DM atau reply untuk dapat invite link.
Slot terbatas — first come first served.

[catatan: slip gaji tidak pernah dibagikan ke pihak lain. Diproses dan 
dihapus otomatis dalam 30 hari sesuai UU PDP No. 27/2022]
```

**Channel 2: LinkedIn DM (personalized)**
```
Hi [Nama],

Saya sedang membangun cekwajar.id — tool gratis yang mengaudit slip gaji 
untuk mendeteksi apakah potongan BPJS dan PPh21 sudah sesuai peraturan.

Sedang cari 100 beta tester dari profesional seperti Anda untuk mencoba 
versi awal dan memberikan feedback.

Imbalan: 3 bulan akses Pro gratis.

Apakah Anda tertarik? Saya bisa kirimkan invite link hari ini.

Salam,
[Nama Founder]
cekwajar.id
```

**Channel 3: WhatsApp/Telegram broadcast (personal network)**
```
Hei! Gue lagi develop app baru — cekwajar.id

Fungsinya: Upload slip gaji kamu (PDF), langsung tau apakah potongan 
BPJS dan pajak lo udah bener atau ada yang kurang bayar.

Lagi cari 100 orang buat beta test.
Reward: 3 bulan Pro gratis (IDR 147K value).

Tinggal klik link ini dan upload slip gaji PDF mu:
[invite_link]

Data kamu aman — diproses otomatis, dihapus dalam 30 hari.
```

### 3.2 Beta Management: Supabase Tables + RLS

```sql
-- Beta invite management
CREATE TABLE beta_invites (
  id             UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  invite_code    VARCHAR(12) NOT NULL UNIQUE,
  email          VARCHAR(255),
  invited_at     TIMESTAMPTZ DEFAULT NOW(),
  claimed_at     TIMESTAMPTZ,
  claimed_by     UUID REFERENCES auth.users(id),
  channel        VARCHAR(50), -- 'reddit', 'linkedin', 'whatsapp', 'direct'
  notes          TEXT,
  is_valid       BOOLEAN DEFAULT TRUE,
  CONSTRAINT valid_code CHECK (length(invite_code) = 12)
);

-- Beta user tracking
CREATE TABLE beta_users (
  id               UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id          UUID NOT NULL REFERENCES auth.users(id),
  invite_code      VARCHAR(12) REFERENCES beta_invites(invite_code),
  enrolled_at      TIMESTAMPTZ DEFAULT NOW(),
  pro_expires_at   TIMESTAMPTZ DEFAULT NOW() + INTERVAL '90 days',
  audits_completed INTEGER DEFAULT 0,
  feedback_given   BOOLEAN DEFAULT FALSE,
  nps_score        INTEGER CHECK (nps_score BETWEEN 0 AND 10),
  nps_comment      TEXT,
  nps_given_at     TIMESTAMPTZ
);

-- Beta audit events for measurement
CREATE TABLE beta_audit_events (
  id          UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id     UUID REFERENCES auth.users(id),
  event_type  VARCHAR(50), -- 'upload_started','upload_complete','ocr_success',
                           -- 'ocr_fallback','verdict_shown','gate_hit','nps_submitted'
  event_data  JSONB,
  created_at  TIMESTAMPTZ DEFAULT NOW()
);

-- RLS policies
ALTER TABLE beta_invites ENABLE ROW LEVEL SECURITY;
ALTER TABLE beta_users ENABLE ROW LEVEL SECURITY;
ALTER TABLE beta_audit_events ENABLE ROW LEVEL SECURITY;

-- Beta users can only read their own data
CREATE POLICY "beta_user_self_read" ON beta_users
  FOR SELECT USING (auth.uid() = user_id);

-- Beta audit events: users write own, read own
CREATE POLICY "beta_events_self" ON beta_audit_events
  FOR ALL USING (auth.uid() = user_id);

-- Admin-only on invites
CREATE POLICY "admin_invites" ON beta_invites
  FOR ALL USING (auth.jwt() ->> 'role' = 'service_role');

-- Grant beta pro access via subscription override
CREATE OR REPLACE FUNCTION is_beta_pro_active(p_user_id UUID)
RETURNS BOOLEAN AS $$
  SELECT EXISTS (
    SELECT 1 FROM beta_users
    WHERE user_id = p_user_id
    AND pro_expires_at > NOW()
  );
$$ LANGUAGE SQL SECURITY DEFINER;
```

### 3.3 Beta Success Metrics Dashboard

```sql
-- Run daily to track beta health
-- Dashboard Query 1: Overall beta funnel
SELECT
  COUNT(DISTINCT bu.user_id)                                        AS total_enrolled,
  COUNT(DISTINCT CASE WHEN bu.audits_completed >= 1 THEN bu.user_id END) AS completed_1_audit,
  COUNT(DISTINCT CASE WHEN bu.audits_completed >= 1 THEN bu.user_id END)::FLOAT 
    / NULLIF(COUNT(DISTINCT bu.user_id), 0) * 100                  AS completion_rate_pct,
  COUNT(DISTINCT CASE WHEN bu.nps_score IS NOT NULL THEN bu.user_id END) AS gave_nps,
  ROUND(AVG(bu.nps_score), 1)                                       AS avg_nps,
  COUNT(DISTINCT CASE WHEN bu.nps_score >= 9 THEN bu.user_id END)  AS promoters,
  COUNT(DISTINCT CASE WHEN bu.nps_score <= 6 THEN bu.user_id END)  AS detractors
FROM beta_users bu;

-- Dashboard Query 2: OCR success rates by event
SELECT
  event_type,
  COUNT(*)                                             AS event_count,
  COUNT(*) FILTER (WHERE event_data->>'success' = 'true')::FLOAT 
    / COUNT(*) * 100                                   AS success_rate_pct
FROM beta_audit_events
WHERE event_type IN ('upload_complete', 'ocr_success', 'ocr_fallback', 'verdict_shown')
GROUP BY event_type
ORDER BY event_count DESC;

-- Dashboard Query 3: Gate hit and conversion
SELECT
  COUNT(*) FILTER (WHERE event_type = 'verdict_shown')  AS verdicts_shown,
  COUNT(*) FILTER (WHERE event_type = 'gate_hit')       AS gate_hits,
  COUNT(*) FILTER (WHERE event_type = 'gate_hit')::FLOAT
    / NULLIF(COUNT(*) FILTER (WHERE event_type = 'verdict_shown'), 0) * 100
                                                         AS gate_hit_rate_pct,
  -- Paid conversions from beta (5 target)
  COUNT(DISTINCT s.user_id)                              AS paid_conversions
FROM beta_audit_events bae
LEFT JOIN subscriptions s ON bae.user_id = s.user_id AND s.status = 'active'
WHERE bae.event_type IN ('verdict_shown', 'gate_hit');

-- Dashboard Query 4: Audit completion rate
SELECT
  ROUND(
    COUNT(*) FILTER (WHERE audits_completed >= 1)::NUMERIC 
    / NULLIF(COUNT(*), 0) * 100, 1
  ) AS completion_rate_pct,
  -- Target: >= 60%
  CASE WHEN COUNT(*) FILTER (WHERE audits_completed >= 1)::FLOAT / 
    NULLIF(COUNT(*), 0) >= 0.60 THEN '✅ PASS' ELSE '❌ FAIL' END AS status
FROM beta_users;
```

### 3.4 Beta Success Criteria

| Metric | Target | Kill Threshold | Measurement |
|---|---|---|---|
| Enrolled testers | 100 | < 60 by Week 2 | beta_users COUNT |
| Audit completion rate | ≥ 60% | < 40% | Query 4 above |
| Average NPS | ≥ 30 | < 15 | Query 1 above |
| OCR success rate (PDF) | ≥ 90% | < 80% | Query 2 above |
| Paid conversions | ≥ 5 | 0 after full beta | Query 3 above |
| Confirmed PPh21 errors | 0 | Any confirmed error | Manual review |

**If audit completion < 40%:** UX/OCR blocking the flow. Do not public launch.
**If NPS < 15:** Product accuracy or trust problem. Do not public launch.
**If 0 paid conversions:** Gate message is not compelling. Redesign gate copy before launch.

---

## GATE 4: MIDTRANS LIVE TEST

### 4.1 Environment Variables — Individual Merchant

```bash
# .env.local (NEVER commit to git)

# Midtrans Individual Merchant
MIDTRANS_SERVER_KEY=         # SB-Mid-server-xxxx (sandbox) / Mid-server-xxxx (prod)
MIDTRANS_CLIENT_KEY=         # SB-Mid-client-xxxx (sandbox) / Mid-client-xxxx (prod)
MIDTRANS_IS_PRODUCTION=      # "false" for sandbox, "true" for production
MIDTRANS_MERCHANT_ID=        # G-xxxxxx (from merchant.midtrans.com)

# Product IDs (create in Midtrans dashboard)
MIDTRANS_PRODUCT_PRO_MONTHLY=  # "wajar-pro-monthly-49000"
MIDTRANS_PRODUCT_PRO_ANNUAL=   # "wajar-pro-annual-499000" (add in v2)

# Webhook security
MIDTRANS_WEBHOOK_SECRET=     # Server key — used for signature verification
```

### 4.2 Webhook Handler — Production-Grade with Signature Verification

```typescript
// app/api/payment/notify/route.ts
// Midtrans payment notification webhook handler

import { NextRequest, NextResponse } from 'next/server';
import crypto from 'crypto';
import { createClient } from '@/lib/supabase/server';

// Midtrans notification types
type MidtransNotification = {
  transaction_id: string;
  order_id: string;
  gross_amount: string;
  payment_type: string;
  transaction_status: string;
  fraud_status?: string;
  signature_key: string;
  status_code: string;
};

type SubscriptionStatus = 'active' | 'expired' | 'cancelled' | 'pending';

export async function POST(request: NextRequest) {
  const body: MidtransNotification = await request.json();
  
  // 1. VERIFY SIGNATURE (critical security step)
  const isValid = verifyMidtransSignature(body);
  if (!isValid) {
    console.error('Invalid Midtrans signature:', body.transaction_id);
    return NextResponse.json({ error: 'Invalid signature' }, { status: 403 });
  }

  const supabase = createClient();
  
  // 2. Parse order_id to get user_id and product
  // Order format: "cekwajar-{userId}-{timestamp}"
  const [, userId] = body.order_id.split('-', 3);
  if (!userId) {
    return NextResponse.json({ error: 'Invalid order_id' }, { status: 400 });
  }

  // 3. Determine subscription action based on transaction_status
  const transactionStatus = body.transaction_status;
  const fraudStatus = body.fraud_status;

  let subscriptionStatus: SubscriptionStatus;
  let expiresAt: Date | null = null;
  let action: string;

  if (transactionStatus === 'capture' && fraudStatus === 'accept') {
    subscriptionStatus = 'active';
    expiresAt = new Date(Date.now() + 30 * 24 * 60 * 60 * 1000); // +30 days
    action = 'payment_success';
  } else if (transactionStatus === 'settlement') {
    subscriptionStatus = 'active';
    expiresAt = new Date(Date.now() + 30 * 24 * 60 * 60 * 1000);
    action = 'payment_settled';
  } else if (transactionStatus === 'deny' || fraudStatus === 'deny') {
    subscriptionStatus = 'expired';
    action = 'payment_denied_fraud';
  } else if (transactionStatus === 'cancel' || transactionStatus === 'expire') {
    subscriptionStatus = 'expired';
    action = 'payment_expired_or_cancelled';
  } else if (transactionStatus === 'pending') {
    subscriptionStatus = 'pending';
    action = 'payment_pending';
  } else {
    // Unhandled status — log but don't error
    console.warn('Unhandled Midtrans status:', transactionStatus);
    return NextResponse.json({ received: true });
  }

  // 4. Upsert subscription record
  const { error: upsertError } = await supabase
    .from('subscriptions')
    .upsert({
      user_id: userId,
      status: subscriptionStatus,
      expires_at: expiresAt?.toISOString(),
      last_transaction_id: body.transaction_id,
      last_payment_amount: parseInt(body.gross_amount),
      payment_type: body.payment_type,
      updated_at: new Date().toISOString(),
    }, {
      onConflict: 'user_id',
    });

  if (upsertError) {
    console.error('Subscription upsert error:', upsertError);
    // Return 200 to Midtrans so they don't retry — log for manual resolution
    return NextResponse.json({ received: true, error: 'db_error' });
  }

  // 5. Log payment event for analytics
  await supabase.from('payment_events').insert({
    user_id: userId,
    transaction_id: body.transaction_id,
    order_id: body.order_id,
    action,
    status: subscriptionStatus,
    amount: parseInt(body.gross_amount),
    payment_type: body.payment_type,
  });

  // 6. If payment success: send confirmation (use Supabase email or Resend)
  if (subscriptionStatus === 'active') {
    // Trigger confirmation email via Edge Function
    await supabase.functions.invoke('send-payment-confirmation', {
      body: { user_id: userId, transaction_id: body.transaction_id }
    });
  }

  // 7. Dunning: if expired — schedule re-engagement
  if (subscriptionStatus === 'expired' && action === 'payment_expired_or_cancelled') {
    await supabase.functions.invoke('schedule-dunning-email', {
      body: { user_id: userId, days_until_retry: 3 }
    });
  }

  return NextResponse.json({ received: true });
}

function verifyMidtransSignature(notification: MidtransNotification): boolean {
  const { order_id, status_code, gross_amount, signature_key } = notification;
  const serverKey = process.env.MIDTRANS_SERVER_KEY!;
  
  // Midtrans signature = SHA512(order_id + status_code + gross_amount + server_key)
  const rawString = `${order_id}${status_code}${gross_amount}${serverKey}`;
  const expectedSignature = crypto
    .createHash('sha512')
    .update(rawString)
    .digest('hex');
  
  // Use timing-safe comparison
  return crypto.timingSafeEqual(
    Buffer.from(signature_key),
    Buffer.from(expectedSignature)
  );
}
```

### 4.3 End-to-End Payment Flow

```
User clicks "Upgrade Pro" (IDR 49K/month)
         │
         ▼
POST /api/payment/create-transaction
  → Generate order_id: "cekwajar-{userId}-{timestamp}"
  → Call Midtrans Snap API
  → Return: { snap_token, redirect_url }
         │
         ▼
Client opens Midtrans Snap popup (GooPay / VA / QRIS / Card)
         │
         ▼
User completes payment
         │
         ├─► Midtrans sends POST to /api/payment/notify (webhook)
         │     → verifyMidtransSignature ✓
         │     → UPDATE subscriptions SET status='active', expires_at=+30days
         │     → Send confirmation email
         │
         └─► Client polls /api/user/subscription-status
               (or Supabase Realtime on subscriptions table)
               → Show "Pro activated" toast
               → Remove gate from verdict UI
```

### 4.4 Refund and Dunning Policy

```typescript
// Dunning sequence — 3 attempts then downgrade
const DUNNING_SCHEDULE = {
  attempt1: { dayOffset: 0,  action: 'notify_failed_in_app_and_email' },
  attempt2: { dayOffset: 3,  action: 'retry_payment_link_email' },
  attempt3: { dayOffset: 7,  action: 'final_warning_email' },
  downgrade: { dayOffset: 10, action: 'set_status_expired' },
};

// Win-back offer after downgrade:
// Email Day 13: "30% off if you re-subscribe this week" → coupon code in Midtrans dashboard
```

**Refund policy (in ToS):**
- Within 24 hours of first charge: full refund, no questions
- After 24 hours: pro-rated refund if no audits conducted; no refund if audits used
- Midtrans refund process: via merchant dashboard → takes 3–14 business days to user

### 4.5 Live Test Checklist

| Test | Expected Result | Done |
|---|---|---|
| Create sandbox transaction (GooPay) | Snap popup opens, payment succeeds | ___ |
| Webhook received with correct signature | Logs show verified | ___ |
| subscription.status updated to 'active' | DB shows 'active' | ___ |
| Verdict gate removed after payment | UI shows full breakdown | ___ |
| Payment expires (simulate via Midtrans sandbox) | Status → 'expired', gate returns | ___ |
| Refund via sandbox | Status → 'expired' after refund | ___ |
| Live IDR 1,000 test transaction | Real payment processed | ___ |
| Live IDR 49,000 transaction | Full Pro month activated | ___ |

---

## GATE 5: LEGAL DOCS READY TO SIGN/DEPLOY

### 5.1 Supabase ap-southeast-1 Migration Script

**Execute this BEFORE any user data is collected. Takes ~1 hour.**

```bash
#!/bin/bash
# Migrate from Supabase us-east-1 to ap-southeast-1
# Run on local machine with Supabase CLI installed

echo "=== SUPABASE REGION MIGRATION: us-east-1 → ap-southeast-1 ==="
echo "Estimated time: 45-60 minutes"

# Step 1: Install Supabase CLI if not installed
# brew install supabase/tap/supabase

# Step 2: Login to Supabase
supabase login

# Step 3: Export schema from current project
echo "Exporting schema from current project..."
supabase db dump --db-url "$OLD_DATABASE_URL" -f schema_backup.sql
supabase db dump --db-url "$OLD_DATABASE_URL" --data-only -f data_backup.sql

echo "✓ Backup complete. Files: schema_backup.sql, data_backup.sql"

# Step 4: Create new Supabase project in ap-southeast-1
echo ""
echo "ACTION REQUIRED: Create new Supabase project at supabase.com"
echo "  Region: Southeast Asia (Singapore) ap-southeast-1"
echo "  Project name: cekwajar-prod"
echo ""
echo "Press ENTER when new project is created and you have the new DATABASE_URL..."
read -r

# Step 5: Apply schema to new project
echo "Applying schema to new project..."
psql "$NEW_DATABASE_URL" < schema_backup.sql

# Step 6: Enable RLS on all tables (CRITICAL - must do before any data)
psql "$NEW_DATABASE_URL" << 'EOF'
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE payslip_uploads ENABLE ROW LEVEL SECURITY;
ALTER TABLE payslip_verdicts ENABLE ROW LEVEL SECURITY;
ALTER TABLE salary_submissions ENABLE ROW LEVEL SECURITY;
ALTER TABLE subscriptions ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_consents ENABLE ROW LEVEL SECURITY;
ALTER TABLE beta_users ENABLE ROW LEVEL SECURITY;
ALTER TABLE beta_invites ENABLE ROW LEVEL SECURITY;
ALTER TABLE payment_events ENABLE ROW LEVEL SECURITY;
EOF
echo "✓ RLS enabled on all tables"

# Step 7: Set up 30-day payslip deletion cron
psql "$NEW_DATABASE_URL" << 'EOF'
-- Enable pg_cron extension
CREATE EXTENSION IF NOT EXISTS pg_cron;

-- Delete payslip files older than 30 days (updates storage path to NULL, marks deleted)
SELECT cron.schedule(
  'delete-old-payslips',
  '0 2 * * *',  -- Run daily at 2 AM Singapore time
  $$
  UPDATE payslip_uploads 
  SET storage_path = NULL, 
      deleted_at = NOW(),
      deletion_reason = 'auto_30day_retention'
  WHERE created_at < NOW() - INTERVAL '30 days'
  AND deleted_at IS NULL
  AND storage_path IS NOT NULL;
  $$
);

-- Also trigger Supabase Storage deletion via Edge Function
SELECT cron.schedule(
  'purge-storage-files',
  '5 2 * * *',  -- 5 minutes after DB update
  $$
  SELECT net.http_post(
    url := 'https://[YOUR_PROJECT_REF].supabase.co/functions/v1/purge-deleted-payslips',
    headers := '{"Authorization": "Bearer [SERVICE_ROLE_KEY]"}'::jsonb
  );
  $$
);
EOF
echo "✓ 30-day auto-deletion cron configured"

# Step 8: Update environment variables in Vercel
echo ""
echo "ACTION REQUIRED: Update these env vars in Vercel dashboard:"
echo "  NEXT_PUBLIC_SUPABASE_URL = https://[NEW_PROJECT_REF].supabase.co"
echo "  NEXT_PUBLIC_SUPABASE_ANON_KEY = [new anon key]"
echo "  SUPABASE_SERVICE_ROLE_KEY = [new service role key]"
echo "  DATABASE_URL = [new connection string]"
echo ""
echo "Press ENTER when Vercel env vars are updated..."
read -r

echo "=== MIGRATION COMPLETE ==="
echo "Verify: curl https://[your-domain]/api/health → should return 200"
```

### 5.2 UU PDP Consent Modal — Full HTML (Drop-in Component)

```html
<!-- components/consent/PayslipConsentModal.tsx rendered as HTML -->
<!-- Implements UU PDP No. 27/2022 Pasal 20 dual-consent requirement -->

<!DOCTYPE html>
<html lang="id">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Persetujuan Pemrosesan Data — cekwajar.id</title>
  <style>
    .consent-overlay {
      position: fixed; inset: 0; background: rgba(0,0,0,0.7);
      z-index: 9999; display: flex; align-items: center; justify-content: center;
      padding: 1rem;
    }
    .consent-modal {
      background: white; border-radius: 12px; padding: 2rem;
      max-width: 540px; width: 100%; max-height: 90vh; overflow-y: auto;
    }
    .consent-modal h2 { font-size: 1.25rem; font-weight: 700; margin-bottom: 0.5rem; }
    .consent-modal p { color: #4B5563; font-size: 0.9rem; line-height: 1.6; }
    .legal-badge {
      background: #EFF6FF; border: 1px solid #BFDBFE;
      border-radius: 6px; padding: 0.75rem; margin: 1rem 0; font-size: 0.8rem;
      color: #1E40AF;
    }
    .consent-item {
      border: 1px solid #E5E7EB; border-radius: 8px; padding: 1rem;
      margin: 0.75rem 0;
    }
    .consent-item.required { border-color: #FCA5A5; background: #FFF5F5; }
    .consent-item label {
      display: flex; gap: 0.75rem; align-items: flex-start; cursor: pointer;
    }
    .consent-item input[type="checkbox"] {
      width: 20px; height: 20px; margin-top: 2px; flex-shrink: 0;
      accent-color: #2563EB; cursor: pointer;
    }
    .consent-item .title { font-weight: 600; font-size: 0.9rem; margin-bottom: 0.25rem; }
    .consent-item .description { font-size: 0.82rem; color: #6B7280; line-height: 1.5; }
    .sensitif-tag {
      display: inline-block; background: #FEF2F2; color: #DC2626;
      border: 1px solid #FECACA; border-radius: 4px; font-size: 0.7rem;
      padding: 1px 6px; margin-left: 6px; font-weight: 600;
    }
    .btn-primary {
      width: 100%; padding: 0.875rem; background: #2563EB; color: white;
      border: none; border-radius: 8px; font-size: 1rem; font-weight: 600;
      cursor: pointer; margin-top: 1rem;
    }
    .btn-primary:disabled { background: #93C5FD; cursor: not-allowed; }
    .btn-secondary {
      width: 100%; padding: 0.75rem; background: white; color: #6B7280;
      border: 1px solid #E5E7EB; border-radius: 8px; font-size: 0.9rem;
      cursor: pointer; margin-top: 0.5rem;
    }
    .privacy-links { text-align: center; margin-top: 1rem; font-size: 0.8rem; }
    .privacy-links a { color: #2563EB; text-decoration: none; }
    .warning-box {
      background: #FFFBEB; border: 1px solid #FCD34D; border-radius: 6px;
      padding: 0.75rem; margin-top: 0.75rem; font-size: 0.82rem; color: #92400E;
    }
  </style>
</head>
<body>

<div class="consent-overlay" id="consentOverlay">
  <div class="consent-modal" role="dialog" aria-modal="true" 
       aria-labelledby="modalTitle">
    
    <!-- Header -->
    <h2 id="modalTitle">🔒 Persetujuan Sebelum Upload Slip Gaji</h2>
    <p>Sebelum Anda mengunggah slip gaji, kami perlu mendapat persetujuan 
       eksplisit Anda sesuai <strong>Undang-Undang No. 27 Tahun 2022 
       tentang Perlindungan Data Pribadi (UU PDP)</strong>.</p>

    <!-- Legal badge -->
    <div class="legal-badge">
      📋 Berdasarkan <strong>Pasal 20 UU PDP No. 27/2022</strong>, 
      pemrosesan data pribadi yang bersifat sensitif memerlukan 
      persetujuan eksplisit yang diberikan secara terpisah.
    </div>

    <!-- Consent 1: General data -->
    <div class="consent-item">
      <label>
        <input type="checkbox" id="consent_umum" required
               onchange="updateSubmitButton()">
        <div>
          <div class="title">
            Data Pekerjaan dan Gaji (Data Umum)
          </div>
          <div class="description">
            Saya menyetujui pemrosesan informasi pekerjaan saya 
            (jabatan, industri, kota) dan jumlah gaji untuk keperluan 
            benchmark anonim. Data ini akan dianonimkan dalam 90 hari 
            dan digunakan untuk meningkatkan akurasi data benchmark 
            cekwajar.id yang membantu sesama karyawan Indonesia.
          </div>
        </div>
      </label>
    </div>

    <!-- Consent 2: Sensitive data (payslip) -->
    <div class="consent-item required">
      <label>
        <input type="checkbox" id="consent_sensitif" required
               onchange="updateSubmitButton()">
        <div>
          <div class="title">
            Slip Gaji Anda <span class="sensitif-tag">DATA SENSITIF</span>
          </div>
          <div class="description">
            Saya memberikan <strong>persetujuan eksplisit</strong> kepada 
            cekwajar.id untuk memproses slip gaji saya (termasuk jumlah 
            gaji, potongan BPJS, PPh21, dan informasi terkait) sesuai 
            <strong>Pasal 20 ayat 2(a) UU No. 27 Tahun 2022</strong>.<br><br>
            
            Saya memahami bahwa:
            <ul style="margin: 0.5rem 0 0; padding-left: 1.25rem;">
              <li>Slip gaji saya akan diproses secara otomatis oleh sistem OCR</li>
              <li>File asli slip gaji akan <strong>dihapus permanen dalam 30 hari</strong></li>
              <li>Data terstruktur (jumlah-jumlah) akan dianonimkan dan disimpan 
                  sebagai data benchmark tanpa identifikasi pribadi</li>
              <li>Saya dapat meminta penghapusan data kapan saja melalui 
                  pengaturan akun</li>
            </ul>
          </div>
        </div>
      </label>
    </div>

    <!-- Warning about data usage -->
    <div class="warning-box">
      ⚠️ <strong>Penting:</strong> Slip gaji Anda tidak akan pernah dibagikan 
      ke pihak ketiga, termasuk atasan atau perusahaan Anda. Data hanya 
      digunakan untuk perhitungan otomatis di sistem kami.
    </div>

    <!-- Data processing details -->
    <details style="margin-top: 0.75rem; font-size: 0.82rem; color: #6B7280;">
      <summary style="cursor: pointer; color: #2563EB;">
        Lihat detail pemrosesan data lengkap
      </summary>
      <div style="margin-top: 0.5rem; padding: 0.75rem; background: #F9FAFB; 
                  border-radius: 6px; line-height: 1.6;">
        <strong>Tujuan pemrosesan:</strong> Audit kepatuhan PPh21 dan BPJS<br>
        <strong>Dasar hukum:</strong> Persetujuan eksplisit (Pasal 20(2)(a) UU PDP)<br>
        <strong>Retensi file asli:</strong> Maksimal 30 hari, lalu dihapus otomatis<br>
        <strong>Retensi data terstruktur:</strong> Dianonimkan setelah 90 hari<br>
        <strong>Lokasi pemrosesan:</strong> Server di Singapore (Supabase ap-southeast-1)<br>
        <strong>Transfer lintas negara:</strong> Menggunakan Data Processing Agreement 
        sesuai Pasal 56 UU PDP<br>
        <strong>Hak Anda:</strong> Akses, koreksi, penghapusan data sesuai Pasal 22–27 
        UU PDP — melalui menu Pengaturan Akun > Data Saya
      </div>
    </details>

    <!-- Action buttons -->
    <button class="btn-primary" id="submitConsent" disabled
            onclick="submitConsent()">
      Saya Setuju — Lanjutkan Upload Slip Gaji
    </button>
    
    <button class="btn-secondary" onclick="cancelConsent()">
      Batal — Kembali
    </button>

    <!-- Privacy links -->
    <div class="privacy-links">
      <a href="/privasi" target="_blank">Kebijakan Privasi</a> ·
      <a href="/syarat" target="_blank">Syarat & Ketentuan</a> ·
      <a href="/data-saya" target="_blank">Kelola Data Saya</a>
    </div>
  </div>
</div>

<script>
function updateSubmitButton() {
  const consent1 = document.getElementById('consent_umum').checked;
  const consent2 = document.getElementById('consent_sensitif').checked;
  const btn = document.getElementById('submitConsent');
  btn.disabled = !(consent1 && consent2);
  if (!btn.disabled) {
    btn.textContent = 'Saya Setuju — Lanjutkan Upload Slip Gaji ✓';
  } else {
    btn.textContent = 'Centang kedua persetujuan untuk melanjutkan';
  }
}

async function submitConsent() {
  // Record consent in Supabase before any file upload
  const response = await fetch('/api/consent/record', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      consent_umum: true,
      consent_sensitif: true,
      consent_version: '2026-04-01', // Update when consent text changes
      ip_address: null, // Server-side only
      user_agent: navigator.userAgent,
    })
  });
  
  if (response.ok) {
    document.getElementById('consentOverlay').remove();
    // Trigger file upload UI
    document.getElementById('payslipUploader').classList.remove('hidden');
  } else {
    alert('Gagal menyimpan persetujuan. Coba refresh halaman.');
  }
}

function cancelConsent() {
  document.getElementById('consentOverlay').remove();
  // Return to tool landing page
  window.location.href = '/slip';
}
</script>

</body>
</html>
```

### 5.3 Tax Consultant SOW (Ready to Send)

Already provided in Gate 1.3 above — complete, ready to customize with names and send.

### 5.4 PSE Registration Checklist (oss.go.id)

```
PSE REGISTRATION CHECKLIST — KOMINFO (Permenkominfo 5/2020)

System: Electronic System Operator (PSE) Private Non-Public
URL to file: https://oss.go.id → Login → Perizinan Usaha → PSE

DOCUMENTS REQUIRED:
□ NIB (Nomor Induk Berusaha) — from OSS.go.id first if not yet registered
□ KTP Founder (upload scan)
□ NPWP Pribadi (upload scan)
□ Description of electronic system (see template below)
□ Privacy policy URL: https://cekwajar.id/privasi
□ Technical security description

SYSTEM DESCRIPTION TEMPLATE (copy into OSS form):
---
Nama Sistem: cekwajar.id
Jenis Layanan: Platform audit kepatuhan penggajian dan benchmark data tenaga kerja
Fungsi Utama: Memungkinkan pengguna mengunggah slip gaji untuk diaudit 
  kepatuhannya terhadap ketentuan PPh21 (PMK 168/2023), BPJS Ketenagakerjaan 
  (PP 46/2015, PP 44/2015, PP 45/2015), dan BPJS Kesehatan (Perpres 82/2018).
Data yang Diproses: 
  - Slip gaji (dokumen sensitif, diproses dan dihapus dalam 30 hari)
  - Data gaji anonim (untuk benchmark pasar tenaga kerja)
  - Data akun pengguna (email, preferensi)
Lokasi Server: Singapore (Supabase ap-southeast-1)
Keamanan Data: Enkripsi AES-256 at rest, TLS 1.3 in transit, 
  Row Level Security (RLS) Supabase PostgreSQL
Kebijakan Privasi: https://cekwajar.id/privasi
---

TIMELINE: File early (Week 1). Processing takes 14–30 working days.
AFTER APPROVAL: Display PSE certificate number in footer: 
  "Terdaftar sebagai PSE di Kominfo No. [XXX/DJPPI/2026]"
COST: IDR 0
RISK IF NOT DONE: Kominfo blocking order (precedent: Steam, Epic Games, PayPal 2022)
```

### 5.5 Privacy Policy and ToS — Minimum Required Sections

**(Full documents require lawyer drafting — this is the outline with required content)**

```
KEBIJAKAN PRIVASI CEKWAJAR.ID
Versi: 1.0 | Berlaku sejak: [launch date] | Bahasa: Bahasa Indonesia

Bagian 1: Siapa Kami dan Hubungi Kami (Pasal 29 UU PDP)
  - Nama entitas: [Nama Founder] / [PT cekwajar jika sudah PT]
  - NPWP: [xxxxxx]
  - Email kontak: privasi@cekwajar.id
  - Respons waktu: 3 hari kerja

Bagian 2: Data yang Kami Kumpulkan (Pasal 4, 20 UU PDP)
  - Tabel data classification (umum vs sensitif) — from block_04_legal_compliance.md
  - Kapan data dikumpulkan, untuk apa

Bagian 3: Dasar Hukum Pemrosesan (Pasal 20 UU PDP)
  - Persetujuan (Pasal 20(2)(a)): slip gaji, PTKP status
  - Kontrak (Pasal 20(2)(b)): pembayaran Midtrans
  - Kepentingan sah (Pasal 20(2)(e)): analytics, fraud detection

Bagian 4: Retensi Data (Pasal 28 UU PDP)
  - Slip gaji: 30 hari → hapus otomatis
  - Data terstruktur: 90 hari → anonimkan
  - Data akun: selama akun aktif → 30 hari setelah penghapusan akun

Bagian 5: Hak Subjek Data (Pasal 22–27 UU PDP)
  - Hak akses: lihat data Anda di /data-saya
  - Hak koreksi: edit profil di pengaturan
  - Hak penghapusan: tombol "Hapus Akun" di pengaturan
  - Hak tarik persetujuan: menu "Kelola Persetujuan"
  - Respons: maksimal 14 hari kerja

Bagian 6: Transfer Data Lintas Negara (Pasal 56 UU PDP)
  - Server: Singapore (Supabase ap-southeast-1)
  - Dasar: Data Processing Agreement dengan Supabase Inc.
  - Jaminan keamanan setara hukum Indonesia

Bagian 7: Keamanan Data (Pasal 35 UU PDP)
  - Enkripsi at-rest dan in-transit
  - Akses terbatas (prinsip least privilege)
  - Audit log akses data sensitif

Bagian 8: Pembaruan Kebijakan
  - Pemberitahuan via email 14 hari sebelum perubahan berlaku

SYARAT & KETENTUAN CEKWAJAR.ID
Bagian kritis yang harus ada:

1. Bukan konsultasi hukum/pajak:
   "Hasil analisis cekwajar.id bukan merupakan konsultasi pajak, konsultasi 
   hukum ketenagakerjaan, atau penilaian resmi. Gunakan sebagai referensi 
   informasi. Untuk keputusan finansial penting, konsultasikan dengan 
   konsultan pajak terdaftar (PKP) atau pengacara ketenagakerjaan."

2. Batas akurasi:
   "Perhitungan PPh21 dan BPJS dilakukan berdasarkan informasi yang Anda 
   berikan dan data yang berhasil diekstrak dari slip gaji Anda. Keakuratan 
   bergantung pada kelengkapan data. cekwajar.id tidak bertanggung jawab 
   atas kerugian yang timbul dari ketidakakuratan data yang diunggah."

3. Batas tanggung jawab:
   "Tanggung jawab cekwajar.id terbatas pada jumlah yang dibayarkan oleh 
   pengguna dalam 12 bulan terakhir."

4. Hak penggunaan data:
   "Dengan menggunakan layanan ini, Anda memberikan cekwajar.id lisensi 
   terbatas untuk memproses data Anda sesuai Kebijakan Privasi."
```

---

## 6. FINAL BUILD GO/NO-GO CHECKLIST

### 6.1 Decision Matrix

| Gate | Name | Status | Launch Blocker? | Evidence / Notes |
|---|---|---|---|---|
| **1** | Tax Consultant Audit | ⚠️ PENDING | **YES** | Must hire PKP, 15 test cases + 5 edges, 5–7 days |
| **2** | OCR 200-Payslip Benchmark | ⚠️ SIMULATED | **YES (PDF-only decision)** | Real corpus needed; PDF launch OK, photo disabled |
| **3** | Closed Beta 100 Users | ✅ PLAN READY | NO (post-Gate 1) | Scripts, SQL, metrics all ready to execute |
| **4** | Midtrans Live | ✅ READY | NO | 3-day setup; webhook handler production-grade |
| **5** | Legal Docs | ⚠️ PARTIAL | **YES** | Consent modal ready; Privacy Policy needs lawyer review |
| **OVERALL** | | 🟡 **BUILD YELLOW** | **2 hard blocks** | Gates 1 + 5 are critical path |

### 6.2 Hardcoded Pre-Launch Checklist (Do Not Skip Any)

```
PRE-LAUNCH HARD GATES — cekwajar.id Wajar Slip MVP
All items must be checked before first public payslip upload is accepted.

GATE 1 — TAX AUDIT
□ PKP konsultan found and contracted (SOW signed)
□ TC-01 through TC-20: ALL PASS (0 failures)
□ December true-up (TC-08): confirmed no false V04 triggered
□ THR/bonus month (TC-09): confirmed TER not applied
□ Below UMK (TC-07): V06 correctly triggered with correct UMK amount
□ Written audit report received with PKP signature and stamp

GATE 2 — OCR BENCHMARK
□ Real test corpus assembled (min 100 PDF payslips)
□ Vision → Textract dual fallback coded and tested
□ PDF P0 accuracy ≥ 90% on real corpus
□ Photo upload disabled in UI with polite message
□ Manual form fallback working (user can enter fields manually)
□ Confidence thresholds implemented: AUTO / SOFT_CHECK / MANUAL

GATE 3 — BETA
(Run after Gates 1+2)
□ 100 beta testers recruited via invite-only links
□ ≥ 60 complete at least 1 audit
□ Average NPS ≥ 30 from post-verdict survey
□ 0 confirmed PPh21 calculation errors from beta users
□ ≥ 5 paid conversions from beta cohort
□ All OCR failures documented and fixed or documented as known limitation

GATE 4 — MIDTRANS
□ Merchant account individual (KTP + NPWP) verified and active
□ Sandbox: all 8 test cases in Gate 4.5 passing
□ Production: IDR 1,000 test transaction successful
□ Production: IDR 49,000 full Pro activation successful
□ Webhook signature verification tested (reject forged signatures)
□ Subscription status correctly updated in DB after payment
□ Dunning email sequence configured for failed payments

GATE 5 — LEGAL
□ Supabase migrated to ap-southeast-1 BEFORE any user data
□ 30-day auto-delete cron: tested and running
□ Consent modal: BOTH checkboxes independently required
□ Consent recorded in user_consents table before any upload accepted
□ Privacy Policy (Bahasa Indonesia): published at /privasi, lawyer-reviewed
□ Terms of Service (Bahasa Indonesia): published at /syarat, lawyer-reviewed
□ Verdict language reviewed: no binary "WAJAR" assertion
□ PSE registration: filed at oss.go.id (accept 14–30 day processing)
□ Data subject rights page (/data-saya): access, correction, deletion flows working
□ Service_role key: confirmed NOT exposed in any frontend code or git history
```

### 6.3 Timeline to GREEN

```
Week 1 (NOW):
  Day 1:   Supabase migration to ap-southeast-1 (1 hour)
  Day 1-2: Midtrans sandbox account created, tested
  Day 2:   PSE registration filed at oss.go.id
  Day 2-4: PKP konsultan identified and contracted (SOW sent)
  Day 3-7: Build OCR dual-fallback code, test on 50 sample PDFs

Week 2:
  Day 8-12: Tax audit sessions with PKP (test cases TC-01 to TC-20)
  Day 8-10: Privacy Policy and ToS lawyer review (can run in parallel)
  Day 10:  Fix any tax audit failures in calculation engine
  Day 11:  Re-run test suite after fixes
  Day 12:  Consent modal deployed, UU PDP flow tested end-to-end

Week 3:
  Day 15:  Received written audit report from PKP ✓
  Day 15:  Lawyer-reviewed Privacy Policy and ToS live at /privasi /syarat ✓
  Day 15:  Midtrans live IDR 49,000 test transaction processed ✓
  Day 15-16: Recruit 100 beta testers (Telegram/Reddit/LinkedIn)
  Day 17-21: Beta running — 100 users attempt payslip audits

Week 4:
  Day 22:  Beta metrics reviewed (completion, NPS, errors, conversions)
  Day 22-24: Fix P0 issues from beta
  Day 25:  Final pre-launch audit: run all 43 checklist items above
  Day 28-30: 🚀 SOFT PUBLIC LAUNCH — TikTok post #1 + r/indonesia post
```

**Total cost to GREEN:**

| Item | Cost (IDR) |
|---|---|
| PKP tax consultant audit | 15,000,000–25,000,000 |
| Indonesian privacy lawyer (Privacy Policy + ToS review) | 5,000,000–12,000,000 |
| Verdict language consumer law review | 3,000,000–5,000,000 |
| OCR test corpus assembly (Fiverr + compensation) | 3,000,000–5,000,000 |
| Beta tester incentives (100 × 3 months Pro = IDR 14.7K cost basis) | 0 (subscription forgone) |
| Infrastructure (Supabase Pro, Vercel, OCR APIs) | 1,400,000–2,800,000/mo |
| **Total one-time pre-launch** | **IDR 26,400,000–47,800,000** |
| **Recommended budget** | **IDR 50,000,000 (buffer included)** |

---

## FINAL ANSWER

**Execute these 7 steps in 28 days → BUILD GREEN.**

1. Day 1: Migrate Supabase to ap-southeast-1 + file PSE registration
2. Day 2: Contract PKP tax consultant (use SOW from Gate 1.3)
3. Day 3–7: Deploy OCR dual-fallback code, test on 50 real PDF payslips
4. Day 8–14: Run all 20 tax audit test cases with PKP, fix any failures
5. Day 10–14: Lawyer reviews Privacy Policy and ToS (in parallel)
6. Day 15–21: 100-user closed beta with beta SQL tables and metrics dashboard
7. Day 22–28: Fix P0 beta issues → check all 43 pre-launch gates → public soft launch

**Currently:** 🟡 BUILD YELLOW — 2 hard blocks (Tax Audit + Legal)
**After 28 days:** 🟢 BUILD GREEN — all gates cleared, product is legally and technically defensible for first 500 users
```

*Sources: master_analysis_cekwajar.md (gate definitions, timelines, costs), block_03_pph21_bpjs_engine.md (all 20 test case formulas, PTKP tables, TER/progressive specs, BPJS rates), block_07_technical_architecture.md (OCR pipeline, Next.js route structure, Midtrans webhook), block_04_legal_compliance.md (UU PDP data classification, consent text, DPO requirements), block_02_database_schema.md (RLS policies, pg_cron setup), vc_evaluation_cekwajar.md (Red Flags 1–5 as gate rationale), Pre-Build Checklist (OCR accuracy benchmarks, Midtrans onboarding requirements, BPS data limitations)*

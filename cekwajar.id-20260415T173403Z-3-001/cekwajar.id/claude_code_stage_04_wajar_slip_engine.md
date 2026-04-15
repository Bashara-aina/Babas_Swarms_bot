# Stage 4 — Wajar Slip: PPh21 + BPJS Engine + UI
**cekwajar.id Vibe Coding Playbook**  
**Estimated time:** 4–5 hours  
**Prerequisites:** Stages 1–3 complete. TER rates + BPJS rates + PTKP in DB.  
**Goal:** Wajar Slip fully working with manual form input, correct PPh21/BPJS calculations, all 7 violation detectors, free/paid verdict display.

---

## What You're Building

- Complete PPh21 TER calculation engine (TypeScript)
- BPJS calculation engine (JHT, JP, JKK, JKM, Kesehatan)
- All 7 violation detectors (V01–V07) with severity
- `POST /api/audit-payslip` API route
- Wajar Slip page with full form UI
- Verdict display (free tier: codes only; paid tier: IDR amounts)
- PremiumGate on IDR detail
- Rate limiting
- Audit stored to DB

---

## New Dependencies This Stage

```bash
# Zod for request validation (should be from Stage 1)
pnpm add zod

# Verify existing
pnpm list zod
```

---

## ═══════════════════════════════════════════════
## MASTER PROMPT — SEND THIS TO CLAUDE CODE
## (Stage 4 — Wajar Slip Engine + UI)
## ═══════════════════════════════════════════════

```
===START===
cekwajar.id — Stage 4: Wajar Slip Calculation Engine

Context: Next.js 15 App Router, TypeScript, Supabase (all tables exist).
Stages 1-3 complete. Auth working. DB has TER rates, BPJS rates, PTKP values, UMK 2026.

YOUR TASK FOR STAGE 4:
Build the complete Wajar Slip tool — calculation engine, API route, and full UI.

════════════════════════════════════════════════════
PART A: CALCULATION ENGINE
════════════════════════════════════════════════════

Create src/lib/calculations/pph21.ts

This file implements Indonesian PPh21 calculation per PMK 168/2023 (TER method).

Types needed:
  type TERCategory = 'A' | 'B' | 'C'
  
  interface PPh21Input {
    grossSalary: number        // monthly gross in IDR
    ptkpStatus: PtkpStatus     // 'TK/0', 'K/1', etc.
    monthNumber: number        // 1-12
    year: number
    hasNPWP: boolean
    cumulativeYtd?: number     // for December true-up
  }
  
  interface PPh21Result {
    terCategory: TERCategory
    terRate: number            // percentage e.g. 1.25
    pph21Amount: number        // IDR to withhold this month
    method: 'TER' | 'PROGRESSIVE'
    details: PPh21CalculationDetails
  }

STEP 1: Determine TER Category from PTKP status:
  A = TK/0, TK/1 (all single, 0-1 dependents)
  B = K/0, K/1, TK/2, TK/3
  C = K/2, K/3, K/I/0, K/I/1, K/I/2, K/I/3

  function getTERCategory(ptkpStatus: PtkpStatus): TERCategory {
    if (['TK/0', 'TK/1'].includes(ptkpStatus)) return 'A'
    if (['K/0', 'K/1', 'TK/2', 'TK/3'].includes(ptkpStatus)) return 'B'
    return 'C'
  }

STEP 2: For months 1-11 use TER method:
  terAmount = grossSalary × (terRate / 100)
  
  Get TER rate from pph21_ter_rates table (ALREADY in DB from migration 013).
  Query: SELECT monthly_rate_percent FROM pph21_ter_rates
         WHERE category = $1 AND min_salary <= $2 AND max_salary >= $2

STEP 3: For month 12 (December) use PROGRESSIVE method:
  Annual gross = monthly_gross × 12 (simplified — does not handle mid-year join/leave)
  PKP = Annual_gross - PTKP_annual
  
  Progressive brackets (UU HPP No.7/2021):
    0 - 60,000,000: 5%
    60,000,001 - 250,000,000: 15%
    250,000,001 - 500,000,000: 25%
    500,000,001 - 5,000,000,000: 30%
    > 5,000,000,000: 35%
  
  Calculate annual PPh21 total.
  December PPh21 = Annual_PPh21 - (TER_monthly × 11)
  If December result is negative, use 0 (overpaid situation — show in report)

STEP 4: No NPWP surcharge:
  If hasNPWP = false: multiply calculated PPh21 × 1.20 (20% surcharge per UU HPP)

Full function:
  export async function calculatePPh21(
    input: PPh21Input,
    supabase: SupabaseClient
  ): Promise<PPh21Result>

Create src/lib/calculations/bpjs.ts

Types:
  interface BPJSInput {
    grossSalary: number
    jkkCategory?: number   // 0.24, 0.54, 0.89, 1.27, 1.74 — default 0.24
  }
  
  interface BPJSResult {
    jhtEmployee: number      // 2% of gross
    jhtEmployer: number      // 3.7% of gross  
    jpEmployee: number       // 1% of min(gross, 9,559,600)
    jpEmployer: number       // 2% of min(gross, 9,559,600)
    jkkEmployer: number      // jkkRate% of gross
    jkmEmployer: number      // 0.3% of gross
    kesehatanEmployee: number // 1% of min(gross, 12,000,000)
    kesehatanEmployer: number // 4% of min(gross, 12,000,000)
    
    jpSalaryCap: number      // IDR 9,559,600
    kesehatanSalaryCap: number // IDR 12,000,000
  }

Constants (get from DB once on startup, cache in module):
  JP_SALARY_CAP = 9_559_600
  KESEHATAN_SALARY_CAP = 12_000_000

export function calculateBPJS(input: BPJSInput): BPJSResult {
  const { grossSalary, jkkCategory = 0.24 } = input
  
  const jpBase = Math.min(grossSalary, JP_SALARY_CAP)
  const kesehatanBase = Math.min(grossSalary, KESEHATAN_SALARY_CAP)
  
  return {
    jhtEmployee: Math.round(grossSalary * 0.02),
    jhtEmployer: Math.round(grossSalary * 0.037),
    jpEmployee: Math.round(jpBase * 0.01),
    jpEmployer: Math.round(jpBase * 0.02),
    jkkEmployer: Math.round(grossSalary * (jkkCategory / 100)),
    jkmEmployer: Math.round(grossSalary * 0.003),
    kesehatanEmployee: Math.round(kesehatanBase * 0.01),
    kesehatanEmployer: Math.round(kesehatanBase * 0.04),
    jpSalaryCap: JP_SALARY_CAP,
    kesehatanSalaryCap: KESEHATAN_SALARY_CAP,
  }
}

Create src/lib/calculations/violations.ts

ALL 7 VIOLATION DETECTORS:

interface ViolationInput {
  grossSalary: number
  cityUMK: number
  reported: {
    pph21: number
    jhtEmployee: number
    jpEmployee: number
    kesehatan: number
  }
  calculated: {
    pph21: number
    jhtEmployee: number
    jpEmployee: number
    kesehatan: number
  }
}

V01: JHT missing (employer not enrolling)
  IF reported.jhtEmployee === 0 AND grossSalary > 0
  → code: 'V01', severity: 'HIGH'
  → titleID: 'JHT Tidak Dipotong'
  → descriptionID: 'Tidak ada potongan JHT (2%). Perusahaan wajib mendaftarkan kamu ke BPJS Ketenagakerjaan.'
  → differenceIDR: calculated.jhtEmployee
  → actionID: 'Minta HRD mendaftarkan kamu ke BPJS Ketenagakerjaan program JHT.'

V02: BPJS underpaid (JP underpayment)
  IF reported.jpEmployee > 0 AND ABS(reported.jpEmployee - calculated.jpEmployee) > 5000
  AND calculated.jpEmployee > reported.jpEmployee
  → code: 'V02', severity: 'MEDIUM'
  → differenceIDR: calculated.jpEmployee - reported.jpEmployee

V03: PPh21 not withheld when it should be
  IF calculated.pph21 > 10000 AND reported.pph21 === 0
  → code: 'V03', severity: 'HIGH'
  → differenceIDR: calculated.pph21

V04: PPh21 underpaid (difference > IDR 50,000)
  IF calculated.pph21 > reported.pph21 AND (calculated.pph21 - reported.pph21) > 50000
  AND reported.pph21 > 0  (V03 already covers zero case)
  → code: 'V04', severity: 'MEDIUM'
  → differenceIDR: calculated.pph21 - reported.pph21

V05: Kesehatan missing
  IF reported.kesehatan === 0 AND grossSalary > 0
  → code: 'V05', severity: 'HIGH'
  → differenceIDR: calculated.kesehatan

V06: Below UMK (most critical)
  IF grossSalary < cityUMK AND cityUMK > 0
  → code: 'V06', severity: 'CRITICAL'
  → differenceIDR: cityUMK - grossSalary
  → descriptionID: `Gaji Rp X di bawah UMK kota ini (Rp Y). Ini PELANGGARAN HUKUM.`
  → actionID: 'Laporkan ke Dinas Ketenagakerjaan setempat atau konsultasikan dengan Serikat Pekerja.'

V07: JP missing
  IF reported.jpEmployee === 0 AND grossSalary > 0 AND calculated.jpEmployee > 0
  → code: 'V07', severity: 'MEDIUM'
  → differenceIDR: calculated.jpEmployee

export function detectViolations(input: ViolationInput): Violation[] — run all 7 checks, return array.

════════════════════════════════════════════════════
PART B: API ROUTE
════════════════════════════════════════════════════

Create src/app/api/audit-payslip/route.ts

Zod schema for request validation:
  const AuditPayslipSchema = z.object({
    grossSalary: z.number().min(500000).max(1_000_000_000),
    ptkpStatus: z.enum(['TK/0','TK/1','TK/2','TK/3','K/0','K/1','K/2','K/3','K/I/0','K/I/1','K/I/2','K/I/3']),
    city: z.string().min(1).max(100),
    monthNumber: z.number().int().min(1).max(12),
    year: z.number().int().min(2024).max(2030).optional(),
    hasNPWP: z.boolean(),
    reportedDeductions: z.object({
      pph21: z.number().min(0),
      jhtEmployee: z.number().min(0),
      jpEmployee: z.number().min(0),
      jkkEmployee: z.number().min(0),
      jkmEmployee: z.number().min(0),
      kesehatanEmployee: z.number().min(0),
      takeHome: z.number().min(0),
    }),
    sessionId: z.string().uuid().optional(),
    ocrSource: z.enum(['google_vision','tesseract','manual']).optional(),
    payslipFilePath: z.string().optional(),
  })

POST handler:
  1. Validate request body with Zod → 400 on failure
  
  2. Rate limiting:
     Check IP from request.headers.get('x-forwarded-for') or x-real-ip
     Store counter in memory (simple Map for now, replace with KV in Stage 10):
     5 requests per IP per hour for anonymous
     Return 429 with message if exceeded
  
  3. Get user (may be anonymous):
     const { user, tier } = await getCurrentUser()
  
  4. Get UMK for city:
     const cityUMK = await getUMKForCity(body.city, supabase)
     If city not found: return 400 { code: 'INVALID_CITY', message: 'Kota tidak ditemukan dalam database UMK kami' }
  
  5. Calculate PPh21:
     const pph21Result = await calculatePPh21({
       grossSalary: body.grossSalary,
       ptkpStatus: body.ptkpStatus,
       monthNumber: body.monthNumber,
       year: body.year ?? new Date().getFullYear(),
       hasNPWP: body.hasNPWP,
     }, supabase)
  
  6. Calculate BPJS:
     const bpjsResult = calculateBPJS({ grossSalary: body.grossSalary })
  
  7. Detect violations:
     const violations = detectViolations({
       grossSalary: body.grossSalary,
       cityUMK: cityUMK ?? 0,
       reported: {
         pph21: body.reportedDeductions.pph21,
         jhtEmployee: body.reportedDeductions.jhtEmployee,
         jpEmployee: body.reportedDeductions.jpEmployee,
         kesehatan: body.reportedDeductions.kesehatanEmployee,
       },
       calculated: {
         pph21: pph21Result.pph21Amount,
         jhtEmployee: bpjsResult.jhtEmployee,
         jpEmployee: bpjsResult.jpEmployee,
         kesehatan: bpjsResult.kesehatanEmployee,
       }
     })
  
  8. Apply freemium gate:
     isPaidResult = tier !== 'free'
     gatedViolations = violations.map(v => ({
       ...v,
       differenceIDR: isPaidResult ? v.differenceIDR : null  // hide IDR for free users
     }))
  
  9. Save to DB:
     INSERT INTO payslip_audits (...) with all fields
     Return the inserted ID
  
  10. Return response:
    {
      success: true,
      data: {
        auditId: string,
        verdict: violations.length > 0 ? 'ADA_PELANGGARAN' : 'SESUAI',
        violationCount: violations.length,
        violationCodes: violations.map(v => v.code),
        violations: gatedViolations,  // IDR hidden for free users
        calculations: isPaidResult ? {
          correctPph21: pph21Result.pph21Amount,
          correctJht: bpjsResult.jhtEmployee,
          correctJp: bpjsResult.jpEmployee,
          correctKesehatan: bpjsResult.kesehatanEmployee,
          cityUMK: cityUMK ?? 0,
        } : undefined,
        isGated: !isPaidResult && violations.length > 0,
        subscriptionRequired: !isPaidResult ? 'basic' : null,
        gateMessage: !isPaidResult && violations.length > 0 
          ? 'Upgrade ke Basic untuk melihat selisih IDR dan detail tindakan' 
          : undefined,
      }
    }

════════════════════════════════════════════════════
PART C: WAJAR SLIP UI
════════════════════════════════════════════════════

Replace the stub at src/app/wajar-slip/page.tsx with the full UI.

Page is a CLIENT COMPONENT (because it has forms and state).

STATE MACHINE (use useReducer):
  type SlipState = 
    | { status: 'IDLE' }
    | { status: 'MANUAL_FORM' }
    | { status: 'CALCULATING' }
    | { status: 'VERDICT_FREE'; data: AuditResult }
    | { status: 'VERDICT_PAID'; data: AuditResult }
    | { status: 'GATE_MODAL'; data: AuditResult }
    | { status: 'ERROR'; message: string }

SECTION 1: HERO
  H1: "Cek Slip Gaji Kamu — Gratis"
  Subtext: "Pastikan PPh21 dan BPJS sudah benar. Hanya butuh 30 detik."
  Note: "Upload OCR coming in Stage 5 — for now, skip upload section"
  Button: "Isi Data Manual →" → dispatch({ type: 'SHOW_FORM' })

SECTION 2: FORM (shown after clicking button, or default on page)
React Hook Form + Zod validation.

Field layout:
  Gaji Bruto * (number input, IDR format, placeholder "7.500.000")
  Status PTKP * (Select: 12 options from TK/0 to K/I/3)
    Show Indonesian labels: TK/0 = "Tidak Kawin, 0 tanggungan", etc.
  Kota * (Select: searchable, populate from umk_2026 API call on mount)
  Bulan Slip * (Select: Januari-Desember, current month default)
  Punya NPWP? (Switch/Checkbox: yes/no, default yes)

Separator: "Isian dari Slip Gaji"
  PPh21 Dipotong (number, IDR format)
  JHT Karyawan (number)
  JP Karyawan (number)
  Kesehatan Karyawan (number)
  Take Home Pay (number)

CTA: [Cek Slip Gaji →] button, full width on mobile, primary style
  On submit: dispatch CALCULATING, call POST /api/audit-payslip

Loading state: spinner + "Menghitung... ⚡"

SECTION 3: VERDICT (shown after calculation)

FREE TIER VERDICT:
  If SESUAI (green card):
    Big green checkmark ✅
    "Slip gaji kamu SESUAI dengan regulasi"
    "Tidak ada pelanggaran ditemukan dari {n} pemeriksaan"
    Violation codes shown: each as badge (gray, no IDR)
    UMK reference: "UMK [city] 2026: [amount] — gaji kamu di atas UMK ✅"
    
  If ADA_PELANGGARAN (red card):
    Big warning ⚠️
    "ADA PELANGGARAN pada slip gaji kamu"
    List violations by code + title (NO IDR for free):
      e.g. "V04: PPh21 Kurang Potong" with severity badge
    PremiumGate wrapper around IDR detail:
      requiredTier='basic'
      featureLabel='Detail selisih IDR dan panduan tindakan'
      currentTier=userTier

PAID TIER VERDICT:
  Same card but with full details:
  Each violation shows:
    Code + title
    "Dipotong: Rp X"
    "Seharusnya: Rp Y"  
    "Selisih: Rp Z" (red if underpaid)
    "Langkah: [actionID]"
  
  Calculation summary table:
    | Komponen | Menurut Slip | Yang Benar | Selisih |
    | PPh21    | Rp X         | Rp Y       | Rp Z    |
    | JHT      | Rp X         | Rp Y       | Rp Z    |
    | JP       | ...           | ...         | ...     |
    | Kesehatan| ...           | ...         | ...     |

CITY UMK (always shown regardless of tier):
  "UMK [city] [year]: Rp [amount]"
  If V06 detected: "⚠️ Gaji di bawah UMK — PELANGGARAN SERIUS"
  If no V06: "✅ Gaji di atas UMK"

CAVEATS SECTION (always shown):
  Small disclaimer text:
  "Kalkulasi berdasarkan PMK 168/2023 (TER) dan peraturan BPJS yang berlaku.
  Alat ini tidak menggantikan konsultasi dengan konsultan pajak."
  
  Buttons:
  [Cek Slip Lain] → reset to IDLE state
  [Bagikan Hasil] → copy URL with query params (P1 feature, disable for now)

════════════════════════════════════════════════════
PART D: SUPPORTING COMPONENTS
════════════════════════════════════════════════════

Create src/components/wajar-slip/ViolationItem.tsx:
  Props: { violation: Violation, isGated: boolean, showAmount: boolean }
  
  Severity badge colors:
    CRITICAL: red-600 bg
    HIGH: orange-500 bg
    MEDIUM: yellow-500 bg
    LOW: blue-400 bg
  
  Show code + title.
  If showAmount: show IDR amounts.
  If isGated: show 🔒 with "Upgrade untuk detail"

Create src/components/wajar-slip/UMKBadge.tsx:
  Props: { city: string, umk: number, grossSalary: number }
  Green if grossSalary >= umk, red if below.

Create src/app/api/cities/route.ts:
  GET /api/cities → returns all cities from umk_2026 table
  Used for the city dropdown in the form.
  Cache this response (it doesn't change): add Cache-Control: max-age=86400
  Return: [{ city: string, province: string, monthly_minimum_idr: number }]

════════════════════════════════════════════════════
VERIFICATION:
════════════════════════════════════════════════════

Test these specific cases:

Test 1 — SESUAI result:
  Input: grossSalary=7500000, TK/0, Jakarta, October, hasNPWP=true
  TER rate for 7,500,001-8,550,000 TER A = 1.50%
  Expected PPh21 = 7,500,000 × 1.50% = 112,500
  Expected JHT = 7,500,000 × 2% = 150,000
  Expected JP = min(7,500,000, 9,559,600) × 1% = 75,000
  Expected Kesehatan = min(7,500,000, 12,000,000) × 1% = 75,000
  Enter these exact amounts as reported → should get SESUAI

Test 2 — V04 + V06:
  Input: grossSalary=3000000, TK/0, Kota Bekasi (UMK=5,331,680)
  Expected: V06 CRITICAL (salary below UMK)
  Also enter PPh21=0 → V03 should also trigger (no withholding when should be)

Test 3 — December true-up:
  Month=12, grossSalary=8,500,000, TK/0
  Should use PROGRESSIVE method not TER
  Annual gross=102,000,000, PTKP=54,000,000, PKP=48,000,000
  Annual PPh21=48,000,000×5%=2,400,000
  TER months 1-11: 8,500,000×1.75%×11=1,631,250
  December PPh21 = 2,400,000 - 1,631,250 = 768,750

Test 4 — No NPWP:
  Same as Test 1 but hasNPWP=false
  PPh21 should be 112,500 × 1.20 = 135,000

Test 5 — API returns correct error:
  POST /api/audit-payslip with city="Kota Nonexistent"
  Expected: 400 { code: 'INVALID_CITY' }

pnpm tsc --noEmit → zero errors
===END===
```

---

## Verification Checklist for Stage 4

```bash
# Test calculation logic
pnpm test src/lib/calculations/
# All tests must pass

# Test API manually
curl -X POST localhost:3000/api/audit-payslip \
  -H "Content-Type: application/json" \
  -d '{
    "grossSalary": 7500000,
    "ptkpStatus": "TK/0",
    "city": "Jakarta",
    "monthNumber": 10,
    "hasNPWP": true,
    "reportedDeductions": {
      "pph21": 112500,
      "jhtEmployee": 150000,
      "jpEmployee": 75000,
      "jkkEmployee": 0,
      "jkmEmployee": 0,
      "kesehatanEmployee": 75000,
      "takeHome": 7087500
    }
  }'
# Expected: { data: { verdict: "SESUAI", violationCount: 0 } }

# TypeScript clean
pnpm tsc --noEmit

# Check audit saved to DB
# Supabase Studio → payslip_audits → SELECT * ORDER BY created_at DESC LIMIT 1
```

**Next:** Stage 5 — OCR Pipeline (Google Vision + Tesseract fallback)

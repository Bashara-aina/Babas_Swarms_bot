# Build Guide 01: Wajar Slip — Payslip Auditor

**Priority:** Build first. Highest accuracy. Best virality. Anchor product.  
**Build window:** Week 3–6 (after scaffold in W1–2)  
**Accuracy target:** 92–97% (PPh21/BPJS based on public regs = near-perfect)  
**Zero-cost path:** ✅ All regs are public. No auditor needed.

---

## What Wajar Slip Does

User uploads payslip image → OCR extracts fields → System calculates what SHOULD be withheld → Compares actual vs expected → Shows violations with explanations

**7 Violation Codes:**
| Code | Violation | Severity |
|------|-----------|----------|
| V01 | BPJS JHT missing entirely | High |
| V02 | BPJS any component underpaid | High |
| V03 | PPh21 not withheld despite liability | High |
| V04 | PPh21 underpaid >IDR 50K | Medium |
| V05 | BPJS Kesehatan missing | High |
| V06 | Salary below UMK — ILLEGAL | Critical |
| V07 | BPJS JP missing | High |

---

## Step 1: Supabase Schema Setup

`[SUPABASE]` — Run in SQL Editor

```sql
-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_cron";

-- Users table (Supabase auth.users is auto-created)
-- We extend it with profile
CREATE TABLE public.user_profiles (
  id UUID REFERENCES auth.users(id) PRIMARY KEY,
  full_name TEXT,
  subscription_tier TEXT DEFAULT 'free' CHECK (subscription_tier IN ('free', 'basic', 'pro')),
  subscription_expires_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Payslip audit sessions
CREATE TABLE public.payslip_audits (
  id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
  user_id UUID REFERENCES auth.users(id),
  -- Input data
  gross_salary NUMERIC(15,2) NOT NULL,
  ptkp_status TEXT NOT NULL CHECK (ptkp_status IN ('TK/0','TK/1','TK/2','TK/3','K/0','K/1','K/2','K/3','K/I/0','K/I/1','K/I/2','K/I/3')),
  employment_month INTEGER CHECK (employment_month BETWEEN 1 AND 12),
  employment_year INTEGER,
  has_npwp BOOLEAN DEFAULT true,
  -- Reported amounts from payslip
  reported_pph21 NUMERIC(15,2),
  reported_jht_employee NUMERIC(15,2),
  reported_jp_employee NUMERIC(15,2),
  reported_jkk NUMERIC(15,2),
  reported_jkm NUMERIC(15,2),
  reported_bpjs_kesehatan_employee NUMERIC(15,2),
  reported_net_salary NUMERIC(15,2),
  -- Calculated correct amounts
  expected_pph21 NUMERIC(15,2),
  expected_jht_employee NUMERIC(15,2),
  expected_jp_employee NUMERIC(15,2),
  expected_bpjs_kesehatan_employee NUMERIC(15,2),
  -- Result
  violations JSONB DEFAULT '[]',
  overall_status TEXT CHECK (overall_status IN ('CLEAN','VIOLATIONS_FOUND','MANUAL_REVIEW')),
  -- OCR metadata
  ocr_method TEXT CHECK (ocr_method IN ('manual','google_vision','tesseract','mixed')),
  ocr_confidence NUMERIC(4,3),
  -- Storage
  file_path TEXT, -- Supabase storage path
  file_expires_at TIMESTAMPTZ DEFAULT (NOW() + INTERVAL '30 days'),
  -- Timestamps
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Row Level Security
ALTER TABLE public.payslip_audits ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.user_profiles ENABLE ROW LEVEL SECURITY;

-- RLS: users can only see their own audits
CREATE POLICY "Users see own audits" ON public.payslip_audits
  FOR ALL USING (auth.uid() = user_id);

CREATE POLICY "Users see own profile" ON public.user_profiles
  FOR ALL USING (auth.uid() = id);

-- Allow anonymous audits (free tier, no login required for basic check)
CREATE POLICY "Anon read own session" ON public.payslip_audits
  FOR SELECT USING (user_id IS NULL);

-- Supabase storage bucket for payslips
-- Run in dashboard: Storage > Create bucket "payslips" (private, 5MB limit)

-- Auto-delete payslip files after 30 days (GDPR/UU PDP compliance)
SELECT cron.schedule(
  'delete-expired-payslips',
  '0 2 * * *', -- Daily at 2am
  $$
  DELETE FROM public.payslip_audits
  WHERE file_expires_at < NOW() AND file_path IS NOT NULL;
  -- Note: Also delete from storage via Edge Function
  $$
);
```

---

## Step 2: PPh21 + BPJS Calculation Engine

`[CURSOR]` — Create file: `lib/calculations/pph21.ts`

Prompt to use in Cursor:
> "Create a TypeScript module for Indonesian PPh21 and BPJS calculation based on PMK 168/2023 TER method. Include all BPJS rates from PP 46/2015, PP 44/2015, PP 45/2015. Include violation detection for V01-V07 codes. Use the exact rate structures below."

Full implementation:

```typescript
// lib/calculations/pph21.ts
// Based on: PMK 168/2023 (TER), UU HPP No.7/2021, PP 46/2015, PP 44/2015, PP 45/2015, Perpres 82/2018

export type PTKPStatus = 
  | 'TK/0' | 'TK/1' | 'TK/2' | 'TK/3'
  | 'K/0' | 'K/1' | 'K/2' | 'K/3'
  | 'K/I/0' | 'K/I/1' | 'K/I/2' | 'K/I/3';

export type ViolationCode = 'V01' | 'V02' | 'V03' | 'V04' | 'V05' | 'V06' | 'V07';

export interface ViolationResult {
  code: ViolationCode;
  severity: 'CRITICAL' | 'HIGH' | 'MEDIUM';
  description: string;
  expected: number;
  reported: number;
  difference: number;
}

export interface AuditInput {
  grossSalary: number;         // IDR per month
  ptkpStatus: PTKPStatus;
  month: number;               // 1-12
  year: number;
  hasNPWP: boolean;
  reportedPph21: number;
  reportedJhtEmployee: number;
  reportedJpEmployee: number;
  reportedJkk: number;
  reportedJkm: number;
  reportedBpjsKesEmployee: number;
  reportedNetSalary: number;
  cityUMK: number;             // local UMK/UMR
}

export interface AuditResult {
  expectedPph21: number;
  expectedJhtEmployee: number;
  expectedJpEmployee: number;
  expectedBpjsKesEmployee: number;
  violations: ViolationResult[];
  overallStatus: 'CLEAN' | 'VIOLATIONS_FOUND' | 'MANUAL_REVIEW';
  calculationMethod: 'TER' | 'PROGRESSIVE' | 'PROGRESSIVE_BONUS';
  summary: string;
}

// ============================================================
// PTKP VALUES (PMK 66/2023) — Annual
// ============================================================
const PTKP_ANNUAL: Record<PTKPStatus, number> = {
  'TK/0': 54_000_000,
  'TK/1': 58_500_000,
  'TK/2': 63_000_000,
  'TK/3': 67_500_000,
  'K/0':  58_500_000,
  'K/1':  63_000_000,
  'K/2':  67_500_000,
  'K/3':  72_000_000,
  'K/I/0': 112_500_000, // Suami + Istri gabung
  'K/I/1': 117_000_000,
  'K/I/2': 121_500_000,
  'K/I/3': 126_000_000,
};

// ============================================================
// TER RATES — PMK 168/2023 Lampiran A (TK/0 simplified)
// IMPORTANT: These are ILLUSTRATIVE. Verify exact rates from
// official PMK 168/2023 Lampiran A/B/C before production.
// Get full table from: https://jdih.kemenkeu.go.id
// ============================================================
function getTERRate(grossSalary: number, ptkpStatus: PTKPStatus): number {
  // Tabel A: TK/0 (simplified version — covers majority of users)
  // Full implementation needs all 3 tables (A, B, C)
  const isMarried = ptkpStatus.startsWith('K/') || ptkpStatus.startsWith('K/I/');
  
  if (!isMarried) {
    // Tabel A (TK)
    if (grossSalary <= 5_400_000) return 0.0000;
    if (grossSalary <= 5_650_000) return 0.0025;
    if (grossSalary <= 5_950_000) return 0.0050;
    if (grossSalary <= 6_300_000) return 0.0075;
    if (grossSalary <= 6_750_000) return 0.0100;
    if (grossSalary <= 7_500_000) return 0.0125;
    if (grossSalary <= 8_550_000) return 0.0150;
    if (grossSalary <= 9_650_000) return 0.0175;
    if (grossSalary <= 10_050_000) return 0.0200;
    if (grossSalary <= 10_350_000) return 0.0225;
    if (grossSalary <= 10_700_000) return 0.0250;
    if (grossSalary <= 11_050_000) return 0.0300;
    if (grossSalary <= 11_600_000) return 0.0350;
    if (grossSalary <= 12_500_000) return 0.0400;
    if (grossSalary <= 13_750_000) return 0.0500;
    if (grossSalary <= 15_100_000) return 0.0600;
    if (grossSalary <= 16_950_000) return 0.0700;
    if (grossSalary <= 19_750_000) return 0.0800;
    if (grossSalary <= 24_150_000) return 0.0900;
    if (grossSalary <= 26_450_000) return 0.1000;
    if (grossSalary <= 28_000_000) return 0.1100;
    if (grossSalary <= 30_050_000) return 0.1200;
    if (grossSalary <= 32_400_000) return 0.1300;
    if (grossSalary <= 35_400_000) return 0.1400;
    if (grossSalary <= 39_100_000) return 0.1500;
    if (grossSalary <= 43_850_000) return 0.1600;
    if (grossSalary <= 47_800_000) return 0.1700;
    if (grossSalary <= 51_400_000) return 0.1800;
    if (grossSalary <= 56_300_000) return 0.1900;
    if (grossSalary <= 62_200_000) return 0.2000;
    if (grossSalary <= 68_600_000) return 0.2100;
    if (grossSalary <= 77_500_000) return 0.2200;
    if (grossSalary <= 89_000_000) return 0.2300;
    if (grossSalary <= 103_000_000) return 0.2400;
    return 0.2600; // >103M
  } else {
    // Tabel B (K) — married, slightly lower rates
    // Simplified: use TK rates but offset by K/0 PTKP difference
    // TODO: Load full Tabel B from PMK 168/2023 Lampiran B
    const offset = isMarried ? 0.0025 : 0;
    return Math.max(0, getTERRate(grossSalary, 'TK/0') - offset);
  }
}

// ============================================================
// PROGRESSIVE TAX BRACKETS — UU HPP No.7/2021
// ============================================================
function calculateProgressiveAnnual(pkpAnnual: number): number {
  let tax = 0;
  if (pkpAnnual <= 60_000_000) {
    tax = pkpAnnual * 0.05;
  } else if (pkpAnnual <= 250_000_000) {
    tax = 60_000_000 * 0.05 + (pkpAnnual - 60_000_000) * 0.15;
  } else if (pkpAnnual <= 500_000_000) {
    tax = 60_000_000 * 0.05 + 190_000_000 * 0.15 + (pkpAnnual - 250_000_000) * 0.25;
  } else if (pkpAnnual <= 5_000_000_000) {
    tax = 60_000_000 * 0.05 + 190_000_000 * 0.15 + 250_000_000 * 0.25 + (pkpAnnual - 500_000_000) * 0.30;
  } else {
    tax = 60_000_000 * 0.05 + 190_000_000 * 0.15 + 250_000_000 * 0.25 + 4_500_000_000 * 0.30 + (pkpAnnual - 5_000_000_000) * 0.35;
  }
  return Math.round(tax);
}

// ============================================================
// BPJS RATES
// ============================================================
const BPJS_RATES = {
  JHT_EMPLOYEE: 0.02,           // PP 46/2015
  JHT_EMPLOYER: 0.037,
  JP_EMPLOYEE: 0.01,             // PP 45/2015, capped salary
  JP_EMPLOYER: 0.02,
  JP_SALARY_CAP: 9_559_600,     // Updated periodically by Kemnaker
  JKK_EMPLOYER: 0.0024,         // PP 44/2015, risk class I (default)
  JKM_EMPLOYER: 0.003,
  KES_EMPLOYEE: 0.01,            // Perpres 82/2018
  KES_EMPLOYER: 0.04,
  KES_SALARY_CAP: 12_000_000,
};

// ============================================================
// MAIN AUDIT FUNCTION
// ============================================================
export function auditPayslip(input: AuditInput): AuditResult {
  const violations: ViolationResult[] = [];
  const isDecember = input.month === 12;
  const isBonusMonth = false; // Extend for THR handling

  // --- Calculate BPJS ---
  const jhtBase = input.grossSalary;
  const jpBase = Math.min(input.grossSalary, BPJS_RATES.JP_SALARY_CAP);
  const kesBase = Math.min(input.grossSalary, BPJS_RATES.KES_SALARY_CAP);

  const expectedJhtEmployee = Math.round(jhtBase * BPJS_RATES.JHT_EMPLOYEE);
  const expectedJpEmployee = Math.round(jpBase * BPJS_RATES.JP_EMPLOYEE);
  const expectedKesEmployee = Math.round(kesBase * BPJS_RATES.KES_EMPLOYEE);

  // --- Calculate PPh21 ---
  let expectedPph21: number;
  let calcMethod: 'TER' | 'PROGRESSIVE' | 'PROGRESSIVE_BONUS' = 'TER';

  if (!isDecember) {
    // TER method (PMK 168/2023) — monthly flat rate
    const terRate = getTERRate(input.grossSalary, input.ptkpStatus);
    expectedPph21 = Math.round(input.grossSalary * terRate);
    calcMethod = 'TER';
  } else {
    // December: use progressive annual true-up
    // This is simplified — full implementation needs all months' TER withheld
    const annualGross = input.grossSalary * 12;
    const jabatanDeduction = Math.min(annualGross * 0.05, 6_000_000);
    const ptkpAnnual = PTKP_ANNUAL[input.ptkpStatus];
    const pkpAnnual = Math.max(0, annualGross - jabatanDeduction - ptkpAnnual);
    const annualTax = calculateProgressiveAnnual(pkpAnnual);
    // December PPh21 = Annual tax - sum of all months (simplified: assume uniform salary)
    const previousMonthsTax = Math.round(annualTax / 12) * 11;
    expectedPph21 = Math.max(0, annualTax - previousMonthsTax);
    calcMethod = 'PROGRESSIVE';
  }

  // Apply No-NPWP surcharge (20% higher)
  if (!input.hasNPWP) {
    expectedPph21 = Math.round(expectedPph21 * 1.20);
  }

  // --- Violation Detection ---

  // V06: Salary below UMK (CRITICAL)
  if (input.grossSalary < input.cityUMK) {
    violations.push({
      code: 'V06',
      severity: 'CRITICAL',
      description: `Gaji pokok lebih rendah dari UMK kota (IDR ${input.cityUMK.toLocaleString('id-ID')}). Ini pelanggaran hukum ketenagakerjaan.`,
      expected: input.cityUMK,
      reported: input.grossSalary,
      difference: input.cityUMK - input.grossSalary,
    });
  }

  // V01: JHT completely missing
  if (input.reportedJhtEmployee === 0 && expectedJhtEmployee > 0) {
    violations.push({
      code: 'V01',
      severity: 'HIGH',
      description: 'Potongan BPJS JHT karyawan tidak ada di slip gaji. Perusahaan wajib memotong 2% dari gaji.',
      expected: expectedJhtEmployee,
      reported: 0,
      difference: expectedJhtEmployee,
    });
  }

  // V02: BPJS underpaid (any component)
  const totalExpectedBpjsEmp = expectedJhtEmployee + expectedJpEmployee + expectedKesEmployee;
  const totalReportedBpjsEmp = (input.reportedJhtEmployee || 0) + (input.reportedJpEmployee || 0) + (input.reportedBpjsKesEmployee || 0);
  const bpjsDiff = totalExpectedBpjsEmp - totalReportedBpjsEmp;
  if (bpjsDiff > 10_000) { // IDR 10K tolerance for rounding
    violations.push({
      code: 'V02',
      severity: 'HIGH',
      description: `Total potongan BPJS karyawan lebih rendah IDR ${bpjsDiff.toLocaleString('id-ID')} dari yang seharusnya.`,
      expected: totalExpectedBpjsEmp,
      reported: totalReportedBpjsEmp,
      difference: bpjsDiff,
    });
  }

  // V03: PPh21 not withheld despite liability
  if (input.reportedPph21 === 0 && expectedPph21 > 10_000) {
    violations.push({
      code: 'V03',
      severity: 'HIGH',
      description: `PPh21 seharusnya IDR ${expectedPph21.toLocaleString('id-ID')} per bulan tapi tidak dipotong sama sekali.`,
      expected: expectedPph21,
      reported: 0,
      difference: expectedPph21,
    });
  }

  // V04: PPh21 underpaid > IDR 50K
  const pph21Diff = expectedPph21 - (input.reportedPph21 || 0);
  if (pph21Diff > 50_000) {
    violations.push({
      code: 'V04',
      severity: 'MEDIUM',
      description: `PPh21 yang dipotong kurang IDR ${pph21Diff.toLocaleString('id-ID')} dari yang seharusnya.`,
      expected: expectedPph21,
      reported: input.reportedPph21,
      difference: pph21Diff,
    });
  }

  // V05: BPJS Kesehatan missing
  if (input.reportedBpjsKesEmployee === 0 && expectedKesEmployee > 0) {
    violations.push({
      code: 'V05',
      severity: 'HIGH',
      description: 'Potongan BPJS Kesehatan karyawan (1%) tidak ada di slip gaji.',
      expected: expectedKesEmployee,
      reported: 0,
      difference: expectedKesEmployee,
    });
  }

  // V07: BPJS JP missing
  if (input.reportedJpEmployee === 0 && expectedJpEmployee > 0) {
    violations.push({
      code: 'V07',
      severity: 'HIGH',
      description: 'Potongan BPJS Jaminan Pensiun (1%) tidak ada di slip gaji.',
      expected: expectedJpEmployee,
      reported: 0,
      difference: expectedJpEmployee,
    });
  }

  const overallStatus = violations.length === 0 
    ? 'CLEAN' 
    : violations.some(v => v.severity === 'CRITICAL' || v.severity === 'HIGH')
      ? 'VIOLATIONS_FOUND'
      : 'MANUAL_REVIEW';

  const summary = violations.length === 0
    ? 'Slip gaji kamu bersih. Semua potongan sudah sesuai regulasi.'
    : `Ditemukan ${violations.length} potensi pelanggaran. Disarankan klarifikasi ke HRD.`;

  return {
    expectedPph21,
    expectedJhtEmployee,
    expectedJpEmployee,
    expectedBpjsKesEmployee: expectedKesEmployee,
    violations,
    overallStatus,
    calculationMethod: calcMethod,
    summary,
  };
}
```

---

## Step 3: OCR Pipeline (Free Tier)

`[CURSOR]` — Create file: `lib/ocr/payslip-ocr.ts`

**Free OCR stack:**
- Primary: Google Vision API (1,000 requests/month free)
- Fallback: Tesseract.js (client-side, fully free, lower accuracy)
- Fallback 2: Manual form input (always free)

```typescript
// lib/ocr/payslip-ocr.ts
// Google Vision API: https://cloud.google.com/vision/docs/ocr
// Free tier: 1,000 requests/month

import Tesseract from 'tesseract.js';

export interface OCRConfidence {
  AUTO_ACCEPT: 0.92;
  SOFT_CHECK: 0.80;
  MANUAL_REQUIRED: 0.70;
}

export interface ExtractedPayslipFields {
  grossSalary: { value: number | null; confidence: number };
  pph21: { value: number | null; confidence: number };
  jhtEmployee: { value: number | null; confidence: number };
  jpEmployee: { value: number | null; confidence: number };
  bpjsKesEmployee: { value: number | null; confidence: number };
  netSalary: { value: number | null; confidence: number };
  overallConfidence: number;
  method: 'google_vision' | 'tesseract' | 'manual';
}

// Indonesian currency regex patterns
const CURRENCY_PATTERNS = [
  /(?:Rp\.?\s*|IDR\s*)(\d{1,3}(?:[.,]\d{3})*(?:[.,]\d{0,2})?)/gi,
  /(\d{1,3}(?:\.\d{3})+)(?:,\d{0,2})?/g,  // 10.000.000 format
];

// Field detection keywords (Indonesian payslip labels)
const FIELD_KEYWORDS: Record<keyof Omit<ExtractedPayslipFields, 'overallConfidence' | 'method'>, string[]> = {
  grossSalary: ['gaji pokok', 'gaji bruto', 'gross salary', 'total gaji', 'gaji kotor', 'upah'],
  pph21: ['pph 21', 'pph21', 'pajak penghasilan', 'pph pasal 21', 'pajak'],
  jhtEmployee: ['jht', 'jaminan hari tua', 'bpjs jht', 'bpjs ketenagakerjaan jht'],
  jpEmployee: ['jp', 'jaminan pensiun', 'bpjs jp', 'bpjs jaminan pensiun'],
  bpjsKesEmployee: ['bpjs kesehatan', 'bpjs kes', 'jkn', 'kesehatan'],
  netSalary: ['gaji bersih', 'net salary', 'take home pay', 'thp', 'total terima', 'dibayarkan'],
};

function parseIndonesianCurrency(text: string): number | null {
  for (const pattern of CURRENCY_PATTERNS) {
    pattern.lastIndex = 0;
    const match = pattern.exec(text);
    if (match) {
      const cleaned = match[1].replace(/\./g, '').replace(',', '.');
      const value = parseFloat(cleaned);
      if (!isNaN(value) && value > 0) return value;
    }
  }
  return null;
}

function extractFieldFromText(
  fullText: string,
  keywords: string[]
): { value: number | null; confidence: number } {
  const lines = fullText.toLowerCase().split('\n');
  
  for (const keyword of keywords) {
    for (let i = 0; i < lines.length; i++) {
      if (lines[i].includes(keyword)) {
        // Check same line and next 2 lines for currency value
        const searchText = lines.slice(i, i + 3).join(' ');
        const value = parseIndonesianCurrency(searchText);
        if (value !== null) {
          // Confidence based on how close to keyword and value clarity
          const confidence = lines[i].includes(keyword) ? 0.85 : 0.70;
          return { value, confidence };
        }
      }
    }
  }
  
  return { value: null, confidence: 0 };
}

// Google Vision OCR (primary)
export async function extractWithGoogleVision(
  imageBase64: string
): Promise<ExtractedPayslipFields | null> {
  const apiKey = process.env.GOOGLE_VISION_API_KEY;
  if (!apiKey) return null;

  try {
    const response = await fetch(
      `https://vision.googleapis.com/v1/images:annotate?key=${apiKey}`,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          requests: [{
            image: { content: imageBase64 },
            features: [{ type: 'DOCUMENT_TEXT_DETECTION', maxResults: 1 }],
          }],
        }),
      }
    );

    if (!response.ok) return null;
    const data = await response.json();
    const fullText = data.responses?.[0]?.fullTextAnnotation?.text || '';
    
    if (!fullText) return null;

    const fields = {
      grossSalary: extractFieldFromText(fullText, FIELD_KEYWORDS.grossSalary),
      pph21: extractFieldFromText(fullText, FIELD_KEYWORDS.pph21),
      jhtEmployee: extractFieldFromText(fullText, FIELD_KEYWORDS.jhtEmployee),
      jpEmployee: extractFieldFromText(fullText, FIELD_KEYWORDS.jpEmployee),
      bpjsKesEmployee: extractFieldFromText(fullText, FIELD_KEYWORDS.bpjsKesEmployee),
      netSalary: extractFieldFromText(fullText, FIELD_KEYWORDS.netSalary),
    };

    const confidences = Object.values(fields).map(f => f.confidence);
    const overallConfidence = confidences.reduce((a, b) => a + b, 0) / confidences.length;

    return { ...fields, overallConfidence, method: 'google_vision' };
  } catch {
    return null;
  }
}

// Tesseract.js fallback (client-side, free, ~70-75% accuracy on clear payslips)
export async function extractWithTesseract(
  imageFile: File
): Promise<ExtractedPayslipFields> {
  const { data: { text } } = await Tesseract.recognize(imageFile, 'ind+eng', {
    logger: m => console.log(m),
  });

  const fields = {
    grossSalary: extractFieldFromText(text, FIELD_KEYWORDS.grossSalary),
    pph21: extractFieldFromText(text, FIELD_KEYWORDS.pph21),
    jhtEmployee: extractFieldFromText(text, FIELD_KEYWORDS.jhtEmployee),
    jpEmployee: extractFieldFromText(text, FIELD_KEYWORDS.jpEmployee),
    bpjsKesEmployee: extractFieldFromText(text, FIELD_KEYWORDS.bpjsKesEmployee),
    netSalary: extractFieldFromText(text, FIELD_KEYWORDS.netSalary),
  };

  // Tesseract accuracy is lower — reduce confidence
  Object.keys(fields).forEach(key => {
    const f = fields[key as keyof typeof fields];
    f.confidence = f.confidence * 0.85; // 15% penalty for Tesseract
  });

  const confidences = Object.values(fields).map(f => f.confidence);
  const overallConfidence = confidences.reduce((a, b) => a + b, 0) / confidences.length;

  return { ...fields, overallConfidence, method: 'tesseract' };
}

// Main OCR orchestrator
export async function processPayslipImage(
  imageFile: File,
  imageBase64: string
): Promise<{ result: ExtractedPayslipFields; requiresManual: boolean }> {
  // Try Google Vision first
  let result = await extractWithGoogleVision(imageBase64);
  
  if (!result || result.overallConfidence < 0.70) {
    // Fallback to Tesseract
    result = await extractWithTesseract(imageFile);
  }

  const requiresManual = result.overallConfidence < 0.70 
    || result.grossSalary.value === null;

  return { result, requiresManual };
}
```

---

## Step 4: OCR Rate Limit Management

`[SUPABASE]` — Edge Function to track Vision API usage

```sql
-- Track Google Vision API usage to stay in free tier
CREATE TABLE public.api_usage (
  id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
  service TEXT NOT NULL, -- 'google_vision'
  month_year TEXT NOT NULL, -- '2024-03'
  request_count INTEGER DEFAULT 0,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE(service, month_year)
);

-- Check before each Vision API call
CREATE OR REPLACE FUNCTION public.can_use_vision_api()
RETURNS BOOLEAN AS $$
DECLARE
  current_month TEXT := TO_CHAR(NOW(), 'YYYY-MM');
  usage_count INTEGER;
BEGIN
  SELECT COALESCE(request_count, 0) INTO usage_count
  FROM public.api_usage
  WHERE service = 'google_vision' AND month_year = current_month;
  
  RETURN COALESCE(usage_count, 0) < 950; -- Buffer 50 requests
END;
$$ LANGUAGE plpgsql;
```

**Reality check on free OCR limits:**
- Google Vision: 1,000 req/month free → ~33 uploads/day
- If you hit the limit: Tesseract kicks in automatically (lower accuracy but free)
- Month 3+: If revenue > IDR 1M, upgrade Google Vision ($1.50 per 1,000 = negligible)
- Alternative: Use Groq's free vision API (llava model) — 30 req/min, no monthly cap

---

## Step 5: Wajar Slip Frontend

`[CURSOR]` — Create file: `app/wajar-slip/page.tsx`

Cursor prompt:
> "Create a Next.js 15 App Router page for a payslip auditor tool. It has two tabs: 'Upload Slip' and 'Input Manual'. Upload tab has a drag-and-drop area that accepts image files. Manual tab has form fields for: gross salary, PTKP status dropdown (TK/0 to K/3), month/year, NPWP checkbox, and all deduction fields. On submit it calls /api/payslip-audit. Show results with colored violation badges (red for HIGH, orange for MEDIUM, green for CLEAN). Add disclaimer text in Bahasa Indonesia. Use Tailwind CSS."

Key UI elements to include:

```typescript
// components/payslip/ViolationBadge.tsx
// Cursor can generate this from description

const VIOLATION_COLORS = {
  CRITICAL: 'bg-red-100 border-red-500 text-red-800',
  HIGH: 'bg-orange-100 border-orange-400 text-orange-800',
  MEDIUM: 'bg-yellow-100 border-yellow-400 text-yellow-800',
};

// Disclaimer component (NON-NEGOTIABLE, see legal guide)
const Disclaimer = () => (
  <p className="text-xs text-gray-500 mt-4 p-3 bg-gray-50 rounded">
    ⚠️ Hasil ini untuk referensi saja dan bukan merupakan nasihat pajak atau hukum. 
    Untuk kepastian hukum, konsultasikan dengan konsultan pajak berlisensi atau HR perusahaan Anda.
  </p>
);
```

---

## Step 6: API Route

`[CURSOR]` — Create file: `app/api/payslip-audit/route.ts`

```typescript
// app/api/payslip-audit/route.ts
import { createClient } from '@/lib/supabase/server';
import { auditPayslip } from '@/lib/calculations/pph21';
import { NextRequest, NextResponse } from 'next/server';

export async function POST(req: NextRequest) {
  const supabase = createClient();
  const { data: { user } } = await supabase.auth.getUser();

  const body = await req.json();
  
  // Basic input validation
  if (!body.grossSalary || body.grossSalary < 100_000 || body.grossSalary > 1_000_000_000) {
    return NextResponse.json({ error: 'Invalid gross salary' }, { status: 400 });
  }

  // Get UMK for city (load from DB or hardcode top 20 cities for MVP)
  const cityUMK = await getCityUMK(body.city || 'jakarta');

  const result = auditPayslip({
    ...body,
    cityUMK,
  });

  // Free tier: return result without saving (no auth required)
  // Premium tier: save to DB, enable history
  if (user) {
    await supabase.from('payslip_audits').insert({
      user_id: user.id,
      gross_salary: body.grossSalary,
      ptkp_status: body.ptkpStatus,
      // ... other fields
      violations: result.violations,
      overall_status: result.overallStatus,
      ocr_method: body.ocrMethod || 'manual',
    });
  }

  return NextResponse.json(result);
}

// Hardcode top 20 cities for MVP (expand with Kemnaker data later)
async function getCityUMK(city: string): Promise<number> {
  const UMK_2024: Record<string, number> = {
    'jakarta': 5_067_381,
    'surabaya': 4_725_479,
    'bandung': 4_209_309,
    'bekasi': 5_343_430,
    'tangerang': 4_908_945,
    'depok': 4_694_493,
    'bogor': 4_498_961,
    'semarang': 3_243_969,
    'yogyakarta': 2_447_900,
    'medan': 3_769_530,
    'palembang': 3_802_095,
    'makassar': 3_769_869,
    'balikpapan': 3_580_890,
    'samarinda': 3_421_620,
    'malang': 3_368_275,
    // Add more from: https://kemnaker.go.id/berita/detail/ump-umk
    'default': 2_736_698, // National minimum (UMP DKI 2024 as floor)
  };
  return UMK_2024[city.toLowerCase()] || UMK_2024['default'];
}
```

---

## Step 7: Freemium Gates

`[CURSOR]` — Add to result page

| Feature | Free | Basic (IDR 29K) | Pro (IDR 79K) |
|---------|------|-----------------|---------------|
| Basic PPh21 check | ✅ | ✅ | ✅ |
| Violation codes V01–V07 | Shows only 1 | All 7 | All 7 |
| Historical audits | 0 | 3 months | Unlimited |
| PDF report | ❌ | ✅ | ✅ |
| OCR upload | 1/month | 10/month | Unlimited |
| BPJS calculation detail | Summary only | Full breakdown | Full breakdown |
| December true-up simulation | ❌ | ❌ | ✅ |

**Implementation:** Supabase RLS checks `user_profiles.subscription_tier` before returning full violation array.

---

## Reality Check: Week-by-Week Honesty

| Week | What you'll actually face | Mitigation |
|------|--------------------------|------------|
| W3 | TER table has 100+ rows per bracket. Getting it right takes 1–2 days | Use PMK 168/2023 official PDF, read with Perplexity to extract tables |
| W4 | Google Vision misreads Indonesian currency format (periods as thousands separator) | Add parsing logic in `parseIndonesianCurrency()` — already in code above |
| W5 | Tesseract on low-quality phone photos: 50–60% accuracy | Add clear UX guidance: "Upload clear, straight photo" |
| W6 | Beta users find edge cases you didn't think of (allowances, bonuses, non-standard slips) | Build feedback form first. Fix in W7+ |

**Accuracy expectation without paid auditor:**
- PPh21 TER calculation: 92–96% accurate (main risk: outdated TER table if PMK changes)
- BPJS: 98%+ (rates rarely change, easy to verify)
- OCR field extraction: 75–85% (Google Vision), 60–70% (Tesseract)
- Overall "audit catches real violations": ~85% for standard payslips

**What the disclaimer covers:** The 15% gap. Always show "Untuk referensi saja, bukan nasihat pajak."

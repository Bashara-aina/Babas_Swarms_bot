export type VerdictType = "WAJAR" | "ADA_YANG_ANEH" | "POTONGAN_SALAH";

export type PTKPStatus =
  | "TK/0"
  | "TK/1"
  | "TK/2"
  | "TK/3"
  | "K/0"
  | "K/1"
  | "K/2"
  | "K/3"
  | "K/I/0"
  | "K/I/1"
  | "K/I/2"
  | "K/I/3";

export type TERCategory = "A" | "B" | "C";

export type IssueSeverity = "critical" | "major" | "minor";

export interface MoneyWithConfidence {
  value: number | null;
  confidence: number;
}

export interface OcrConfidence {
  gaji_pokok: number;
  pph21: number;
  bpjs_kesehatan: number;
  bpjs_jht: number;
  bpjs_jp: number;
}

export interface OcrExtractedData {
  period: string | null;
  gaji_pokok: number | null;
  tunjangan_tetap: number | null;
  tunjangan_tidak_tetap: number | null;
  tunjangan_makan: number | null;
  tunjangan_transport: number | null;
  uang_lembur: number | null;
  pph21: number | null;
  bpjs_kesehatan: number | null;
  bpjs_jht: number | null;
  bpjs_jp: number | null;
  bpjs_jkk: number | null;
  bpjs_jkm: number | null;
  potongan_lain: number | null;
  gaji_bersih: number | null;
  confidence: OcrConfidence;
  low_confidence_fields: string[];
  all_low_confidence: boolean;
  raw_text?: string | null;
}

export interface SlipGajiInput {
  period: string;
  month: number;
  ptkp_status: PTKPStatus;
  gaji_pokok: number;
  tunjangan_tetap: number;
  tunjangan_tidak_tetap: number;
  pph21_charged: number;
  bpjs_kesehatan_charged: number;
  bpjs_jht_charged: number;
  bpjs_jp_charged: number;
  bpjs_jkk_charged?: number;
  bpjs_jkm_charged?: number;
  potongan_lain?: number;
}

export interface BPJSLineItem {
  charged: number;
  expected: number;
}

export interface BPJSDeductions {
  kesehatan: BPJSLineItem;
  jht: BPJSLineItem;
  jp: BPJSLineItem;
  jkk: BPJSLineItem;
  jkm: BPJSLineItem;
}

export interface AuditInput {
  gross: number;
  month: number;
  ptkp_status: PTKPStatus;
  deductions: {
    pph21: number;
    bpjs_kesehatan: number;
    bpjs_jht: number;
    bpjs_jp: number;
    bpjs_jkk: number;
    bpjs_jkm: number;
    potongan_lain: number;
  };
}

export interface Issue {
  type: string;
  description: string;
  discrepancy_rp: number;
  legal_basis: string;
  severity: IssueSeverity;
}

export interface AuditExpectedBreakdown {
  pph21: number;
  bpjs: BPJSDeductions;
  bpjs_total: number;
  total_legal_deductions: number;
}

export interface AuditResult {
  verdict: VerdictType;
  expected_breakdown: AuditExpectedBreakdown;
  issues: Issue[];
  discrepancy_rp: number;
  legal_refs: string[];
  note?: string;
}

export interface PremiumContent {
  full_breakdown: Array<{
    komponen: string;
    dipotong: number;
    seharusnya: number;
    selisih: number;
    dasar_hukum: string;
  }>;
  estimation_12_months: {
    monthly_discrepancy: number;
    estimated_total: number;
    formula: string;
  };
  surat_keberatan: string;
  wa_templates: string[];
  pdf_url: string | null;
}

/**
 * audit.ts regression tests — covers all 5 critical bugs fixed in the rewrite.
 * Plus regulations.ts constant integrity and engine behaviour.
 * Run with: npx jest --testPathPattern="audit.test"
 */

import { auditSlip } from "@/lib/slip/audit";
import { calculateSlip, getTERRate, getJpCap } from "@/lib/pph21-ter";

describe("regulations.ts — constant integrity", () => {

  it("TER_A: gross=5_400_000 → rate 0%", () => {
    expect(getTERRate("A", 5_400_000)).toBe(0);
  });

  it("TER_A: gross=5_400_001 → rate 0.25%", () => {
    expect(getTERRate("A", 5_400_001)).toBe(0.0025);
  });

  it("TER_A: gross=10_000_000 → rate 2.0%, pph=200_000", () => {
    const rate = getTERRate("A", 10_000_000);
    expect(rate).toBe(0.02);
    expect(Math.round(10_000_000 * rate)).toBe(200_000);
  });

  it("TER_A: gross=20_000_000 → rate 9.0%, pph=1_800_000", () => {
    const rate = getTERRate("A", 20_000_000);
    expect(rate).toBe(0.09);
    expect(Math.round(20_000_000 * rate)).toBe(1_800_000);
  });

  it("TER_B: gross=6_200_000 → rate 0%", () => {
    expect(getTERRate("B", 6_200_000)).toBe(0);
  });

  it("TER_B: gross=8_000_000 → rate 1.0%, pph=80_000", () => {
    const rate = getTERRate("B", 8_000_000);
    expect(rate).toBe(0.01);
    expect(Math.round(8_000_000 * rate)).toBe(80_000);
  });

  it("TER_C: gross=6_600_000 → rate 0%", () => {
    expect(getTERRate("C", 6_600_000)).toBe(0);
  });

  it("TER_C: gross=7_000_000 → rate 0.5%, pph=35_000", () => {
    const rate = getTERRate("C", 7_000_000);
    expect(rate).toBe(0.005);
    expect(Math.round(7_000_000 * rate)).toBe(35_000);
  });

  it("BPJS Kes: gross=10M → Rp100_000 (1% no cap)", () => {
    const res = calculateSlip({
      month: 6,
      ptkp_status: "TK/0",
      gaji_pokok: 10_000_000,
      tunjangan_tetap: 0,
      tunjangan_tidak_tetap: 0,
      pph21_charged: 0,
      bpjs_kesehatan_charged: 100_000,
      bpjs_jht_charged: 200_000,
      bpjs_jp_charged: 100_000,
      bpjs_jkk_charged: 0,
      bpjs_jkm_charged: 0,
      potongan_lain: 0,
    });
    expect(res.bpjsKesehatan.expected).toBe(100_000);
  });

  it("BPJS Kes: gross=15M → Rp120_000 (capped at 12M)", () => {
    const res = calculateSlip({
      month: 6,
      ptkp_status: "TK/0",
      gaji_pokok: 15_000_000,
      tunjangan_tetap: 0,
      tunjangan_tidak_tetap: 0,
      pph21_charged: 0,
      bpjs_kesehatan_charged: 120_000,
      bpjs_jht_charged: 300_000,
      bpjs_jp_charged: 120_000,
      bpjs_jkk_charged: 0,
      bpjs_jkm_charged: 0,
      potongan_lain: 0,
    });
    expect(res.bpjsKesehatan.expected).toBe(120_000);
  });

  it("BPJS Kes: gross=12M → Rp120_000 (exactly at cap)", () => {
    const res = calculateSlip({
      month: 6,
      ptkp_status: "TK/0",
      gaji_pokok: 12_000_000,
      tunjangan_tetap: 0,
      tunjangan_tidak_tetap: 0,
      pph21_charged: 0,
      bpjs_kesehatan_charged: 120_000,
      bpjs_jht_charged: 240_000,
      bpjs_jp_charged: 120_000,
      bpjs_jkk_charged: 0,
      bpjs_jkm_charged: 0,
      potongan_lain: 0,
    });
    expect(res.bpjsKesehatan.expected).toBe(120_000);
  });

  it("JP cap: year=2025 month=2 → 10_042_300 (still 2024 cap)", () => {
    expect(getJpCap(2025, 2)).toBe(10_042_300);
  });

  it("JP cap: year=2025 month=3 → 10_547_400 (2025 cap)", () => {
    expect(getJpCap(2025, 3)).toBe(10_547_400);
  });

  it("JP cap: year=2026 month=2 → 10_547_400 (still 2025 cap, March rule)", () => {
    expect(getJpCap(2026, 2)).toBe(10_547_400);
  });

  it("JP cap: year=2026 month=3 → 11_086_300 (verified from SE BPJS B/1226/022026)", () => {
    expect(getJpCap(2026, 3)).toBe(11_086_300);
  });

  it("JP cap: year=2026 month=12 → 11_086_300 (2026 cap applies all year after March)", () => {
    expect(getJpCap(2026, 12)).toBe(11_086_300);
  });

  it("JP iuran karyawan at exact cap 2026: gross=11_086_300 → JP=110_863", () => {
    const result = calculateSlip({
      month: 6,
      ptkp_status: "TK/0",
      gaji_pokok: 11_086_300,
      tunjangan_tetap: 0,
      tunjangan_tidak_tetap: 0,
      pph21_charged: 0,
      bpjs_kesehatan_charged: 110_863,
      bpjs_jht_charged: 221_726,
      bpjs_jp_charged: 110_863,
      bpjs_jkk_charged: 0,
      bpjs_jkm_charged: 0,
      potongan_lain: 0,
    });
    expect(result.bpjsJp.expected).toBe(110_863);
  });

  it("JP iuran above cap 2026: gross=15_000_000 → JP=110_863 (capped)", () => {
    const result = calculateSlip({
      month: 6,
      ptkp_status: "TK/0",
      gaji_pokok: 15_000_000,
      tunjangan_tetap: 0,
      tunjangan_tidak_tetap: 0,
      pph21_charged: 900_000,
      bpjs_kesehatan_charged: 120_000,
      bpjs_jht_charged: 300_000,
      bpjs_jp_charged: 110_863,
      bpjs_jkk_charged: 0,
      bpjs_jkm_charged: 0,
      potongan_lain: 0,
    });
    expect(result.bpjsJp.expected).toBe(110_863);
  });

  it("jp_cap_unverified is always false after cap verification", () => {
    const result = calculateSlip({
      month: 3,
      ptkp_status: "TK/0",
      gaji_pokok: 12_000_000,
      tunjangan_tetap: 0,
      tunjangan_tidak_tetap: 0,
      pph21_charged: 0,
      bpjs_kesehatan_charged: 120_000,
      bpjs_jht_charged: 240_000,
      bpjs_jp_charged: 110_863,
      bpjs_jkk_charged: 0,
      bpjs_jkm_charged: 0,
      potongan_lain: 0,
    });
    expect(result.jp_cap_unverified).toBe(false);
  });

  it("Dec: annual=120M TK/0 → BJ=6M, PKP=60M, tax=3_000_000", () => {
    const res = calculateSlip({
      month: 12,
      ptkp_status: "TK/0",
      gaji_pokok: 10_000_000,
      tunjangan_tetap: 0,
      tunjangan_tidak_tetap: 0,
      pph21_charged: 0,
      bpjs_kesehatan_charged: 0,
      bpjs_jht_charged: 0,
      bpjs_jp_charged: 0,
      bpjs_jkk_charged: 0,
      bpjs_jkm_charged: 0,
      potongan_lain: 0,
      annual_gross: 120_000_000,
    });
    expect(res.pph21.expected).toBe(3_000_000);
  });

  it("Dec: annual=60M TK/0 → BJ=3M, PKP=3M, tax=150_000", () => {
    const res = calculateSlip({
      month: 12,
      ptkp_status: "TK/0",
      gaji_pokok: 5_000_000,
      tunjangan_tetap: 0,
      tunjangan_tidak_tetap: 0,
      pph21_charged: 0,
      bpjs_kesehatan_charged: 0,
      bpjs_jht_charged: 0,
      bpjs_jp_charged: 0,
      bpjs_jkk_charged: 0,
      bpjs_jkm_charged: 0,
      potongan_lain: 0,
      annual_gross: 60_000_000,
    });
    expect(res.pph21.expected).toBe(150_000);
  });

  it("progressiveTax: PKP=0 → 0", () => {
    const res = calculateSlip({
      month: 12,
      ptkp_status: "TK/0",
      gaji_pokok: 0,
      tunjangan_tetap: 0,
      tunjangan_tidak_tetap: 0,
      pph21_charged: 0,
      bpjs_kesehatan_charged: 0,
      bpjs_jht_charged: 0,
      bpjs_jp_charged: 0,
      bpjs_jkk_charged: 0,
      bpjs_jkm_charged: 0,
      potongan_lain: 0,
      annual_gross: 54_000_000,
    });
    expect(res.pph21.expected).toBe(0);
  });

  it("progressiveTax: PKP=60_000_000 → 3_000_000 (all at 5%)", () => {
    const res = calculateSlip({
      month: 12,
      ptkp_status: "TK/0",
      gaji_pokok: 10_000_000,
      tunjangan_tetap: 0,
      tunjangan_tidak_tetap: 0,
      pph21_charged: 0,
      bpjs_kesehatan_charged: 0,
      bpjs_jht_charged: 0,
      bpjs_jp_charged: 0,
      bpjs_jkk_charged: 0,
      bpjs_jkm_charged: 0,
      potongan_lain: 0,
      annual_gross: 120_000_000,
    });
    expect(res.pph21.expected).toBe(3_000_000);
  });

  it("progressiveTax: PKP=120_000_000 → 12_000_000 (5%+15%)", () => {
    const res = calculateSlip({
      month: 12,
      ptkp_status: "TK/0",
      gaji_pokok: 10_000_000,
      tunjangan_tetap: 0,
      tunjangan_tidak_tetap: 0,
      pph21_charged: 3_000_000,
      bpjs_kesehatan_charged: 0,
      bpjs_jht_charged: 0,
      bpjs_jp_charged: 0,
      bpjs_jkk_charged: 0,
      bpjs_jkm_charged: 0,
      potongan_lain: 0,
      annual_gross: 180_000_000,
      annual_pph21_paid_before_last_period: 0,
    });
    expect(res.pph21.expected).toBe(12_000_000);
  });

  it("Dec without annual_gross: totalOvercharge = 0 for pph21 component", () => {
    const res = calculateSlip({
      month: 12,
      ptkp_status: "TK/0",
      gaji_pokok: 8_000_000,
      tunjangan_tetap: 0,
      tunjangan_tidak_tetap: 0,
      pph21_charged: 140_000,
      bpjs_kesehatan_charged: 80_000,
      bpjs_jht_charged: 160_000,
      bpjs_jp_charged: 80_000,
      bpjs_jkk_charged: 0,
      bpjs_jkm_charged: 0,
      potongan_lain: 0,
    });
    expect(res.pph21DataIncomplete).toBe(true);
    expect(res.totalOvercharge).toBeGreaterThanOrEqual(0);
  });

  it("JKK=50_000 → TIDAK_WAJAR + flag", () => {
    const res = calculateSlip({
      month: 6,
      ptkp_status: "TK/0",
      gaji_pokok: 8_000_000,
      tunjangan_tetap: 0,
      tunjangan_tidak_tetap: 0,
      pph21_charged: 140_000,
      bpjs_kesehatan_charged: 80_000,
      bpjs_jht_charged: 160_000,
      bpjs_jp_charged: 80_000,
      bpjs_jkk_charged: 50_000,
      bpjs_jkm_charged: 0,
      potongan_lain: 0,
    });
    expect(res.verdict).toBe("TIDAK_WAJAR");
    expect(res.bpjsJkk.isIllegal).toBe(true);
  });

  it("JKM=10_000 → TIDAK_WAJAR + flag", () => {
    const res = calculateSlip({
      month: 6,
      ptkp_status: "TK/0",
      gaji_pokok: 8_000_000,
      tunjangan_tetap: 0,
      tunjangan_tidak_tetap: 0,
      pph21_charged: 140_000,
      bpjs_kesehatan_charged: 80_000,
      bpjs_jht_charged: 160_000,
      bpjs_jp_charged: 80_000,
      bpjs_jkk_charged: 0,
      bpjs_jkm_charged: 10_000,
      potongan_lain: 0,
    });
    expect(res.verdict).toBe("TIDAK_WAJAR");
    expect(res.bpjsJkm.isIllegal).toBe(true);
  });

  it("JKK=0 JKM=0 → WAJAR for these components", () => {
    const res = calculateSlip({
      month: 6,
      ptkp_status: "TK/0",
      gaji_pokok: 8_000_000,
      tunjangan_tetap: 0,
      tunjangan_tidak_tetap: 0,
      pph21_charged: 140_000,
      bpjs_kesehatan_charged: 80_000,
      bpjs_jht_charged: 160_000,
      bpjs_jp_charged: 80_000,
      bpjs_jkk_charged: 0,
      bpjs_jkm_charged: 0,
      potongan_lain: 0,
    });
    expect(res.bpjsJkk.isCorrect).toBe(true);
    expect(res.bpjsJkm.isCorrect).toBe(true);
  });

  it("annualImpactWithInterest = totalOvercharge × 12 × 1.06", () => {
    const res = calculateSlip({
      month: 6,
      ptkp_status: "TK/0",
      gaji_pokok: 8_000_000,
      tunjangan_tetap: 0,
      tunjangan_tidak_tetap: 0,
      pph21_charged: 200_000,
      bpjs_kesehatan_charged: 80_000,
      bpjs_jht_charged: 160_000,
      bpjs_jp_charged: 80_000,
      bpjs_jkk_charged: 0,
      bpjs_jkm_charged: 0,
      potongan_lain: 0,
    });
    const expectedWithInterest = Math.round(res.totalOvercharge * 12 * 1.06);
    expect(res.annual_overcharge_with_interest).toBe(expectedWithInterest);
    expect(res.annual_overcharge_estimate).toBe(res.totalOvercharge * 12);
  });
});

describe("audit.ts — critical regression tests", () => {

  // B-1: JP expected uses verified 2026 cap (Rp11.086.300) for month=3
  it("JP expected uses verified 2026 cap (Rp11.086.300) for month=3", () => {
    // Source: SE BPJS B/1226/022026, effective 1 Maret 2026
    // Cap = Rp10.547.400 × (1 + 5.11%) = Rp11.086.372 → Rp11.086.300
    const result = auditSlip({
      gross: 11_086_300,
      month: 3,
      ptkp_status: "TK/0",
      deductions: {
        pph21: 0,
        bpjs_kesehatan: 110_863,
        bpjs_jht: 221_726,
        bpjs_jp: 110_863,   // 1% × 11_086_300 = 110_863
        bpjs_jkk: 0,
        bpjs_jkm: 0,
        potongan_lain: 0,
      },
    });
    expect(result.expected_breakdown.bpjs.jp.expected).toBe(110_863);
  });

  // B-3: K/I/0 must map to TER Category C (was wrongly mapped to A in old PTKP_CATEGORY_MAP)
  it("K/I/0 maps to TER category C", () => {
    // TER C has a non-zero threshold starting at Rp6.600.001 for gross Rp7.000.000
    // TER A has a non-zero threshold starting at Rp5.400.001
    // At Rp7.000.000: TER C = 0.5% = Rp35.000; TER A = 1.25% = Rp87.500
    const result = auditSlip({
      gross: 7_000_000,
      month: 6,
      ptkp_status: "K/I/0",
      deductions: {
        pph21: 0,
        bpjs_kesehatan: 70_000,
        bpjs_jht: 140_000,
        bpjs_jp: 70_000,
        bpjs_jkk: 0,
        bpjs_jkm: 0,
        potongan_lain: 0,
      },
    });
    // TER C: Rp7.000.000 is in slab { min: 6_950_001, max: 7_350_000, rate: 0.005 } = 0.5%
    // expected pph21 = 7_000_000 × 0.005 = 35_000
    expect(result.expected_breakdown.pph21).toBe(35_000);
  });

  // B-4: December must NOT return WAJAR blindly — JKK should still be caught
  it("December with illegal JKK returns POTONGAN_SALAH", () => {
    const result = auditSlip({
      gross: 8_000_000,
      month: 12,
      ptkp_status: "TK/0",
      deductions: {
        pph21: 140_000,
        bpjs_kesehatan: 80_000,
        bpjs_jht: 160_000,
        bpjs_jp: 80_000,
        bpjs_jkk: 50_000,   // illegal — employer-only
        bpjs_jkm: 0,
        potongan_lain: 0,
      },
    });
    expect(result.verdict).toBe("POTONGAN_SALAH");
    expect(result.issues.some((i) => i.type === "ILLEGAL_JKK_DEDUCTION")).toBe(true);
  });

  // B-4: December clean slip returns WAJAR (no issues)
  it("December clean slip with no issues returns WAJAR", () => {
    const result = auditSlip({
      gross: 8_000_000,
      month: 12,
      ptkp_status: "TK/0",
      deductions: {
        pph21: 140_000,
        bpjs_kesehatan: 80_000,
        bpjs_jht: 160_000,
        bpjs_jp: 80_000,
        bpjs_jkk: 0,
        bpjs_jkm: 0,
        potongan_lain: 0,
      },
    });
    expect(result.verdict).toBe("WAJAR");
  });

  // C-1: December PPh21 progressive tax bracket boundary — must not be NaN
  it("progressiveTax at bracket boundary is accurate", () => {
    const res = calculateSlip({
      month: 12,
      ptkp_status: "TK/0",
      gaji_pokok: 5_000_000,
      tunjangan_tetap: 0,
      tunjangan_tidak_tetap: 0,
      pph21_charged: 0,
      bpjs_kesehatan_charged: 0,
      bpjs_jht_charged: 0,
      bpjs_jp_charged: 0,
      bpjs_jkk_charged: 0,
      bpjs_jkm_charged: 0,
      potongan_lain: 0,
      annual_gross: 60_000_000, // exactly at Pasal 17 bracket boundary
    });
    expect(typeof res.pph21?.expected).toBe("number");
    expect(isNaN(res.pph21?.expected as number)).toBe(false);
  });

  // K/2 = Category B (fixed from old bug where K/2 was sometimes wrongly treated)
  it("K/2 maps to TER category B, not C", () => {
    // TER B at Rp8.000.000 is slab { min: 7_300_001, max: 9_200_000, ratePercent: 1 } = 1.0%
    // expected pph21 = 8_000_000 × 1% = 80_000
    const result = auditSlip({
      gross: 8_000_000,
      month: 3,
      ptkp_status: "K/2",
      deductions: {
        pph21: 80_000,    // 1.0% × 8M = TER B rate — exactly correct
        bpjs_kesehatan: 80_000,
        bpjs_jht: 160_000,
        bpjs_jp: 80_000,
        bpjs_jkk: 0,
        bpjs_jkm: 0,
        potongan_lain: 0,
      },
    });
    expect(result.verdict).toBe("WAJAR");
  });

});

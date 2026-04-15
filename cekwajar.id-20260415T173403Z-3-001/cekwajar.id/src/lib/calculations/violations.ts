// ══════════════════════════════════════════════════════════════════════════════
// cekwajar.id — Violation Detectors (V01–V07)
// ══════════════════════════════════════════════════════════════════════════════

import type { Violation, ViolationCode, ViolationSeverity } from '@/types'

export interface ViolationInput {
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

interface ViolationCandidate {
  code: ViolationCode
  severity: ViolationSeverity
  titleID: string
  descriptionID: string
  differenceIDR: number | null
  actionID: string
}

function v(
  code: ViolationCode,
  severity: ViolationSeverity,
  titleID: string,
  descriptionID: string,
  differenceIDR: number | null,
  actionID: string
): ViolationCandidate {
  return { code, severity, titleID, descriptionID, differenceIDR, actionID }
}

/**
 * Run all 7 violation detectors against the payslip data.
 * Returns violations sorted by severity (CRITICAL first).
 */
export function detectViolations(input: ViolationInput): Violation[] {
  const { grossSalary, cityUMK, reported, calculated } = input

  const candidates: ViolationCandidate[] = []

  // V01: JHT missing — employer not enrolling
  if (reported.jhtEmployee === 0 && grossSalary > 0) {
    candidates.push(
      v(
        'V01',
        'HIGH',
        'JHT Tidak Dipotong',
        'Tidak ada potongan JHT (2%). Perusahaan wajib mendaftarkan kamu ke BPJS Ketenagakerjaan program JHT.',
        calculated.jhtEmployee,
        'Minta HRD mendaftarkan kamu ke BPJS Ketenagakerjaan program JHT.'
      )
    )
  }

  // V02: JP underpaid
  if (
    reported.jpEmployee > 0 &&
    calculated.jpEmployee > reported.jpEmployee &&
    Math.abs(calculated.jpEmployee - reported.jpEmployee) > 5000
  ) {
    candidates.push(
      v(
        'V02',
        'MEDIUM',
        'JP Kurang Potong',
        `JP dipotong Rp ${reported.jpEmployee.toLocaleString('id-ID')} tapi seharusnya Rp ${calculated.jpEmployee.toLocaleString('id-ID')}.`,
        calculated.jpEmployee - reported.jpEmployee,
        'Minta HRD atau bagian payroll koreksi potongan JP sesuai gaji terbaru.'
      )
    )
  }

  // V03: PPh21 not withheld when it should be
  if (calculated.pph21 > 10_000 && reported.pph21 === 0) {
    candidates.push(
      v(
        'V03',
        'HIGH',
        'PPh21 Tidak Dipotong',
        'Seharusnya ada pemotongan PPh21 tapi di slip gaji tertulis Rp 0.',
        calculated.pph21,
        'Konsultasikan dengan HRD atau gunakan jasa konsultan pajak untuk koreksi.'
      )
    )
  }

  // V04: PPh21 underpaid (not zero — V03 covers zero case)
  if (
    calculated.pph21 > reported.pph21 &&
    reported.pph21 > 0 &&
    calculated.pph21 - reported.pph21 > 50_000
  ) {
    candidates.push(
      v(
        'V04',
        'MEDIUM',
        'PPh21 Kurang Potong',
        `PPh21 dipotong Rp ${reported.pph21.toLocaleString('id-ID')} tapi seharusnya Rp ${calculated.pph21.toLocaleString('id-ID')}.`,
        calculated.pph21 - reported.pph21,
        'Minta HRD koreksi pemotongan PPh21 dan laporkan ke atasan.'
      )
    )
  }

  // V05: BPJS Kesehatan missing
  if (reported.kesehatan === 0 && grossSalary > 0) {
    candidates.push(
      v(
        'V05',
        'HIGH',
        'BPJS Kesehatan Tidak Dipotong',
        'Tidak ada potongan BPJS Kesehatan (1%). Perusahaan wajib mendaftarkan kamu ke program BPJS Kesehatan.',
        calculated.kesehatan,
        'Minta HRD mendaftarkan kamu ke BPJS Kesehatan dan potong iuran yang tertunggak.'
      )
    )
  }

  // V06: Below UMK — most critical violation
  if (cityUMK > 0 && grossSalary < cityUMK) {
    candidates.push(
      v(
        'V06',
        'CRITICAL',
        'Gaji Di Bawah UMK',
        `Gaji Rp ${grossSalary.toLocaleString('id-ID')} di bawah UMK kota ini (Rp ${cityUMK.toLocaleString('id-ID')}). Ini PELANGGARAN HUKUM berat.`,
        cityUMK - grossSalary,
        'Laporkan ke Dinas Ketenagakerjaan setempat atau konsultasikan dengan Serikat Pekerja/LC KCHI.'
      )
    )
  }

  // V07: JP missing
  if (
    reported.jpEmployee === 0 &&
    grossSalary > 0 &&
    calculated.jpEmployee > 0
  ) {
    candidates.push(
      v(
        'V07',
        'MEDIUM',
        'JP Tidak Dipotong',
        'Tidak ada potongan JP (1%). Perusahaan wajib mendaftarkan kamu ke BPJS Ketenagakerjaan program JP.',
        calculated.jpEmployee,
        'Minta HRD mendaftarkan kamu ke program JP dan bayarkan iuran yang tertunggak.'
      )
    )
  }

  // Sort by severity: CRITICAL > HIGH > MEDIUM > LOW
  const severityOrder: Record<ViolationSeverity, number> = {
    CRITICAL: 0,
    HIGH: 1,
    MEDIUM: 2,
    LOW: 3,
  }

  return candidates
    .sort((a, b) => severityOrder[a.severity] - severityOrder[b.severity])
    .map((c) => ({
      code: c.code,
      severity: c.severity,
      titleID: c.titleID,
      descriptionID: c.descriptionID,
      differenceIDR: c.differenceIDR,
      actionID: c.actionID,
    }))
}

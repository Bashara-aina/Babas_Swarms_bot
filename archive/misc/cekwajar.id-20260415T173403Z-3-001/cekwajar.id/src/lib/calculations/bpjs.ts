// ══════════════════════════════════════════════════════════════════════════════
// cekwajar.id — BPJS Contribution Calculator
// JHT, JP, JKK, JKM, Kesehatan per Indonesian labor regulations
// ══════════════════════════════════════════════════════════════════════════════

// Salary caps (BPJS Kesehatan = 12M, JP cap updated annually)
export const JP_SALARY_CAP = 9_559_600
export const KESEHATAN_SALARY_CAP = 12_000_000

export interface BPJSInput {
  grossSalary: number
  /** JKK risk category: 0.24 (I), 0.54 (II), 0.89 (III), 1.27 (IV), 1.74 (V) */
  jkkCategory?: number
}

export interface BPJSResult {
  jhtEmployee: number
  jhtEmployer: number
  jpEmployee: number
  jpEmployer: number
  jkkEmployer: number
  jkmEmployer: number
  kesehatanEmployee: number
  kesehatanEmployer: number
  jpSalaryCap: number
  kesehatanSalaryCap: number
}

/**
 * Calculate all BPJS contributions for an employee.
 * JKK/JKM are employer-only. JHT and JP have employee+employer portions.
 * Kesehatan: 1% employee / 4% employer.
 */
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

// ══════════════════════════════════════════════════════════════════════════════
// cekwajar.id — Calculation Engines
// ══════════════════════════════════════════════════════════════════════════════

export { calculateBPJS, JP_SALARY_CAP, KESEHATAN_SALARY_CAP } from './bpjs'
export type { BPJSInput, BPJSResult } from './bpjs'

export { calculatePPh21 } from './pph21'
export type { PPh21Input, PPh21Result, PPh21CalculationDetails, TERCategory } from './pph21'

export { detectViolations } from './violations'
export type { ViolationInput } from './violations'

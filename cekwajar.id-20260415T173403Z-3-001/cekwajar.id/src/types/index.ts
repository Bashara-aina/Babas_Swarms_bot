// ══════════════════════════════════════════════════════════════════════════════
// cekwajar.id — Shared TypeScript Types
// ══════════════════════════════════════════════════════════════════════════════

export type SubscriptionTier = 'free' | 'basic' | 'pro'

export type PtkpStatus =
  | 'TK/0' | 'TK/1' | 'TK/2' | 'TK/3'
  | 'K/0'  | 'K/1'  | 'K/2'  | 'K/3'
  | 'K/I/0' | 'K/I/1' | 'K/I/2' | 'K/I/3'

export type PropertyType = 'RUMAH' | 'TANAH' | 'APARTEMEN' | 'RUKO'

export type PropertyVerdict = 'MURAH' | 'WAJAR' | 'MAHAL' | 'SANGAT_MAHAL'

export type ViolationCode = 'V01' | 'V02' | 'V03' | 'V04' | 'V05' | 'V06' | 'V07'

export type ViolationSeverity = 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW'

export interface Violation {
  code: ViolationCode
  severity: ViolationSeverity
  titleID: string
  descriptionID: string
  differenceIDR: number | null
  actionID: string
}

export interface UserProfile {
  id: string
  email: string
  full_name?: string
  subscription_tier: SubscriptionTier
  created_at: string
}

export interface Tool {
  id: string
  name: string
  href: string
  emoji: string
  description: string
}

export interface AuditResult {
  isCompliant: boolean
  violations: Violation[]
  grossSalary: number
  netSalary: number
  totalDeductions: number
  pph21Annual: number
  pph21Monthly: number
  bpjsMonthly: number
  bpjsEmployer: number
}

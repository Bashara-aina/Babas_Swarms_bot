// ══════════════════════════════════════════════════════════════════════════════
// cekwajar.id — Constants & Feature Flags
// ══════════════════════════════════════════════════════════════════════════════

import type { Tool } from '@/types'

export const TOOLS: Tool[] = [
  { id: 'wajar-slip', name: 'Wajar Slip', href: '/wajar-slip', emoji: '📋' },
  { id: 'wajar-gaji', name: 'Wajar Gaji', href: '/wajar-gaji', emoji: '💰' },
  { id: 'wajar-tanah', name: 'Wajar Tanah', href: '/wajar-tanah', emoji: '🏠' },
  { id: 'wajar-kabur', name: 'Wajar Kabur', href: '/wajar-kabur', emoji: '✈️' },
  { id: 'wajar-hidup', name: 'Wajar Hidup', href: '/wajar-hidup', emoji: '🏙️' },
]

export const SUBSCRIPTION_TIERS = {
  free: { name: 'Gratis', price: 0 },
  basic: { name: 'Basic', price: 29000 },
  pro: { name: 'Pro', price: 79000 },
} as const

export const FREE_TOOLS_LIMIT = {
  auditPerDay: 3,
  historyMonths: 0,
} as const

export const APP_NAME = 'cekwajar.id'
export const APP_URL = process.env.NEXT_PUBLIC_APP_URL || 'http://localhost:3000'

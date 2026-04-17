// ══════════════════════════════════════════════════════════════════════════════
// cekwajar.id — Constants & Feature Flags
// ══════════════════════════════════════════════════════════════════════════════

import type { Tool } from '@/types'
import {
  FileText,
  TrendingUp,
  Home,
  Plane,
  Building2
} from 'lucide-react'

export const TOOLS: Tool[] = [
  { id: 'wajar-slip', name: 'Wajar Slip', href: '/wajar-slip', Icon: FileText, description: 'Cek ketidakwajaran slip gaji' },
  { id: 'wajar-gaji', name: 'Wajar Gaji', href: '/wajar-gaji', Icon: TrendingUp, description: 'Benchmark gaji berdasarkan UMK' },
  { id: 'wajar-tanah', name: 'Wajar Tanah', href: '/wajar-tanah', Icon: Home, description: 'Analisis harga properti' },
  { id: 'wajar-kabur', name: 'Wajar Kabur', href: '/wajar-kabur', Icon: Plane, description: 'Cost of living 20 negara' },
  { id: 'wajar-hidup', name: 'Wajar Hidup', href: '/wajar-hidup', Icon: Building2, description: 'PPP dan kelayakan hidup' },
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

'use client'

// ══════════════════════════════════════════════════════════════════════════════
// cekwajar.id — DashboardStats (Client Component)
// Wraps StatsGrid with real subscription audit data
// ══════════════════════════════════════════════════════════════════════════════

import { StatsGrid, type StatItem } from '@/components/shared/StatsGrid/StatsGrid'
import { Customizer } from '@/components/shared/Customizer/Customizer'
import { PageHeader } from '@/components/shared/PageHeader/PageHeader'

// Mock audit stats — replace with real data from your DB
const AUDIT_STATS: StatItem[] = [
  {
    title: 'Total Audit',
    value: 847,
    trend: 23.5,
    trendLabel: 'dari bulan lalu',
    prefix: '',
    suffix: '',
    accent: 'emerald',
  },
  {
    title: 'Pelanggaran Terdeteksi',
    value: 312,
    trend: -8.2,
    trendLabel: 'dari bulan lalu',
    prefix: '',
    suffix: '',
    accent: 'amber',
  },
  {
    title: 'Pengguna Aktif',
    value: 1240,
    trend: 15.7,
    trendLabel: 'dari bulan lalu',
    prefix: '',
    suffix: '',
    accent: 'violet',
  },
  {
    title: 'Akurasi Audit',
    value: 99.2,
    trend: 0.4,
    trendLabel: 'dari bulan lalu',
    prefix: '',
    suffix: '%',
    decimals: 1,
    accent: 'emerald',
  },
]

export function DashboardStats() {
  return (
    <>
      <StatsGrid stats={AUDIT_STATS} />
      <Customizer />
    </>
  )
}

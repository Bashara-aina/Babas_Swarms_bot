// ══════════════════════════════════════════════════════════════════════════════
// cekwajar.id — TrustBadges Component
// Social proof badges shown on homepage and tool pages
// ══════════════════════════════════════════════════════════════════════════════

import { ShieldCheck, Trash2, UserX, FileCheck, Lock } from 'lucide-react'
import { cn } from '@/lib/utils'

interface Badge {
  icon: React.ElementType
  label: string
  sublabel?: string
}

const DEFAULT_BADGES: Badge[] = [
  {
    icon: Lock,
    label: 'Enkripsi TLS 1.3',
    sublabel: 'Data aman saat transfer',
  },
  {
    icon: Trash2,
    label: 'Hapus Otomatis 30 Hari',
    sublabel: 'Data tidak disimpan permanen',
  },
  {
    icon: UserX,
    label: 'Tanpa Nama Tersimpan',
    sublabel: 'Audit bisa tanpa daftar',
  },
  {
    icon: FileCheck,
    label: 'Berbasis PMK 168/2023',
    sublabel: 'Regulasi pajak resmi Indonesia',
  },
]

interface TrustBadgesProps {
  badges?: Badge[]
  className?: string
  variant?: 'row' | 'grid'
}

export function TrustBadges({ badges = DEFAULT_BADGES, className, variant = 'row' }: TrustBadgesProps) {
  if (variant === 'grid') {
    return (
      <div className={cn('grid grid-cols-2 md:grid-cols-4 gap-3', className)}>
        {badges.map((badge) => {
          const Icon = badge.icon
          return (
            <div
              key={badge.label}
              className="flex flex-col items-center text-center p-3 bg-emerald-50 dark:bg-emerald-950/20 rounded-xl border border-emerald-100 dark:border-emerald-900"
            >
              <Icon className="w-5 h-5 text-emerald-600 dark:text-emerald-400 mb-1.5" />
              <p className="text-xs font-semibold text-emerald-800 dark:text-emerald-300">{badge.label}</p>
              {badge.sublabel && (
                <p className="text-xs text-emerald-700/70 dark:text-emerald-400/70 mt-0.5 leading-tight">
                  {badge.sublabel}
                </p>
              )}
            </div>
          )
        })}
      </div>
    )
  }

  return (
    <div className={cn('flex flex-wrap items-center justify-center gap-6 text-sm text-muted-foreground', className)}>
      {badges.map((badge) => {
        const Icon = badge.icon
        return (
          <div key={badge.label} className="flex items-center gap-1.5">
            <div className="flex h-6 w-6 items-center justify-center rounded-full bg-emerald-100">
              <Icon className="h-3.5 w-3.5 text-emerald-700" />
            </div>
            <span>{badge.label}</span>
          </div>
        )
      })}
    </div>
  )
}

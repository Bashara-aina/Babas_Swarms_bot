'use client'

// ══════════════════════════════════════════════════════════════════════════════
// cekwajar.id — UMKBadge Component
// Shows city UMK with compliance indicator
// ══════════════════════════════════════════════════════════════════════════════

interface UMKBadgeProps {
  city: string
  umk: number
  grossSalary: number
}

export function UMKBadge({ city, umk, grossSalary }: UMKBadgeProps) {
  const isAbove = grossSalary >= umk
  const gap = Math.abs(grossSalary - umk)

  return (
    <div
      className={`rounded-lg border px-4 py-3 ${
        isAbove
          ? 'border-emerald-200 bg-emerald-50'
          : 'border-red-200 bg-red-50'
      }`}
    >
      <div className="flex items-center justify-between gap-4">
        <div>
          <p className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
            UMK/UMR {city} 2026
          </p>
          <p className="mt-0.5 text-lg font-bold text-foreground">
            Rp {umk.toLocaleString('id-ID')}
          </p>
        </div>
        <div className="text-right">
          {isAbove ? (
            <>
              <p className="text-sm font-semibold text-emerald-700">
                ↑ Di atas UMK
              </p>
              <p className="text-xs text-emerald-600">
                +Rp {gap.toLocaleString('id-ID')}
              </p>
            </>
          ) : (
            <>
              <p className="text-sm font-semibold text-red-700">
                ⚠️ Di bawah UMK
              </p>
              <p className="text-xs text-red-600">
                -Rp {gap.toLocaleString('id-ID')}
              </p>
            </>
          )}
        </div>
      </div>
    </div>
  )
}

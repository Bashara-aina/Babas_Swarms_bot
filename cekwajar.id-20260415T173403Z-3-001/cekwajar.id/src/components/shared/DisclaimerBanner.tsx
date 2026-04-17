// ══════════════════════════════════════════════════════════════════════════════
// cekwajar.id — Disclaimer Banner
// Information-first warning banners for tools with regulatory context
// Reframed from liability-first to informative
// ══════════════════════════════════════════════════════════════════════════════

import { AlertTriangle, Info } from 'lucide-react'

interface DisclaimerBannerProps {
  type:
    | 'tax'
    | 'ppp'
    | 'col'
    | 'property'
    | 'kjpp'
}

const DISCLAIMERS: Record<DisclaimerBannerProps['type'], { icon?: React.ElementType; body: React.ReactNode }> = {
  tax: {
    icon: Info,
    body: (
      <div className="flex items-start gap-2 text-sm text-amber-800 dark:text-amber-300">
        <Info className="w-4 h-4 flex-shrink-0 mt-0.5" />
        <div>
          <strong>Tentang akurasi:</strong> Hasil audit berdasarkan regulasi PMK 168/2023 dan data UMK 2026 resmi.
          Untuk kepastian hukum atau perselisihan kerja, konsultasikan dengan konsultan pajak atau Disnaker setempat.
        </div>
      </div>
    ),
  },
  ppp: {
    body: (
      <div className="flex items-start gap-2 text-sm text-amber-800 dark:text-amber-300">
        <AlertTriangle className="w-4 h-4 flex-shrink-0 mt-0.5" />
        <div>
          <strong>Tentang data PPP:</strong> World Bank PPP + Frankfurter kurs. Untuk keputusan relokasi penting,
          konsultasikan dengan agen migrasi bersertifikat.
        </div>
      </div>
    ),
  },
  col: {
    body: (
      <div className="flex items-start gap-2 text-sm text-amber-800 dark:text-amber-300">
        <AlertTriangle className="w-4 h-4 flex-shrink-0 mt-0.5" />
        <div>
          <strong>Tentang indeks biaya hidup:</strong> Diukur dari komunitas + data pemerintah. Biaya aktual
          tergantung gaya hidup dan kebutuhan pribadimu.
        </div>
      </div>
    ),
  },
  property: {
    icon: Info,
    body: (
      <div className="flex items-start gap-2 text-sm text-amber-800 dark:text-amber-300">
        <Info className="w-4 h-4 flex-shrink-0 mt-0.5" />
        <div>
          <strong>Estimasi pasar:</strong> Harga berdasarkan data listing publik, bukan penilaian KJPP.
          Untuk transaksi resmi, gunakan jasa penilai properti bersertifikat.
        </div>
      </div>
    ),
  },
  kjpp: {
    body: (
      <div className="flex items-start gap-2 text-sm text-amber-800 dark:text-amber-300">
        <AlertTriangle className="w-4 h-4 flex-shrink-0 mt-0.5" />
        <div>
          <strong>Tentang penilaian properti:</strong> Estimasi IQR dari listing publik, bukan penilaian resmi KJPP.
          Untuk keputusan bisnis penting, gunakan jasa KJPP berlisensi.
        </div>
      </div>
    ),
  },
}

export function DisclaimerBanner({ type }: DisclaimerBannerProps) {
  const { body } = DISCLAIMERS[type]

  return (
    <div className="rounded-lg border border-amber-200 bg-amber-50 p-3 dark:border-amber-800 dark:bg-amber-950/20">
      {body}
    </div>
  )
}

// ==============================================================================
// cekwajar.id ? Disclaimer Banner
// Warning banners for tools with regulatory disclaimers
// ==============================================================================

import { AlertTriangle } from 'lucide-react'

interface DisclaimerBannerProps {
  type:
    | 'tax'
    | 'ppp'
    | 'col'
    | 'property'
    | 'kjpp'
}

const DISCLAIMERS: Record<DisclaimerBannerProps['type'], { title: string; body: string }> = {
  tax: {
    title: 'Catatan Penting',
    body: 'Hasil kalkulasi PPh21 bersifat indikatif berdasarkan PMK 168/2023. Angka aktual mungkin berbeda tergantung situasi pajak kamu. Ini bukan?? nasihat perpajakan.',
  },
  ppp: {
    title: 'Tentang Data PPP',
    body: 'Data PPP dari World Bank adalah ukuran ekonometrik. Data biaya hidup dari Numbeo bersifat estimasi komunitas dan mungkin tidak akurat untuk semua situasi. Gunakan sebagai referensi saja.',
  },
  col: {
    title: 'Tentang Indeks Biaya Hidup',
    body: 'Indeks biaya hidup dihitung berdasarkan data komunitas dan gaya hidup rata-rata. Biaya aktual bisa berbeda signifikan tergantung kebutuhan dan kebiasaan pribadi.',
  },
  property: {
    title: 'Tentang Data Properti',
    body: 'Data harga properti dari berbagai sumber online. Harga aktual di pasar bisa berbeda. Selalu lakukan survei lapangan sebelum mengambil keputusan.',
  },
  kjpp: {
    title: 'Penafian KJPP',
    body: 'Nilai wajar properti dihitung menggunakan metodologi appraisal standar. Hasil ini adalah estimasi indikatif, bukan penilaian resmi KJPP. Untuk keputusan bisnis penting, silakan gunakan jasa KJPP berlisensi.',
  },
}

export function DisclaimerBanner({ type }: DisclaimerBannerProps) {
  const { title, body } = DISCLAIMERS[type]

  return (
    <div className="flex gap-3 rounded-lg border border-amber-200 bg-amber-50 p-3">
      <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0 text-amber-600" />
      <div>
        <p className="text-sm font-semibold text-amber-800">{title}</p>
        <p className="mt-0.5 text-xs text-amber-700">{body}</p>
      </div>
    </div>
  )
}

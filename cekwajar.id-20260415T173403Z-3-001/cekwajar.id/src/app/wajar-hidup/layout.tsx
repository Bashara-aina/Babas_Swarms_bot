import type { Metadata } from 'next'

export const metadata: Metadata = {
  title: 'Wajar Hidup — Bandingkan Biaya Hidup Antar Kota | cekwajar.id',
  description:
    'Perbandingan biaya hidup bulanan antar kota di Indonesia. food, transportasi, kos, dan pengeluaran lainnya.',
}

export default function WajarHidupLayout({ children }: { children: React.ReactNode }) {
  return <>{children}</>
}

import type { Metadata } from 'next'

export const metadata: Metadata = {
  title: 'Wajar Hidup — Perbandingan Biaya Hidup Kota | cekwajar.id',
  description: 'Perbandingan biaya hidup bulanan antar kota di Indonesia.',
}

export default function WajarHidupLayout({ children }: { children: React.ReactNode }) {
  return children
}

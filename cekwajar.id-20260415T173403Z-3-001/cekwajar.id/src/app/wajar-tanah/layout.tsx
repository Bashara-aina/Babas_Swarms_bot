import type { Metadata } from 'next'

export const metadata: Metadata = {
  title: 'Wajar Tanah — Cek Harga Properti | cekwajar.id',
  description:
    'Cek apakah harga tanah atau properti yang kamu lihat tergolong murah, wajar, atau mahal.',
}

export default function WajarTanahLayout({ children }: { children: React.ReactNode }) {
  return children
}

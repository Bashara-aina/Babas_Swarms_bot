import type { Metadata } from 'next'

export const metadata: Metadata = {
  title: 'Wajar Tanah — Cek Harga Wajar Properti Indonesia | cekwajar.id',
  description:
    'Cek apakah harga tanah atau properti yang kamu lihat tergolong murah, wajar, atau mahal. Benchmark harga per kecamatan.',
}

export default function WajarTanahLayout({ children }: { children: React.ReactNode }) {
  return <>{children}</>
}

import type { Metadata } from 'next'

export const metadata: Metadata = {
  title: 'Wajar Kabur — Perbandingan Daya Beli Internasional | cekwajar.id',
  description:
    'Bandingkan daya beli gajimu dengan 30+ negara menggunakan PPP World Bank.',
}

export default function WajarKaburLayout({ children }: { children: React.ReactNode }) {
  return children
}

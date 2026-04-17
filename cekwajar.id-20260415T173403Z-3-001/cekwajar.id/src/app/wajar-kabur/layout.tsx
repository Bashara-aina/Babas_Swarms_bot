import type { Metadata } from 'next'

export const metadata: Metadata = {
  title: 'Wajar Kabur — Bandingkan Daya Beli Gaji di LN | cekwajar.id',
  description:
    'Bandingkan daya beli gajimu dengan 30+ negara menggunakan PPP World Bank. Tau berapa nilai riil gajimu di SG, AU, US, dan lainnya.',
}

export default function WajarKaburLayout({ children }: { children: React.ReactNode }) {
  return <>{children}</>
}

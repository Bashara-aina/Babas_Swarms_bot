import type { Metadata } from 'next'

export const metadata: Metadata = {
  title: 'Wajar Gaji — Benchmark Gaji Standar Indonesia | cekwajar.id',
  description:
    'Benchmark gaji posisimu dengan data crowdsourced ribuan karyawan Indonesia. Cek apakah gajimu di bawah, sesuai, atau di atas standar.',
}

export default function WajarGajiLayout({ children }: { children: React.ReactNode }) {
  return <>{children}</>
}

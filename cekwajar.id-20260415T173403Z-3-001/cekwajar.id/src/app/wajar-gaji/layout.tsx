import type { Metadata } from 'next'

export const metadata: Metadata = {
  title: 'Wajar Gaji — Benchmark Gaji Indonesia | cekwajar.id',
  description:
    'Benchmark gaji posisimu dengan data crowdsourced ribuan karyawan Indonesia.',
}

export default function WajarGajiLayout({ children }: { children: React.ReactNode }) {
  return children
}

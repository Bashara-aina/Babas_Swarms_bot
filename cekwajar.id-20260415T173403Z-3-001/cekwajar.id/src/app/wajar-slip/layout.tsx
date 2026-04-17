import type { Metadata } from 'next'

export const metadata: Metadata = {
  title: 'Wajar Slip — Audit PPh21 & BPJS Slip Gaji Gratis | cekwajar.id',
  description:
    'Upload slip gaji kamu. AI audit PPh21, BPJS, dan UMK dalam 30 detik. Gratis, berbasis PMK 168/2023.',
}

export default function WajarSlipLayout({ children }: { children: React.ReactNode }) {
  return <>{children}</>
}

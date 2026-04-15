// ══════════════════════════════════════════════════════════════════════════════
// cekwajar.id — Wajar Slip (Stub)
// Stage 4: Full implementation with PPh21 TER + BPJS + violation detectors
// ══════════════════════════════════════════════════════════════════════════════

import Link from 'next/link'

export default function WajarSlipPage() {
  return (
    <div className="flex flex-col items-center justify-center px-4 py-16">
      <div className="w-full max-w-md text-center">
        <div className="mb-6 text-5xl">📋</div>
        <h1 className="text-2xl font-bold text-slate-900">Wajar Slip</h1>
        <p className="mt-3 text-slate-500">
          Audit PPh21 & BPJS slip gaji kamu dalam 30 detik.
          <br />
          Deteksi 7 jenis pelanggaran umum.
        </p>
        <div className="mt-6 rounded-lg border border-dashed border-slate-300 bg-slate-50 p-4">
          <p className="text-sm font-medium text-slate-600">
            ⏳ Sedang dibangun — Stage 4 dari 10
          </p>
          <p className="mt-1 text-xs text-slate-400">
            Implementasi lengkap meliputi: kalkulasi PPh21 TER (PMK 168/2023),
            validasi BPJS (JHT, JP, JKK, JKM, Kesehatan), dan 7 detektor pelanggaran.
          </p>
        </div>
        <Link
          href="/"
          className="mt-6 inline-block text-sm font-medium text-emerald-600 hover:text-emerald-700"
        >
          ← Kembali ke Homepage
        </Link>
      </div>
    </div>
  )
}

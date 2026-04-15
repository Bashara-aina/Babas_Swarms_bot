// ══════════════════════════════════════════════════════════════════════════════
// cekwajar.id — Wajar Tanah (Stub)
// Stage 7: Full implementation with property benchmark + scrapers
// ══════════════════════════════════════════════════════════════════════════════

import Link from 'next/link'

export default function WajarTanahPage() {
  return (
    <div className="flex flex-col items-center justify-center px-4 py-16">
      <div className="w-full max-w-md text-center">
        <div className="mb-6 text-5xl">🏠</div>
        <h1 className="text-2xl font-bold text-slate-900">Wajar Tanah</h1>
        <p className="mt-3 text-slate-500">
          Cek apakah harga properti yang kamu incar sudah wajar.
          <br />
          Bandingkan dengan data pasar aktual.
        </p>
        <div className="mt-6 rounded-lg border border-dashed border-slate-300 bg-slate-50 p-4">
          <p className="text-sm font-medium text-slate-600">
            ⏳ Sedang dibangun — Stage 7 dari 10
          </p>
          <p className="mt-1 text-xs text-slate-400">
            Implementasi lengkap meliputi: IQR outlier detection, nilai wajar properti,
            dan scraper 99.co + Rumah123.
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

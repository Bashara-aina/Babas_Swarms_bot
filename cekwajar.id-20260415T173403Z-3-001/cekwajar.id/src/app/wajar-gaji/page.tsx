// ══════════════════════════════════════════════════════════════════════════════
// cekwajar.id — Wajar Gaji (Stub)
// Stage 6: Full implementation with salary benchmark + crowdsource
// ══════════════════════════════════════════════════════════════════════════════

import Link from 'next/link'

export default function WajarGajiPage() {
  return (
    <div className="flex flex-col items-center justify-center px-4 py-16">
      <div className="w-full max-w-md text-center">
        <div className="mb-6 text-5xl">💰</div>
        <h1 className="text-2xl font-bold text-slate-900">Wajar Gaji</h1>
        <p className="mt-3 text-slate-500">
          Benchmark gaji kamu dengan data 12.000+ karyawan Indonesia.
          <br />
          Tau apakah gajimu sudah wajar di pasaran.
        </p>
        <div className="mt-6 rounded-lg border border-dashed border-slate-300 bg-slate-50 p-4">
          <p className="text-sm font-medium text-slate-600">
            ⏳ Sedang dibangun — Stage 6 dari 10
          </p>
          <p className="mt-1 text-xs text-slate-400">
            Implementasi lengkap meliputi: API benchmark gaji, Bayesian blending
            untuk dataset kecil, crowdsource submission, dan scraper BPS/JobStreet.
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

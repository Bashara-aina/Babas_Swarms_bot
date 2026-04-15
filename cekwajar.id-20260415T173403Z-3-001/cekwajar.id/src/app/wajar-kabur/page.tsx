// ══════════════════════════════════════════════════════════════════════════════
// cekwajar.id — Wajar Kabur (Stub)
// Stage 8: Full implementation with PPP comparison + World Bank API
// ══════════════════════════════════════════════════════════════════════════════

import Link from 'next/link'

export default function WajarKaburPage() {
  return (
    <div className="flex flex-col items-center justify-center px-4 py-16">
      <div className="w-full max-w-md text-center">
        <div className="mb-6 text-5xl">✈️</div>
        <h1 className="text-2xl font-bold text-slate-900">Wajar Kabur</h1>
        <p className="mt-3 text-slate-500">
          Kerja di luar negeri — berapa gaji riil yang setara?
          <br />
          Perbandingan PPP (Purchasing Power Parity).
        </p>
        <div className="mt-6 rounded-lg border border-dashed border-slate-300 bg-slate-50 p-4">
          <p className="text-sm font-medium text-slate-600">
            ⏳ Sedang dibangun — Stage 8 dari 10
          </p>
          <p className="mt-1 text-xs text-slate-400">
            Implementasi lengkap meliputi: World Bank PPP API, Frankfurter exchange rates,
            perbandingan gaji nominal vs PPP, dan breakdown biaya hidup negara tujuan.
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

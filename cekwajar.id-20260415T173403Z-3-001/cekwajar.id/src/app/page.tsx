// ══════════════════════════════════════════════════════════════════════════════
// cekwajar.id — Homepage
// Hero + 5 tool cards
// ══════════════════════════════════════════════════════════════════════════════

import Link from 'next/link'
import { ArrowRight, Calculator, TrendingUp, Home, Plane, Landmark } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { TOOLS } from '@/lib/constants'

const TOOL_ICONS: Record<string, React.ReactNode> = {
  'wajar-slip': <Calculator className="h-7 w-7 text-emerald-600" />,
  'wajar-gaji': <TrendingUp className="h-7 w-7 text-blue-600" />,
  'wajar-tanah': <Home className="h-7 w-7 text-amber-600" />,
  'wajar-kabur': <Plane className="h-7 w-7 text-indigo-600" />,
  'wajar-hidup': <Landmark className="h-7 w-7 text-rose-600" />,
}

const TOOL_DESCRIPTIONS: Record<string, string> = {
  'wajar-slip': 'Audit PPh21 & BPJS dalam 30 detik. Deteksi 7 jenis pelanggaran umum.',
  'wajar-gaji': 'Benchmark gaji dengan data 12.000+ karyawan. Tau apakah gajimu sudah wajar.',
  'wajar-tanah': 'Cek harga properti vs pasar. Deteksi harga tidak wajar dalam detik.',
  'wajar-kabur': 'Kerja di luar negeri — berapa gaji riil yang setara? Perbandingan PPP.',
  'wajar-hidup': 'Pindah kota? Hitung gaji setara berdasarkan biaya hidup kota tujuan.',
}

export default function HomePage() {
  return (
    <div className="flex flex-col">
      {/* Hero */}
      <section className="bg-gradient-to-b from-emerald-50 to-white px-4 py-16 lg:py-24">
        <div className="mx-auto max-w-3xl text-center">
          <h1 className="text-3xl font-bold leading-tight text-slate-900 sm:text-4xl lg:text-5xl">
            Audit Slip Gaji, Benchmark Gaji & Harga Properti
            <span className="mt-2 block text-emerald-600">— Gratis</span>
          </h1>
          <p className="mt-4 text-base text-slate-600 sm:text-lg">
            5 alat gratis untuk karyawan Indonesia. Tidak perlu login untuk memulai.
          </p>
          <div className="mt-8 flex flex-col items-center gap-3 sm:flex-row sm:justify-center">
            <Link href="/wajar-slip">
              <Button size="lg" className="bg-emerald-600 hover:bg-emerald-700">
                Cek Slip Gaji Gratis
                <ArrowRight className="ml-2 h-4 w-4" />
              </Button>
            </Link>
            <Link href="#alat">
              <Button
                size="lg"
                variant="outline"
                className="border-emerald-600 text-emerald-700 hover:bg-emerald-50"
              >
                Lihat Semua Alat
              </Button>
            </Link>
          </div>
        </div>
      </section>

      {/* Tool Cards */}
      <section id="alat" className="px-4 py-12 lg:py-16">
        <div className="mx-auto max-w-5xl">
          <h2 className="text-center text-xl font-bold text-slate-900 sm:text-2xl">
            Semua Alat
          </h2>
          <p className="mt-2 text-center text-sm text-slate-500">
            Pilih alat yang kamu butuhkan
          </p>

          <div className="mt-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {TOOLS.map((tool) => (
              <Link
                key={tool.id}
                href={tool.href}
                className="group flex flex-col gap-3 rounded-xl border bg-white p-5 shadow-sm transition-all hover:border-emerald-200 hover:shadow-md"
              >
                <div className="flex items-center gap-3">
                  <div className="rounded-lg bg-slate-50 p-2">
                    {TOOL_ICONS[tool.id]}
                  </div>
                  <span className="text-base font-semibold text-slate-900">
                    {tool.emoji} {tool.name}
                  </span>
                </div>

                <p className="text-sm text-slate-500">
                  {TOOL_DESCRIPTIONS[tool.id]}
                </p>

                <div className="mt-auto flex items-center text-sm font-medium text-emerald-600 group-hover:gap-1">
                  Mulai Gratis
                  <ArrowRight className="ml-1 h-3.5 w-3.5 transition-all group-hover:ml-2" />
                </div>
              </Link>
            ))}
          </div>
        </div>
      </section>

      {/* How it works */}
      <section className="bg-slate-50 px-4 py-12 lg:py-16">
        <div className="mx-auto max-w-3xl text-center">
          <h2 className="text-xl font-bold text-slate-900 sm:text-2xl">
            Cara Kerja
          </h2>
          <div className="mt-8 grid gap-6 sm:grid-cols-3">
            <div className="flex flex-col items-center gap-2">
              <div className="flex h-10 w-10 items-center justify-center rounded-full bg-emerald-100 text-sm font-bold text-emerald-700">
                1
              </div>
              <p className="text-sm font-medium text-slate-800">Pilih Alat</p>
              <p className="text-xs text-slate-500">Tidak perlu login</p>
            </div>
            <div className="flex flex-col items-center gap-2">
              <div className="flex h-10 w-10 items-center justify-center rounded-full bg-emerald-100 text-sm font-bold text-emerald-700">
                2
              </div>
              <p className="text-sm font-medium text-slate-800">Masukkan Data</p>
              <p className="text-xs text-slate-500">Slip gaji, gaji pokok, atau harga properti</p>
            </div>
            <div className="flex flex-col items-center gap-2">
              <div className="flex h-10 w-10 items-center justify-center rounded-full bg-emerald-100 text-sm font-bold text-emerald-700">
                3
              </div>
              <p className="text-sm font-medium text-slate-800">Dapat Hasil</p>
              <p className="text-xs text-slate-500">Analisis instan + rekomendasi tindakan</p>
            </div>
          </div>
        </div>
      </section>
    </div>
  )
}

// ══════════════════════════════════════════════════════════════════════════════
// cekwajar.id — Pricing Page
// Detailed feature comparison + FAQ
// ══════════════════════════════════════════════════════════════════════════════

import Link from 'next/link'
import { Fragment } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'

const FEATURES: {
  category: string
  items: { label: string; free: string | boolean; basic: string | boolean; pro: string | boolean }[]
}[] = [
  {
    category: 'Audit Slip Gaji',
    items: [
      { label: 'Audit slip gaji/hari', free: '3', basic: '3', pro: '3' },
      { label: 'Detail pelanggaran IDR per komponen', free: false, basic: true, pro: true },
      { label: 'Riwayat audit lengkap', free: false, basic: true, pro: true },
      { label: 'Export PDF laporan', free: false, basic: false, pro: true },
    ],
  },
  {
    category: 'Benchmark',
    items: [
      { label: 'Benchmark UMK/UMR provinsi', free: true, basic: true, pro: true },
      { label: 'P25–P75 per kota', free: false, basic: true, pro: true },
      { label: 'COL Index per negara', free: false, basic: false, pro: true },
    ],
  },
  {
    category: 'Analisis',
    items: [
      { label: 'Wajar Kabur (20 negara)', free: false, basic: true, pro: true },
      { label: 'Analisis tanah & properti', free: false, basic: false, pro: true },
      { label: 'PPP purchasing power parity', free: false, basic: false, pro: true },
    ],
  },
  {
    category: 'Lainnya',
    items: [
      { label: 'PPh21 TER method (PMK 168/2023)', free: true, basic: true, pro: true },
      { label: 'BPJS Kesehatan & Ketenagakerjaan', free: true, basic: true, pro: true },
      { label: 'Support', free: 'Komunitas', basic: 'Email', pro: 'Prioritas' },
    ],
  },
]

const FAQ = [
  {
    q: 'Bagaimana cara upgrade paket?',
    a: 'Pilih paket Basic atau Pro, lalu selesaikan pembayaran melalui Midtrans. Langsung aktif setelah pembayaran terkonfirmasi.',
  },
  {
    q: 'Apakah bisa batalkan kapan saja?',
    a: 'Ya, kamu bisa batalkan langganan kapan saja. Akses tetap aktif sampai akhir periode billing.',
  },
  {
    q: 'Apa itu metode TER (PTKP)?',
    a: 'TER adalah metode perpajakan PPh21 sesuai PMK 168/2023 yang menghitung pajak berdasarkan PTKP yang berlaku untuk semua level karyawan.',
  },
  {
    q: 'Apakah data slip gaji saya aman?',
    a: 'Semua data dienkripsi dan disimpan di Supabase. Kami tidak membagikan data kamu ke pihak manapun.',
  },
]

export default function PricingPage() {
  return (
    <div className="min-h-screen bg-muted">
      <div className="mx-auto max-w-5xl px-4 py-12">
        {/* Header */}
        <div className="text-center mb-12">
          <Badge variant="outline" className="mb-4 border-emerald-200 text-emerald-700 bg-emerald-50">
            Transparansi Harga
          </Badge>
          <h1 className="text-3xl font-bold text-foreground mb-3">
            Harga yang Jujur, Tanpa Biaya Tersembunyi
          </h1>
          <p className="text-muted-foreground max-w-lg mx-auto">
            Mulai gratis, upgrade kalau butuh lebih. Semua fitur PPh21 dan BPJS
            sudah termasuk di semua paket.
          </p>
        </div>

        {/* Feature comparison table */}
        <Card className="mb-12">
          <CardHeader>
            <CardTitle>Perbandingan Fitur</CardTitle>
          </CardHeader>
          <CardContent className="overflow-x-auto -mx-4 px-4 sm:mx-0 sm:px-0">
            <table className="min-w-[600px] sm:min-w-0 sm:w-full text-sm">
              <thead>
                <tr className="border-b">
                  <th className="text-left py-3 pr-4 font-medium text-muted-foreground">Fitur</th>
                  <th className="text-center py-3 px-4 font-medium text-muted-foreground w-1/4">Gratis</th>
                  <th className="text-center py-3 px-4 font-medium text-blue-700 dark:text-blue-400 w-1/4">Basic</th>
                  <th className="text-center py-3 px-4 font-medium text-purple-700 dark:text-purple-400 w-1/4">Pro</th>
                </tr>
              </thead>
              <tbody>
                {FEATURES.map((cat) => (
                  <Fragment key={cat.category}>
                    <tr className="bg-muted">
                      <td colSpan={4} className="py-2 px-0 font-semibold text-foreground text-xs uppercase tracking-wide">
                        {cat.category}
                      </td>
                    </tr>
                    {cat.items.map((item) => (
                      <tr key={item.label} className="border-b border-border">
                        <td className="py-2.5 pr-4 text-foreground">{item.label}</td>
                        {(['free', 'basic', 'pro'] as const).map((tier) => {
                          const value = item[tier]
                          return (
                            <td key={tier} className="py-2.5 px-4 text-center">
                              {typeof value === 'boolean' ? (
                                value ? (
                                  <span className="text-emerald-500 font-medium">✓</span>
                                ) : (
                                  <span className="text-muted-foreground">—</span>
                                )
                              ) : (
                                <span className="text-muted-foreground text-xs">{value}</span>
                              )}
                            </td>
                          )
                        })}
                      </tr>
                    ))}
                  </Fragment>
                ))}
              </tbody>
            </table>
            <p className="text-xs text-center text-muted-foreground mt-2 sm:hidden">
              ← Geser untuk lihat semua fitur →
            </p>
          </CardContent>
        </Card>

        {/* Pricing cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-12">
          {[
            {
              id: 'free', name: 'Gratis', price: 'Rp 0', period: 'selamanya',
              color: 'slate', description: 'Coba fitur dasar tanpa batas waktu.',
              features: ['3 audit slip gaji/hari', 'Benchmark provinsi', 'PPh21 TER & BPJS'],
              cta: 'Paket Saat Ini', disabled: true, href: '#',
            },
            {
              id: 'basic', name: 'Basic', price: 'Rp 29.000', period: 'per bulan',
              color: 'blue', description: 'Untuk audit slip gaji yang mendalam.',
              features: ['Semua fitur Gratis', 'Detail pelanggaran IDR', 'P25–P75 per kota', 'Wajar Kabur 20 negara'],
              cta: 'Pilih Basic', disabled: false, href: '/upgrade#basic',
            },
            {
              id: 'pro', name: 'Pro', price: 'Rp 79.000', period: 'per bulan',
              color: 'purple', description: 'Fitur lengkap untuk profesional.',
              features: ['Semua fitur Basic', 'Analisis tanah & properti', 'COL Index per negara', 'PPP purchasing power'],
              cta: 'Pilih Pro', disabled: false, href: '/upgrade#pro',
            },
          ].map((tier) => (
            <Card key={tier.id} id={tier.id} className={`border-2 ${
              tier.color === 'blue' ? 'border-blue-300' :
              tier.color === 'purple' ? 'border-purple-300' : 'border-border'
            }`}>
              <CardHeader>
                <CardTitle className="text-xl">{tier.name}</CardTitle>
                <p className="text-sm text-muted-foreground mt-1">{tier.description}</p>
                <div className="mt-3">
                  <span className="text-2xl font-bold">{tier.price}</span>
                  <span className="text-muted-foreground text-sm ml-1">{tier.period}</span>
                </div>
              </CardHeader>
              <CardContent>
                <ul className="space-y-1.5">
                  {tier.features.map((f) => (
                    <li key={f} className="flex items-center gap-2 text-sm text-foreground">
                      <span className="text-emerald-500">✓</span> {f}
                    </li>
                  ))}
                </ul>
              </CardContent>
              <CardContent className="pt-0">
                {tier.disabled ? (
                  <button disabled className="w-full py-2 rounded-md border border-border text-muted-foreground text-sm cursor-not-allowed">
                    {tier.cta}
                  </button>
                ) : (
                  <Link
                    href={tier.href}
                    className={`block text-center py-2 rounded-md text-sm font-medium text-white ${
                      tier.color === 'blue' ? 'bg-blue-600 hover:bg-blue-700' : 'bg-purple-600 hover:bg-purple-700'
                    }`}
                  >
                    {tier.cta}
                  </Link>
                )}
              </CardContent>
            </Card>
          ))}
        </div>

        {/* FAQ */}
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Pertanyaan Umum</CardTitle>
          </CardHeader>
          <CardContent className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {FAQ.map((item) => (
              <div key={item.q}>
                <p className="font-medium text-foreground mb-1">{item.q}</p>
                <p className="text-sm text-muted-foreground">{item.a}</p>
              </div>
            ))}
          </CardContent>
        </Card>
      </div>
    </div>
  )
}

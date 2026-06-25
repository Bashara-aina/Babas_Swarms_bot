// ==============================================================================
// cekwajar.id — Contact Page
// Simple static page with contact information
// ==============================================================================

import type { Metadata } from 'next'
import { Mail, MessageCircle } from 'lucide-react'
import Link from 'next/link'
import { Card, CardContent } from '@/components/ui/card'
import { FounderSection } from '@/components/FounderSection'

export const metadata: Metadata = {
  title: 'Kontak — cekwajar.id',
  description: 'Hubungi tim cekwajar.id untuk pertanyaan, masukan, atau kerja sama.',
}

export default function KontakPage() {
  return (
    <div className="min-h-screen bg-muted">
      <FounderSection />
      <div className="mx-auto max-w-2xl px-4 py-12">
        <div className="text-center mb-10">
          <div className="mb-4"><Mail className="h-12 w-12 text-emerald-600 mx-auto" /></div>
          <h1 className="text-3xl font-bold text-foreground mb-3">Hubungi Kami</h1>
          <p className="text-muted-foreground max-w-md mx-auto">
            Punya pertanyaan, masukan, atau ingin bekerja sama? Kami senang mendengar dari kamu.
          </p>
        </div>

        {/* Contact Methods */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-10">
          <a href="mailto:support@cekwajar.id">
            <Card className="hover:border-emerald-300 hover:shadow-md transition-all cursor-pointer h-full">
              <CardContent className="p-6 flex items-start gap-4">
                <div className="rounded-lg bg-emerald-100 p-3">
                  <Mail className="h-5 w-5 text-emerald-600" />
                </div>
                <div>
                  <div className="font-semibold text-foreground">Email</div>
                  <div className="text-sm text-muted-foreground">support@cekwajar.id</div>
                  <div className="text-xs text-muted-foreground mt-1">Respon dalam 1-2 hari kerja</div>
                </div>
              </CardContent>
            </Card>
          </a>

          <a href="https://wa.me/6281234567890" target="_blank" rel="noopener noreferrer">
            <Card className="hover:border-emerald-300 hover:shadow-md transition-all cursor-pointer h-full">
              <CardContent className="p-6 flex items-start gap-4">
                <div className="rounded-lg bg-emerald-100 p-3">
                  <MessageCircle className="h-5 w-5 text-emerald-600" />
                </div>
                <div>
                  <div className="font-semibold text-foreground">WhatsApp</div>
                  <div className="text-sm text-muted-foreground">+62 812 3456 7890</div>
                  <div className="text-xs text-muted-foreground mt-1">Chat only, bukan support resmi</div>
                </div>
              </CardContent>
            </Card>
          </a>
        </div>

        {/* About Section */}
        <Card className="mb-8">
          <CardContent className="p-6">
            <h2 className="text-lg font-semibold text-foreground mb-4">Kenapa cekwajar.id ada?</h2>
            <div className="space-y-3 text-sm text-muted-foreground">
              <p className="text-muted-foreground leading-relaxed">
                Karena kebanyakan karyawan Indonesia tidak tahu apakah slip gaji mereka benar —
                dan tidak ada tools yang mudah untuk mengeceknya.
              </p>
              <p className="text-muted-foreground leading-relaxed">
                Saya bikin cekwajar.id karena pernah kena underpay BPJS hampir setahun penuh
                sebelum sadar. Waktu itu saya tidak tahu harus cek ke mana, dan tidak ada tools
                yang mudah dipakai orang biasa tanpa latar belakang pajak.
              </p>
              <p className="text-muted-foreground leading-relaxed">
                Sekarang kamu tidak perlu ngalamin hal yang sama.
              </p>
            </div>

            <div className="mt-5 pt-5 border-t border-border">
              <p className="text-xs text-muted-foreground">
                cekwajar.id bukan bagian dari pemerintah Indonesia. Data benchmark bersumber dari
                Badan Pusat Statistik (BPS), World Bank, dan sumber publik lainnya.
              </p>
            </div>
          </CardContent>
        </Card>

        {/* FAQ */}
        <Card>
          <CardContent className="p-6">
            <h2 className="text-lg font-semibold text-foreground mb-4">Pertanyaan Umum</h2>
            <div className="space-y-4">
              {[
                {
                  q: 'Bagaimana cara kerja Wajar Slip?',
                  a: 'Upload slip gaji (foto atau teks), dan kami akan menganalisis kepatuhannya terhadap PPn 36/2021 dan UU Ketenagakerjaan. Hasil menunjukkan komponen yang tidak sesuai dan estimasi pelanggaran IDR.',
                },
                {
                  q: 'Apakah data slip gaji saya aman?',
                  a: 'Ya. Foto slip gaji disimpan maksimal 30 hari dan otomatis dihapus. Kami tidak membagikan data kamu ke pihak ketiga untuk tujuan pemasaran.',
                },
                {
                  q: 'Bagaimana cara membatalkan langganan?',
                  a: 'Login, pergi ke /dashboard, dan klik "Batalkan Langganan". Langganan tetap aktif sampai akhir periode yang sudah dibayar.',
                },
                {
                  q: 'Apakah ada garansi uang kembali?',
                  a: 'Saat ini tidak tersedia. Namun, paket gratis selalu dapat digunakan untuk mencoba layanan.',
                },
              ].map((item, i) => (
                <div key={i}>
                  <p className="text-sm font-medium text-foreground">{item.q}</p>
                  <p className="text-sm text-muted-foreground mt-1">{item.a}</p>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Footer Links */}
        <div className="flex justify-center gap-6 mt-8">
          <Link href="/privacy-policy" className="text-sm text-muted-foreground hover:text-emerald-600">
            Kebijakan Privasi
          </Link>
          <Link href="/terms" className="text-sm text-muted-foreground hover:text-emerald-600">
            Syarat & Ketentuan
          </Link>
        </div>
      </div>
    </div>
  )
}

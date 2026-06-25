// ══════════════════════════════════════════════════════════════════════════════
// cekwajar.id — FounderSection
// Brief introduction to the team behind cekwajar.id
// ══════════════════════════════════════════════════════════════════════════════

import { Card, CardContent } from '@/components/ui/card'
import { Building2, MapPin } from 'lucide-react'

export function FounderSection({ className }: { className?: string }) {
  return (
    <section className={className}>
      <div className="mx-auto max-w-5xl px-4 py-16">
        <div className="text-center mb-12">
          <h2 className="text-xl font-bold text-foreground">
            Dibuat untuk Pekerja Indonesia
          </h2>
          <p className="mt-2 text-sm text-muted-foreground max-w-md mx-auto">
            Kami membangun cekwajar.id setelah melihat sendiri bagaimana banyak karyawan Indonesia
            menerima slip gaji yang tidak sesuai regulasi.
          </p>
        </div>

        <div className="grid gap-6 md:grid-cols-2 max-w-2xl mx-auto">
          {/* Founder */}
          <Card>
            <CardContent className="p-6">
              <div className="flex items-start gap-4">
                <div className="w-14 h-14 rounded-full bg-emerald-100 flex items-center justify-center shrink-0">
                  <Building2 className="h-7 w-7 text-emerald-600" />
                </div>
                <div className="min-w-0">
                  <p className="font-semibold text-foreground">Tim cekwajar.id</p>
                  <p className="text-sm text-muted-foreground mt-0.5">
                    Founders, Jakarta
                  </p>
                  <p className="text-sm text-muted-foreground mt-2 leading-relaxed">
                    Diproduksi oleh sekelompok praktisi HR dan developer Indonesia
                    yang peduli tentang transparansi upah. Didasarkan pada pengalaman
                    pribadi dan data dari ribuan laporan slip gaji.
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Mission */}
          <Card>
            <CardContent className="p-6">
              <div className="flex items-start gap-4">
                <div className="w-14 h-14 rounded-full bg-blue-100 flex items-center justify-center shrink-0">
                  <MapPin className="h-7 w-7 text-blue-600" />
                </div>
                <div className="min-w-0">
                  <p className="font-semibold text-foreground">Misi Kami</p>
                  <p className="text-sm text-muted-foreground mt-0.5">
                    Transparansi Upah di Indonesia
                  </p>
                  <p className="text-sm text-muted-foreground mt-2 leading-relaxed">
                    Setiap pekerja Indonesia berhak tahu apakah slip gaji mereka wajar.
                    Kami percaya data adalah alat pertama untuk добиться keadilan —
                    dan kami menambahkannya secara gratis.
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </section>
  )
}

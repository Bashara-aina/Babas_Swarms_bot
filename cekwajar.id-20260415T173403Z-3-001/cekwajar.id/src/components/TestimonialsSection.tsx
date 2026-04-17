// ══════════════════════════════════════════════════════════════════════════════
// cekwajar.id — TestimonialsSection
// Social proof from anonymous Indonesian workers
// ══════════════════════════════════════════════════════════════════════════════

import { Card, CardContent } from '@/components/ui/card'
import { Star, Quote } from 'lucide-react'

interface Testimonial {
  quote: string
  name: string
  role: string
  location: string
  rating: number
}

const TESTIMONIALS: Testimonial[] = [
  {
    quote:
      'Gak pernah tau slip gaji aku那么多人这么多年来 ternyata salahitung JHT. Pas cek di sini, ketahuan — perusahaan kurang bayar 3 bulan. Langsung kirim email ke HR.',
    name: 'Arif W.',
    role: 'Software Engineer, 4 tahun pengalaman',
    location: 'Jakarta',
    rating: 5,
  },
  {
    quote:
      'Cek Wajar Gaji buktiin kalo gaji aku di bawah UMK Medan padahal udah 3 tahun. Besok langsung nego sama manager. Gak bakal tau kalo gak ada tools ini.',
    name: 'Rina S.',
    role: 'Akuntan, 3 tahun pengalaman',
    location: 'Medan',
    rating: 5,
  },
  {
    quote:
      'Dulu thought slip gaji aku udah bener. Tapi cek di sini, PPh21 nya salah — aku overpaid pajak 400rb per tahun. Thanks buat toolsnya!',
    name: 'Dimas P.',
    role: 'Marketing Lead, 5 tahun pengalaman',
    location: 'Surabaya',
    rating: 5,
  },
]

function StarRating({ count }: { count: number }) {
  return (
    <div className="flex items-center gap-0.5">
      {Array.from({ length: count }).map((_, i) => (
        <Star key={i} className="h-3.5 w-3.5 fill-amber-400 text-amber-400" />
      ))}
    </div>
  )
}

export function TestimonialsSection({ className }: { className?: string }) {
  return (
    <section className={className}>
      <div className="mx-auto max-w-5xl px-4 py-16">
        <div className="text-center mb-10">
          <h2 className="text-xl font-bold text-foreground">
            Apa Kata Pekerja Indonesia
          </h2>
          <p className="mt-1 text-sm text-muted-foreground">
            Cerita nyata dari pengguna yang menemukan pelanggaran di slip gaji mereka
          </p>
        </div>

        <div className="grid gap-4 md:grid-cols-3">
          {TESTIMONIALS.map((t) => (
            <Card key={t.name} className="bg-white">
              <CardContent className="p-5">
                <Quote className="h-5 w-5 text-emerald-200 mb-3" />
                <p className="text-sm text-foreground leading-relaxed mb-4">
                  &ldquo;{t.quote}&rdquo;
                </p>
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-semibold text-foreground">{t.name}</p>
                    <p className="text-xs text-muted-foreground mt-0.5">{t.role}</p>
                    <p className="text-xs text-muted-foreground">{t.location}</p>
                  </div>
                  <StarRating count={t.rating} />
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    </section>
  )
}

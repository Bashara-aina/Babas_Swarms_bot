// ══════════════════════════════════════════════════════════════════════════════
// cekwajar.id — TestimonialsSection
// Social proof from anonymous Indonesian workers
// ══════════════════════════════════════════════════════════════════════════════

interface Testimonial {
  initials: string
  name: string
  city: string
  quote: string
  tool: string
}

const TESTIMONIALS: Testimonial[] = [
  {
    initials: 'R',
    name: 'Rizky',
    city: 'Tangerang',
    quote: 'Ternyata BPJS saya kurang dipotong selama 8 bulan. Langsung saya tunjukkan ke HRD dan sudah dikoreksi.',
    tool: 'Wajar Slip',
  },
  {
    initials: 'D',
    name: 'Dimas',
    city: 'Bandung',
    quote: 'Gajimu ada di P38 — itu yang bikin saya akhirnya berani negosiasi saat review tahunan.',
    tool: 'Wajar Gaji',
  },
  {
    initials: 'S',
    name: 'Sari',
    city: 'Jakarta',
    quote:
      'Niat pindah ke Singapore, tapi setelah cek PPP ternyata gaya hidup saya di Jakarta lebih terjangkau. Jadi lebih objektif pertimbangannya.',
    tool: 'Wajar Kabur',
  },
]

export function TestimonialsSection({ className }: { className?: string }) {
  const SHOW_TESTIMONIALS = false
  if (!SHOW_TESTIMONIALS) return null

  return <section className={className} data-count={TESTIMONIALS.length} />
}

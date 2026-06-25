import Link from "next/link"
import { Shield, Clock, Lock, Scale } from "lucide-react"
import { WordmarkLogo } from "@/components/Footer"

function TrustBadge({ icon: Icon, text }: { icon: typeof Shield; text: string }) {
  return (
    <div className="flex items-center gap-2 text-xs text-muted-foreground">
      <Icon className="h-4 w-4 text-emerald-600" aria-hidden="true" />
      <span>{text}</span>
    </div>
  )
}

function ToolCard({
  href,
  title,
  description,
  badge,
  accent,
}: {
  href: string
  title: string
  description: string
  badge?: string
  accent: string
}) {
  return (
    <Link
      href={href}
      className={`group relative flex flex-col gap-3 rounded-2xl border border-border bg-card p-6 shadow-sm transition-all hover:shadow-md hover:bg-muted/30 dark:bg-slate-800/50`}
      aria-label={`${title} — ${description}`}
    >
      {badge && (
        <span className={`absolute right-4 top-4 rounded-full ${badge} px-2.5 py-0.5 text-xs font-semibold`}>
          {badge}
        </span>
      )}
      <h2 className={`text-lg font-bold ${accent}`}>{title}</h2>
      <p className="text-sm text-muted-foreground">{description}</p>
      <div className="mt-auto flex items-center gap-2 text-xs font-medium text-emerald-600">
        <span>Cek sekarang</span>
        <svg className="h-4 w-4 transition-transform group-hover:translate-x-1" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M9 5l7 7-7 7" />
        </svg>
      </div>
    </Link>
  )
}

export default function HomePage() {
  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="sticky top-0 z-40 border-b border-border bg-background/80 backdrop-blur">
        <div className="mx-auto flex max-w-5xl items-center justify-between px-6 py-4">
          <WordmarkLogo />
          <nav className="flex items-center gap-4 text-sm">
            <Link href="/slip" className="text-muted-foreground hover:text-foreground transition-colors">
              Wajar Slip
            </Link>
          </nav>
        </div>
      </header>

      {/* Hero */}
      <section className="mx-auto max-w-5xl px-6 py-16 text-center">
        <h1 className="text-3xl font-bold tracking-tight text-foreground sm:text-4xl lg:text-5xl">
          Slip Gaji Kamu Dipotong Sesuai Aturan Nggak?
        </h1>
        <p className="mx-auto mt-4 max-w-xl text-base text-muted-foreground sm:text-lg">
          AI audit PPh21 TER, BPJS Kesehatan, JP, JHT dalam 30 detik.
          Gratis, tanpa daftar, 100% privat.
        </p>
        <div className="mt-8 flex flex-col sm:flex-row items-center justify-center gap-4">
          <Link
            href="/slip"
            className="inline-flex items-center justify-center gap-2 rounded-xl bg-emerald-600 px-8 py-4 text-base font-semibold text-white shadow-md transition-all hover:bg-emerald-700 active:scale-95"
          >
            <Scale className="h-5 w-5" aria-hidden="true" />
            Cek Slip Gaji Sekarang — Gratis
          </Link>
          <span className="text-xs text-muted-foreground">Tanpa harus daftar akun</span>
        </div>
      </section>

      {/* Trust badges */}
      <section className="border-y border-border bg-muted/20">
        <div className="mx-auto flex max-w-5xl flex-wrap items-center justify-center gap-6 px-6 py-4">
          <TrustBadge icon={Lock} text="Enkripsi TLS 1.3" />
          <TrustBadge icon={Clock} text="Hapus Otomatis 30 Hari" />
          <TrustBadge icon={Shield} text="Tanpa Nama Tersimpan" />
          <TrustBadge icon={Scale} text="Berbasis PMK 168/2023" />
        </div>
      </section>

      {/* Featured tool */}
      <section className="mx-auto max-w-5xl px-6 py-12">
        <p className="mb-4 text-xs font-semibold uppercase tracking-wide text-muted-foreground">
          Mulai dari sini
        </p>
        <ToolCard
          href="/slip"
          title="Wajar Slip"
          description="Cek apakah potongan PPh21 TER, BPJS Kesehatan, JP, dan JHT di slip gaji kamu sudah sesuai regulasi PMK 168/2023."
          badge="Gratis"
          accent="text-emerald-700 dark:text-emerald-400"
        />
      </section>

      {/* Other tools placeholder */}
      <section className="mx-auto max-w-5xl px-6 py-8">
        <p className="mb-4 text-xs font-semibold uppercase tracking-wide text-muted-foreground">
          Juga tersedia
        </p>
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {[
            { title: "Wajar Gaji", desc: "Bandingkan gajimu dengan benchmark pasar", href: "#" },
            { title: "Wajar Tanah", desc: "Cek harga properti wajar atau kemahalan", href: "#" },
            { title: "Wajar Kabur", desc: "Bandingkan gajigross di luar negeri", href: "#" },
            { title: "Wajar Hidup", desc: "Bandingkan biaya hidup antar kota", href: "#" },
          ].map((tool) => (
            <div
              key={tool.title}
              className="rounded-xl border border-border bg-card px-4 py-3 opacity-60 dark:bg-slate-800/50"
            >
              <p className="text-sm font-semibold text-foreground">{tool.title}</p>
              <p className="mt-0.5 text-xs text-muted-foreground">{tool.desc}</p>
              <p className="mt-1 text-xs text-muted-foreground">(Segera hadir)</p>
            </div>
          ))}
        </div>
      </section>

      {/* Social proof placeholder */}
      <section className="mx-auto max-w-5xl px-6 py-8 text-center">
        <p className="text-sm text-muted-foreground">
          <span className="font-semibold text-foreground">Ratusan slip</span> sudah dicek menggunakan cekwajar.id
        </p>
      </section>

      {/* Footer */}
      <footer className="border-t border-border bg-muted/20">
        <div className="mx-auto max-w-5xl px-6 py-8">
          <div className="flex flex-col items-center gap-4 text-center">
            <WordmarkLogo />
            <p className="text-xs text-muted-foreground">
              Data tidak disimpan. Perhitungan berdasarkan regulasi resmi.
            </p>
            <div className="flex gap-4 text-xs text-muted-foreground">
              <Link href="/privacy-policy" className="hover:text-foreground transition-colors">
                Kebijakan Privasi
              </Link>
            </div>
          </div>
        </div>
      </footer>
    </div>
  )
}
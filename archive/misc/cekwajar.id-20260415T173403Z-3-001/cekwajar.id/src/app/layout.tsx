import type { Metadata, Viewport } from 'next'
import { Plus_Jakarta_Sans, Geist_Mono } from 'next/font/google'
import './globals.css'
import { GlobalNav } from '@/components/layout/GlobalNav'
import { Footer } from '@/components/layout/Footer'
import { validateEnvVars } from '@/lib/config/validate'
import { SettingsProvider } from '@/contexts/settings-context'
import { ClientProviders } from '@/components/ClientProviders'

// Validate required env vars on every server component render
validateEnvVars()

const jakartaSans = Plus_Jakarta_Sans({
  variable: '--font-jakarta',
  subsets: ['latin'],
  weight: ['400', '500', '600', '700', '800'],
})

const geistMono = Geist_Mono({
  variable: '--font-geist-mono',
  subsets: ['latin'],
})

export const metadata: Metadata = {
  title: 'cekwajar.id — Audit Slip Gaji, Benchmark Gaji & Harga Properti',
  description:
    '5 alat gratis untuk karyawan Indonesia. Audit PPh21 & BPJS, benchmark gaji, dan cek harga properti.',
  keywords: ['gaji', 'slip gaji', 'pph21', 'bpjs', 'Indonesia', 'audit', 'benchmark'],
  openGraph: {
    title: 'cekwajar.id',
    description: 'Audit slip gaji, benchmark gaji & harga properti — gratis.',
    locale: 'id_ID',
    type: 'website',
  },
}

export const viewport: Viewport = {
  width: 'device-width',
  initialScale: 1,
  themeColor: [
    { media: '(prefers-color-scheme: light)', color: '#ffffff' },
    { media: '(prefers-color-scheme: dark)', color: '#0f172a' },
  ],
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="id" className={`${jakartaSans.variable} ${geistMono.variable} h-full antialiased`} suppressHydrationWarning>
      <body className="flex min-h-full flex-col">
        {/* Skip to content — accessibility requirement */}
        <a
          href="#main-content"
          className="sr-only focus:not-sr-only focus:fixed focus:top-4 focus:left-4 focus:z-[100] focus:bg-emerald-600 focus:text-white focus:px-4 focus:py-2 focus:rounded-lg focus:text-sm focus:font-medium"
        >
          Langsung ke konten utama
        </a>
        <SettingsProvider>
          <ClientProviders>
            <GlobalNav />
            <main id="main-content" className="flex-1">{children}</main>
            <Footer />
          </ClientProviders>
        </SettingsProvider>
      </body>
    </html>
  )
}

import type { Metadata } from "next"
import { Inter } from "next/font/google"
import "./globals.css"

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-inter",
  display: "swap",
})

export const metadata: Metadata = {
  title: "Cek Potongan Gaji | Wajar Slip — cekwajar.id",
  description: "Cek PPh 21 TER + BPJS sesuai regulasi 2024. Gratis, instan, 100% privat.",
  keywords: ["cek gaji", "PPh 21", "BPJS", "TER", "potongan gaji", "slip gaji"],
  openGraph: {
    title: "Wajar Slip — Potongan gaji lo bener gak?",
    description: "Cek PPh 21 TER + BPJS sesuai regulasi 2024 dalam 30 detik.",
    url: "https://cekwajar.id/slip",
    siteName: "cekwajar.id",
    locale: "id_ID",
    type: "website",
  },
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="id" suppressHydrationWarning>
      <body className={`${inter.variable} font-sans antialiased`}>{children}</body>
    </html>
  )
}

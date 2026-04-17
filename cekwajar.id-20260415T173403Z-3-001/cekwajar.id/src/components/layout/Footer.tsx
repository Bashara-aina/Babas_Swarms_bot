// ══════════════════════════════════════════════════════════════════════════════
// cekwajar.id — Footer
// ══════════════════════════════════════════════════════════════════════════════

import Link from 'next/link'
import { WordmarkLogo } from '@/components/WordmarkLogo'

export function Footer() {
  return (
    <footer className="border-t bg-muted">
      <div className="mx-auto max-w-5xl px-4 py-8 lg:px-6">
        <div className="grid gap-6 md:grid-cols-3">
          {/* Brand */}
          <div>
            <WordmarkLogo size="sm" />
            <p className="mt-2 text-xs text-muted-foreground">
              5 alat gratis untuk karyawan Indonesia.<br />
              Audit slip gaji, benchmark gaji, dan cek harga properti.
            </p>
          </div>

          {/* Tools */}
          <div>
            <p className="text-sm font-semibold text-foreground">Alat</p>
            <ul className="mt-2 space-y-1">
              <li>
                <Link href="/wajar-slip" className="text-xs text-muted-foreground hover:text-emerald-600">
                  Wajar Slip — Audit PPh21 & BPJS
                </Link>
              </li>
              <li>
                <Link href="/wajar-gaji" className="text-xs text-muted-foreground hover:text-emerald-600">
                  Wajar Gaji — Benchmark Gaji
                </Link>
              </li>
              <li>
                <Link href="/wajar-tanah" className="text-xs text-muted-foreground hover:text-emerald-600">
                  Wajar Tanah — Cek Harga Properti
                </Link>
              </li>
              <li>
                <Link href="/wajar-kabur" className="text-xs text-muted-foreground hover:text-emerald-600">
                  Wajar Kabur — Perbandingan LN
                </Link>
              </li>
              <li>
                <Link href="/wajar-hidup" className="text-xs text-muted-foreground hover:text-emerald-600">
                  Wajar Hidup — Biaya Hidup Kota
                </Link>
              </li>
            </ul>
          </div>

          {/* Legal */}
          <div>
            <p className="text-sm font-semibold text-foreground">Legal</p>
            <ul className="mt-2 space-y-1">
              <li>
                <Link href="/privacy-policy" className="text-xs text-muted-foreground hover:text-emerald-600">
                  Kebijakan Privasi
                </Link>
              </li>
              <li>
                <Link href="/terms" className="text-xs text-muted-foreground hover:text-emerald-600">
                  Syarat & Ketentuan
                </Link>
              </li>
              <li>
                <Link href="/kontak" className="text-xs text-muted-foreground hover:text-emerald-600">
                  Hubungi Kami
                </Link>
              </li>
            </ul>
          </div>
        </div>

        <div className="mt-6 border-t border-border pt-4 text-center">
          <p className="text-xs text-muted-foreground">
            &copy; {new Date().getFullYear()} cekwajar.id — Hasil kalkulasi bersifat indikatif, bukan nasihat keuangan.
          </p>
        </div>
      </div>
    </footer>
  )
}

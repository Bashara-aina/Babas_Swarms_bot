// ==============================================================================
// cekwajar.id — Terms of Service
// Static server component in Bahasa Indonesia
// ==============================================================================

import type { Metadata } from 'next'

export const metadata: Metadata = {
  title: 'Syarat dan Ketentuan — cekwajar.id',
  description: 'Syarat dan ketentuan penggunaan layanan cekwajar.id.',
}

export default function TermsPage() {
  return (
    <div className="min-h-screen bg-muted">
      <div className="mx-auto max-w-3xl px-4 py-12">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-foreground mb-2">Syarat dan Ketentuan</h1>
          <p className="text-sm text-muted-foreground">Terakhir diperbarui: April 2026</p>
        </div>

        <div className="prose max-w-none space-y-8">

          {/* Section 1 */}
          <section>
            <h2 className="text-xl font-semibold text-foreground mb-3">1. Deskripsi Layanan</h2>
            <div className="space-y-3 text-sm text-muted-foreground">
              <p>cekwajar.id menyediakan layanan konsultasi dan analisis berbasis data untuk membantu pengguna memahami hak-upah mereka di Indonesia. Layanan utama meliputi:</p>
              <ul className="list-disc pl-5 space-y-1">
                <li><strong>Wajar Slip</strong> — Analisis kepatuhan slip gaji terhadap peraturan ketenagakerjaan Indonesia (PPn 36/2021, UU Ketenagakerjaan 13/2003).</li>
                <li><strong>Wajar Gaji</strong> — Benchmark gaji berdasarkan grade dan provinsi.</li>
                <li><strong>Wajar Hidup</strong> — Perbandingan biaya hidup antar kota di Indonesia.</li>
                <li><strong>Wajar Kabur</strong> — Perbandingan daya beli internasional (PPP).</li>
                <li><strong>Wajar Tanah</strong> — Analisis kelayakan properti.</li>
              </ul>
            </div>
          </section>

          {/* Section 2 */}
          <section>
            <h2 className="text-xl font-semibold text-foreground mb-3">2. Batasan Tanggung Jawab</h2>
            <div className="space-y-3 text-sm text-muted-foreground">
              <p>
                <strong>Kalkulasi bersifat indikatif.</strong> Semua hasil kalkulasi yang ditampilkan oleh cekwajar.id merupakan perkiraan berdasarkan data dan formula yang kami gunakan. Hasil ini{' '}
                <em>tidak constitue nasihat hukum atau konsultasi profesional</em>. Pengguna disarankan untuk memverifikasi dengan sumber resmi atau berkonsultasi dengan profesional人力资源 sebelum mengambil keputusan berdasarkan hasil kami.
              </p>
              <p>
                cekwajar.id tidak bertanggung jawab atas kerugian langsung maupun tidak langsung yang timbul dari penggunaan layanan ini. Selalu konsultasikan dengan HR departemen, sindical, atau penasihat hukum untuk kepastian hak-hak kamu.
              </p>
            </div>
          </section>

          {/* Section 3 */}
          <section>
            <h2 className="text-xl font-semibold text-foreground mb-3">3. Hak Kekayaan Intelektual</h2>
            <div className="space-y-3 text-sm text-muted-foreground">
              <p>Semua konten, logo, desain, dan fitur yang ada di cekwajar.id dilindungi oleh hak cipta dan hak kekayaan intelektual lainnya. Penggunaan tanpa izin tertulis dilarang.</p>
              <p>Data benchmark yang berasal dari sumber publik (BPS, World Bank, dll.) dapat digunakan untuk tujuan referensi dengan atribusi yang sesuai.</p>
            </div>
          </section>

          {/* Section 4 */}
          <section>
            <h2 className="text-xl font-semibold text-foreground mb-3">4. Larangan Penggunaan</h2>
            <div className="space-y-3 text-sm text-muted-foreground">
              <p>Penggunaan layanan ini untuk tujuan berikut dilarang:</p>
              <ul className="list-disc pl-5 space-y-1">
                <li>Mengirimkan slip gaji palsu atau dimanipulasi untuk tujuan penipuan.</li>
                <li>Menggunakan layanan untuk mengidentifikasi dan menarget individu tertentu tanpa persetujuan.</li>
                <li>Menggunakan automated bot atau scraper untuk mengakses layanan.</li>
                <li>Mereproduksi atau mendistribusikan konten premium tanpa izin.</li>
              </ul>
              <p className="mt-2 p-3 bg-red-50 border border-red-200 rounded-lg text-xs">
                Pelanggaran terhadap larangan ini dapat mengakibatkan penghentian akun dan tindakan hukum lebih lanjut.
              </p>
            </div>
          </section>

          {/* Section 5 */}
          <section>
            <h2 className="text-xl font-semibold text-foreground mb-3">5. Paket Berlangganan dan Pembayaran</h2>
            <div className="space-y-3 text-sm text-muted-foreground">
              <ul className="list-disc pl-5 space-y-1">
                <li>Pembayaran dilakukan melalui Midtrans. Kami tidak menyimpan data pembayaran penuh.</li>
                <li>Langganan diperpanjang secara otomatis pada akhir periode kecuali dibatalkan.</li>
                <li>Pembatalan dapat dilakukan kapan saja melalui halaman akun atau menghubungi support.</li>
                <li>Pengembalian dana (refund) mengikuti kebijakan Midtrans dan diberikan dalam kasus langka.</li>
                <li>Masa percobaan atau jaminan uang kembali tidak tersedia saat ini.</li>
              </ul>
            </div>
          </section>

          {/* Section 6 */}
          <section>
            <h2 className="text-xl font-semibold text-foreground mb-3">6. Pembatasan Layanan</h2>
            <div className="space-y-3 text-sm text-muted-foreground">
              <ul className="list-disc pl-5 space-y-1">
                <li>Pengguna gratis dibatasi hingga 3 audit slip gaji per hari.</li>
                <li>Data benchmark kota dan negara tertentu mungkin tidak tersedia untuk paket gratis.</li>
                <li>Layanan mungkin mengalami downtime terjadwal untuk pemeliharaan.</li>
                <li>Kami tidak menjamin ketersediaan 100% layanan.</li>
              </ul>
            </div>
          </section>

          {/* Section 7 */}
          <section>
            <h2 className="text-xl font-semibold text-foreground mb-3">7. Privasi dan Cookie</h2>
            <div className="space-y-3 text-sm text-muted-foreground">
              <p> Penggunaan layanan ini diatur oleh Kebijakan Privasi kami. Dengan menggunakan cekwajar.id, kamu menyetujui pengumpulan dan penggunaan data sesuai kebijakan tersebut.</p>
              <p>Kebijakan Privasi dapat dibaca di <a href="/privacy-policy" className="text-emerald-600 hover:underline">Kebijakan Privasi</a>.</p>
            </div>
          </section>

          {/* Section 8 */}
          <section>
            <h2 className="text-xl font-semibold text-foreground mb-3">8. Hukum yang Berlaku</h2>
            <div className="space-y-3 text-sm text-muted-foreground">
              <p>Layanan ini beroperasi di Indonesia dan diatur oleh hukum Republik Indonesia. Setiap perselisihan yang timbul dari penggunaan layanan ini akan diselesaikan melalui Badan Arbitrase atau Pengadilan Negeri yang berwenang di Indonesia.</p>
            </div>
          </section>

          {/* Section 9 */}
          <section>
            <h2 className="text-xl font-semibold text-foreground mb-3">9. Perubahan Syarat</h2>
            <div className="space-y-3 text-sm text-muted-foreground">
              <p>Kami berhak mengubah syarat dan ketentuan ini sewaktu-waktu. Perubahan signifikan akan diumumkan melalui email atau pemberitahuan di situs. Penggunaan berkelanjutan setelah perubahan berarti kamu terikat pada syarat yang diperbarui.</p>
            </div>
          </section>

          {/* Section 10 */}
          <section>
            <h2 className="text-xl font-semibold text-foreground mb-3">10. Kontak</h2>
            <div className="space-y-3 text-sm text-muted-foreground">
              <p>Untuk pertanyaan terkait syarat dan ketentuan:</p>
              <ul className="list-disc pl-5 space-y-1">
                <li>Email: <a href="mailto:support@cekwajar.id" className="text-emerald-600 hover:underline">support@cekwajar.id</a></li>
              </ul>
            </div>
          </section>

        </div>
      </div>
    </div>
  )
}

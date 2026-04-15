// ==============================================================================
// cekwajar.id — Privacy Policy
// Static server component in Bahasa Indonesia
// ==============================================================================

import type { Metadata } from 'next'

export const metadata: Metadata = {
  title: 'Kebijakan Privasi — cekwajar.id',
  description: 'Kebijakan privasi cekwajar.id. Bagaimana kami mengumpulkan, menggunakan, dan melindungi data kamu.',
}

export default function PrivacyPolicyPage() {
  return (
    <div className="min-h-screen bg-slate-50">
      <div className="mx-auto max-w-3xl px-4 py-12">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-slate-900 mb-2">Kebijakan Privasi</h1>
          <p className="text-sm text-slate-500">Terakhir diperbarui: April 2026</p>
        </div>

        <div className="prose prose-slate max-w-none space-y-8">

          {/* Section 1 */}
          <section>
            <h2 className="text-xl font-semibold text-slate-800 mb-3">1. Data Apa yang Kami Kumpulkan</h2>
            <div className="space-y-3 text-sm text-slate-600">
              <p>Kami mengumpulkan data berikut untuk menyediakan layanan cekwajar.id:</p>
              <ul className="list-disc pl-5 space-y-1">
                <li><strong>Data slip gaji</strong> — Foto atau teks slip gaji yang kamu upload untuk dianalisis. Slip gaji diproses dan tidak disimpan lebih dari 30 hari.</li>
                <li><strong>Data akun</strong> — Nama, email, dan informasi langganan yang kamu berikan saat mendaftar.</li>
                <li><strong>Data penggunaan</strong> — Metadata penggunaan fitur (jumlah audit, kota yang dibandingkan, dll.) untuk meningkatkan layanan.</li>
                <li><strong>DataAnonim</strong> — Submission gaji yang kamu pilih untuk dianonimkan. Data ini tidak dapat dilacak ke akun kamu.</li>
              </ul>
            </div>
          </section>

          {/* Section 2 */}
          <section>
            <h2 className="text-xl font-semibold text-slate-800 mb-3">2. Bagaimana Kami Menggunakan Data Kamu</h2>
            <div className="space-y-3 text-sm text-slate-600">
              <ul className="list-disc pl-5 space-y-1">
                <li>Menyediakan layanan audit slip gaji dan analisis benchmark.</li>
                <li>Mengaktifkan dan mengelola langganan premium kamu.</li>
                <li>Mengirim notifikasi terkait langganan dan keamanan akun.</li>
                <li>Meningkatkan akurasi kalkulasi dan fitur berdasarkan pola penggunaan.</li>
              </ul>
              <p className="mt-3 p-3 bg-amber-50 border border-amber-200 rounded-lg text-xs">
                <strong>Kami tidak menjual data kamu.</strong> Data tidak pernah diberikan ke pihak ketiga untuk tujuan pemasaran.
              </p>
            </div>
          </section>

          {/* Section 3 */}
          <section>
            <h2 className="text-xl font-semibold text-slate-800 mb-3">3. Retensi dan Penghapusan Data</h2>
            <div className="space-y-3 text-sm text-slate-600">
              <p>Kami menyimpan data dengan durasi berikut:</p>
              <table className="w-full text-xs border-collapse">
                <thead>
                  <tr className="border-b border-slate-200">
                    <th className="text-left py-2 font-semibold text-slate-700">Jenis Data</th>
                    <th className="text-left py-2 font-semibold text-slate-700">Durasi Penyimpanan</th>
                  </tr>
                </thead>
                <tbody className="text-slate-600">
                  <tr className="border-b border-slate-100"><td className="py-2">Foto slip gaji</td><td className="py-2">30 hari, otomatis dihapus</td></tr>
                  <tr className="border-b border-slate-100"><td className="py-2">Data audit slip</td><td className="py-2">12 bulan</td></tr>
                  <tr className="border-b border-slate-100"><td className="py-2">Submission gaji anonim</td><td className="py-2">24 bulan</td></tr>
                  <tr className="border-b border-slate-100"><td className="py-2">Transaksi pembayaran</td><td className="py-2">3 tahun (kewajiban pajak)</td></tr>
                  <tr><td className="py-2">Akun pengguna</td><td className="py-2">Sampai penghapusan diminta</td></tr>
                </tbody>
              </table>
              <p className="mt-2">Untuk meminta penghapusan data, kirim email ke <a href="mailto:privacy@cekwajar.id" className="text-emerald-600 hover:underline">privacy@cekwajar.id</a>.</p>
            </div>
          </section>

          {/* Section 4 */}
          <section>
            <h2 className="text-xl font-semibold text-slate-800 mb-3">4. Hak Kamu (UU PDP No. 27/2022)</h2>
            <div className="space-y-3 text-sm text-slate-600">
              <p>Berdasarkan Undang-Undang Perlindungan Data Pribadi (UU PDP) No. 27 Tahun 2022, kamu berhak:</p>
              <ul className="list-disc pl-5 space-y-1">
                <li><strong>Mengakses</strong> — Meminta salinan data pribadi yang kami miliki.</li>
                <li><strong>Memperbaiki</strong> — Meminta koreksi data yang tidak akurat.</li>
                <li><strong>Menghapus</strong> — Meminta penghapusan data dalam kondisi tertentu.</li>
                <li><strong>Menarik persetujuan</strong> — Berhenti memproses data sewaktu-waktu.</li>
                <li><strong>Mengajukan keberatan</strong> — Berkeberatan atas pemrosesan data tertentu.</li>
              </ul>
              <p className="mt-2">Untuk menggunakan hak-hak ini, hubungi <a href="mailto:privacy@cekwajar.id" className="text-emerald-600 hover:underline">privacy@cekwajar.id</a>.</p>
            </div>
          </section>

          {/* Section 5 */}
          <section>
            <h2 className="text-xl font-semibold text-slate-800 mb-3">5. Keamanan Data</h2>
            <div className="space-y-3 text-sm text-slate-600">
              <p>Kami menggunakan langkah-langkah keamanan berikut:</p>
              <ul className="list-disc pl-5 space-y-1">
                <li>Enkripsi TLS untuk semua komunikasi data.</li>
                <li>Penyimpanan data di infrastruktur Supabase dengan enkripsi at-rest.</li>
                <li>Pembatasan akses service role hanya untuk operasi internal.</li>
                <li>Token Midtrans (Snap) yang dihosting oleh Midtrans — kami tidak menyimpan data pembayaran penuh.</li>
              </ul>
              <p className="mt-2">Meskipun kami 최선을, tidak ada sistem yang 100% aman. Kami mendorong kamu untuk menggunakan kata sandi yang kuat dan unik.</p>
            </div>
          </section>

          {/* Section 6 */}
          <section>
            <h2 className="text-xl font-semibold text-slate-800 mb-3">6. Cookie</h2>
            <div className="space-y-3 text-sm text-slate-600">
              <p>cekwajar.id menggunakan cookie untuk:</p>
              <ul className="list-disc pl-5 space-y-1">
                <li><strong>Autentikasi</strong> — Mempertahankan sesi login kamu.</li>
                <li><strong>Preferensi</strong> — Menyimpan pilihan cookie consent kamu.</li>
              </ul>
              <p>Cookie tidak digunakan untuk pelacakan iklan atau dibagikan ke pihak ketiga.</p>
            </div>
          </section>

          {/* Section 7 */}
          <section>
            <h2 className="text-xl font-semibold text-slate-800 mb-3">7. Perubahan Kebijakan</h2>
            <div className="space-y-3 text-sm text-slate-600">
              <p>Kami dapat memperbarui kebijakan ini sewaktu-waktu. Perubahan signifikan akan diumumkan melalui email atau pemberitahuan di situs. Penggunaan berkelanjutan setelah perubahan berarti kamu menyetujui kebijakan yang diperbarui.</p>
            </div>
          </section>

          {/* Section 8 */}
          <section>
            <h2 className="text-xl font-semibold text-slate-800 mb-3">8. Kontak</h2>
            <div className="space-y-3 text-sm text-slate-600">
              <p>Untuk pertanyaan tentang kebijakan privasi ini:</p>
              <ul className="list-disc pl-5 space-y-1">
                <li>Email: <a href="mailto:privacy@cekwajar.id" className="text-emerald-600 hover:underline">privacy@cekwajar.id</a></li>
              </ul>
              <p className="mt-3 p-3 bg-slate-100 rounded-lg text-xs">
                <strong>Pengendali Data:</strong> cekwajar.id. Data disimpan di infrastruktur Supabase (PT Supabase Indonesia).
              </p>
            </div>
          </section>

        </div>
      </div>
    </div>
  )
}

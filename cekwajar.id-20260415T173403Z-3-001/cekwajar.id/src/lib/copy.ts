/**
 * cekwajar.id Brand Voice
 * ========================
 * Tone: Teman finansial yang tahu hukum ketenagakerjaan.
 * Voice: Berpihak pada karyawan. Bicara seperti teman pintar, bukan portal pemerintah.
 * Never: corporate, passive, blame-shifting, overly formal.
 * Always: specific, actionable, warm, slightly combative on behalf of the user.
 */

export const COPY = {
  // ─── Loading States ─────────────────────────────────────────
  loading: {
    calculating: 'Lagi ngitung PPh21 kamu... ⚡',
    fetchingData: 'Ambil data dari database... 🗺️',
    analyzingSlip: 'AI lagi baca slip gaji kamu...',
    fetchingBenchmark: 'Cari data gaji untuk posisi ini...',
    analyzingProperty: 'Cek harga properti di area tersebut...',
    fetchingPPP: 'Ambil data daya beli dari World Bank...',
    uploadingFile: 'Upload foto slip gaji...',
    ocrProcessing: 'OCR lagi baca teks dari foto kamu...',
    generic: 'Tunggu sebentar...',
  },

  // ─── Success States ──────────────────────────────────────────
  success: {
    sesuai: 'Slip gaji kamu 100% sesuai regulasi ✓',
    sesuaiSub: 'HRD-mu taat aturan bulan ini. Keren! 🎉',
    uploadSuccess: 'Foto berhasil dibaca! Data sudah diisi otomatis.',
    paymentSuccess: 'Pembayaran berhasil! Paket aktif sekarang.',
    submittedSalary: 'Data gaji kamu sudah masuk. Terima kasih kontribusinya! 🙏',
  },

  // ─── Error Messages (with action guidance) ──────────────────
  error: {
    cityNotFound: 'Kota ini belum ada di database UMK kami. Coba kota terdekat, atau pilih dari daftar.',
    invalidNumber: 'Angka ini keliatan kurang pas — coba cek lagi ya.',
    uploadFailed: 'Upload gagal. File terlalu besar atau bukan gambar? Coba lagi atau isi manual di bawah.',
    ocrFailed: 'OCR tidak bisa baca foto ini. Coba foto ulang dengan pencahayaan lebih baik, atau isi manual.',
    ocrLowConfidence: 'Hasil OCR kurang yakin di beberapa angka. Cek dan koreksi dulu sebelum lanjut.',
    networkError: 'Koneksi bermasalah. Cek internet kamu dan coba lagi.',
    noBenchmarkData: 'Belum ada data gaji untuk posisi ini di kota tersebut. Coba kota terdekat atau jabatan yang lebih umum.',
    noPropertyData: 'Belum ada data properti di area ini. Coba kecamatan terdekat.',
    sessionExpired: 'Sesi kamu habis. Login lagi untuk lanjut.',
    genericError: 'Ada yang salah di server kami. Tim sudah dikabari. Coba lagi dalam beberapa menit.',
    formValidation: 'Ada kolom yang belum diisi atau nilainya tidak valid. Cek yang ditandai merah.',
    paymentFailed: 'Pembayaran gagal. Cek detail kartu kamu atau coba metode lain.',
  },

  // ─── Empty States ───────────────────────────────────────────
  empty: {
    auditHistory: 'Belum ada riwayat audit. Mulai cek slip gaji pertama kamu — butuh 30 detik.',
    auditHistoryCTA: 'Audit Slip Gaji Sekarang →',
    noBenchmark: 'Data gaji untuk posisi ini belum tersedia. Jadilah yang pertama kontribusi! 🙌',
    noNotifications: 'Tidak ada notifikasi.',
    noSavedProperties: 'Belum ada properti yang disimpan.',
  },

  // ─── Violation Descriptions ─────────────────────────────────
  violations: {
    V01: {
      title: 'PPh21 Dibulatkan Salah',
      description: 'Pembulatan PPh21 di slip tidak sesuai aturan PMK 168/2023. Selisihnya mungkin kecil, tapi tetap tidak benar secara regulasi.',
      recommendation: 'Tunjukkan perbedaan pembulatan ke HRD dan minta koreksi di slip bulan depan.',
    },
    V02: {
      title: 'PPh21 Tidak Dipotong',
      description: 'HRD kamu tidak memotong PPh21 bulan ini. Ini artinya kewajiban pajak itu tetap ada — kamu yang akan bayar lebih besar di akhir tahun, bukan perusahaan.',
      recommendation: 'Tanyakan ke HRD kenapa PPh21 tidak dipotong. Ini kewajiban perusahaan, bukan pilihan.',
    },
    V03: {
      title: 'PPh21 Dipotong Berlebih',
      description: 'PPh21 yang dipotong lebih besar dari yang seharusnya berdasarkan tarif TER. Kamu membayar pajak lebih dari kewajiban.',
      recommendation: 'Minta HRD untuk rekap dan koreksi selisih PPh21. Kelebihan bisa dikembalikan atau dikompensasi.',
    },
    V04: {
      title: 'JP Karyawan Kurang Dipotong',
      description: 'Jaminan Pensiun yang dipotong dari slip-mu lebih kecil dari 1% seharusnya. Hak pensiun BPJS-mu tidak terpenuhi bulan ini.',
      recommendation: 'Cek apakah perusahaanmu terdaftar BPJS TK. Jika iya, minta rekap iuran JP dari HR.',
    },
    V05: {
      title: 'JHT Karyawan Kurang Dipotong',
      description: 'Jaminan Hari Tua yang dipotong tidak sesuai — seharusnya 2% dari gaji. Ini mempengaruhi saldo JHT kamu yang bisa dicairkan saat resign atau pensiun.',
      recommendation: 'Minta slip BPJS TK untuk cek apakah iuran benar-benar disetorkan sesuai gaji aktual.',
    },
    V06: {
      title: 'Gaji di Bawah UMK — PELANGGARAN HUKUM',
      description: 'Gaji pokokmu berada di bawah Upah Minimum Kota yang berlaku tahun ini. Ini bukan sekadar ketidaksesuaian — ini pelanggaran UU Ketenagakerjaan No.13/2003 Pasal 90. Perusahaan bisa dikenai sanksi pidana.',
      recommendation: 'Kamu berhak melaporkan ini ke Dinas Tenaga Kerja setempat. Simpan bukti slip gaji dan kontrak kerja. Konsultasikan dengan LBH atau Disnaker.',
    },
    V07: {
      title: 'BPJS Kesehatan Kurang Dipotong',
      description: 'Potongan BPJS Kesehatan dari gajimu lebih kecil dari 1% yang seharusnya. Ini bisa mempengaruhi status kepesertaan BPJS Kesehatan aktif kamu.',
      recommendation: 'Cek status kepesertaan BPJS Kesehatan di aplikasi Mobile JKN. Hubungi HR untuk klarifikasi iuran yang dibayarkan.',
    },
  },

  // ─── Verdict Copy ────────────────────────────────────────────
  verdict: {
    sesuai: {
      title: 'Slip Gaji Kamu SESUAI ✓',
      subtitle: 'Semua komponen PPh21 dan BPJS sudah benar.',
      note: 'HRD-mu taat regulasi bulan ini. 🎉',
    },
    pelanggaran: {
      title: (count: number) => `${count} Pelanggaran Ditemukan`,
      subtitle: 'Kamu berhak tahu ini. Cek detail di bawah.',
      critical: 'Ada pelanggaran bersifat KRITIS — segera tindaklanjuti.',
    },
  },

  // ─── Form Copy ────────────────────────────────────────────────
  form: {
    submitSlip: 'Cek Slip Gaji Sekarang',
    submitting: 'Lagi ngitung PPh21 kamu... ⚡',
    uploadBtn: 'Upload Foto Slip Gaji',
    orManual: 'atau isi manual di bawah',
    tryAgain: 'Coba Lagi',
    back: '← Kembali',
    next: 'Lanjut →',
    review: 'Review & Cek',
    optional: '(opsional)',
    notSure: 'Tidak tahu? → gunakan nilai 0',
  },

  // ─── General UI ───────────────────────────────────────────────
  ui: {
    upgradeBtn: 'Upgrade Paket Basic',
    upgradeSubtext: 'Kurang dari 1 kopi per hari',
    shareWA: 'Bagikan ke WhatsApp',
    shareResult: 'Bagikan Hasil',
    seeDetails: 'Lihat Detail',
    hideDetails: 'Sembunyikan',
    learnMore: 'Pelajari lebih lanjut →',
    close: 'Tutup',
    copyLink: 'Salin Link',
    copied: 'Tersalin! ✓',
  },
}

export const UPGRADE_COPY = {
  priceLabel: 'Rp 29K/bulan',
  valueFrame: 'Kurang dari 1 kopi per hari',
  roiFrame: 'Jika selisih PPh21 Rp 50K/bulan → BEP 2 minggu',
  ctaPrimary: 'Upgrade Paket Basic',
  ctaSecondary: 'Lihat paket lengkap →',
  cancelAnytime: 'Bisa dibatalkan kapan saja',
  trialNote: 'Tidak ada kontrak, tidak ada biaya tersembunyi',
}

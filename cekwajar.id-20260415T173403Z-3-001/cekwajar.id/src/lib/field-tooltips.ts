export const FIELD_TOOLTIPS = {
  ptkp: 'Status pajak penghasilan kamu. TK = Tidak Kawin, K = Kawin. Angka setelah huruf = jumlah tanggungan. Contoh: K/1 = Kawin dengan 1 anak tanggungan.',
  npwp: 'Nomor Pokok Wajib Pajak. Karyawan dengan NPWP dikenakan tarif PPh21 normal. Tanpa NPWP, tarif lebih tinggi 20%.',
  gapok: 'Gaji bruto bulanan sebelum dipotong pajak dan iuran BPJS.',
  tunjangan: 'Semua tunjangan tetap di luar gaji pokok: tunjangan jabatan, transport, makan, dan sejenisnya.',
  jht_karyawan: 'JHT (Jaminan Hari Tua) dipotong 2% dari gaji bulanan dan menjadi tabungan hari tua.',
  jht_perusahaan: 'Kontribusi JHT dari perusahaan adalah 3.7% dan tidak mengurangi gaji yang diterima karyawan.',
  jp_karyawan: 'JP (Jaminan Pensiun) dipotong 1% dari gaji sesuai aturan BPJS Ketenagakerjaan.',
  jp_perusahaan: 'Kontribusi JP dari perusahaan adalah 2% dan tidak dipotong dari gaji karyawan.',
  jkk: 'JKK (Jaminan Kecelakaan Kerja) ditanggung perusahaan, bukan potongan karyawan.',
  jkm: 'JKM (Jaminan Kematian) ditanggung perusahaan sebesar 0.3% dari gaji.',
  bpjs_kes_karyawan: 'BPJS Kesehatan karyawan umumnya 1% dari gaji sesuai ketentuan kepesertaan.',
  bpjs_kes_perusahaan: 'Kontribusi BPJS Kesehatan dari perusahaan sebesar 4% dari gaji.',
  pph21: 'PPh21 adalah pajak penghasilan karyawan yang dipotong perusahaan sesuai metode TER.',
  kota: 'Kota tempat kamu bekerja (bukan domisili) untuk referensi UMK.',
  bulan: 'Bulan slip gaji yang diaudit. Tarif UMK/aturan berlaku per periode.',
  take_home: 'Take home pay adalah jumlah gaji bersih yang benar-benar diterima setelah semua potongan.',
} as const


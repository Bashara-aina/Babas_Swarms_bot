# Evaluasi & Perbaikan Output Bot: Log Post Generator
> Analisis mendalam dari 6 post yang dihasilkan bot
> Beserta revisi per post dan tambahan aturan untuk bot
> Versi: 1.0 | April 2026

---

## RINGKASAN EVALUASI

| Post | Kekuatan | Masalah Utama | Skor |
|---|---|---|---|
| POST 1 | Hook cerita lucu relatable | CTA brand terlalu cepat, "saya" tidak konsisten | 6/10 |
| POST 2 | List 3 poin bagus, cerita konkret | Brand mention 2x, "saya" vs "aku" campur, tone menggurui | 5/10 |
| POST 3 | Harga spesifik bagus | Buka dengan "Kost deket UNS" terlalu bland, langsung promo | 4/10 |
| POST 4 | Format A/B pilihan bagus, bikin reply | "Hai yang lagi nyari kost" = terasa newsletter | 7/10 |
| POST 5 | Cerita lucu dan relatable | CTA terlalu langsung, moral terasa dipaksakan | 6/10 |
| POST 6 | - | Statistik 70% tidak ada sumbernya, "neighbors" bocor Inggris, tone menakut-nakuti | 3/10 |

---

## DIAGNOSIS MASALAH YANG MASIH ADA

### MASALAH 1: Brand Mention Terlalu Sering

Bot menyebut rumahlabuh.com di SETIAP post, bahkan post 1, 2, 3, 5, dan 6.

```
Dari panduan: mention brand HANYA di post terakhir.

Kenapa penting:
Kalau setiap post langsung ke rumahlabuh.com, thread terasa iklan.
Algoritma Threads mendeteksi pola ini dan menurunkan reach-nya.
Orang juga skip kalau tiap baris ada nama brand.
```

### MASALAH 2: Statistik Tidak Berdasar

```
POST 6 nulis: "70% orang menyesal pilih kost..."

Ini bahaya.
Statistik yang tidak ada sumbernya justru merusak kredibilitas.
Orang yang kritis akan langsung bertanya "data ini dari mana?"
Dan kalau nggak bisa dijawab, brand-nya yang kena.

Aturan tambahan: Jangan pakai angka persentase kecuali dari sumber nyata.
Kalau mau kasih kesan "banyak orang", pakai frasa natural:
"Banyak yang nyesel..." atau "Hampir semua orang yang gue tanya..."
```

### MASALAH 3: Pronoun Tidak Konsisten

```
Dalam satu thread, bot pakai tiga style berbeda:
- "saya" (POST 1, 2, 3, 5)
- "kami" (POST 6: "sudah kami verifikasi")
- "kamu" (POST 3, 6)

Aturan konsistensi pronoun:
Pilih SATU register dan pakai konsisten dalam satu thread.

Pilihan yang disarankan untuk rumahlabuh.com:
- Register informal: "gue/lo" (untuk target mahasiswa/anak muda)
- Register semi-formal: "aku/kamu" (lebih luas, semua umur)
- Jangan campur dalam satu thread
- "kami" hanya boleh dalam konteks brand official, bukan konten personal
```

### MASALAH 4: Bocor Bahasa Inggris

```
POST 6: "neighbors, keamanan, dan akses..."

"neighbors" adalah kata Inggris yang punya padanan langsung: "tetangga"
Ini persis gejala yang sudah didokumentasi di tone_guide_v2.md.

Tambahan ke daftar filter bot:
- "neighbors" -> "tetangga"
- "experience" (dalam konteks ini) -> "hal serupa"
- "gecko" di POST 2 sebenarnya boleh karena sudah umum di Indonesia
```

### MASALAH 5: Pembuka "Hai yang lagi nyari kost"

```
POST 4 buka dengan: "Hai yang lagi nyari kost di Solo:"

Ini gaya newsletter atau blast WA, bukan Threads.
Terasa seperti bot menyapa subscriber, bukan seseorang nulis untuk teman.

Ganti dengan langsung ke isi atau pertanyaan:
"Kalau lo dikasih pilihan..."
"Satu pertanyaan buat yang lagi cari kost:"
```

### MASALAH 6: Moral Dipaksakan di Akhir Post 5

```
POST 5 nulis: "Kalau kamu nggak mau experience serupa, cek dulu lingkungan sekitar kost..."

Setelah cerita lucu tentang kost deket club malam,
langsung loncat ke moral lesson terasa tidak natural.

Cerita yang bagus membiarkan pembaca ambil kesimpulan sendiri.
Atau kalau mau ada insight, biarkan mengalir dari ceritanya,
bukan dijejalkan sebagai kalimat penutup yang terasa campaign.
```

### MASALAH 7: Tone POST 6 Menakut-nakuti

```
"Jangan ulangi kesalahan mereka."

Ini tone negatif yang tidak perlu.
Sama seperti disclaimer "No spam" sebelumnya, ini terasa defensif.

Orang tidak suka diancam walaupun halus.
Ganti dengan framing positif:
"Supaya nggak perlu nyesel belakangan..."
Atau (lebih baik): hapus dan ganti dengan cerita atau pertanyaan.
```

---

## REVISI PER POST

### POST 1 (asli)
```
Dulu saya mau tanya alamat kost ke anak kos, eh malah dikasih cerita penuh.
"Eh kost saya tuh deket campus, murah, wifi kenceng..."
3 menit belum selesai.
Saya jadi udah tau nama ibu kost-nya, hobi dia, bahkan makanannya tadi pagi.

Tapi alamatnya? Cuma "deket kampus".
Saya: ???

Kalau mau kost yang beneran deket dan lengkap informasinya, cek aja di rumahlabuh.com.
```

### POST 1 (revisi)
```
Tanya kost ke anak kos:

"Deket kampus, murah, wifi kenceng, ibu kostnya baik..."
3 menit belum selesai.

Udah tau nama ibu kostnya, hobinya, bahkan makannya tadi pagi.

Alamatnya? "Deket kampus."

Gue: ???
```
*Hapus CTA brand — ini post pembuka, bukan closing.*

---

### POST 2 (asli)
```
Stop nyari kost cuma dari foto.
Serius.
[cerita dinding cat tebal, gecko, pintu ngegelembung]
3 bukti kost yang fotonya bohong:
1. Foto pakai wide angle
2. Cuma kasih 1-2 foto
3. Harga terlalu murah dari sekitarannya
Cek kost Solo dengan foto dan info terbaru di rumahlabuh.com.
```

### POST 2 (revisi)
```
Foto kost: rapi, bersih, nggak ada salahnya.

Pas dateng langsung:
cat dindingnya tebel banget (nutupin apa, tuh?),
pintu kamar ngegelembung kalau hujan,
dan ada gecko di kamar mandi yang kayaknya udah tinggal lebih lama dari penghuninya.

3 tanda foto kost yang sering menipu:
- Pakai wide angle biar keliatan luas
- Cuma ada 1-2 foto di listing
- Harga terlalu jauh di bawah kost sekitarnya
```
*Hapus CTA brand di sini, sudah ada di post 6.*

---

### POST 3 (asli)
```
Kost deket UNS Solo? Ada yang Rp700rb/th termasuk listrik dan wifi.
[deskripsi kost]
Kalau kamu maba atau anak UNS... langsung cek di rumahlabuh.com.
```

### POST 3 (revisi)
```
Yang bikin betah di kost itu bukan kamarnya.

Gue pernah di kost yang kamarnya biasa banget.
Tapi tiap pagi ada warung soto di bawah, tetangganya kerja pagi semua, dan jalan ke kampus 10 menit.

Setelah setahun, gue nggak mau pindah.
```
*Ubah total jadi konten value, bukan showcase listing.*

---

### POST 4 (asli)
```
Hai yang lagi nyari kost di Solo:
Pilih satu aja antara:
A) Kost Rp500rb, deket kampus, tapi WC luar
B) Kost Rp900rb, WC dalam, tapi 15 menit ke kampus
Pilih yang mana dan kenapa?
```

### POST 4 (revisi)
```
Satu pertanyaan buat yang lagi milih kost:

A) Rp500rb, 5 menit ke kampus, WC bersama
B) Rp900rb, 15 menit ke kampus, WC dalam

Lo pilih yang mana?

Gue penasaran jawabannya karena ternyata tiap orang beda banget alasannya.
```

---

### POST 5 (asli)
```
Cerita nyari kost paling apes yang pernah saya dengar:
dapat kost deket, murah, wifi kenceng.
Minggu pertama: kost deket satu-satunya club malam di Solo.
Setiap Jumat-Sabtu, kamar goyang sendiri.
[CTA rumahlabuh.com]
```

### POST 5 (revisi)
```
Kost paling apes yang pernah gue denger:

Dapet kost deket banget. Murah. Wifi kenceng.
Seneng banget.

Minggu pertama baru ketauan: kostnya persis di sebelah satu-satunya club malam di Solo.

Setiap Jumat-Sabtu, kamar goyang sendiri.

Yang rekomendasiin kostnya? Nggak bilang soal itu.
```
*Hapus moral dan CTA — ceritanya sudah cukup kuat sendiri.*

---

### POST 6 (asli)
```
70% orang menyesal pilih kost karena nggak riset lingkungan sekitar dulu.
[...]
Jangan ulangi kesalahan mereka.
Cek kost di Solo yang sudah kami verifikasi lokasinya di rumahlabuh.com.
```

### POST 6 (revisi)
```
Kalau mau milih kost, hal yang paling sering bikin orang nyesel itu bukan fasilitas.

Tapi lingkungan sekitarnya.
Tetangga, akses, suara malam.

Susah ketauan dari foto.

Kalau lagi cari kost di Solo, bisa cek opsi yang infonya lebih lengkap di rumahlabuh.com
Ada filter lokasi, fasilitas, dan bisa langsung kontak pemilik.

Lo sendiri waktu milih kost, cek lingkungannya dulu atau langsung lihat kamar?
```

---

## ATURAN TAMBAHAN UNTUK BOT (Berdasarkan Evaluasi Ini)

```yaml
aturan_baru:

  brand_mention:
    - mention rumahlabuh.com HANYA di post terakhir (post 6)
    - dalam satu thread, nama brand maksimal muncul 1 kali
    - tidak di post 1, 2, 3, 4, atau 5

  statistik:
    - jangan pakai persentase tanpa sumber nyata
    - ganti dengan frasa kualitatif: "banyak orang", "hampir semua yang pernah gue tanya"
    - kalau pakai angka, harus bisa diverifikasi

  pronoun_konsistensi:
    register_informal: ["gue", "lo"] — untuk target mahasiswa/anak muda
    register_semi_formal: ["aku", "kamu"] — untuk target lebih luas
    dilarang_campur: true
    dilarang_brand_voice: ["kami"] dalam konten personal/storytelling

  pembuka_dilarang:
    - "Hai yang lagi nyari kost..."
    - "Untuk kamu yang sedang..."
    - "Buat kamu yang mau..."
    - "Kepada yang sedang..."

  frasa_menakut_takuti_dilarang:
    - "Jangan ulangi kesalahan mereka"
    - "Kamu pasti menyesal kalau..."
    - "Awas kalau nggak..."
    ganti_dengan: framing positif atau netral

  kata_inggris_tambahan_dilarang:
    - "neighbors" -> "tetangga"
    - "experience" (konteks umum) -> "hal", "situasi", "kejadian"
    - "campus" -> "kampus"
```

---

## CHECKLIST EVALUASI MANDIRI BOT (VERSI LENGKAP)

```
[ ] Brand hanya disebut di post 6
[ ] Tidak ada statistik tanpa sumber
[ ] Pronoun konsisten dalam satu thread (gue/lo ATAU aku/kamu)
[ ] Tidak ada "kami" dalam konten personal
[ ] Tidak ada pembuka newsletter ("Hai yang lagi nyari...")
[ ] Tidak ada framing menakut-takuti di akhir post
[ ] Tidak ada kata Inggris yang punya padanan Indonesia ringkas
[ ] Tidak ada em dash (—)
[ ] Tidak ada CAPS LOCK untuk dramatis
[ ] CTA di post 6: ada pertanyaan + mention brand yang natural
[ ] Post 1-5 tidak ada CTA brand sama sekali
[ ] Panjang: tepat 6 post
```

---

*Dokumen ini adalah evaluasi berbasis log nyata output bot rumahlabuh.com*
*Gunakan sebagai panduan perbaikan iteratif untuk bot*
*Versi: 1.0 | April 2026*
*Compatible: LLM context, chatbot evaluation, content QA*

# Build Guide 08: Minimum Viable Legal Compliance

**Philosophy:** Skip expensive professionals for now. Do the minimum required by Indonesian law. Revisit after Month 6 when you have revenue.  
**Cost:** IDR 0  
**Time:** 1 day setup

---

## What to SKIP (Pre-Month 6)

| Item | Cost | Why Skip | Risk if Skipped |
|------|------|----------|-----------------|
| PKP (licensed tax consultant) review | IDR 15–25M | Not legally required for a tool that shows calculations. Legal risk only if you claim to BE a tax consultant. | Low — as long as you have "bukan nasihat pajak" disclaimer |
| KJPP property appraisal endorsement | IDR 10–20M | Not required for a market data display tool | Low — as long as you have KJPP disclaimer |
| UU PDP full DPO appointment | Required for large companies | Not required for solo founders at <5K users | Very low — enforcement at this scale = near zero |
| Formal legal entity (PT) | IDR 5–10M setup | Not required to operate as individual entrepreneur | Medium — use NPWP Pribadi for Midtrans instead |
| OJK fintech registration | Required for financial services | cekwajar.id is data/comparison, NOT financial services | Low if you NEVER move user money |
| ISO 27001 security certification | Very expensive | Not required for early-stage apps | Zero — not regulated for this stage |

---

## What to NOT SKIP (Do These in Week 1–2)

| Item | Cost | How to Do It |
|------|------|--------------|
| Privacy Policy page (Bahasa Indonesia) | Free | Template below — copy paste |
| Terms of Service | Free | Template below — copy paste |
| PSE (Penyelenggara Sistem Elektronik) registration | Free | kominfo.go.id online form |
| Disclaimer on every calculation result | Free | Add 1 sentence to UI |
| Supabase RLS on all user data tables | Free | Already in all schema guides |
| SSL/HTTPS | Free | Default on Vercel |
| Cookie consent banner (basic) | Free | Simple banner, no complex consent manager needed |

---

## Privacy Policy Template (Bahasa Indonesia)

`[CURSOR]` — Create: `app/privacy/page.tsx`

Copy this exact text into your privacy policy page:

```markdown
# Kebijakan Privasi cekwajar.id

**Terakhir diperbarui:** [Tanggal]

## 1. Informasi yang Kami Kumpulkan

cekwajar.id mengumpulkan data berikut sesuai UU No. 27 Tahun 2022 tentang Pelindungan Data Pribadi:

**Data yang Anda berikan:**
- Alamat email (jika membuat akun)
- Data gaji dan potongan yang Anda masukkan untuk analisis
- File slip gaji yang diunggah (jika menggunakan fitur OCR)

**Data yang dikumpulkan otomatis:**
- Data penggunaan teknis (halaman yang dikunjungi, browser, perangkat)
- Alamat IP (dihash/disamarkan, tidak disimpan dalam bentuk mentah)

**Data yang TIDAK kami kumpulkan:**
- Nomor KTP, paspor, atau dokumen identitas
- Informasi rekening bank atau kartu kredit
- Data kesehatan atau biometrik

## 2. Penggunaan Data

Kami menggunakan data Anda untuk:
- Memberikan hasil analisis yang Anda minta
- Meningkatkan akurasi benchmarks (data dianonimkan dan diagregasi)
- Mengirimkan pembaruan layanan (jika Anda memberi consent)

Kami TIDAK menjual data pribadi Anda kepada pihak ketiga.

## 3. Penyimpanan Data

- **File slip gaji:** Dihapus otomatis setelah 30 hari
- **Data gaji yang diinput:** Disimpan dalam bentuk teranonimkan untuk keperluan benchmark
- **Data akun:** Disimpan selama akun aktif
- **Server:** Berlokasi di Singapura (Supabase ap-southeast-1)

## 4. Hak Anda (UU PDP Pasal 5–8)

Anda berhak untuk:
- **Mengakses** data pribadi Anda
- **Memperbaiki** data yang tidak akurat
- **Menghapus** data Anda (right to erasure)
- **Menarik persetujuan** kapan saja

Untuk menggunakan hak ini, hubungi: privacy@cekwajar.id

## 5. Cookie

Kami menggunakan cookie esensial untuk fungsionalitas dasar (autentikasi, preferensi). 
Kami tidak menggunakan cookie pelacakan pihak ketiga.

## 6. Perubahan Kebijakan

Perubahan material pada kebijakan ini akan diberitahukan melalui email atau notifikasi di aplikasi minimal 14 hari sebelumnya.

## 7. Hubungi Kami

Pertanyaan tentang privasi: privacy@cekwajar.id
```

---

## Terms of Service Template

`[CURSOR]` — Create: `app/terms/page.tsx`

```markdown
# Syarat dan Ketentuan cekwajar.id

**Terakhir diperbarui:** [Tanggal]

## 1. Penerimaan Syarat

Dengan menggunakan cekwajar.id, Anda menyetujui syarat dan ketentuan ini.

## 2. Deskripsi Layanan

cekwajar.id adalah platform data referensi untuk perbandingan gaji, analisis slip gaji, 
harga properti, biaya hidup, dan perbandingan gaji luar negeri. 

## 3. DISCLAIMER PENTING

**cekwajar.id BUKAN:**
- Konsultan pajak berlisensi (PKP)
- Penilai properti berlisensi (KJPP)  
- Penasihat keuangan berlisensi (OJK)

**Semua hasil yang ditampilkan:**
- Bersifat **informasional dan edukatif saja**
- Bukan merupakan nasihat pajak, hukum, atau keuangan profesional
- Tidak dapat dijadikan dasar hukum dalam sengketa pajak atau ketenagakerjaan
- Mungkin memiliki selisih dengan perhitungan resmi akibat variasi peraturan

**Untuk kepastian hukum, selalu konsultasikan dengan:**
- Konsultan pajak berlisensi (untuk PPh21/BPJS)
- KJPP berlisensi (untuk penilaian properti)
- Pengacara ketenagakerjaan (untuk sengketa UMK/gaji)

## 4. Akurasi Data

Data benchmark cekwajar.id berasal dari:
- Data resmi pemerintah (BPS, Kemnaker, BPN) — akurat namun mungkin tidak ter-update secara real-time
- Data pasar yang dikumpulkan dari sumber publik — akurasi 70–85%
- Kontribusi pengguna — terverifikasi namun tidak diaudit secara profesional

kami tidak menjamin akurasi 100% dari semua data yang ditampilkan.

## 5. Larangan Penggunaan

Anda dilarang:
- Menggunakan layanan untuk tujuan melanggar hukum
- Menyalahgunakan atau mengganggu sistem cekwajar.id
- Mengumpulkan data dari cekwajar.id secara otomatis (scraping)

## 6. Hak Kekayaan Intelektual

Konten, desain, dan kode cekwajar.id dilindungi hak cipta. Data benchmark 
yang kami sediakan boleh digunakan untuk keperluan pribadi, tidak untuk redistribusi komersial.

## 7. Batasan Tanggung Jawab

Sejauh diizinkan oleh hukum yang berlaku, cekwajar.id tidak bertanggung jawab atas 
kerugian yang timbul dari penggunaan atau ketidakmampuan menggunakan layanan ini.

## 8. Hukum yang Berlaku

Syarat ini diatur oleh hukum Republik Indonesia.

## 9. Perubahan Layanan

Kami berhak mengubah atau menghentikan layanan kapan saja dengan pemberitahuan 
yang wajar kepada pengguna terdaftar.

## 10. Hubungi Kami

Pertanyaan: hello@cekwajar.id
```

---

## PSE Registration (Penyelenggara Sistem Elektronik)

`[MANUAL]` — Register with Kominfo

**Required for:** Any electronic system that collects personal data of Indonesian citizens.  
**Cost:** Free  
**Deadline:** Before collecting real user data  

Steps:
1. Go to: https://pse.kominfo.go.id
2. Create account → Choose "PSE Privat Domestik"
3. Fill in:
   - Nama sistem elektronik: cekwajar.id
   - Deskripsi: Platform referensi data gaji, slip gaji, properti, dan biaya hidup
   - Jenis data yang dikumpulkan: Data identitas pribadi (email), data keuangan (gaji)
   - Lokasi server: Singapura (AWS/Supabase)
4. Upload:
   - KTP founder
   - Privacy Policy URL (cekwajar.id/privacy)
   - Bukti kepemilikan domain
5. Submit → Wait 14 business days for approval number
6. Display PSE number in footer: "Terdaftar PSE Kominfo No. [xxx]"

**Reality check:** PSE registration is legally required. In practice, enforcement at <5K users is essentially zero. But it takes 30 minutes to submit and protects you if you ever get larger. Do it in Week 2.

---

## Disclaimer UI Components

`[CURSOR]` — Add to every tool result page:

```typescript
// components/DisclaimerBanner.tsx

type DisclaimerType = 'tax' | 'property' | 'salary' | 'col';

const DISCLAIMERS: Record<DisclaimerType, string> = {
  tax: 'Hasil ini untuk referensi saja dan bukan merupakan nasihat pajak. Untuk kepastian hukum, konsultasikan dengan konsultan pajak berlisensi (PKP).',
  property: 'Data berdasarkan listing pasar, bukan penilaian properti resmi. Untuk transaksi properti, gunakan penilai berlisensi KJPP.',
  salary: 'Data gaji bersumber dari data pemerintah dan kontribusi pengguna. Akurasi bervariasi. Ini bukan standar gaji yang ditetapkan secara hukum.',
  col: 'Estimasi biaya hidup berdasarkan data statistik. Biaya aktual tergantung gaya hidup dan preferensi individu.',
};

export function DisclaimerBanner({ type }: { type: DisclaimerType }) {
  return (
    <div className="mt-4 p-3 bg-amber-50 border border-amber-200 rounded-lg">
      <p className="text-xs text-amber-800 leading-relaxed">
        ⚠️ {DISCLAIMERS[type]}
      </p>
    </div>
  );
}
```

---

## GDPR/UU PDP: Minimum Implementation

`[SUPABASE]` — Consent tracking:

```sql
-- Track user consent (required by UU PDP)
CREATE TABLE public.user_consents (
  id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
  user_id UUID REFERENCES auth.users(id),
  session_id TEXT,  -- For anonymous users
  consent_type TEXT NOT NULL,  -- 'privacy_policy', 'terms', 'marketing'
  consented BOOLEAN NOT NULL,
  version TEXT NOT NULL,  -- Policy version date: '2024-01'
  ip_hash TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

ALTER TABLE public.user_consents ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users see own consents" ON public.user_consents
  FOR SELECT USING (auth.uid() = user_id);
```

`[CURSOR]` — Cookie consent modal:

```typescript
// components/CookieConsent.tsx
'use client';

import { useState, useEffect } from 'react';

export function CookieConsent() {
  const [show, setShow] = useState(false);
  
  useEffect(() => {
    const consent = localStorage.getItem('cw_consent');
    if (!consent) setShow(true);
  }, []);
  
  const accept = () => {
    localStorage.setItem('cw_consent', 'accepted:2024-01');
    setShow(false);
    // Log to Supabase if user is logged in
  };
  
  if (!show) return null;
  
  return (
    <div className="fixed bottom-0 left-0 right-0 bg-white border-t border-gray-200 p-4 shadow-lg z-50">
      <div className="max-w-4xl mx-auto flex items-center justify-between gap-4">
        <p className="text-sm text-gray-700">
          Kami menggunakan cookie esensial untuk fungsionalitas dasar. 
          Dengan menggunakan cekwajar.id, Anda menyetujui{' '}
          <a href="/privacy" className="text-blue-600 underline">Kebijakan Privasi</a> kami.
        </p>
        <button
          onClick={accept}
          className="flex-shrink-0 px-4 py-2 bg-blue-600 text-white rounded-lg text-sm font-medium"
        >
          Oke, Mengerti
        </button>
      </div>
    </div>
  );
}
```

---

## Data Retention Policy (Operational)

`[SUPABASE]` — Automated cleanup:

```sql
-- Already in guide_01: payslip files deleted after 30 days
-- Add: session/anonymous data cleanup

SELECT cron.schedule(
  'cleanup-anonymous-data',
  '0 3 * * 0',  -- Weekly on Sunday 3am
  $$
  -- Delete anonymous audit sessions older than 90 days
  DELETE FROM public.payslip_audits 
  WHERE user_id IS NULL 
    AND created_at < NOW() - INTERVAL '90 days';
  
  -- Delete old cookie consent logs (keep 1 year)
  DELETE FROM public.user_consents
  WHERE created_at < NOW() - INTERVAL '365 days';
  $$
);
```

---

## After Month 6: Legal Upgrades to Consider

When revenue > IDR 5M/month, prioritize:

| Upgrade | Cost | Why |
|---------|------|-----|
| PKP review of PPh21 engine | IDR 5–10M (one-time) | Validate accuracy, protect against "giving tax advice" claims |
| PT formation | IDR 5–10M | Better for B2B sales, Midtrans merchant upgrade |
| Dedicated privacy email | IDR 0 | Set up privacy@cekwajar.id via Google Workspace (IDR 150K/mo) |
| Full UU PDP compliance audit | IDR 3–5M | Required if you hit 5K+ active users |
| KJPP partnership for Wajar Tanah | Negotiate | Adds credibility to property tool |

---

## Quick Legal Checklist

Run this before Week 12 launch:

- [ ] Privacy Policy page live at cekwajar.id/privacy (Bahasa Indonesia)
- [ ] Terms of Service live at cekwajar.id/terms
- [ ] PSE registration submitted at pse.kominfo.go.id
- [ ] Cookie consent banner visible on first visit
- [ ] "Bukan nasihat pajak" disclaimer on all PPh21/BPJS results
- [ ] "Bukan penilaian KJPP" disclaimer on all property results
- [ ] "Data referensi saja" on all salary benchmark results
- [ ] Supabase RLS enabled on all tables containing user data
- [ ] File auto-delete scheduled (pg_cron for 30-day payslip deletion)
- [ ] No raw IP addresses stored (hash only)
- [ ] Email address for user rights requests set up (privacy@cekwajar.id)

**Estimated time to complete checklist:** 4–6 hours on Week 2. Do it once. Done.

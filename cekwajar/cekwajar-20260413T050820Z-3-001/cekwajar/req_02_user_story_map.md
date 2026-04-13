# req_02 — User Story Map: cekwajar.id
**Document Type:** User Story Map  
**Version:** 1.0 | **Format:** Trigger → Action → Result + As a [user] cards

---

## How to Read This Document

Each tool has:
1. **Journey flow** — the end-to-end sequence of steps
2. **User stories per step** — written in standard Agile format
3. **Acceptance criteria** — what "done" means technically

Stories are tagged: `[P0]` = must have at launch, `[P1]` = Week 2–4, `[P2]` = Month 2+

---

## TOOL 1: Wajar Slip

### Journey Flow

```
ENTRY → UPLOAD/INPUT → OCR PROCESSING → FIELD CONFIRM → CALCULATE → 
VERDICT (FREE) → GATE → PAYMENT → VERDICT (PAID) → SHARE/EXPORT
                                          ↓ (error paths)
                           LOW CONFIDENCE → MANUAL ENTRY FALLBACK
```

### User Stories

**ENTRY**

`[P0]` As a karyawan who suspects their payslip is wrong, I want to land on a clear home page that immediately tells me what Wajar Slip does, so that I understand the value before I upload anything.
- AC: Hero section loads in <2s, shows "Cek apakah potongan gaji kamu benar" headline, "Mulai Gratis" CTA visible without scrolling on mobile

`[P0]` As a new visitor, I want to see an example result before I upload my own data, so that I know what I'll get.
- AC: Sample result card shown on landing page with example violations blurred/mocked

---

**UPLOAD PATH**

`[P1]` As a karyawan, I want to upload a photo or PDF of my payslip, so that I don't have to manually type all the numbers.
- AC: Accepts PNG, JPG, HEIC, PDF ≤ 5MB; drag-and-drop + file picker; shows upload progress bar

`[P1]` As a karyawan, I want to be asked for my consent before my payslip is stored, so that I feel safe sharing sensitive financial data.
- AC: Consent modal appears before file upload completes; explicit checkbox required; consent logged to `user_consents` table with timestamp; no upload proceeds without consent = true

`[P1]` As a karyawan who uploaded a clear PDF, I want the system to automatically extract all payslip fields, so that I don't have to type anything manually.
- AC: If OCR confidence ≥ 0.92 on all P0 fields: auto-advance to calculation step with pre-filled form; user can still edit any field

`[P1]` As a karyawan whose payslip photo was blurry, I want to know which fields couldn't be read clearly and be given a form to fill them in, so that I can still complete the audit.
- AC: If OCR confidence 0.70–0.92: show "Konfirmasi Data" screen with extracted fields + confidence indicator (green/yellow/red per field); user edits low-confidence fields; submit proceeds

`[P1]` As a karyawan whose payslip OCR completely failed, I want to be routed to the manual entry form automatically, so that OCR failure doesn't block me.
- AC: If OCR confidence <0.70 or gross_salary=null: auto-route to manual form with message "Kami tidak bisa membaca beberapa kolom. Masukkan nilai berikut secara manual."

---

**MANUAL INPUT PATH**

`[P0]` As a karyawan, I want to manually enter my payslip details using a simple form, so that I can audit my payslip even without uploading a photo.
- AC: Form fields: gross salary (IDR), PTKP status dropdown (TK/0 → K/I/3, 13 options), month/year, NPWP checkbox, optional fields for each deduction; city dropdown for UMK lookup; all fields labeled in Bahasa Indonesia

`[P0]` As a karyawan, I want to enter only my gross salary and PTKP status for a quick check, so that I can get a basic result without filling in all deduction fields.
- AC: Gross salary + PTKP are the only required fields; all deduction fields default to 0 (treated as "not reported"); system flags all missing deductions as violations

---

**CALCULATION**

`[P0]` As a karyawan, I want the system to calculate what my PPh21 should be based on the latest regulation, so that I can compare it to what was actually deducted.
- AC: Uses TER method (PMK 168/2023) for months 1–11; progressive method for December; NPWP flag increases rate by 20% if false; calculation completes in <500ms

`[P0]` As a karyawan, I want the system to calculate all 6 BPJS components (JHT, JP, JKK, JKM, Kesehatan employee + employer), so that I can see the full picture.
- AC: All 6 components calculated; salary caps applied (JP cap: IDR 9,559,600; Kesehatan cap: IDR 12,000,000); JKK defaults to risk class I (0.24%) if job type not specified

---

**VERDICT — FREE**

`[P0]` As a karyawan (free user), I want to see whether violations were found on my payslip, so that I know if I need to take action.
- AC: Shows: overall status badge (BERSIH / ADA PELANGGARAN / PERLU DICEK); list of violation codes found (e.g., "V03 — PPh21 tidak dipotong"); calculated vs reported summary for each component; first violation shown in full; subsequent violations blurred/hidden behind gate

`[P0]` As a karyawan (free user), I want to see the disclaimer clearly, so that I understand this is a reference tool, not legal advice.
- AC: Disclaimer text renders below result: "Hasil ini untuk referensi saja dan bukan merupakan nasihat pajak. Untuk kepastian hukum, konsultasikan dengan konsultan pajak berlisensi."

---

**FREEMIUM GATE**

`[P0]` As a karyawan who found violations, I want to see the exact IDR shortfall amounts, so that I know how much I've been underpaid.
- AC: IDR amounts blurred; "Lihat Selisih Lengkap" CTA shows upgrade modal; modal shows Basic tier at IDR 29K with 3 key benefits

`[P0]` As a karyawan, I want to upgrade directly from the result page without losing my result, so that I don't have to re-enter data after paying.
- AC: Payment flow preserves audit session ID; after successful webhook, same result page refreshes with full data unlocked; no re-calculation required

---

**PAYMENT**

`[P0]` As a karyawan ready to upgrade, I want to pay via GoPay, QRIS, or bank transfer, so that I can use my preferred Indonesian payment method.
- AC: Midtrans Snap opens with GoPay, QRIS, ShopeePay, BCA VA, Mandiri VA, BNI VA, BRI VA enabled; payment completes in Snap iframe; no redirect away from cekwajar.id

`[P0]` As a karyawan who just paid, I want the full violation details to appear immediately, so that I'm not left waiting after payment.
- AC: Midtrans webhook arrives within 5–30 seconds; subscription table updated; page auto-refreshes via polling or SSE; if webhook delayed >60s: show "Pembayaran diterima, mohon tunggu sebentar" + retry button

---

**VERDICT — PAID**

`[P1]` As a Basic subscriber, I want to see the exact IDR shortfall for each violation, so that I know exactly how much my employer owes me.
- AC: All 7 violation slots show: code + description + expected IDR + reported IDR + difference

`[P2]` As a Pro subscriber, I want to export a PDF audit report, so that I can share it with my HRD department.
- AC: PDF generated via server-side rendering; includes all violation details + calculation breakdown + disclaimer; downloadable from result page

`[P2]` As a Pro subscriber, I want to simulate my December true-up, so that I can predict how much extra will be withheld in December.
- AC: Input: salary × 11 months (or irregular); output: estimated December PPh21 withholding vs January–November monthly average; shows "more" or "less" than expected

---

**SHARE**

`[P1]` As a karyawan who found violations, I want to share my result on social media, so that my friends know about this tool.
- AC: OG share card generated via @vercel/og; shows: platform name + verdict badge (BERSIH or ADA PELANGGARAN) + "Cek slip gajimu di cekwajar.id"; no personal data in card

---

## TOOL 2: Wajar Gaji

### Journey Flow

```
ENTRY → INPUT FORM → BENCHMARK LOOKUP → 
  ↓ (sufficient data)                  ↓ (insufficient data)
VERDICT (FREE) → GATE → PAID BREAKDOWN     "DATA BELUM CUKUP" + SUBMIT CTA
         ↓
SUBMIT OWN SALARY (any user, any tier)
```

### User Stories

`[P0]` As a karyawan negotiating salary, I want to enter my job title, city, and experience level and immediately see the median salary for that role, so that I have a data point to anchor my negotiation.
- AC: Input form: job title (text + autocomplete from existing titles), city (34 provinces + 50+ cities dropdown), industry (dropdown: 15 categories), years experience (1–30 slider), education (SMA/D3/S1/S2/S3); result rendered within 500ms from DB

`[P0]` As a user in a city with no data yet, I want to see a province-level BPS estimate with a clear "data belum cukup" label, so that I'm not misled by a thin benchmark.
- AC: If city-level n<10: show province BPS P50 with badge "Data Provinsi BPS — Belum cukup data kota ini"; CTA: "Bantu kami dengan kirim data gajimu"

`[P0]` As any user (free or paid), I want to anonymously submit my own salary, so that I'm contributing to a better benchmark for everyone.
- AC: Submit form: job title, city, industry, experience, education, monthly gross salary (IDR), year; no login required; IP hash dedup prevents multiple submissions for same title+city within 7 days; outlier filter rejects if >30x or <0.7x city UMK

`[P1]` As a free user, I want to see the P50 for my province (BPS data), so that I have a free baseline reference.
- AC: Province P50 visible without login or payment; "Sumber: BPS Sakernas [year]" shown below number; confidence badge = "Rendah"

`[P1]` As a Basic subscriber, I want to see the P25/P75 salary range for my job title in my city, so that I understand the full distribution.
- AC: P25 and P75 shown as IDR amounts; bar chart visualization with my input salary marked on scale; shown only when n≥10

`[P2]` As a Pro subscriber, I want to compare my salary across 3 different industries in the same city, so that I can evaluate switching industries.
- AC: Side-by-side comparison table for selected job title across industries; only shows industries with n≥5 in that city

---

## TOOL 3: Wajar Tanah

### Journey Flow

```
ENTRY → INPUT FORM (location + property details + asking price) → 
BENCHMARK LOOKUP → 
  ↓ (data exists)           ↓ (no data for kelurahan)
VERDICT + PRICE RANGE    "BELUM ADA DATA" + crowdsource CTA
→ GATE (P25/P75) → BASIC UPGRADE
```

### User Stories

`[P0]` As a first-time property buyer, I want to enter a kelurahan/kecamatan and see the market price per m² for similar properties, so that I know if the price I was quoted is fair.
- AC: Input: province → city → district → property type → land area → total asking price; output: P50 price/m², verdict badge, sample count, NJOP reference

`[P0]` As a property buyer, I want to see the NJOP value for the area as a reference floor, so that I understand the official government valuation.
- AC: NJOP/m² displayed as "Nilai NJOP Referensi" with note "NJOP biasanya 40–60% di bawah harga pasar"

`[P0]` As a property buyer (free), I want to see whether the asking price is murah/wajar/mahal without logging in, so that I can do a quick sanity check.
- AC: Verdict badge rendered for all users; P50 market price shown; P25/P75 blurred behind gate

`[P1]` As a Basic subscriber, I want to see the full P25/P75 price range, so that I can understand price distribution in this area.
- AC: P25 and P75 rendered as IDR amounts and as price/m²; "X% di atas median" or "X% di bawah median" text relative to asked price

`[P2]` As a Pro subscriber, I want to see a 3-month price trend for this area, so that I can time my purchase.
- AC: If 3 monthly scraper runs exist: show month-over-month P50 for kecamatan; trend arrow (up/down/flat)

`[P0]` As a property buyer, I want to see the required disclaimer clearly before the verdict, so that I understand the result is not a licensed appraisal.
- AC: "Data berdasarkan listing pasar (bukan penilaian KJPP). Harga aktual tergantung kondisi fisik properti, dokumen, dan negosiasi." shown above verdict card

---

## TOOL 4: Wajar Kabur

### Journey Flow

```
ENTRY → INPUT (current IDR salary + job role + target country) → 
PPP CONVERSION → 
SIDE-BY-SIDE DISPLAY (Indonesia vs Target) →
  [FREE: Top 5 countries, PPP only]
  [BASIC: All 15 countries + CoL breakdown + market salary]
  [PRO: All + after-tax + multi-country comparison]
→ GATE → UPGRADE → FULL RESULT
```

### User Stories

`[P0]` As a professional with a job offer from Singapore, I want to enter my current IDR salary and see the PPP-adjusted equivalent in SGD, so that I can compare apples to apples.
- AC: Input: monthly IDR salary, job role (text), target country (dropdown 15 countries); PPP data from World Bank API (cached 30 days); result: IDR equivalent purchasing power displayed; exchange rate shown as "nilai tukar referensi"

`[P0]` As a free user, I want to compare my salary against 5 countries for free, so that I can explore options without paying.
- AC: Free tier shows SGP, MYS, AUS, USA, GBR; remaining 10 countries blurred; "Lihat 10 negara lainnya" gate CTA

`[P1]` As a Basic subscriber, I want to see the cost of living breakdown for my target city, so that I understand what my purchasing power actually means on the ground.
- AC: Numbeo CoL data for top city in target country shown; 6 categories (food, rent, transport, utilities, entertainment, personal); amounts in local currency and IDR PPP equivalent

`[P1]` As a Basic subscriber, I want to see the market salary range for my job role in the target country, so that I can benchmark the offer I received.
- AC: Market P25/P50/P75 for job role in target country shown (from scraped data or Numbeo); source labeled; disclaimer "Data dari sumber publik, mungkin tidak akurat untuk peran spesifik"

`[P2]` As a Pro subscriber, I want to see the estimated after-tax net salary in the target country, so that I know what I'll actually take home.
- AC: Shows typical effective income tax rate for target country at given salary level; net salary = gross × (1 - effective_rate); note: "Estimasi umum, bukan perhitungan pajak resmi"

`[P0]` As any user, I want to see a required political/accuracy disclaimer, so that I understand the limitations of this comparison.
- AC: "Perbandingan ini menggunakan data PPP Bank Dunia dan estimasi biaya hidup. Biaya aktual bervariasi berdasarkan gaya hidup, kota spesifik, dan kebijakan pajak setempat. Ini bukan nasihat imigrasi atau keuangan." shown before results

---

## TOOL 5: Wajar Hidup

### Journey Flow

```
ENTRY → INPUT (current city + target city + salary + lifestyle) → 
COL CALCULATION → ADJUSTMENT DISPLAY →
  [FREE: % adjustment + required salary]
  [BASIC: Category breakdown]
  [PRO: Historical trend + multi-city]
→ GATE → UPGRADE
```

### User Stories

`[P0]` As a worker relocating from Jakarta to Surabaya, I want to enter both cities and my current salary and see how much I need to earn in Surabaya to maintain the same lifestyle, so that I can evaluate the job offer.
- AC: Input: from_city (dropdown), to_city (dropdown), monthly salary IDR, lifestyle (Hemat/Standar/Nyaman radio); result: required salary in target city + % difference + verdict badge

`[P0]` As a free user, I want to see the total percentage cost difference between two cities, so that I have a quick reference without paying.
- AC: "Biaya hidup di [target] X% lebih [mahal/murah] dari [current]" displayed; required salary shown; category breakdown hidden

`[P1]` As a Basic subscriber, I want to see a breakdown of how each spending category changes between cities, so that I understand where the cost difference comes from.
- AC: Table with 10 categories (makanan, tempat tinggal, transportasi, utilitas, hiburan, pendidikan, kesehatan, pakaian, komunikasi, tabungan); IDR amounts for each city; difference column

`[P2]` As a Pro subscriber, I want to compare 3 or more cities simultaneously, so that I can evaluate multiple job offer locations at once.
- AC: Up to 4 cities in side-by-side table; summary row shows total required salary per city; sorted by cost (cheapest to most expensive)

`[P0]` As any user, I want to understand the lifestyle tiers before selecting, so that I choose the right reference point.
- AC: Hemat label shows example: "Kos, masak sendiri, transportasi umum (~IDR 3–5M/bulan di Jakarta)"; Standar: "Kontrakan 1BR, makan campuran (~IDR 7–12M)"; Nyaman: "Apartemen, makan restoran, mobil (~IDR 15–25M)"

---

## Cross-Tool User Stories

`[P0]` As any user, I want to see a cookie consent banner on my first visit, so that I know my data rights.
- AC: Banner renders on first visit; "Oke, Mengerti" accepts; choice stored in localStorage; Supabase consent log created if user is logged in

`[P0]` As any user, I want to navigate between all 5 tools from a persistent nav bar, so that I can explore the platform without getting lost.
- AC: Top nav: Wajar Slip | Wajar Gaji | Wajar Tanah | Wajar Kabur | Wajar Hidup; active tool highlighted; mobile: hamburger menu

`[P0]` As a subscriber, I want my subscription to be recognized automatically when I'm logged in, so that I don't have to re-enter payment details to access premium features.
- AC: Supabase auth session token used; RLS checks `user_profiles.subscription_tier` and `subscription_expires_at`; gate hidden if subscription valid

`[P1]` As a logged-in user, I want to see my audit/lookup history, so that I can reference past results.
- AC: `/dashboard` page shows last 10 audits with date, tool used, verdict; free users see last 1; Basic sees 3 months; Pro sees unlimited

`[P1]` As a logged-in user whose subscription expired, I want to be notified before it expires and given a renewal option, so that I don't lose access unexpectedly.
- AC: 3 days before expiry: email sent (Resend); on login: toast notification "Langgananmu berakhir dalam X hari"; after expiry: gate reinstated; data retained for 30 days

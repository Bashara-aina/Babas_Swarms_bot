# req_09 — Frontend & UX Spec: cekwajar.id
**Document Type:** Frontend & UX Specification  
**Version:** 1.0  
**Stack:** Next.js 15 App Router, TypeScript, Tailwind CSS, shadcn/ui

---

## 6.1 Wireframes (Text-Based Low-Fi)

### Global Layout

```
┌─────────────────────────────────────────────────────────────────┐
│  HEADER (sticky, h=56px mobile / h=64px desktop)                │
│  [Logo: cekwajar.id]  [Wajar Slip] [Gaji] [Tanah] [Kabur] [Hidup]  [Login/Profile] │
└─────────────────────────────────────────────────────────────────┘
│                                                                 │
│  MAIN CONTENT (max-w-2xl centered on desktop, full-width mobile)│
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
│  FOOTER (minimal)                                               │
│  Privacy Policy · Terms · © 2026 cekwajar.id                   │
└─────────────────────────────────────────────────────────────────┘
```

---

### Wajar Slip Wireframe

```
PAGE: /wajar-slip
════════════════════════════════════════════

[HERO]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Cek Slip Gaji Kamu — Gratis
Pastikan potongan PPh21 dan BPJS sudah benar
[CTA: Mulai Cek Gratis ▼]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[UPLOAD SECTION]  (State: idle)
┌─────────────────────────────────────┐
│                                     │
│   📷  Upload Foto/PDF Slip Gaji     │
│                                     │
│   JPEG · PNG · PDF · Maks 5MB      │
│                                     │
│   [Pilih File]  atau  drag & drop   │
│                                     │
└─────────────────────────────────────┘
     ─── atau ───
[Isi Manual]  (toggle to show form below)

[DISCLAIMER BANNER]
⚠️ Alat ini bukan nasihat pajak. Hasil bersifat
   indikatif berdasarkan regulasi PMK 168/2023.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[MANUAL FORM] (shown after toggle or after OCR soft-check)

Gaji Bruto Sebulan *
┌─────────────────────────────────┐
│  Rp  __________________________│
└─────────────────────────────────┘
(contoh: 7.500.000)

Status PTKP *              Kota *
┌──────────────────┐  ┌──────────────────┐
│  TK/0 ▼          │  │  Kota Bekasi ▼   │
└──────────────────┘  └──────────────────┘

Bulan Slip *              Punya NPWP?
┌──────────────────┐  ┌──────────────────┐
│  Oktober 2025 ▼  │  │  ✅ Ya           │
└──────────────────┘  └──────────────────┘

── Potongan di Slip Gaji ──────────────

PPh21 Dipotong             JHT Karyawan
┌──────────────────┐  ┌──────────────────┐
│  Rp __________   │  │  Rp __________   │
└──────────────────┘  └──────────────────┘

JP Karyawan               Kesehatan (1%)
┌──────────────────┐  ┌──────────────────┐
│  Rp __________   │  │  Rp __________   │
└──────────────────┘  └──────────────────┘

Take Home Pay
┌─────────────────────────────────┐
│  Rp __________________________  │
└─────────────────────────────────┘

[Cek Slip Gaji →]  (primary CTA, full width on mobile)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[VERDICT — FREE TIER — shows after calculation]

┌─────────────────────────────────────┐
│                                     │
│  ⚠️  ADA PELANGGARAN                │ ← red if violations, green if OK
│                                     │
│  2 pelanggaran ditemukan            │
│                                     │
│  ✅ V02: BPJS JP Kurang Bayar       │ ← free: shows code + title only
│  ✅ V04: PPh21 Kurang Potong        │
│                                     │
│  ┌─────────────────────────────┐    │
│  │  🔒 Berapa selisihnya?      │    │ ← gate modal trigger
│  │  Upgrade ke Basic           │    │
│  │  [IDR 29.000/bulan]  →     │    │
│  └─────────────────────────────┘    │
│                                     │
└─────────────────────────────────────┘

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[VERDICT — PAID TIER — same position, no gate]

┌─────────────────────────────────────┐
│  ⚠️  ADA PELANGGARAN                │
│                                     │
│  V02: BPJS JP Kurang Bayar          │
│  Dipotong: Rp 85.596                │
│  Seharusnya: Rp 95.596              │
│  Selisih: Rp 10.000 ⬆               │
│  → Minta klarifikasi tertulis ke HRD│
│                                     │
│  V04: PPh21 Kurang Potong           │
│  Dipotong: Rp 0                     │
│  Seharusnya: Rp 62.500              │
│  Selisih: Rp 62.500 ⬆               │
│  → Segera daftarkan NPWP kamu      │
│                                     │
│  [📄 Unduh Laporan PDF]             │ ← Pro only
└─────────────────────────────────────┘
```

---

### Wajar Gaji Wireframe

```
PAGE: /wajar-gaji
════════════════════════════════════════════

[HERO]
Berapa Standar Gaji untuk Posisimu?
Data dari BPS + 12.000+ laporan karyawan

[FORM]
Judul Pekerjaan *
┌─────────────────────────────────────────┐
│  Ketik judul... (autocomplete dropdown) │
└─────────────────────────────────────────┘
  ↓ matches as user types:
  ┌─────────────────────────────────────┐
  │  Software Engineer                  │
  │  Staff Keuangan                     │
  │  HRD Officer                        │
  └─────────────────────────────────────┘

Kota *                   Pengalaman *
┌──────────────────┐  ┌──────────────────┐
│  Kota Bekasi ▼   │  │  3-5 tahun ▼     │
└──────────────────┘  └──────────────────┘

Gaji Saya Saat Ini (opsional — untuk perbandingan)
┌─────────────────────────────────────────┐
│  Rp ____________________________________│
└─────────────────────────────────────────┘

[Cek Benchmark →]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[RESULT — FREE TIER]

HRD Officer · Kota Bekasi · 3-5 tahun
─────────────────────────────────────
Median Provinsi (Jawa Barat)

  Rp 7.200.000/bulan

  Confidence: 🟡 Cukup (n=14)

UMK Kota Bekasi 2026: Rp 5.331.680
Gaji kamu [████░░░░░░] di bawah median

┌─────────────────────────────────────┐
│  🔒 Lihat rentang P25–P75 kota ini  │
│  [Upgrade Basic IDR 29K →]          │
└─────────────────────────────────────┘

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[RESULT — PAID TIER]

HRD Officer · Kota Bekasi · 3-5 tahun
─────────────────────────────────────
                P25       P50       P75
          ┌─────────────────────────┐
Bekasi    │ 5.8M  ████|████  10.2M│
          └─────────────────────────┘
                   7.2M (median)

Gaji kamu (7.5M) ── di atas median ✅

UMK: Rp 5.331.680 ✅ (di atas UMK)

Sumber: 14 laporan terverifikasi · data 3 bulan lalu

─────────────────────────────────────
Kontribusi Data Anonim:
[Tambah laporan gaji saya →]
```

---

### Wajar Tanah Wireframe

```
PAGE: /wajar-tanah
════════════════════════════════════════════

[HERO]
Cek Harga Tanah/Rumah — MURAH, WAJAR, atau MAHAL?
Data dari 99.co dan Rumah123

[FORM — cascading dropdowns]
Provinsi *
┌─────────────────────────────────────────┐
│  Jawa Barat ▼                           │
└─────────────────────────────────────────┘
        ↓ unlocks
Kota/Kabupaten *
┌─────────────────────────────────────────┐
│  Kota Bekasi ▼                          │
└─────────────────────────────────────────┘
        ↓ unlocks
Kecamatan *
┌─────────────────────────────────────────┐
│  Pondok Gede ▼                          │
└─────────────────────────────────────────┘

Tipe Properti *
( ) Rumah   ( ) Tanah   ( ) Apartemen   ( ) Ruko

Luas Tanah (m²) *          Harga yang Ditawarkan *
┌──────────────────┐   ┌──────────────────┐
│  72              │   │  Rp 850.000.000  │
└──────────────────┘   └──────────────────┘
                            = Rp 11.805.556/m²

[Cek Harga →]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[RESULT]

┌─────────────────────────────────────┐
│                                     │
│  ██████████████  MAHAL              │ ← bold, red
│                                     │
│  Harga/m² diminta:  Rp 11.805.556   │
│  Median pasar:      Rp 9.800.000    │
│  Posisi:            ≈ P83           │
│                                     │
│  NJOP: Rp 4.200.000/m² (2024)      │
│  Pasar/NJOP: 2.3× (tipikal)        │
│                                     │
│  ┌──────────────────────────────┐   │
│  │  🔒 P25: ████████           │   │ ← blurred
│  │  🔒 P75: ████████████       │   │
│  │  [Lihat rentang IDR 29K →]  │   │
│  └──────────────────────────────┘   │
│                                     │
│  Berdasarkan 23 listing             │
│  Data terakhir: 4 hari lalu        │
│                                     │
└─────────────────────────────────────┘

⚠️ KJPP Disclaimer (see req_07)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[PAID RESULT — additional]

P25: Rp 8.200.000/m²  ← good deal threshold
P50: Rp 9.800.000/m²  ← fair market
P75: Rp 11.500.000/m² ← expensive threshold

Harga diminta (11.8M) masuk P83 — di atas P75.
Ada ruang negosiasi ke ≈ Rp 10M/m².

[📄 Unduh Laporan Mini Valuasi]  ← P1
```

---

### Wajar Kabur Wireframe

```
PAGE: /wajar-kabur
════════════════════════════════════════════

[HERO]
Kerja di Luar Negeri — Lebih Besar atau Sama?
Bandingkan gaji real dengan daya beli

[FORM]
Gaji Saat Ini *              Peran Pekerjaan
┌──────────────────┐   ┌──────────────────────────┐
│ Rp 8.500.000     │   │  Backend Developer        │
└──────────────────┘   └──────────────────────────┘

Negara Tujuan *
[🇸🇬 Singapura] [🇲🇾 Malaysia] [🇦🇺 Australia] [🇺🇸 Amerika] [🇬🇧 Inggris]
[🔒 Jepang]    [🔒 Korsel]    [🔒 UAE]      [+8 lainnya]

[Bandingkan →]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[RESULT — Singapura]

Gaji IDR 8.500.000 di Indonesia

Setara secara nominal:    SGD 730/bulan
                         (kurs 1 SGD = Rp 11.644)

Setara secara daya beli:  SGD 1.775/bulan ← PPP
                         (kamu bisa beli sebanyak ini di SG)

─────────────────────────────────────

Tawaran SGD 4.500:   = 2.54× daya beli riilmu

🟢 Lebih besar secara riil

PPP sumber: World Bank 2023

┌────────────────────────────────────┐
│  🔒 Detail biaya hidup Singapura   │ ← Basic gate
│  [Lihat breakdown IDR 29K →]       │
└────────────────────────────────────┘

⚠️ Disclaimer PPP (see req_07)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[PAID — CoL breakdown]

Biaya Hidup Singapura (estimasi):

Sewa 1BR luar pusat:  Rp 18.200.000/bulan
Makan sehari-hari:    Rp 6.500.000/bulan
Transport publik:     Rp 1.100.000/bulan
Total estimasi:       Rp 32.500.000/bulan

SGD 4.500 = Rp 52.400.000 — surplus Rp 19.9M/bulan
```

---

### Wajar Hidup Wireframe

```
PAGE: /wajar-hidup
════════════════════════════════════════════

[HERO]
Pindah Kota — Gaji Harus Naik Berapa?

[FORM]
Dari Kota *               Ke Kota *
┌──────────────────┐   ┌──────────────────┐
│  Jakarta ▼       │   │  Surabaya ▼      │
└──────────────────┘   └──────────────────┘

Gaji Sekarang *
┌─────────────────────────────────────────┐
│  Rp 12.000.000                          │
└─────────────────────────────────────────┘

Gaya Hidup *
( ) Hemat   (•) Standar   ( ) Nyaman

[Hitung →]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[RESULT]

┌─────────────────────────────────────┐
│                                     │
│  🟢 LEBIH MURAH                    │
│                                     │
│  Jakarta (100) → Surabaya (78.5)   │
│                                     │
│  Gaji setara di Surabaya:           │
│  Rp 9.420.000/bulan                 │
│  (-21.5% dari sekarang)             │
│                                     │
│  Kamu bisa hemat Rp 2.580.000/bln  │
│  atau turunkan tawaran 21% tetap OK│
│                                     │
└─────────────────────────────────────┘

[🔒 Lihat breakdown per kategori]  ← Basic gate

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[PAID — Category breakdown]

Kategori          Jakarta      Surabaya    Selisih
─────────────────────────────────────────────────
Tempat Tinggal    Rp 3.360K    Rp 2.352K   -Rp 1.008K
Makanan           Rp 3.360K    Rp 2.352K   -Rp 1.008K
Transportasi      Rp 1.440K    Rp 1.131K   -Rp 309K
Listrik & Air     Rp 600K      Rp 471K     -Rp 129K
Hiburan           Rp 720K      Rp 566K     -Rp 154K
...
─────────────────────────────────────────────────
TOTAL             Rp 12.000K   Rp 9.420K   -Rp 2.580K
```

---

## 6.2 Component Inventory

### Global Components

| Component | File Path | Props | States | Used In |
|-----------|-----------|-------|--------|---------|
| `GlobalNav` | `components/layout/GlobalNav.tsx` | `currentTool?: string` | sticky/scrolled | All pages |
| `Footer` | `components/layout/Footer.tsx` | — | — | All pages |
| `PremiumGate` | `components/shared/PremiumGate.tsx` | `requiredTier: 'basic'\|'pro', featureLabel: string, children: ReactNode` | open/closed modal | Wajar Slip, Gaji, Tanah |
| `SubscriptionBadge` | `components/shared/SubscriptionBadge.tsx` | `tier: 'free'\|'basic'\|'pro'` | — | Dashboard, nav |
| `DisclaimerBanner` | `components/shared/DisclaimerBanner.tsx` | `text: string, type: 'warning'\|'info'` | expandable | Wajar Slip (tax), Tanah (KJPP), Kabur (PPP) |
| `LoadingSpinner` | `components/shared/LoadingSpinner.tsx` | `size: 'sm'\|'md'\|'lg', label?: string` | — | All tools during API call |
| `ErrorCard` | `components/shared/ErrorCard.tsx` | `code: string, message: string, retry?: () => void` | — | All tools on error |
| `CookieConsent` | `components/layout/CookieConsent.tsx` | — | hidden/shown/accepted | App root |
| `FormatIDR` | `utils/format.ts` (function) | `amount: number, compact?: boolean` | — | All tools |

---

### Wajar Slip Components

| Component | Props | States | Notes |
|-----------|-------|--------|-------|
| `PayslipUploader` | `onOCRComplete: (result: OCRResult) => void, onManualToggle: () => void` | idle / dragging / uploading / processing / complete / error | Handles both drag-drop and click-to-select |
| `OCRConfirmScreen` | `extractedFields: ExtractedFields, onConfirm: (fields: Fields) => void` | — | Shows for SOFT_CHECK confidence only |
| `PayslipForm` | `initialValues?: Partial<PayslipInput>, onSubmit: (data: PayslipInput) => void` | idle / submitting / error | Main manual form |
| `PTKPDropdown` | `value: PtkpStatus, onChange: (v: PtkpStatus) => void` | — | 12 PTKP options |
| `CityDropdown` | `value: string, onChange: (v: string) => void` | — | 514 cities from UMK table |
| `VerdictCard` | `verdict: VerdictData, userTier: Tier` | — | Shows violations (gated or full) |
| `ViolationItem` | `violation: ViolationDetail, isGated: boolean` | — | Single violation row |
| `AuditHistory` | `audits: AuditHistoryItem[]` | — | Dashboard sub-component |

---

### Wajar Gaji Components

| Component | Props | States | Notes |
|-----------|-------|--------|-------|
| `JobTitleAutocomplete` | `value: string, onChange: (v: string) => void, onSelect: (category: JobCategory) => void` | idle / searching / results / no-match | Debounced 300ms |
| `SalaryBenchmarkResult` | `result: SalaryBenchmarkResponse, userTier: Tier` | — | Main result card |
| `ConfidenceBadge` | `level: string, label: string, count: number` | — | Inline in result |
| `SalaryRangeBar` | `p25: number, p50: number, p75: number, userSalary?: number` | — | Horizontal bar chart |
| `CrowdsourceForm` | `jobCategoryId: string, city: string` | idle / submitting / success / duplicate | Anonymous submission |

---

### Wajar Tanah Components

| Component | Props | States | Notes |
|-----------|-------|--------|-------|
| `LocationDrilldown` | `onChange: (loc: LocationSelection) => void` | each level: idle/loading/selected | Province → City → District |
| `PropertyTypeSelector` | `value: PropertyType, onChange: (v: PropertyType) => void` | — | 4 types as radio cards |
| `PropertyVerdict` | `verdict: PropertyBenchmarkResponse, userTier: Tier` | — | Main verdict display |
| `VerdictBadge` | `verdict: PropertyVerdict` | — | MURAH/WAJAR/MAHAL/SANGAT_MAHAL with color |
| `PriceComparisonBar` | `p25: number, p50: number, p75: number, asking: number` | — | Shows where asking lands |
| `NJOPReference` | `njop: number, market: number, year: number` | — | NJOP context text |
| `SampleCountBadge` | `count: number, freshness: string` | — | "23 listing · 4 hari lalu" |

---

### Wajar Kabur Components

| Component | Props | States | Notes |
|-----------|-------|--------|-------|
| `CountrySelector` | `selected: string, onChange: (code: string) => void, userTier: Tier` | — | 5 free + 10 locked grid |
| `PPPResultCard` | `result: AbroadComparisonResponse` | — | Core PPP display |
| `RealValueComparison` | `nominal: number, realPPP: number, currency: string` | — | Side-by-side |
| `COLBreakdown` | `items: COLBreakdownItem[], currency: string` | — | Basic tier table |
| `MultiCountryTable` | `countries: ComparisonResult[]` | — | Pro tier only |

---

### Wajar Hidup Components

| Component | Props | States | Notes |
|-----------|-------|--------|-------|
| `CityPairSelector` | `fromCity: string, toCity: string, onChange: (pair: CityPair) => void` | — | Two dropdowns (20 cities) |
| `LifestyleTierSelector` | `value: LifestyleTier, onChange: (v: LifestyleTier) => void` | — | 3-option radio with descriptions |
| `COLAdjustmentResult` | `result: COLCompareResponse, userTier: Tier` | — | Verdict + required salary |
| `CategoryTable` | `breakdown: CategoryBreakdown[]` | — | Basic tier only |

---

## 6.3 UI State Machine (Per Tool)

### Wajar Slip State Machine

```
States:
  IDLE          → Initial load
  UPLOADING     → File selected, uploading to storage
  OCR_VISION    → Google Vision processing
  OCR_TESSERACT → Tesseract.js processing (fallback)
  CONFIRM_FIELDS→ Soft-check: user reviews pre-filled form
  MANUAL_FORM   → Manual input mode
  CALCULATING   → API call to /api/audit-payslip
  VERDICT_FREE  → Result shown, violations gated
  VERDICT_PAID  → Full result shown
  GATE_MODAL    → Upgrade modal open
  PAYMENT_FLOW  → Midtrans Snap open
  ERROR         → Any unrecoverable error

Transitions:
  IDLE → UPLOADING          (user selects/drops file)
  IDLE → MANUAL_FORM        (user clicks "Isi Manual")
  UPLOADING → OCR_VISION    (file uploaded, quota available)
  UPLOADING → OCR_TESSERACT (file uploaded, Vision quota exhausted)
  UPLOADING → ERROR         (file too large, wrong type)
  OCR_VISION → CONFIRM_FIELDS  (confidence 0.80-0.91)
  OCR_VISION → CALCULATING     (confidence ≥ 0.92 AUTO_ACCEPT)
  OCR_VISION → MANUAL_FORM     (confidence < 0.80)
  OCR_TESSERACT → CONFIRM_FIELDS (always — Tesseract always needs confirm)
  CONFIRM_FIELDS → CALCULATING  (user confirms/edits fields)
  MANUAL_FORM → CALCULATING     (user submits form)
  CALCULATING → VERDICT_FREE   (result: user is free tier)
  CALCULATING → VERDICT_PAID   (result: user is Basic+)
  CALCULATING → ERROR          (API error)
  VERDICT_FREE → GATE_MODAL    (user clicks "Lihat selisih IDR")
  GATE_MODAL → PAYMENT_FLOW    (user clicks upgrade)
  GATE_MODAL → VERDICT_FREE    (user dismisses)
  PAYMENT_FLOW → VERDICT_PAID  (payment success + subscription activated)
  PAYMENT_FLOW → GATE_MODAL    (payment cancelled/failed)
  * → IDLE                     (user clicks "Cek baru")
  * → ERROR                    (unhandled exception)
  ERROR → IDLE                 (user clicks retry)
```

---

### Wajar Gaji State Machine

```
States:
  IDLE
  SEARCHING_TITLE    → Autocomplete API call
  FORM_READY         → All inputs filled, ready to submit
  LOADING_BENCHMARK  → API call to /api/salary/benchmark
  RESULT_FREE        → Province P50 shown, city P25-P75 gated
  RESULT_PAID        → Full city breakdown shown
  CROWDSOURCE_OPEN   → Submission form shown
  CROWDSOURCE_SUCCESS
  GATE_MODAL
  ERROR

Transitions:
  IDLE → SEARCHING_TITLE (user types in job title field)
  SEARCHING_TITLE → FORM_READY (title match found)
  SEARCHING_TITLE → IDLE (no match — show "not found" state)
  FORM_READY → LOADING_BENCHMARK (user submits)
  LOADING_BENCHMARK → RESULT_FREE (user is free)
  LOADING_BENCHMARK → RESULT_PAID (user is Basic+)
  LOADING_BENCHMARK → ERROR (API error or "belum ada data")
  RESULT_FREE → GATE_MODAL (user clicks P25/P75)
  RESULT_* → CROWDSOURCE_OPEN (user clicks "Tambah laporan")
  CROWDSOURCE_OPEN → CROWDSOURCE_SUCCESS (submit)
  CROWDSOURCE_OPEN → RESULT_* (cancel)
```

---

### Wajar Tanah State Machine

```
States:
  IDLE
  LOADING_DISTRICTS  → Province/city change triggers district load
  FORM_READY
  CALCULATING
  RESULT_FREE        → Verdict + P50 shown, P25/P75 gated
  RESULT_PAID
  NO_DATA            → "Belum ada data" for entered district
  GATE_MODAL
  ERROR

Transitions:
  IDLE → LOADING_DISTRICTS (province/city selected)
  LOADING_DISTRICTS → FORM_READY (districts loaded)
  FORM_READY → CALCULATING (user submits)
  CALCULATING → RESULT_FREE (has data, free user)
  CALCULATING → RESULT_PAID (has data, paid user)
  CALCULATING → NO_DATA (n < 5 for entered cell)
  CALCULATING → ERROR (API error)
  RESULT_FREE → GATE_MODAL (user clicks P25/P75)
  NO_DATA → IDLE (user changes location)
```

---

### Wajar Kabur State Machine

```
States:
  IDLE
  FORM_FILLED
  CALCULATING
  RESULT_FREE_COUNTRY   → Selected country is in free tier (top 5)
  RESULT_GATED_COUNTRY  → Country requires Basic+
  RESULT_PAID
  GATE_MODAL
  ERROR

Transitions:
  IDLE → FORM_FILLED (all inputs provided)
  FORM_FILLED → CALCULATING (user clicks compare)
  FORM_FILLED → GATE_MODAL (user selects locked country without auth)
  CALCULATING → RESULT_FREE_COUNTRY (top-5 country, any tier)
  CALCULATING → RESULT_GATED_COUNTRY (non-top-5, free tier)
  CALCULATING → RESULT_PAID (paid user, any country)
  RESULT_GATED_COUNTRY → GATE_MODAL (user clicks unlock)
  RESULT_FREE_COUNTRY → GATE_MODAL (user clicks CoL detail)
```

---

### Wajar Hidup State Machine

```
States:
  IDLE
  FORM_READY
  CALCULATING
  RESULT_FREE     → Verdict + required salary shown, category breakdown gated
  RESULT_PAID
  SAME_CITY_ERROR → fromCity === toCity
  GATE_MODAL
  ERROR

Transitions:
  IDLE → FORM_READY (both cities selected, salary entered)
  FORM_READY → CALCULATING (submit)
  FORM_READY → SAME_CITY_ERROR (fromCity === toCity)
  CALCULATING → RESULT_FREE
  CALCULATING → RESULT_PAID
  CALCULATING → ERROR
  RESULT_FREE → GATE_MODAL (user clicks category breakdown)
```

---

## 6.4 Error State Catalog

Every error shown to users must be in Bahasa Indonesia with a clear recovery action.

| Error Code | Trigger | Display | Message (ID) | Recovery Action |
|-----------|---------|---------|-------------|----------------|
| `INVALID_CITY` | City not in UMK DB | Inline form | "Kota ini belum ada dalam database kami. Coba kota terdekat." | Dropdown with suggestions |
| `INVALID_SALARY` | Salary < 500K or > 1B | Inline form | "Gaji tidak valid. Masukkan antara Rp 500.000 – Rp 1.000.000.000" | Clear + refocus field |
| `FILE_TOO_LARGE` | Upload > 5MB | Upload zone | "File terlalu besar (maks 5MB). Kompres foto atau gunakan JPEG." | Retry button |
| `INVALID_FILE_TYPE` | Not JPEG/PNG/PDF | Upload zone | "Format tidak didukung. Gunakan JPEG, PNG, atau PDF." | Retry button |
| `OCR_FAILED` | Vision + Tesseract both fail | Result area | "Gagal membaca slip. Coba foto dengan pencahayaan lebih baik, atau isi manual." | Switch to manual mode |
| `RATE_LIMIT` | Too many requests | Toast | "Terlalu banyak percobaan. Coba lagi dalam 1 jam." | None (just info) |
| `CALCULATION_ERROR` | Unexpected calc error | Error card | "Terjadi kesalahan kalkulasi. Tim kami sudah diberitahu." | Retry button + mailto link |
| `NO_DATA` | Property district n<5 | Result area | "Belum cukup data untuk area ini. Coba kecamatan terdekat." | Location change button |
| `NO_SALARY_DATA` | Job+city no match | Result area | "Belum ada data untuk kombinasi ini. Data akan bertambah seiring waktu." | Suggest submit own salary |
| `PPP_UNAVAILABLE` | World Bank API down | Result area | "Data PPP tidak tersedia saat ini. Coba beberapa menit lagi." | Retry button (auto-retry 3×) |
| `PAYMENT_FAILED` | Midtrans error | Modal | "Pembayaran gagal. Coba metode lain atau ulangi." | Midtrans Snap re-open |
| `SESSION_EXPIRED` | Supabase token expired | Toast | "Sesi berakhir. Masuk kembali untuk melanjutkan." | Login redirect (preserves state) |
| `CITY_PAIR_SAME` | Wajar Hidup: from=to | Inline | "Pilih dua kota berbeda untuk perbandingan." | Clear "to city" field |
| `NETWORK_ERROR` | Fetch failed | Error card | "Periksa koneksi internetmu dan coba lagi." | Retry button |
| `AUTH_REQUIRED` | Non-top-5 country without auth | Gate modal | "Login untuk membandingkan negara ini. Gratis!" | Login button |

---

## 6.5 Mobile Responsiveness Spec

### Breakpoints

| Name | Viewport | Class | Priority |
|------|---------|-------|---------|
| Mobile S | 375px | default (mobile-first) | Highest — Rina's Samsung Galaxy |
| Mobile L | 390px | — | Same as mobile (minor adjustments) |
| Tablet | 768px | `md:` | Navigation changes |
| Desktop | 1280px | `lg:` | Side-by-side layouts |

**Design priority:** Mobile-first. Desktop is secondary. Most users (Rina, Sari) are on phones.

---

### Navigation

| Viewport | Behavior |
|---------|---------|
| Mobile (<768px) | Hamburger menu. Tool links collapse. Show only logo + menu icon + login avatar |
| Tablet (768px+) | Show 5 tool links horizontally in smaller font. Hamburger gone. |
| Desktop (1280px+) | Full nav bar. Tool names in full. |

```
Mobile nav (768px):
[logo]                        [☰] [👤]

Desktop nav:
[logo] [Wajar Slip] [Wajar Gaji] [Wajar Tanah] [Wajar Kabur] [Wajar Hidup] [Login]
```

---

### Form Layout

| Element | Mobile | Desktop |
|---------|--------|---------|
| Form width | Full width (padding: 16px) | max-width: 640px, centered |
| Two-column inputs (PTKP + City) | Stack vertically | Side by side |
| CTA button | Full width, height 56px | Width: 200px, height 48px |
| Input font size | 16px minimum (prevents iOS zoom) | 14px |

**iOS Zoom Prevention:** All `<input>` elements must have `font-size: 16px` minimum. Below 16px, iOS Safari auto-zooms on focus, which breaks the layout.

---

### Touch Targets

All interactive elements must meet the 44×44px minimum:

| Element | Default Size | Enforced Size |
|---------|-------------|---------------|
| Nav links (mobile) | varies | min-height: 44px |
| Dropdown selectors | varies | min-height: 48px |
| CTA buttons | varies | min-height: 56px (mobile), 48px (desktop) |
| Upload zone trigger | varies | min-height: 100px (entire zone tappable) |
| Close/dismiss buttons | varies | min-width: 44px, min-height: 44px |
| Radio buttons | varies | Wrapped in label with padding: 12px |
| Violation items (info expand) | varies | min-height: 44px |

**Implementation (Tailwind):**
```
<button className="h-14 px-6 w-full md:w-auto md:h-12">
```

---

### Country Selector (Wajar Kabur Mobile)

On mobile: vertical list instead of grid.

```
Mobile (375px):                Desktop (1280px):
┌──────────────────────────┐  [🇸🇬 SG] [🇲🇾 MY] [🇦🇺 AU] [🇺🇸 US] [🇬🇧 GB]
│ 🇸🇬 Singapura      →    │  [🔒 JP ] [🔒 KR ] [🔒 UAE] [🔒 NL ] [🔒 DE ]
├──────────────────────────┤  ...
│ 🇲🇾 Malaysia       →    │
├──────────────────────────┤
│ 🇦🇺 Australia      →    │
...
```

---

### Result Cards on Mobile

Verdict cards expand to full width. Tables become scrollable horizontally:

```css
/* Category table on mobile */
.category-table-wrapper {
  overflow-x: auto;
  -webkit-overflow-scrolling: touch;
}
```

Or alternatively: collapse to accordion on mobile, expand per category.

---

### Performance Targets

| Metric | Mobile Target | Desktop Target | Notes |
|--------|--------------|----------------|-------|
| LCP (Largest Contentful Paint) | < 2.5s | < 1.5s | Vercel Edge CDN |
| FID / INP | < 100ms | < 100ms | No heavy JS on initial load |
| CLS | < 0.1 | < 0.1 | Reserve height for images/results |
| Bundle size (initial JS) | < 150KB gzipped | < 200KB | |
| Tesseract.js (lazy) | Loaded on demand | Loaded on demand | Only when user enters upload flow |
| OCR result display | < 8s end-to-end | < 5s end-to-end | Vision API latency dominates |

**Safari-specific notes (Sari's iPhone):**
- Test drag-and-drop in Safari — use click-to-select as primary on mobile
- `position: sticky` requires `-webkit-sticky`
- CSS Grid gap works, but test on iOS 15+
- Test Midtrans Snap popup doesn't get blocked by Safari popup blocker
- BFCACHE: ensure back-navigation restores form state

---

### Component Collapse Behavior at 375px

| Component | Desktop | Mobile (375px) |
|-----------|---------|---------------|
| Two-col form row | Side by side | Stacked |
| Salary range bar + numbers | Inline | Chart on top, numbers below |
| Category table | Full table | Scrollable or accordion |
| Verdict card | Icon + text side by side | Icon above text |
| Country grid | 5-column grid | Vertical list |
| Nav links | Horizontal | Hamburger drawer |
| PDF download button | Inline with verdict | Full-width below verdict |
| Confidence badge | Inline next to P50 | Below P50 |

# req_03 — User Persona Docs: cekwajar.id
**Document Type:** User Persona  
**Version:** 1.0  
**Based on:** Indonesian formal workforce data (BPS 2023), Indonesian digital behavior reports (APJII 2023), Wajar Slip beta feedback assumptions

---

## Persona 1: Rina — "Karyawan Curiga"

### Demographic Profile

| Attribute | Value |
|-----------|-------|
| **Name** | Rina Andriani |
| **Age** | 28 years old |
| **Location** | Bekasi, commutes to Jakarta Selatan |
| **Education** | S1 Akuntansi, Universitas Gunadarma |
| **Job** | Staff HRD & GA at a trading company (50 employees) |
| **Tenure** | 3 years |
| **Monthly Gross Salary** | IDR 7,500,000 |
| **PTKP Status** | TK/0 (single, no dependents) |
| **NPWP** | Yes, registered 2 years ago |
| **Device** | Samsung Galaxy A34 (primary), laptop at work |
| **Browser** | Chrome mobile |
| **Data plan** | Telkomsel 10GB/month |
| **Social media** | TikTok (daily, 2 hours), Instagram (daily), LinkedIn (weekly) |

### Psychographic Profile

**Goals:**
- Understand if her payslip deductions are correct
- Have enough savings to put down DP for a KPR in 2–3 years
- Eventually move to a larger company with better compensation

**Pain points:**
- Her company uses a small payroll software and she's not sure the PPh21 is calculated with the new TER method (changed January 2024)
- She processes payroll for the company but doesn't fully understand the PPh21 rules herself
- She's afraid to ask finance directly in case it's awkward or she looks incompetent
- She googled "cara hitung PPh21 2024" and got confused by multiple conflicting articles

**Frustrations:**
- DJP's online tools (e-SPT) are confusing and not designed for employees
- WageIndicator.co.id exists but feels outdated and not in Bahasa Indonesia
- Tax consultants cost IDR 500K–2M per consultation — way above her WTP

**Information sources:**
- TikTok (financial TikTok / "FinTok") — she learned about BPJS rights from a TikTok video
- r/finansialku on Reddit — reads it but rarely posts
- WhatsApp group with fellow HRD staff

### Trigger for Using cekwajar.id

Rina sees a TikTok video: "Gajimu dipotong PPh21 tapi ngga punya NPWP? Kamu harusnya kena 20% lebih besar." She realizes she registered her NPWP late (February 2023) and wonders if all her 2022 deductions were calculated at +20%. She searches for a quick checker tool.

### Product Interaction Pattern

1. Lands on Wajar Slip from TikTok link
2. Reads landing page hero for 10 seconds, clicks "Mulai Gratis"
3. Tries to upload photo of payslip (taken on phone) — OCR confidence 0.75 (soft check)
4. Corrects 2 fields manually, submits
5. Sees "ADA PELANGGARAN — V02: BPJS JP kurang IDR X" (first violation visible)
6. Curious about exact IDR amount → hits gate
7. Considers IDR 29K — thinks for 2 days
8. Returns, upgrades, sees full breakdown
9. Prints result, brings printed copy to finance to ask "Ini betul ngga?"
10. Submits Wajar Gaji — wants to know if her IDR 7.5M is market rate for HRD Staff in Bekasi

### Willingness to Pay

**Amount:** IDR 29K/month (Basic)  
**Trigger:** "If I can show finance this printout and get even IDR 100K back, it's worth it"  
**WTP ceiling:** IDR 49K — above this she'll wait  
**Payment preference:** GoPay (she has Gojek daily anyway)  
**Upgrade to Pro:** Only if she needs December true-up simulation

### Wajar Slip Design Implications

- Mobile-first: upload photo, not scan PDF (she doesn't have a scanner)
- Form labels must be in Bahasa Indonesia, not English field names
- Never use the word "SPT" — she'll be scared off
- Violation message must explain consequence in plain language ("kamu bisa minta kembali selisihnya ke HRD")
- OCR flow must handle Samsung phone photos gracefully

---

## Persona 2: Dimas — "Gen Z Global"

### Demographic Profile

| Attribute | Value |
|-----------|-------|
| **Name** | Dimas Pratama |
| **Age** | 24 years old |
| **Location** | Surabaya (living with parents) |
| **Education** | S1 Teknik Informatika, ITS Surabaya (graduated 2023) |
| **Job** | Backend Developer, startup (30 employees), WFH |
| **Tenure** | 1 year |
| **Monthly Gross Salary** | IDR 8,500,000 |
| **PTKP Status** | TK/0 |
| **NPWP** | Yes |
| **Device** | MacBook Pro M3 (primary), iPhone 14 |
| **Browser** | Chrome desktop |
| **Social media** | Twitter/X (tech discourse), TikTok, LinkedIn (active) |
| **Communities** | Discord tech servers, r/cscareerquestions, LinkedIn |

### Psychographic Profile

**Goals:**
- Work at a company in Singapore or Australia within 2 years
- Understand if his current IDR 8.5M salary is fair or if he should switch companies
- Move out of parents' house — needs to understand if Surabaya vs Jakarta cost of living math works

**Pain points:**
- He received a LinkedIn message from a Singapore company offering SGD 4,500/month but has no idea if that's actually better than his current salary in real terms
- He compared IDR/SGD exchange rate (≈IDR 68M) and thinks it's amazing, but doesn't know about cost of living in Singapore
- He wants to know if Surabaya → Jakarta for a salary bump of IDR 4M is actually worth it after accounting for cost of living difference
- He tried using Numbeo manually but found it confusing to interpret

**Frustrations:**
- No Indonesian-language tool does this comparison
- Expatistan and Numbeo are in English, use USD, and don't account for Indonesia as the baseline
- LinkedIn Salary is behind a paywall and doesn't have good Indonesian data

**Information sources:**
- Twitter/X tech community (Indonesian tech Twitter is active)
- TikTok: financial content about "kerja di Singapore"
- YouTube: Indonesian vloggers abroad ("kehidupan di Singapura")

### Trigger for Using cekwajar.id

Dimas sees a tweet: "Tools baru nih buat ngitung gaji luar negeri setara berapa IDR secara riil, bukan cuma kurs. cekwajar.id/wajar-kabur" — he clicks immediately.

### Product Interaction Pattern

1. Lands directly on Wajar Kabur from tweet link
2. Enters IDR 8,500,000 + "Backend Developer" + Singapore
3. Sees PPP result instantly (free tier): his salary ≈ SGD 1,800 in purchasing power
4. The offer was SGD 4,500 — he sees it's 2.5× in real terms, not just nominal
5. Curious about CoL breakdown → hits gate for "lihat detail biaya hidup Singapura"
6. Buys Basic IDR 29K — he's impulse-buying, very fast decision
7. Opens Wajar Hidup next: Surabaya → Jakarta comparison
8. Enters current salary IDR 8.5M: needs IDR 10.8M in Jakarta to maintain same lifestyle (+27%)
9. He uses this data in a negotiation with a Jakarta company: "I need at least IDR 11M to consider relocating"

### Willingness to Pay

**Amount:** IDR 29K (impulse buy, Basic)  
**Trigger:** Emotional + immediate data need (live offer negotiation)  
**WTP ceiling:** IDR 79K for Pro if in active job search mode  
**Payment preference:** GoPay or OVO (instant)  
**Upgrade to Pro:** Yes, if multi-country comparison saves time during active search

### Wajar Kabur Design Implications

- Desktop-friendly: Dimas is on MacBook, side-by-side layout works
- Results must answer: "Is it worth going?" in one sentence — not buried in data
- PPP explanation must be 1 simple sentence: "IDR Xjt di Indonesia setara dengan [amount] di Singapore dalam daya beli riil"
- Must show comparison to his current salary, not just absolute numbers
- CoL breakdown should show Jakarta vs Singapore too (he lives this comparison daily)

---

## Persona 3: Sari — "Pembeli Properti Pertama"

### Demographic Profile

| Attribute | Value |
|-----------|-------|
| **Name** | Sari Wulandari |
| **Age** | 32 years old |
| **Location** | Bekasi, married (K/0), 1 toddler |
| **Education** | S1 Manajemen, Universitas Trisakti |
| **Job** | Supervisor Procurement, manufacturing company (500+ employees) |
| **Tenure** | 5 years at current company |
| **Monthly Gross Salary** | IDR 14,000,000 |
| **PTKP Status** | K/1 |
| **NPWP** | Yes |
| **Device** | iPhone 12 (primary), company laptop |
| **Browser** | Safari mobile |
| **Social media** | Instagram (daily), Facebook (family), TikTok (light) |
| **Communities** | Facebook group "KPR & Properti Indonesia", WhatsApp group with colleagues |

### Psychographic Profile

**Goals:**
- Buy first home in Bekasi or Depok within 12 months
- Determine if a specific house priced at IDR 850M for 72m² land in Pondok Gede area is a fair price
- Avoid being scammed or overpaying — she's heard stories of buyers paying 30% above market
- Understand NJOP vs market price before signing anything

**Pain points:**
- Real estate agents quote prices with no justification — "harga pasaran" claims with zero data
- Online sites (99.co, Rumah123) show listings but she can't tell if the listed prices are actually market rate or inflated asking prices
- NJOP from the PBB certificate is IDR 4.2M/m² but she's told market is IDR 11–12M/m² — she doesn't know which to trust
- She can't afford a KJPP appraisal (IDR 2–5M per property) just for preliminary research on 5 different properties she's considering

**Frustrations:**
- No tool gives a clean "Mahal / Wajar / Murah" verdict for a specific kecamatan
- Google shows property news but not kelurahan-level price data
- Friends give anecdotal advice ("di situ mahal") without data

**Information sources:**
- Facebook groups for KPR buyers (very active, lots of sharing)
- YouTube: property review channels (channel "Sobat Properti", "Property Hunter")
- WhatsApp: asks friends who recently bought
- Instagram: property agent accounts

### Trigger for Using cekwajar.id

Sari is in the "KPR & Properti Indonesia" Facebook group. Someone posts: "Tools gratis buat ngecek harga tanah/rumah wajar atau ngga di satu kelurahan: cekwajar.id/wajar-tanah". She clicks immediately — this is exactly what she's been looking for.

### Product Interaction Pattern

1. Lands on Wajar Tanah from Facebook link (mobile Safari)
2. Selects: Jawa Barat → Bekasi → Pondok Gede → Rumah → 72m² → IDR 850M (= IDR 11.8M/m²)
3. Sees verdict immediately: **MAHAL** — P50 market for Pondok Gede is IDR 9.8M/m²
4. Sees P25 is blurred (gate) — wants full range
5. Deliberates more than Rina or Dimas — this is a major purchase, IDR 29K feels trivial
6. Upgrades Basic: sees P25 = IDR 8.2M, P75 = IDR 11.5M — asked price is at P85
7. Downloads PDF report, WhatsApps it to husband: "Lihat ini, kita harusnya nego ke 10M/m²"
8. They negotiate: seller comes down to IDR 10.3M/m² — IDR 504M saving on total price

### Willingness to Pay

**Amount:** IDR 29K–79K (she'll pay Basic immediately, may pay Pro for detailed report)  
**Trigger:** High-stakes purchase — IDR 29K is negligible vs IDR 800M home  
**WTP ceiling:** IDR 150K for a professional-looking PDF report  
**Payment preference:** Transfer bank / VA (she's more conservative, not GoPay user for large transactions)  
**Upgrade to Pro:** If she's actively viewing 5+ properties simultaneously

### Wajar Tanah Design Implications

- Mobile Safari must work perfectly — no layout breaks
- Property input must have a smooth provincial → city → district drill-down (no free text — she doesn't know the spelling of all kelurahan)
- Verdict must be bold and unambiguous — "MAHAL" in red, not a vague score
- NJOP vs market price explanation must be simple: "NJOP adalah nilai pajak, bukan harga pasar"
- PDF output must look "professional" enough to show an agent or husband — not a screenshot
- Sample count must be visible — she wants to know if the data is based on 5 listings or 500

---

## Persona Summary Table

| Attribute | P1: Rina (Karyawan Curiga) | P2: Dimas (Gen Z Global) | P3: Sari (Pembeli Pertama) |
|-----------|---------------------------|--------------------------|---------------------------|
| Age | 28 | 24 | 32 |
| City | Bekasi/Jakarta | Surabaya | Bekasi |
| Salary | IDR 7.5M | IDR 8.5M | IDR 14M |
| Primary tool | Wajar Slip + Gaji | Wajar Kabur + Hidup | Wajar Tanah |
| Decision speed | Medium (2 days) | Fast (impulse) | Slow (1 week) |
| WTP | IDR 29K/mo | IDR 29K (impulse) | IDR 29–79K (one-time) |
| Payment method | GoPay | GoPay/OVO | VA Bank |
| Primary device | Android mobile | Desktop Mac | iPhone (mobile Safari) |
| Content channel | TikTok | Twitter/X | Facebook group |
| Key design need | Simple Indonesian labels | Side-by-side desktop comparison | Clear verdict + PDF export |

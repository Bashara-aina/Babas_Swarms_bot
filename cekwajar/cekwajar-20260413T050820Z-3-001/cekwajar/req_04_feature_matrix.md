# req_04 — Feature Prioritization Matrix: cekwajar.id
**Document Type:** Feature Priority Matrix  
**Version:** 1.0  
**Priority Definitions:**
- **P0** = Launch blocker. Ship without this = don't ship.
- **P1** = Must ship by Week 4. Significant UX degradation without it.
- **P2** = Target Month 2. Valuable but not launch-critical.
- **Excluded** = Explicitly not building. Re-open requires new decision.

---

## Shared Platform Features

| Feature | Priority | Rationale | Owner | Effort |
|---------|----------|-----------|-------|--------|
| Next.js 15 App Router scaffold | P0 | Foundation for all tools | Cursor | 4h |
| Supabase project + all base tables | P0 | Required for auth, data, edge functions | Supabase setup | 2h |
| Supabase Auth (Email + Google OAuth) | P0 | User identity for subscription gating | Cursor + Supabase | 3h |
| Global nav bar (5 tool links) | P0 | Discoverability across tools | Cursor | 1h |
| Privacy Policy page (Bahasa Indonesia) | P0 | UU PDP legal requirement | Cursor | 1h |
| Terms of Service page | P0 | Legal requirement | Cursor | 1h |
| Cookie consent banner | P0 | UU PDP Pasal 25 | Cursor | 2h |
| PSE Kominfo registration | P0 | Mandatory before collecting personal data | Manual | 0.5h |
| HTTPS / SSL | P0 | Default on Vercel | Auto | 0h |
| RLS on all user data tables | P0 | UU PDP + security | Supabase setup | 2h |
| Supabase Storage bucket "payslips" (private) | P0 | File storage for OCR | Supabase setup | 0.5h |
| Midtrans Snap integration | P0 | Required for any monetization | Cursor | 4h |
| Midtrans webhook handler + signature verify | P0 | Without this, payments fail silently | Cursor | 2h |
| subscription_tier gating (RLS + component) | P0 | Core freemium model | Cursor | 3h |
| Sentry error monitoring | P1 | Error detection — can survive without briefly | Manual | 0.5h |
| Vercel Analytics | P1 | Basic traffic monitoring | Manual | 0.5h |
| Email (Resend) — transactional | P1 | Welcome + payment confirmation emails | Cursor | 2h |
| User dashboard (audit history) | P1 | Required for subscriber retention | Cursor | 4h |
| Subscription expiry notification (email) | P1 | Reduce churn | Cursor | 2h |
| Share card (OG image, @vercel/og) | P2 | Viral loop support | Cursor | 3h |
| B2B licensing API | Excluded | Month 9+ | — | — |
| Native iOS/Android app | Excluded | Month 12+ | — | — |
| Multi-language (English) | Excluded | Month 9+ | — | — |

---

## Tool 1: Wajar Slip

| Feature | Priority | Rationale | Effort |
|---------|----------|-----------|--------|
| Manual input form (all deduction fields) | P0 | Core free path, no OCR dependency | 6h |
| PPh21 TER calculation engine (TypeScript) | P0 | Core product — cannot launch without | 8h |
| PPh21 progressive annual engine | P0 | Required for December + full calculation | 4h |
| BPJS 6-component calculation | P0 | Core violation detection | 4h |
| Violation detector V01–V07 | P0 | The actual value delivered to user | 4h |
| UMK comparison (salary floor check) | P0 | V06 violation — legally significant | 2h |
| Verdict display: free tier (codes only, 1 shown) | P0 | Freemium gate | 3h |
| Freemium gate modal (IDR amounts blurred) | P0 | Revenue conversion path | 2h |
| Disclaimer banner ("bukan nasihat pajak") | P0 | Legal non-negotiable | 0.5h |
| PTKP dropdown (13 options TK/0 → K/I/3) | P0 | Required for correct TER rate | 1h |
| City dropdown for UMK lookup | P0 | V06 detection | 2h |
| December true-up algorithm | P0 | TC-08 — highest bug risk, must be correct | 4h |
| THR/bonus month PPh21 switching | P0 | TC-09 — progressive method on bonus month | 3h |
| No-NPWP surcharge (+20%) | P0 | Regulation requirement | 0.5h |
| Google Vision OCR integration | P1 | Reduces friction, increases conversions | 6h |
| OCR confidence routing (0.70/0.80/0.92) | P1 | Determines OCR path | 3h |
| "Konfirmasi Data" pre-fill screen | P1 | Soft-check OCR fallback | 3h |
| Tesseract.js client-side fallback | P1 | When Vision quota exhausted | 4h |
| Payslip file storage (30-day auto-delete) | P1 | UU PDP data minimization | 2h |
| Audit history (Basic: 3mo, Pro: unlimited) | P1 | Subscriber retention | 4h |
| Full violation IDR amounts (paid) | P0 | Gate unlock — what user actually pays for | 2h |
| PDF audit report export | P2 | Sari persona — high WTP trigger | 6h |
| December true-up simulation (Pro) | P2 | Pro-only value | 4h |
| Employer contribution breakdown | P2 | Extra depth for HRD users | 3h |
| Freelance Pasal 21 (50% deemed PKP) | P2 | TC-14 edge case | 4h |
| SPT form generation | Excluded | Licensed tax software territory | — |
| Multi-year tax history | Excluded | Not in scope | — |

---

## Tool 2: Wajar Gaji

| Feature | Priority | Rationale | Effort |
|---------|----------|-----------|--------|
| Job title input with autocomplete | P0 | Core input | 2h |
| Province P50 from BPS Sakernas (loaded to DB) | P0 | Minimum viable benchmark | 2h |
| UMK floor display for entered city | P0 | Always useful baseline | 1h |
| Confidence badge (Low/Cukup/Terverifikasi) | P0 | Transparency requirement | 1h |
| "Belum ada data" state (honest fallback) | P0 | Better than showing garbage data | 1h |
| Crowdsource anonymous submission form | P0 | Data collection flywheel | 4h |
| K-anonymity check (n≥10 before showing) | P0 | Privacy + credibility | 2h |
| Bayesian blend formula | P0 | Core calculation | 3h |
| Province P50 display (free tier) | P0 | Free value to convert submitters | 1h |
| BPS Sakernas CSV loader (Python agent) | P0 | Must load BPS data before launch | 3h |
| UMK Excel loader (Python agent) | P0 | Floor reference required | 2h |
| City-level P50 when n≥30 (Basic) | P1 | Gate value for Basic | 2h |
| P25/P75 bar chart (Basic) | P1 | Gate value visual | 3h |
| JobStreet scraped salary data (monthly) | P1 | Additional data source | 8h |
| Job title fuzzy matching (pgvector) | P1 | Better UX for title variants | 4h |
| Outlier filter on submission (3×UMK rule) | P1 | Data quality gate | 1h |
| Industry comparison (Pro) | P2 | Pro value | 3h |
| YoY salary trend (Pro) | P2 | Pro value | 4h |
| Company-specific salary data | Excluded | Trade secret legal risk | — |
| Real-time job ad matching | Excluded | Scope creep | — |

---

## Tool 3: Wajar Tanah

| Feature | Priority | Rationale | Effort |
|---------|----------|-----------|--------|
| Province → City → District drill-down | P0 | Core location input | 4h |
| Property type selector (4 types) | P0 | Required for meaningful benchmark | 1h |
| Land area + asking price inputs | P0 | Calculates price/m² | 1h |
| Price/m² benchmark from scraped data | P0 | Core value | 3h |
| Verdict: MURAH/WAJAR/MAHAL/SANGAT_MAHAL | P0 | Primary deliverable | 2h |
| NJOP reference display | P0 | Legitimacy anchor | 2h |
| KJPP disclaimer | P0 | Legal non-negotiable | 0.5h |
| "Belum ada data" state for uncovered areas | P0 | Honest fallback | 1h |
| 99.co + Rumah123 Playwright scraper (monthly) | P0 | Primary data source | 12h |
| Scraper stealth plugin + rate limiting | P0 | Avoid immediate ban | 2h |
| Outlier flag (IQR 1.5x) | P0 | Data quality | 2h |
| Benchmark aggregator (P25/P50/P75) | P0 | Powers the verdict | 3h |
| BJUMI/BPN NJOP data loader | P0 | Official reference | 4h |
| P25/P75 range (Basic) | P1 | Gate value | 2h |
| NJOP/market ratio (Basic) | P1 | Gate value | 1h |
| PDF "mini valuation" export | P1 | Sari persona trigger | 6h |
| Sample count badge | P1 | Data credibility | 1h |
| Price trend (3-month, Pro) | P2 | Requires 3 monthly scrape runs | 3h |
| Nearby comparable summary (Pro) | P2 | Complex, lower priority | 6h |
| Property listings marketplace | Excluded | Different business | — |
| KJPP-certified appraisal | Excluded | Requires licensed professional | — |

---

## Tool 4: Wajar Kabur

| Feature | Priority | Rationale | Effort |
|---------|----------|-----------|--------|
| IDR salary + job role + country inputs | P0 | Core input | 2h |
| World Bank PPP API call + cache | P0 | Core calculation | 3h |
| PPP-adjusted equivalent display | P0 | Primary value | 2h |
| Exchange rate (frankfurter.app) | P0 | Required for context | 1h |
| Free: top 5 countries (SGP, MYS, AUS, USA, GBR) | P0 | Free value tier | 1h |
| Gate: remaining 10 countries | P0 | Basic gate | 1h |
| Political/accuracy disclaimer | P0 | Legal non-negotiable | 0.5h |
| Numbeo CoL basket per target city | P1 | Basic gate value | 4h |
| Market salary for role in target country | P1 | Basic gate value (scraped) | 6h |
| All 15 countries (Basic) | P1 | Expanding free tier | 1h |
| Estimated after-tax (Pro) | P2 | Pro value | 4h |
| Multi-country side-by-side (Pro) | P2 | Pro value | 4h |
| Visa/immigration advice | Excluded | Different profession | — |

---

## Tool 5: Wajar Hidup

| Feature | Priority | Rationale | Effort |
|---------|----------|-----------|--------|
| From city + to city dropdowns | P0 | Core input | 1h |
| Monthly salary input | P0 | Core input | 0.5h |
| Lifestyle tier selector (Hemat/Standar/Nyaman) | P0 | Personalizes result | 1h |
| COL index lookup from BPS CPI data | P0 | Core calculation | 2h |
| % adjustment calculation + required salary | P0 | Core output | 1h |
| Verdict badge (Lebih Murah / Lebih Mahal / Sama) | P0 | Visual verdict | 1h |
| BPS CPI Excel loader (Python agent) | P0 | Data prerequisite | 2h |
| 20-city seed data (COL indices) | P0 | Cover main markets at launch | 2h |
| Category breakdown table (Basic) | P1 | Gate value | 3h |
| Lifestyle tier explanation (with IDR examples) | P1 | UX clarity | 1h |
| BPS CPI trend overlay | P1 | Data context | 2h |
| Historical COL trend (Pro) | P2 | Pro value | 4h |
| Multi-city comparison table (Pro) | P2 | Pro value | 4h |

---

## Priority Summary by Week

### Week 1–2: Foundation (Zero features, pure scaffold)
All P0 "Shared Platform" items above.

### Week 3–6: Wajar Slip full P0 + P1
All P0 + P1 items in Wajar Slip table.

### Week 5–8: Wajar Gaji P0
All P0 items in Wajar Gaji (parallel with Wajar Slip P1).

### Week 7–10: Wajar Tanah + Kabur + Hidup P0
All P0 items for remaining 3 tools.

### Week 11–12: Monetization + GTM
Midtrans live, freemium gates activated, content calendar running.

### Month 2: P1 features across all tools
All P1 items from all 5 tools.

### Month 3+: P2 features (funded by revenue)
Only if MAU and revenue targets from req_01 are met.

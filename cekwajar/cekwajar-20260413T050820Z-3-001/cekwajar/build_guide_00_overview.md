# cekwajar.id — Ultimate Build Guide: Overview & Master Timeline

**For:** 1 Founder + AI Agent Swarms  
**Budget:** IDR 0 (except AI subscription)  
**Target:** All 5 tools live + monetizing by Month 3  
**Reality Level:** Honest — hard things are called hard

---

## Step Type Legend

Every step in all 9 build guide files uses this tagging system:

| Tag | Tool | What you do |
|-----|------|-------------|
| `[CURSOR]` | Cursor IDE | Write/edit code, prompt Cursor AI to generate files |
| `[SWARMS]` | kyegomez/swarms (Python) | Run AI agent pipelines, scraping orchestration, data processing |
| `[SUPABASE]` | Supabase dashboard + SQL editor | Create tables, RLS, Edge Functions, Storage buckets |
| `[PERPLEXITY]` | Perplexity.ai or any AI research | Research regulations, find free APIs, validate data sources |
| `[MANUAL]` | You, no tools | Decisions, registrations, account creations, community posts |
| `[VERCEL]` | Vercel dashboard + CLI | Deploy, env vars, domain, preview URLs |

---

## Reality Check: Can You Actually Do This?

### What IS 100% doable in 3 months, 1 founder + AI agents

| Task | Doable? | Reality Note |
|------|---------|--------------|
| PPh21 + BPJS calculator | ✅ Yes | Regulations are public. Pure math. No paid API needed |
| Payslip OCR (70–85% accuracy) | ✅ Yes | Google Vision free tier (1,000 req/mo) + Tesseract fallback |
| Property price scraping | ✅ Technical | Grey area legally. Covered in detail in guide_03 |
| Salary benchmarks from scraping | ✅ Technical | LinkedIn/Glassdoor block aggressively. Covered in guide_02 |
| Cost of living comparison | ✅ Yes | BPS free data + Numbeo (scraping or free tier) |
| Abroad salary comparison | ✅ Yes | World Bank API + Numbeo |
| Full Next.js frontend for 5 tools | ✅ Yes | Cursor generates 80% of boilerplate |
| Supabase backend | ✅ Yes | Free tier: 500MB DB, 2GB storage, 50K Edge Function calls/mo |
| Midtrans payment integration | ✅ Yes | Free to set up, 1% fee per transaction |
| 70–90% calculation accuracy | ✅ Yes (with caveats) | PPh21/BPJS = 95%+ if built from PMK. Property = 70–80% |
| TikTok content + community GTM | ✅ Yes | Your job, not AI's |

### What is HARD but doable

| Task | Hard Why | Mitigation |
|------|----------|------------|
| 3 months for ALL 5 tools | That's 12 weeks, including bugs, UX, beta | Stagger: Wajar Slip (W1–6), Wajar Gaji (W5–8), rest (W7–12) |
| Scraping not getting blocked | 99.co/Rumah123 have bot detection | Playwright + stealth plugin + rotating proxies |
| BPS data being useful | Province-level only, not city-level job titles | Use for baseline only, crowdsource fills gaps |
| Solo context switching across 5 tools | Mental load is real | Strict week-by-week sprint plan below |
| Accuracy without paid auditor | No professional sign-off | Add "for reference only" disclaimer, get community validation |

### What you should NOT skip even at zero cost

| Item | Why non-negotiable | Cost |
|------|-------------------|------|
| Privacy Policy (Bahasa Indonesia) | UU PDP Pasal 25 requires it | Free: use template in guide_08 |
| PSE registration (Kominfo) | Required for apps collecting personal data | Free: kominfo.go.id form |
| "Bukan nasihat pajak" disclaimer | UU Perlindungan Konsumen Pasal 8 | Free: 1 line of UI text |
| Supabase RLS on user tables | If breached, you have zero legal defense | Free: built into Supabase |
| HTTPS/SSL | Default on Vercel | Free |

---

## 12-Week Master Sprint Plan

### Phase 1: Foundation (Week 1–2)
> **Goal:** Everything scaffolded, Supabase live, domain connected, no tools working yet

| Week | Day | Task | Tag | Reality Check |
|------|-----|------|-----|---------------|
| W1 | 1 | Set up Supabase project (ap-southeast-1 Singapore) | `[SUPABASE]` | 15 min |
| W1 | 1 | Create Vercel project, connect GitHub repo | `[VERCEL]` | 10 min |
| W1 | 1 | Buy cekwajar.id domain (Niagahoster/Domainesia ~IDR 150K/year) | `[MANUAL]` | Only allowed spend |
| W1 | 1–2 | Cursor: scaffold Next.js 15 monorepo with all 5 tool routes | `[CURSOR]` | 3–4 hours |
| W1 | 2–3 | Cursor: create shared UI components (layout, nav, footer, result cards) | `[CURSOR]` | 4–6 hours |
| W1 | 4 | Supabase: create all base tables (users, audit_events, beta signups) | `[SUPABASE]` | 2 hours |
| W1 | 5 | Supabase: enable RLS, create service role Edge Function | `[SUPABASE]` | 1 hour |
| W2 | 1–2 | Cursor: privacy policy page + consent modal (UU PDP minimum) | `[CURSOR]` | 2 hours |
| W2 | 2–3 | Cursor: auth flow (Supabase Auth, Google OAuth) | `[CURSOR]` | 3 hours |
| W2 | 3–4 | Swarms: set up Python environment, install swarms library | `[SWARMS]` | 1 hour |
| W2 | 5 | Register Kominfo PSE (online form) | `[MANUAL]` | 30 min, 2–4 week approval |
| W2 | 5 | Set up Google Cloud account → enable Vision API → get free 1000/mo | `[MANUAL]` | 30 min |

**End of Week 2 checkpoint:** Skeleton app deployed on Vercel, auth works, DB live, no tools functional yet. ✅

---

### Phase 2: Wajar Slip + Wajar Gaji Core (Week 3–6)
> **Goal:** Wajar Slip fully working, Wajar Gaji in beta with crowdsource data collection

| Week | Day | Task | Tag |
|------|-----|------|-----|
| W3 | 1–3 | Cursor: PPh21 + BPJS calculation engine (TypeScript) | `[CURSOR]` |
| W3 | 3–5 | Cursor: manual payslip input form (free path, no OCR) | `[CURSOR]` |
| W4 | 1–3 | Cursor: Google Vision OCR integration (free tier) | `[CURSOR]` |
| W4 | 3–5 | Cursor: OCR field extractor + confidence scoring UI | `[CURSOR]` |
| W5 | 1–2 | Swarms: build `PayslipOCRAgent` (batch processing pipeline) | `[SWARMS]` |
| W5 | 2–3 | Supabase: payslip storage bucket (30-day auto-delete via pg_cron) | `[SUPABASE]` |
| W5 | 3–5 | Cursor: violation detector UI (V01–V07 violation codes) | `[CURSOR]` |
| W6 | 1–2 | Cursor: Wajar Gaji form + result card | `[CURSOR]` |
| W6 | 2–3 | Swarms: `BPSDataAgent` — download + parse BPS Sakernas CSV | `[SWARMS]` |
| W6 | 3–4 | Supabase: salary_benchmarks table, load BPS data | `[SUPABASE]` |
| W6 | 5 | Manual beta: recruit 30 people from community | `[MANUAL]` |

**End of Week 6 checkpoint:** Wajar Slip working (manual input + OCR). Wajar Gaji shows benchmarks (BPS province data only, clear disclaimer). 30 beta users. ✅

---

### Phase 3: Property + Abroad + Living (Week 7–10)
> **Goal:** All 5 tools functional with real data (scraping live)

| Week | Day | Task | Tag |
|------|-----|------|-----|
| W7 | 1–3 | Swarms: `PropertyScraperAgent` for 99.co + Rumah123 (Playwright stealth) | `[SWARMS]` |
| W7 | 3–5 | Cursor: Wajar Tanah UI + result card | `[CURSOR]` |
| W8 | 1–2 | Supabase: property_listings table, load scraped data | `[SUPABASE]` |
| W8 | 2–3 | Cursor: Wajar Tanah median/P25/P75 per kelurahan | `[CURSOR]` |
| W8 | 3–5 | Swarms: `WorldBankAgent` — fetch PPP + GDP per capita via free API | `[SWARMS]` |
| W9 | 1–2 | Cursor: Wajar Kabur form + abroad salary comparison | `[CURSOR]` |
| W9 | 2–3 | Swarms: `NumbeoScraperAgent` for cost of living data | `[SWARMS]` |
| W9 | 3–5 | Cursor: Wajar Hidup city comparison UI | `[CURSOR]` |
| W10 | 1–3 | Integration testing: all 5 tools end-to-end | `[CURSOR]` |
| W10 | 3–5 | Bug fixes, mobile responsiveness, loading states | `[CURSOR]` |

**End of Week 10 checkpoint:** All 5 tools functional. Not perfect. Property data 70–80% accuracy. Salary data BPS + crowdsource only. ✅

---

### Phase 4: Public Launch + Monetization (Week 11–12)
> **Goal:** Public, TikTok GTM firing, Midtrans live, first paying users**

| Week | Day | Task | Tag |
|------|-----|------|-----|
| W11 | 1–2 | Cursor: Midtrans Snap integration (freemium gates) | `[CURSOR]` |
| W11 | 2–3 | Supabase: subscriptions table, RLS-gated premium features | `[SUPABASE]` |
| W11 | 3–4 | Cursor: premium result card (blurred P25/P75 for free users) | `[CURSOR]` |
| W11 | 5 | Manual: Midtrans sandbox → production approval (3–5 days) | `[MANUAL]` |
| W12 | 1–2 | TikTok: 10 launch videos (scripts from block_06_gtm_execution.md) | `[MANUAL]` |
| W12 | 2–3 | Community seeding: r/finansialku, TikTok, Twitter/X, WhatsApp groups | `[MANUAL]` |
| W12 | 3–4 | Monitor first users, fix critical bugs | `[CURSOR]` |
| W12 | 5 | Week 12 review: traffic, conversions, bug reports | `[MANUAL]` |

**End of Week 12:** Public launch. Target: 200–500 unique users, 5–15 paying subscribers. Not viral, but alive. ✅

---

## Month 3–6: Post-Launch Survival

| Month | Priority | Goal |
|-------|----------|------|
| Month 3 | Monetization live | First IDR revenue via Midtrans. Even 10 × IDR 29K = IDR 290K validates it |
| Month 4 | Crowdsource acceleration | More Wajar Gaji submissions = better data. TikTok consistency |
| Month 5 | Scraper health | Check if 99.co/Rumah123 blocked scrapers. Re-run if needed |
| Month 6 | Revenue threshold | If >IDR 5M/month ARR: upgrade Supabase Pro (IDR 250K/mo), buy Mercer data snippet |

---

## Full Stack Summary (Zero Paid Tools)

| Layer | Tool | Free Tier | Limit |
|-------|------|-----------|-------|
| Frontend | Next.js 15 | Free forever | — |
| Hosting | Vercel Hobby | Free | 100GB bandwidth/mo |
| Database | Supabase Free | Free | 500MB DB, 50K Edge Function calls |
| Auth | Supabase Auth | Free | 50K MAU |
| Storage | Supabase Storage | Free | 1GB |
| OCR | Google Vision API | Free | 1,000 req/month |
| OCR fallback | Tesseract.js | Free forever | — |
| Scraping | Playwright + Python | Free forever | — |
| AI Agents | kyegomez/swarms | Free + local | Needs OpenRouter or Ollama |
| LLM for agents | Ollama (local) or Groq | Free | Groq: 30 req/min free |
| Payments | Midtrans | Free setup | 1% MDR per transaction |
| World Bank API | Free REST API | Free | 500 req/min |
| BPS data | Manual CSV download | Free | Updated yearly |
| Exchange rates | exchangerate-api.com | Free | 1,500 req/month |
| Email | Resend | Free | 3,000 emails/mo |
| Analytics | Vercel Analytics | Free | Basic only |
| Cron jobs | Supabase pg_cron | Free | Included |
| Monitoring | Sentry | Free | 5K errors/month |

**Monthly cost at launch:** ~IDR 0 (AI subscription excluded)  
**Month 6 upgrade threshold:** If ARR > IDR 5M/month, upgrade Supabase Pro + buy targeted data

---

## Data Accuracy Reality Table

| Tool | Free Data Source | Expected Accuracy | Gap vs Paid |
|------|-----------------|-------------------|-------------|
| Wajar Slip (PPh21/BPJS) | PMK 168/2023, PP 46/2015 (public regs) | 92–97% | Near-zero. Regs are exact |
| Wajar Gaji | BPS Sakernas + crowdsource | 65–75% | ±15–25% vs Mercer/WTW |
| Wajar Tanah | 99.co/Rumah123 scraping + NJOP | 70–80% | ±20–30% vs KJPP appraisal |
| Wajar Kabur | World Bank API + Numbeo | 75–85% | ±10–20% vs Mercer global |
| Wajar Hidup | BPS CPI + Numbeo scrape | 70–80% | ±15–25% vs actual surveys |

**Key insight:** Wajar Slip is your anchor product because regulatory math = near-perfect accuracy at zero cost. Build that first, use it to acquire users, then add others.

---

## Legal Risk Summary (Honest Assessment)

| Risk | Severity | Probability | Mitigation |
|------|----------|-------------|------------|
| Scraping 99.co/Rumah123 ToS violation | Medium | High | Rotate IPs, don't hammer servers, add scraped-data disclaimer in UI |
| UU ITE Pasal 30 (unauthorized system access) | High if prosecuted | Low (no enforcement precedent for small startups) | Never bypass CAPTCHA, never use stolen auth tokens |
| UU PDP data breach | High | Low if RLS implemented | Supabase RLS + 30-day auto-delete |
| PPh21 calculation error causing financial harm | Medium | Low if disclaimers clear | "Untuk referensi saja, bukan nasihat pajak" on every result |
| OJK/Kominfo enforcement | Low | Very low at 0–5K users | PSE registration covers minimum obligation |

**Bottom line:** At <5K users and zero claims of professional advice, enforcement risk is close to zero. Disclaimers + PSE registration is the minimum viable legal posture.

---

## Continue To Individual Tool Guides

| Guide | File | Estimated Build Time |
|-------|------|---------------------|
| 01 | `build_guide_01_wajar_slip.md` | 6 weeks total (hardest) |
| 02 | `build_guide_02_wajar_gaji.md` | 2 weeks after scaffold |
| 03 | `build_guide_03_wajar_tanah.md` | 2 weeks after scaffold |
| 04 | `build_guide_04_wajar_kabur.md` | 1 week after scaffold |
| 05 | `build_guide_05_wajar_hidup.md` | 1 week after scaffold |
| 06 | `build_guide_06_ai_agents_swarms.md` | Parallel with all above |
| 07 | `build_guide_07_monetization.md` | Week 11–12 |
| 08 | `build_guide_08_legal_minimum.md` | Week 1–2 |

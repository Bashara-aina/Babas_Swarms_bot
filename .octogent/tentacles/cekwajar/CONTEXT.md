# Cekwajar Suite — Indonesian Financial Compliance Tools

The Cekwajar product suite: five B2C SaaS tools for Indonesian workers and
employers covering salary auditing, cost-of-living analysis, land valuation,
and emigration planning. Compliant with Indonesian PDP Law and tax regulations.

## The five tools
1. Wajar Slip — pay slip analyzer (UMR compliance, deductions, overtime)
2. Wajar Gaji — salary benchmarking (by region, industry, experience)
3. Wajar Hidup — cost-of-living calculator (by city, lifestyle)
4. Wajar Tanah — land/property valuation (NJOP vs market price)
5. Wajar Kabur — emigration financial readiness calculator

## Stack
- Frontend: Next.js 14, TypeScript, Tailwind CSS
- Backend: Supabase (auth + DB + storage)
- Deployment: Vercel
- Regulations: UMR 2025, PPh 21, BPJS Kesehatan + Ketenagakerjaan

## Important files (adjust paths to actual repo location)
- src/app/ — Next.js app router pages
- src/components/ — shared UI components
- src/lib/ — utility functions, Supabase client
- supabase/migrations/ — DB schema

## Constraints
- Indonesian regulations change annually — always cite source and year
- UMR/UMP data must be from official BPS or Kemenaker sources
- BPJS rates: Kesehatan 5% (employer 4%, employee 1%), TK varies by program
- PPh 21 uses PTKP 2024: Rp 54,000,000/year (single), Rp 4,500,000/month
- Never store PII — all calculations must be stateless or anonymized
- PDP Law compliance: explicit consent before any data processing

<!-- octogent:suggested-skills:start -->
<!-- octogent:suggested-skills:end -->
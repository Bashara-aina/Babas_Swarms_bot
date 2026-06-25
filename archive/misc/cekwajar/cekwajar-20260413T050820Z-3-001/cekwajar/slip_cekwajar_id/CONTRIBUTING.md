# Maintenance Checklist — cekwajar.id

## Every February (before 1 March)
- [ ] Check BPJS TK official site for new JP upah maximum
       https://www.bpjsketenagakerjaan.go.id/berita/
- [ ] Check for new Peraturan Presiden on upah JP
       https://peraturan.bpk.go.id (search: Perpres upah JP [year])
- [ ] Update BPJS_JP.wage_cap_[year] in lib/regulations.ts
- [ ] Add changelog entry to REGULATION_META
- [ ] Set JP_CAP_[year]_VERIFIED=true in .env.local and Vercel
- [ ] Run: npm test — all tests must pass
- [ ] Update REGULATION_META.jp_cap_next_update to next year

## Every January
- [ ] Check DJP for any PMK amendments to TER tables
       https://pajak.go.id
- [ ] Check for UU HPP amendments (Pasal 17 brackets)
       https://peraturan.bpk.go.id
- [ ] Check Perpres BPJS Kesehatan for rate changes
       https://peraturan.bpk.go.id

## Data Sources Reference
| Data | Source | Update frequency |
|------|--------|-----------------|
| TER tables (PPh 21) | PMK 168/2023 | When DJP amends |
| Pasal 17 brackets | UU HPP No. 7/2021 | When DPR amends |
| PTKP values | PMK 101/2016 | When DJP amends |
| JP wage cap | Perpres tahunan | Every March |
| BPJS Kesehatan rate | Perpres 64/2020 | When Perpres amends |
| JHT rate | PP 46/2015 | When PP amends |
| JKK/JKM rate | PP 44/2015 | When PP amends |

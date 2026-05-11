---
{
  "page_path": "/home/newadmin/swarm-bot/.wiki/logs/contracts-2026-04-23-cekwajar-sprint-master.md",
  "reason": "daily_fast_scan: verdict=REJECT, score=0.000 < 0.3",
  "score": 0.0,
  "quarantined_at": "2026-05-07T01:00:00.218422"
}
---

---
title: Contracts 2026 04 23 Cekwajar Sprint Master
type: concept
status: active
tags: [/]
created: 2026-05-03
updated: 2026-05-03
---

# Master Sprint Contract — cekwajar.id Improvement Sprint

## 47 Issues → 47 Contracts Across 9 Batches

| Batch | Priority | Contracts | Topic |
|-------|----------|-----------|-------|
| 1 | CRITICAL | #1-#2 | Test import fix + ESLint config |
| 2 | CRITICAL | #3-#5 | Dead code removal (useDarkMode, dead links, JP cap dead code) |
| 3 | MAJOR | #6-#8 | Touch target fix + SEO files (sitemap, robots) |
| 4 | MAJOR | #9-#12 | Dead hooks removal + PWA manifest |
| 5 | ACCESSIBILITY | #13-#18 | aria-live, aria-expanded, aria-current, contrast, aria-describedby, aria-errormessage |
| 6 | MOBILE | #19-#22 | Collapsible VerdictCard, responsive fonts, PTKP grid, overflow-x-auto |
| 7 | COPY/UX | #23-#28 | Emoji consistency, grammar fix, success message, FAQ, how-it-works, gue→saya |
| 8 | PSYCHOLOGY | #29-#33 | Testimonials, trust logos, live counter, viral mechanics, email capture |
| 9 | TECHNICAL | #34-#47 | Bundle analyzer, Core Web Vitals, OG image, next.config, rate limiting, test coverage, icon.svg, useReducedMotion, stale types, loading skeleton, bundle optimization, PTKP K/I verification, privacy email note |

## Contract Count
- Batch 1: 2 contracts (#1-#2)
- Batch 2: 3 contracts (#3-#5)
- Batch 3: 3 contracts (#6-#8)
- Batch 4: 4 contracts (#9-#12)
- Batch 5: 6 contracts (#13-#18)
- Batch 6: 4 contracts (#19-#22)
- Batch 7: 6 contracts (#23-#28)
- Batch 8: 5 contracts (#29-#33)
- Batch 9: 14 contracts (#34-#47)

**Total: 47 contracts**

---

## Critical Path (Dependencies)

```
Contract #1 (Test fix) ──────────────────┐
                                          ├─► Contract #47 (Final test)
Contract #39 (Test coverage) ────────────┤
Contract #9 (usePayment removal) ──────────┤
Contract #44 (Unused deps removal) ───────┘
```

**Execution:** All batches 1-9 can run IN PARALLEL. Only the final verification (Contract #47) must run last, after batches 1-9 complete.

---

## Batch File Locations

| Batch | File |
|-------|------|
| 1 | `.wiki/logs/contracts-2026-04-23-cekwajar-sprint-batch1.md` |
| 2 | `.wiki/logs/contracts-2026-04-23-cekwajar-sprint-batch2.md` |
| 3 | `.wiki/logs/contracts-2026-04-23-cekwajar-sprint-batch3.md` |
| 4 | `.wiki/logs/contracts-2026-04-23-cekwajar-sprint-batch4.md` |
| 5 | `.wiki/logs/contracts-2026-04-23-cekwajar-sprint-batch5.md` |
| 6 | `.wiki/logs/contracts-2026-04-23-cekwajar-sprint-batch6.md` |
| 7 | `.wiki/logs/contracts-2026-04-23-cekwajar-sprint-batch7.md` |
| 8 | `.wiki/logs/contracts-2026-04-23-cekwajar-sprint-batch8.md` |
| 9 | `.wiki/logs/contracts-2026-04-23-cekwajar-sprint-batch9.md` |

---

## Verification Commands

After ALL batches complete, run:

```bash
# 1. Tests pass
cd /home/newadmin/swarm-bot/cekwajar/cekwajar-20260413T050820Z-3-001/cekwajar/slip_cekwajar_id
npx jest --passWithNoTests

# 2. TypeScript passes
npx tsc --noEmit

# 3. ESLint passes
npx next lint

# 4. Build passes
npm run build
```

## Key Risks

| Risk | Mitigation |
|------|------------|
| Removing `@react-pdf/renderer` breaks something | Grep all imports first |
| Breaking test import changes test coverage | Keep all test cases, just redirect imports |
| aria-live conflicts with animations | Only announce on verdict change |
| Bundle size changes affect performance | Compare before/after bundle sizes |

## Anti-Fabrication Checklist
- [ ] All file paths verified to exist via ls or grep before writing contracts
- [ ] All function names verified by reading actual source files
- [ ] All import paths verified by reading actual files
- [ ] No assumed file existence — confirmed test file exists, components exist, etc.

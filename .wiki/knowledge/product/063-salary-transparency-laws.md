---
title: Salary Transparency Laws
type: concept
status: active
tags:
- /
- home
- newadmin
- swarm-bot
- product
created: '2026-04-14'
updated: '2026-04-14'
summary: Global trend toward salary transparency is accelerating. Colorado's law (effective
  Jan 2024) requires salary ranges on job postings. EU directive (June 2026 deadline)
  mandates pay information durin...
wikilinks: []
confidence: medium
source: research
---

# Salary Transparency Laws: Colorado, EU, UK Impact Analysis

## Why This Matters for cekwajar.id
Global trend toward salary transparency is accelerating. Colorado's law (effective Jan 2024) requires salary ranges on job postings. EU directive (June 2026 deadline) mandates pay information during recruitment. cekwajar.id can position as compliance tool for companies hiring internationally.

## Core Knowledge

### Colorado Equal Pay for Equal Work Act (Effective Jan 1, 2024)
**Key Requirements:**
- Salary ranges MUST be included in all job postings
- Pay history questions prohibited during recruitment
- No pay discrimination based on prior salary
- Applies to all employers with 1+ employees in Colorado

**Impact:**
- Immediately affected 30,000+ Colorado job postings
- Companies globally started adding ranges for remote positions
- Reduced negotiation asymmetry between employers/employees

### EU Pay Transparency Directive (2023/970)
**Timeline:**
- Adopted: June 2023
- Transposition deadline: June 2026
- Belgium already implemented (Jan 2025)

**Key Requirements:**
- "Work of equal value" principle
- Gender pay gap reporting for 100+ employee companies
- Pay information to applicants before interview
- Employees can request pay data
- Prohibition on asking salary history

**Implementation Status:**
| Country | Status | Key Features |
|---------|--------|--------------|
| Belgium | First (Jan 2025) | Accessibility for disabled, family leave pay comparison |
| Sweden | Draft | 25+ employees, salary range disclosure before interviews |
| Poland | Passed Sejm | Salary range in recruitment, ban on history questions |
| Ireland | Draft | 150+ employees (reducing to 50+ by 2025) |
| Netherlands | Draft | Closely follows directive text |
| Finland | Draft | €5,000-80,000 fines for non-compliance |

### UK Context
- Existing Equality Act 2010 requires equal pay for equal work
- No specific salary range disclosure law yet
- Growing pressure from EU alignment

## Exact Formulas / Numbers (if applicable)

```typescript
// Compliance checking for salary range posting
interface JobPosting {
  title: string;
  location: string;
  remote: boolean;
  minSalary?: number;
  maxSalary?: number;
  currency: string;
}

function checkTransparencyCompliance(
  posting: JobPosting,
  jurisdiction: string
): ComplianceResult {
  const rules = {
    'Colorado': {
      requiresRange: true,
      currency: 'USD',
      maxSpreadPct: 2.0, // Max 200% spread between min and max
      appliesIf: (p: JobPosting) => 
        p.location.includes('Colorado') || p.remote
    },
    'EU': {
      requiresRange: true,
      currency: 'EUR',
      maxSpreadPct: 1.0, // 100% max spread
      appliesIf: (p: JobPosting, country: string) => 
        country !== 'UK' // Post-Brexit
    }
  };
  
  const rule = rules[jurisdiction];
  if (!rule) return { compliant: true, warnings: [] };
  
  const errors = [];
  if (rule.appliesIf(posting, jurisdiction) && !posting.minSalary) {
    errors.push("Missing minimum salary");
  }
  if (rule.appliesIf(posting, jurisdiction) && !posting.maxSalary) {
    errors.push("Missing maximum salary");
  }
  if (posting.maxSalary / posting.minSalary > rule.maxSpreadPct) {
    errors.push(`Salary range exceeds ${rule.maxSpreadPct * 100}% maximum`);
  }
  
  return {
    compliant: errors.length === 0,
    errors
  };
}
```

## Edge Cases and Common Mistakes
- **Range too wide**: Posting $30k-$300k is suspicious; regulators may challenge
- **Outdated ranges**: Must update when pay changes
- **Cross-border confusion**: Remote workers trigger multiple state/country rules
- **Bonus exclusion**: Must clarify if range includes or excludes variable pay

## cekwajar.id Implementation Notes
- **File to update**: `swarms_bot/services/compliance_checker.py` (new file)
- **Function to modify/create**: `validate_job_posting_compliance()`, `generate_compliant_range()`
- **Data source to query**: `job_postings` table, jurisdiction rules config
- **Update frequency**: Real-time compliance checking
- **Legion action**: Can build compliance engine; needs Bashara for legal review

## Monetization Angle
1. **Compliance verification**: Rp 20-50k per job posting compliance check
2. **Employer dashboard**: SaaS for companies to manage multi-jurisdiction compliance
3. **Training**: Rp 500k-1M per HR team training on transparency laws
4. **Consultancy referrals**: Commission from legal service partners

## Sources and Cross-References
- EU implementation tracker: https://ogletree.com/eu-pay-transparency-directive-implementation-tracker/
- Colorado law details: https://www.forbes.com/sites/alonzomartinez/2023/12/15/pay-transparency-laws-in-colorado-and-hawaii-become-effective-january-1-2024/
- Colorado trend coverage: https://www.staffingindustry.com/news/global-daily-news/colorado-pay-transparency-law-starts-trend
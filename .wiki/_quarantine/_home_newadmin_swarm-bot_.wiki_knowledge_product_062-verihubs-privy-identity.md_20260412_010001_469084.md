---
{
  "page_path": "/home/newadmin/swarm-bot/.wiki/knowledge/product/062-verihubs-privy-identity.md",
  "reason": "daily_fast_scan: score=0.000 < 0.3",
  "score": 0.0,
  "quarantined_at": "2026-04-12T01:00:01.469108"
}
---

---
source_id: 062
title: "Verihubs & Privy Indonesian Identity Verification B2B SaaS"
source_type: COMPETITOR_ANALYSIS
authority: INDUSTRY
url: "https://verihubs.com/en/pricing/"
last_verified: "2026-04-11"
tags: [verihubs, privy, KYC, identity-verification, eKYC, SaaS, pricing, Indonesia, fintech, B2B]
cekwajar_impact: HIGH
legion_can_act: YES
---

# Verihubs & Privy Indonesian Identity Verification B2B SaaS

## Why This Matters for cekwajar.id
Verihubs and Privy are Indonesia's leading identity verification providers. cekwajar.id needs KYC for employer verification and could integrate these services for trusted salary data collection. Both offer enterprise pricing with custom packages.

## Core Knowledge

### Verihubs Profile
| Attribute | Value |
|-----------|-------|
| Founded | Indonesia-based |
| Funding | $2.8M seed (Insignia Ventures) |
| Y Combinator | Portfolio company |
| Certification | ISO 27001, FIME ISO/IEC 30107 |
| Clients | 400+ including BCA, Prudential, Tokocrypto |
| Products | ID Verification, Face Recognition, Deepfake Detection, Liveness, OCR |

### Verihubs Pricing Strategy
- **2-month free trial**: Full AI Verification Suite access
- **Post-paid billing**: Pay after usage with monitoring
- **Custom enterprise**: Volume-based discounts up to 30%
- **Contact sales**: No public pricing, custom quotes

### Verihubs Products
1. **AI Verification Suite**: Bundled package (30% discount available)
2. **ID Verification**: Government ID validation (KTP, SIM)
3. **Face Recognition**: 1:1 and 1:N matching
4. **Liveness Detection**: Anti-spoofing for biometric auth
5. **Deepfake Detection**: First in Indonesia
6. **Watchlist Screening**: AML/compliance checks
7. **SMS/WhatsApp OTP**: 2FA services

### Privy Profile
| Attribute | Value |
|-----------|-------|
| Focus | Digital identity and electronic signatures |
| Products | Personal Plan, Enterprise Plan, PDF Verification |
| Pricing | Rp 395,000/year (personal), enterprise custom |
| Compliance | Recognized by OJK |

## Exact Formulas / Numbers (if applicable)

```typescript
// Verihubs volume-based pricing (estimate)
interface VerificationVolume {
  monthlyVerifications: number;
  productMix: 'basic' | 'standard' | 'premium';
}

function estimateVerihubsCost(volume: VerificationVolume): number {
  const baseRate = {
    basic: 15000,   // ID verification only
    standard: 35000, // + face match + liveness
    premium: 55000   // + deepfake detection
  }[volume.productMix];
  
  // Volume discount tiers
  let discount = 0;
  if (volume.monthlyVerifications >= 10000) discount = 0.30;
  else if (volume.monthlyVerifications >= 5000) discount = 0.20;
  else if (volume.monthlyVerifications >= 1000) discount = 0.10;
  
  return volume.monthlyVerifications * baseRate * (1 - discount);
}

// Privy subscription pricing
const PRIVY_PRICING = {
  personal: {
    annual: 395000,  // Rp per year
    monthly: 54000   // Rp per month
  },
  enterprise: "Custom pricing (contact sales)"
};
```

## Edge Cases and Common Mistakes
- **False acceptance rate**: Must balance security vs user experience
- **Government ID variations**: KTP, SIM, passport all need validation
- **Network issues**: Mobile verification requires stable connection
- **Privacy regulations**: PDP (Personal Data Protection) compliance required

## cekwajar.id Implementation Notes
- **File to update**: `swarms_bot/services/employer_verification.py` (new file)
- **Function to modify/create**: `verify_employer_identity()`, `authenticate_salary_submitter()`
- **Data source to query**: External Verihubs/Privy APIs
- **Update frequency**: Real-time on verification requests
- **Legion action**: Can build integration; needs Bashara for API contracts

## Monetization Angle
1. **Verification service markup**: Add Rp 5-15k per verification on top of provider cost
2. **Employer verification packages**: Rp 100-500k per company verification
3. **Trust badge subscription**: Verified employer status for Rp 50k/month
4. **Data services**: Anonymized verification statistics for market research

## Sources and Cross-References
- Verihubs pricing: https://verihubs.com/en/pricing/
- Privy pricing: https://privy.id/compare-plan
- TechCrunch funding: https://techcrunch.com/2021/09/27/indonesian-id-and-data-verification-startup-verihubs-gets-2-8m-led-by-insignia-venture-partners/
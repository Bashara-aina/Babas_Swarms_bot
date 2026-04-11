---
source_id: 074
title: "UU PDP Indonesia 27 2022 Personal Data Protection Compliance"
source_type: REGULATION
authority: OFFICIAL_GOV
url: "https://peraturan.bpk.go.id/Details/219490"
last_verified: "2026-04-11"
tags: [uu-pdp, pdp-law, personal-data, indonesia, privacy, compliance, bi-data]
cekwajar_impact: CRITICAL
legion_can_act: YES
---

# UU PDP Indonesia 27 2022 Personal Data Protection Compliance

## Why This Matters for cekwajar.id
UU PDP (Undang-Undang Pelindungan Data Pribadi) is Indonesia's first comprehensive data protection law. **CRITICAL COMPLIANCE REQUIREMENT**: All companies processing Indonesian personal data must comply by October 2024. Non-compliance risks fines of IDR 4-6 billion and 4-6 years imprisonment.

## Core Knowledge

### Law Overview
- **Law Number**: 27 of 2022
- **Effective Date**: October 17, 2022 (2-year compliance transition)
- **Compliance Deadline**: October 16, 2024
- **Alignment**: Modeled after EU GDPR

### Personal Data Categories

| Category | Examples | Protection Level |
|----------|----------|-----------------|
| **General** | Name, gender, nationality, religion, marital status | Standard |
| **Specific (Sensitive)** | Health, biometric, genetic, criminal records, children's data, financial data | Enhanced |

### Data Subject Rights (11 Rights)
1. **Right to be Informed**: Know data collector identity, purpose, usage
2. **Right of Access**: Receive copies of personal data
3. **Right to Rectification**: Update/correct inaccuracies
4. **Right to Erasure**: Delete when no longer needed or consent withdrawn
5. **Right to Restrict Processing**: Limit how data is used
6. **Right to Object**: Object to processing for direct marketing, automated decisions
7. **Right to Data Portability**: Transfer data between providers
8. **Right to Withdraw Consent**: At any time
9. **Right to Non-Discrimination**: Exercise rights without penalty
10. **Right to File Lawsuit & Receive Compensation**: Legal remedies
11. **Right to Complain**: Lodge with data protection authority

### Controller vs Processor Obligations

| Obligation | Controller | Processor |
|------------|-----------|----------|
| Process lawfully, fairly, transparently | ✓ | - |
| Purpose limitation | ✓ | - |
| Ensure accuracy | ✓ | ✓ |
| Update/correct errors | ✓ | - |
| Record processing activities | ✓ | ✓ |
| Provide data subject access | ✓ | - |
| Risk impact assessment (high risk) | ✓ | - |
| Ensure data security | ✓ | ✓ |
| Maintain confidentiality | ✓ | ✓ |
| Delete on legal conditions | ✓ | - |
| Notify breaches (72 hours) | ✓ | ✓ |

### Breach Notification
- **Timeline**: 72 hours to DPA and affected data subjects
- **Content**: Nature of breach, circumstances, mitigation steps
- **Public announcement**: Required if affects public services

### Sanctions

| Type | Penalty |
|------|---------|
| **Administrative** | Written warning, suspension, forced deletion, fines |
| **Criminal** | IDR 4-6 billion fine AND 4-6 years imprisonment |
| **Corporate** | Fine multiplied up to 10× + profit seizure |

### Cross-Border Data Transfer Rules
1. **Adequacy**: Recipient country must have equivalent protection
2. **Safeguards**: Standard contractual clauses if not adequate
3. **Consent**: Explicit consent if neither adequacy nor safeguards

## Exact Formulas / Numbers (if applicable)
```typescript
// PDP Compliance Checklist
interface PDPComplianceRequirements {
  dataInventory: boolean;        // Complete data mapping
  consentMechanism: boolean;      // Valid consent collection
  rightsImplementation: boolean; // All 11 rights supported
  breachNotification: boolean;    // 72-hour notification system
  dpoAppointment: boolean;       // If high-risk processing
  crossBorderSafeguards: boolean; // For international transfers
  privacyByDesign: boolean;      // Data protection built-in
}

// Calculate compliance score
function calculateComplianceScore(requirements: PDPComplianceRequirements): number {
  const checks = Object.values(requirements);
  const passed = checks.filter(Boolean).length;
  return (passed / checks.length) * 100;
}

// PDP Risk Assessment
interface DataProcessingRisk {
  dataVolume: number;
  sensitivityLevel: 'general' | 'specific';
  automatedDecisions: boolean;
  crossBorderTransfer: boolean;
  riskScore: number;
}

function assessPDPRisk(processing: DataProcessingRisk): 'low' | 'medium' | 'high' {
  let score = 0;
  
  // Volume factor
  score += processing.dataVolume > 10000 ? 2 : processing.dataVolume > 1000 ? 1 : 0;
  
  // Sensitivity factor
  score += processing.sensitivityLevel === 'specific' ? 3 : 1;
  
  // Automated decisions
  score += processing.automatedDecisions ? 2 : 0;
  
  // Cross-border
  score += processing.crossBorderTransfer ? 2 : 0;
  
  if (score >= 7) return 'high';
  if (score >= 4) return 'medium';
  return 'low';
}
```

## Edge Cases and Common Mistakes
1. **Missing 72-hour notification**: Breach must be reported within 72 hours
2. **No DPO appointed**: Required for high-risk processing or systematic monitoring
3. **Cross-border transfer without safeguards**: Must have adequacy, SCCs, or consent
4. **Ignoring children's data**: Special protections required
5. **No consent mechanism**: All processing requires legal basis

## cekwajar.id Implementation Notes
- **File to update**: `compliance/pdp_checklist.py`, `security/data_protection.py`
- **Function to modify/create**: `check_consent()`, `implement_right()`, `breach_notification()`
- **Data source to query**: Supabase `user_consents`, `personal_data`, `audit_logs`
- **Update frequency**: Real-time consent tracking, quarterly compliance audit
- **Legion action**: Can autonomously track consent, generate compliance reports, alert on breaches

## Monetization Angle
- PDP compliance automation for SaaS ($200-1000/month)
- Consent management platform
- Data protection impact assessments
- DPO-as-a-service (outsourced Data Protection Officer)
- Employee PDP training certification

## Sources and Cross-References
- Official URL: https://peraturan.bpk.go.id/Details/219490
- ASEAN Briefing guide: https://www.aseanbriefing.com/doing-business-guide/indonesia/company-establishment/personal-data-protection-law
- BDO Indonesia introduction: https://www.bdo.co.id/en-gb/insights/introduction-of-the-official-personal-data-protection-act-(uu-pdp)
- Last regulation update: October 2022 (enactment), October 2024 (compliance deadline)
- Last verified: 2026-04-11

# Payroll Indonesia (PPh 21 + BPJS + THR Audit)

Use this protocol for salary slip validation and payroll calculations in Indonesia.

## 1) Core inputs to collect first

- PTKP status: `TK/0`, `TK/1`, `TK/2`, `TK/3`, `K/0`, `K/1`, `K/2`, `K/3`
- Gross monthly components: base salary, fixed allowance, variable allowance, overtime, bonus
- Deductions: BPJS employee portions, loans, penalties
- Tax method: TER 2024 or progressive annualized
- THR policy + employment tenure at payout date

Do not calculate before these are explicit.

## 2) PTKP reference (commonly used)

| Status | PTKP Tahunan |
|---|---:|
| TK/0 | 54,000,000 |
| TK/1 | 58,500,000 |
| TK/2 | 63,000,000 |
| TK/3 | 67,500,000 |
| K/0 | 58,500,000 |
| K/1 | 63,000,000 |
| K/2 | 67,500,000 |
| K/3 | 72,000,000 |

If company policy/regulation update differs, flag and request legal verification.

## 3) BPJS contribution checks

### BPJS Kesehatan
- Employer: 4%
- Employee: 1%
- Apply payroll cap rules per current regulation.

### BPJS Ketenagakerjaan (common components)
- JKK: employer only (rate by risk class)
- JKM: employer only
- JHT: employer + employee
- JP: employer + employee (with wage ceiling)

Audit rule: separate employer vs employee portions; employee deduction must match slip.

## 4) PPh 21 method protocol

### TER 2024 monthly method
1. Determine gross taxable monthly basis per policy.
2. Map to TER rate bracket.
3. Apply TER to taxable basis.
4. Reconcile annually if required.

### Progressive annualized method
1. Annualize taxable income.
2. Subtract PTKP.
3. Apply progressive brackets.
4. De-annualize to monthly withholding schedule.

If method unclear, do not assume. Mark as compliance risk.

## 5) Gross vs Nett method

- Gross: employee bears tax withholding.
- Nett: company bears tax (tax allowance/gross-up logic may apply).
- Gross-up: add allowance so effective net meets target.

Audit check: slip presentation must align with policy and employment contract.

## 6) THR calculation rules (high-level)

- Employee ≥12 months: generally 1 month wage equivalent.
- Employee <12 months: prorated by service period.
- Use wage component basis defined by regulation/company policy.

Audit checks:
- tenure start date correctness
- wage basis consistency
- proration formula consistency

## 7) Wajar Slip-specific audit patterns

1. **Rounding drift**
   - monthly rounding repeated causes annual mismatch.
2. **Wrong PTKP status**
   - marital/dependent status not updated.
3. **Missing allowance inclusion**
   - taxable component omitted in gross base.
4. **Incorrect BPJS cap handling**
   - contribution continues above ceiling incorrectly.
5. **TER table mismatch**
   - outdated mapping used for current payroll period.

## 8) Validation checklist per payslip

- [ ] PTKP status matches HR master data
- [ ] Gross components sum correctly
- [ ] BPJS employee deductions correct by rate/cap
- [ ] PPh 21 method documented and consistent
- [ ] Net pay arithmetic exact
- [ ] THR (if month applicable) follows tenure rule

## 9) Output format for audit response

- Summary verdict: pass / warning / fail
- Table of findings: item, expected, actual, impact
- Compliance risk level: low/medium/high
- Recommended correction actions
- If legal uncertainty: explicitly request tax/legal confirmation

## 10) Safety note

Tax/payroll rules can change. If period/regulation ambiguity exists, state assumptions and require final validation against latest DJP/BPJS guidance.

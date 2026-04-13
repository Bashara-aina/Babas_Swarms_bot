---
title: "Track B — rumahlabuh Booking UX Research"
type: research
status: active
tags: [research, rumahlabuh, booking-ux, trust, payment-flows, indonesia, mobile-first]
created: 2026-04-13
updated: 2026-04-13
summary: "Applying Domain 12 (Hayek knowledge problem, Smith invisible hand) and Domain 15 (Gibbon institutional memory) to rumahlabuh's booking UX. The key insight: in a trust-deficit market (Indonesian kost rental), the platform's UX must solve the information asymmetry problem before the transaction can proceed. Midtrans Snap is not just a payment tool — it is a trust signal."
wikilinks:
  - [[projects/rumahlabuh-com]]
  - [[projects/cekwajar-id]]
confidence: high
source: synthesis
project: rumahlabuh
---

# Track B — rumahlabuh Booking UX Research

## Research Question

**How do we design a booking UX that converts curious browsers into paying tenants, given Indonesian kost market conditions (trust deficit, cash-preference, mobile-first) and the specific business rules of rumahlabuh?**

This article synthesizes wisdom from Domain 12 (Hayek, Smith), Domain 15 (Gibbon), and Domain 18 (Communication) to answer this question.

---

## 1. The Core Problem: Hayek's Knowledge Problem in Kost Rental

### 1.1 The Information Asymmetry

Hayek's knowledge problem (Domain 12) applies directly: the relevant information for a kost rental decision is distributed across multiple parties and much of it is tacit:

| Knowledge Type | Who Has It | Available on Platform? |
|---------------|------------|----------------------|
| Room condition (real photos) | Owner/manager | Partially |
| Neighbourhood safety | Tenant (word-of-mouth) | No |
| Payment reliability of tenant | Owner | No |
| Manager responsiveness | Previous tenants | No |
| Actual waitlist length | Platform | Partially |
| Late fee enforcement consistency | Owner/manager | No |

**The platform cannot solve this fully — but it can reduce the asymmetry enough to make the transaction feasible.**

### 1.2 Trust as Channel Capacity

In Domain 12, Shannon's channel capacity framework applies: trust is a communication channel with finite bandwidth. The more trust signals you transmit within the user's context window of attention, the more likely they are to convert. Each element of the UI is a trust signal — or a trust deficit.

**Indonesian market specifics**:
- Cash preference: many tenants are paid in cash daily/weekly, not via bank transfer
- Bilingual friction: mixed Indonesian/English UI creates hesitation
- WhatsApp expectation: Indonesian users expect to be able to message someone directly
- Mobile-first: >70% of traffic is mobile, but most kost platforms have desktop-first UX

### 1.3 LEGION RULE (Hayek)

> "For rumahlabuh's booking flow, ask: what information does the tenant need to make a decision, and does the current flow transmit that information efficiently? The test is not 'does the page look good' — it is 'does the tenant know exactly what they are agreeing to and who to call if it goes wrong?'"

---

## 2. Payment Flow Design: Smith's Invisible Hand + Keynes Animal Spirits

### 2.1 Midtrans as Trust Infrastructure

Smith's invisible hand (Domain 12) works when: property rights are clear, competition exists, and contract enforcement is present. Midtrans Snap provides the contract enforcement signal — when the platform shows "Payment secured via Midtrans," it signals that the transaction has third-party enforcement. This transforms the platform from "random website" to "regulated intermediary."

**The invisible hand requires three things — rumahlabuh has two (property rights over the listing, competition from other platforms), but the third (contract enforcement) is weak. Midtrans fills this gap.**

### 2.2 Variable Confirmation to Reduce Anxiety

Keynes's animal spirits (Domain 12) explain why booking abandonment happens: tenants are not purely rational calculators of cost/benefit. They are anxious about the unknown. The anxiety is disproportionate to the actual risk — but it is real and it kills conversions.

**Design implication**: the confirmation screen after payment should be maximally reassuring:
- Clear "what happens next" steps in Indonesian
- WhatsApp contact number prominently displayed
- Expected timeline: "Manager will contact you within 2 hours"
- Reference code that can be cited in WhatsApp message

### 2.3 LEGION RULE (Smith + Keynes)

> "For payment confirmation UX, apply Smith's invisible hand test: does the UI make it clear that (a) the tenant's money is protected, (b) the owner's obligation is enforced, and (c) a third party (Midtrans) holds the transaction? For Keynes's animal spirits: the confirmation screen must address the anxiety of 'did I just get scammed' — not with words but with structure. Every element should say 'this is real.'"

---

## 3. Move-Out Notice: Gibbon's Institutional Memory Problem

### 3.1 The Deposit Memory Failure

Gibbon's institutional memory problem (Domain 15) is directly relevant: the rule "≥14 days notice = full refund" is a contractual obligation. But the tenant's memory of this obligation will be reconstructed at move-out time — not at signing time. Ebbinghaus's forgetting curve (Domain 13) says: without reinforcement, the 14-day rule will be forgotten.

**The platform's job is to prevent this memory failure from causing real harm.**

### 3.2 Intervention Points

| Time | Intervention | Method |
|------|-------------|--------|
| Booking confirmation | Show rule with icon + "Save this" | Push notification |
| 21 days before potential move-out | "Your move-out notice deadline is in X days" | WhatsApp message |
| 14 days before | "Last day to give notice for full deposit refund" | WhatsApp message |
| 7 days before | "You have not given notice. Your deposit may be forfeited." | WhatsApp + in-app |

**This is spaced repetition applied to contract compliance.** The intervention cost is near zero (automated WhatsApp messages). The benefit is high (prevents real harm to tenants and reputation harm to platform).

### 3.3 LEGION RULE (Gibbon + Ebbinghaus)

> "For deposit compliance, apply Gibbon's institutional memory principle: write down the rule at booking time and reinforce it at intervals calculated from Ebbinghaus's forgetting curve. The 14-day rule is not just a contract clause — it is an instruction that must survive 6-12 months of tenancy. Memory consolidation requires repetition at the right intervals."

---

## 4. Booking Extension: Communication & Clarity

### 4.1 Strunk's Omit Needless Words Applied

The extension workflow (`/perpanjang`) is the highest-stakes interaction — it involves money and is triggered when the tenant is already in a financial stress situation (they're late or extending). Clear communication is not aesthetic — it is ethical.

**Current flow issue**: the late fee explanation ("daysLate > 3: Rp250K") is presented numerically but the emotional weight ("this is a Rp250,000 penalty, roughly 2-3 days of wages for an Indonesian worker") is absent. The number is abstract; the comparison makes it concrete.

### 4.2 Orwell's Passive Construction Check

The current UI says "Kontrak fleksibel: anda dikenakan biaya keterlambatan." The passive construction ("anda dikenakan") obscures who is doing the charging. Orwell's rule: use the active voice. Better: "Aturan 3: jika pembayaran telat 4-15 hari, anda harus bayar Rp250.000 biaya keterlambatan."

### 4.3 Naval's Communication Mode Match

Extension workflow is persuasion + explanation combined. The tenant needs to:
1. **Understand** the rule (explanation mode)
2. **Feel** it is fair and worth paying (persuasion mode)

Most UIs fail because they use explanation mode for both. Naval's framework (Domain 18): start with why the rule exists ("biaya ini melindungi pemilik dari kerugian") before explaining what it is. The why creates buy-in; the what is just the details.

### 4.4 LEGION RULE (Strunk + Orwell + Naval)

> "For extension UX copy, apply three tests: (1) Strunk: every word must carry new information — if it can be cut without losing meaning, cut it; (2) Orwell: no passive constructions, no euphemisms, no bureaucratic language; (3) Naval: before explaining what the rule is, explain why it exists. The order is: why → what → how much → what to do next."

---

## 5. Mobile-First Design: Dalio's Economic Machine

### 5.1 Indonesian Mobile Context

Dalio's economic machine (Domain 15) for Indonesia's kost market: the credit cycle affects tenant cash flow directly. Indonesian workers on daily/weekly wages (ojek drivers, market vendors, factory workers) have highly variable income timing. A monthly billing cycle that assumes regular monthly income is structurally misaligned with their actual economic reality.

**UX implication**: the platform should offer weekly/biweekly payment options aligned with actual income cycles, not just monthly. This is not generosity — it is market design that matches the economic reality.

### 5.2 Trust Signal Hierarchy for Mobile

On mobile, screen space is limited. The trust signals must be prioritized:

| Priority | Signal | Location |
|----------|--------|----------|
| 1 | Midtrans logo + "Payment secured" | Immediately below price |
| 2 | WhatsApp contact (human) | Top of every page |
| 3 | Photo gallery (real, not stock) | Hero section |
| 4 | Rule summary (deposit, late fee) | Below room details |

### 5.3 LEGION RULE (Dalio)

> "For mobile-first design, apply Dalio's economic machine test: does the payment schedule match the tenant's actual income cycle? If the platform assumes monthly payment but the tenant is paid weekly, the platform will fail the tenant. Design for how people actually earn, not how institutions assume they earn."

---

## 6. Conversion Optimization: Amabile's Intrinsic Motivation

### 6.1 Extrinsic vs Intrinsic in Booking

Amabile's intrinsic motivation research (Domain 17): extrinsic rewards (discounts, urgency timers) can undermine the intrinsic appeal of a good product. The urgency timer ("only 1 room left at this price") may produce a click but not a conversion — the anxiety it generates may cause the user to leave rather than buy.

**The intrinsic appeal of rumahlabuh**: "This is a real place with a real manager who will answer your WhatsApp." The platform should lean into this, not obscure it with artificial urgency.

### 6.2 LEGION RULE (Amabile)

> "For conversion optimization, use Amabile's intrinsic motivation test: does this UI element appeal to the tenant's genuine interest in a good place to live, or does it try to manipulate them into a transaction? Urgency timers, countdown clocks, and discount pressure are extrinsic motivators that undermine the platform's genuine advantage (real photos, verified reviews, manager responsiveness)."

---

## 7. Summary: Track B UX Principles for rumahlabuh

| Principle | Source | Application |
|-----------|--------|-------------|
| Trust as channel capacity | Hayek (D12) | Every UI element either transmits or destroys trust |
| Midtrans as invisible hand signal | Smith (D12) | Show payment protection prominently |
| Address booking anxiety | Keynes (D12) | Confirmation screen must say "this is real" |
| Spaced repetition for deposit rules | Ebbinghaus (D13) | Automated reminders at 21d, 14d, 7d before move-out |
| Active voice for penalties | Orwell (D18) | "You owe Rp250K" not "Biaya dikenakan" |
| Why before what in copy | Naval (D18) | Explain why the rule exists before stating the rule |
| Match payment to income cycle | Dalio (D15) | Weekly/biweekly payment options |
| Intrinsic motivation in conversion | Amabile (D17) | Real photos + WhatsApp contact > urgency timers |

---

## 8. Current Status

Track B synthesis complete. These principles should be reviewed against the current rumahlabuh UX implementation at `rumahlabuh.com` to identify specific improvement opportunities. Highest priority: (1) move-out notice reminders, (2) extension workflow copy rewrite, (3) payment schedule options (weekly/biweekly).

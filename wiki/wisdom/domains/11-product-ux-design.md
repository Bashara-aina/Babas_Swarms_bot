---
title: Domain 11 — Product & UX Design
type: concept
status: active
tags: [wisdom, product, UX, design, JTBD, research]
created: 2026-04-13
updated: 2026-04-13
summary: "Great product design starts with understanding the job the user is trying to accomplish, not the feature they request. Teresa Torres' continuous discovery framework replaces periodic user research with ongoing, small-batch experimentation. Don Norman's affordances/signifiers model explains why some interfaces feel intuitive while others confuse — the key is making possible actions perceivable."
wikilinks:
  - [[projects/rumahlabuh]]
  - [[projects/cekwajar-id]]
confidence: high
source: synthesized
project: general
---

# Domain 11 — Product & UX Design

The gap between what users say they want and what they actually need is the central problem of product design. Good designers close this gap through continuous, small-batch discovery — not big research initiatives that produce reports nobody reads.

---

## Christensen — Jobs to Be Done

**Type**: Framework | **Year**: 2016 | **Source**: Clayton Christensen et al., *Competing Against Luck*

**Core Insight**: Customers don't hire products — they hire solutions to jobs in their lives. The job has functional dimensions (what gets done), emotional dimensions (how they want to feel), and social dimensions (how they want to be seen). A product that owns the job becomes difficult to displace; a product that owns a feature is always one feature release away from being overtaken.

**Why it matters**: Feature-driven roadmaps chase what competitors do. Job-driven roadmaps create products people depend on because they reliably accomplish the job better than alternatives.

**LEGION RULE**: "Before building or evaluating any feature, state the job it serves: 'I hire [this feature] to [accomplish X] so I can [achieve Y outcome].' If you cannot state this clearly, the feature serves an internal roadmap need, not a user job."

**Applied to Bashara**: [[projects/rumahlabuh]] owners don't hire "booking management" — they hire it to "eliminate the anxiety of double-booking while maintaining the feeling that each guest receives a personal welcome." The first is functional, the second emotional.

**Example**: IKEA doesn't sell furniture — it sells "furnishing a new home quickly and affordably, with the experience of being smart with money." The flat-pack assembly is not a bug — it is part of the job. People who want beautiful homes without spending a lot hire IKEA and leave with a story to tell.

**Wikilinks**: [[projects/rumahlabuh]] | [[projects/cekwajar-id]]

---

## Torres — Continuous Discovery

**Type**: Framework | **Year**: 2021 | **Source**: Teresa Torres, *Continuous Discovery Habits*

**Core Insight**: Product discovery should happen weekly — small-batch interviews with 5 customers per week, looking for patterns across what customers are trying to do, what they're doing differently, and where friction exists. Not quarterly research reports, but continuous thread through every product decision.

**Why it matters**: The "big research then build" model produces artifacts that are obsolete before they're published. Continuous discovery keeps the product team's mental model of the customer synchronized with reality, not with a snapshot from 6 months ago.

**LEGION RULE**: "For any product decision, ask: what did we learn from customers this week that informs this decision? If the answer is 'nothing recent,' the decision is being made from stale information. The discipline is weekly customer contact, not annual research sprints."

**Applied to Bashara**: [[projects/cekwajar-id]] could run a monthly 5-owner interview cycle for rumahlabuh — 5 owners, 30 minutes each, asking: what broke this month? What did you try to do that the system made hard? The accumulated answers over 3 months form a better product roadmap than any internal brainstorming.

**Example**: A B2B SaaS company shifted from annual customer advisory boards to weekly 15-minute calls with rotating customers. Within 6 months they had identified 3 features that customers were secretly building workarounds for, and built those features. Churn rate dropped 40% in the following year.

**Wikilinks**: [[projects/rumahlabuh]] | [[projects/cekwajar-id]]

---

## Norman — Affordances & Signifiers

**Type**: Framework | **Year**: 1988 | **Source**: Don Norman, *The Design of Everyday Things*

**Core Insight**: An affordance is what an object allows you to do with it — a door affords pushing. A signifier is what communicates where the door should be pushed. When affordances and signifiers don't match (a door that looks like it should be pulled), users fail. Good design makes the correct action obvious.

**Why it matters**: Interface confusion is not a user failure — it is a design failure. The designer's job is to make every possible action's correct execution perceivable, not to explain it with instructions.

**LEGION RULE**: "When evaluating any interface (UI, CLI, API), ask: what actions are possible here, and are those actions clearly communicated by the interface itself? If a user must read documentation to know how to interact, the interface has failed the signifier test."

**Applied to Bashara**: [[projects/rumahlabuh]]'s booking calendar should make it obvious which dates are available (affordance: clickable selection) vs. blocked (signifier: visibly different color/state). If owners regularly book the wrong dates, the signifier design is broken — not the owner's error.

**Example**: A glass door with a metal frame — if the metal bar is horizontal, most people push. If the metal bar is vertical, most people pull. The same physical door, different expected action based on signifier alone. The affordance (door can open) hasn't changed — only the signifier has.

**Wikilinks**: [[projects/rumahlabuh]]

---

## Nielsen — Heuristics

**Type**: Framework | **Year**: 1994 | **Source**: Jakob Nielsen, *Usability Engineering* (10 usability heuristics)

**Core Insight**: 10 design heuristics capture the major failure modes of user interfaces: visibility of system status, match between system and real world, user control and freedom, consistency and standards, error prevention, recognition not recall, flexibility and efficiency of use, aesthetic and minimalist design, help users recover from errors, help and documentation.

**Why it matters**: These 10 heuristics are not opinions — they are empirically-derived failure modes. An interface that violates any of them will produce predictable user errors.

**LEGION RULE**: "For any Legion interface (Telegram responses, CLI output, wiki format), evaluate against Nielsen's 10 heuristics. If the response format is inconsistent with prior responses (heuristic: consistency), or if the user must remember information from previous steps (heuristic: recognition not recall), the interface is degrading."

**Applied to Bashara**: [[projects/rumahlabuh]]'s booking confirmation email should match the format of the booking page — same fields, same order, same terminology. When the email says "check-out date" and the page says "departure date," this violates consistency.

**Wikilinks**: [[projects/rumahlabuh]]

---

## Current Status

Domain 11 initial synthesis complete. Next steps:
- Add Scott Young's "deliberate practice" for skill acquisition
- Add Cagan's "how top product managers work" framework
- Add Krug's "don't make me think" principle for reducing cognitive load

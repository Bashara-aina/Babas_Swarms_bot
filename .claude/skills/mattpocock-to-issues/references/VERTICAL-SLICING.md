# Vertical Slicing Guide

How to break plans into independently-grabbable issues.

## What is a Vertical Slice?

A **vertical slice** is a thin end-to-end cut through ALL layers of the system. Each slice delivers a complete, demoable path.

```
Horizontal (BAD):
  Issue 1: Backend API endpoints
  Issue 2: Database schema
  Issue 3: Frontend components
  Issue 4: Tests

Vertical (GOOD):
  Slice 1: Basic checkout flow (API + DB + UI + tests)
  Slice 2: Add payment step (API + DB + UI + tests)
  Slice 3: Add shipping step (API + DB + UI + tests)
```

## Rules

1. **Each slice cuts through all layers** — API, database, UI, tests
2. **Completed slice is demoable** — user can see the feature working
3. **Prefer many thin slices** over few thick ones
4. **Minimize dependencies** between slices
5. **Slice along user workflows**, not technical layers

## Slice Types

### AFK (Autonomous)
Can be implemented without human interaction. Agent can pick up, implement, test, and merge.

### HITL (Human-in-the-Loop)
Requires human judgment or interaction:
- Architectural decisions
- Design reviews
- External integrations (payment gateway, etc.)
- Manual testing scenarios

## How to Slice

### Step 1: Identify User Workflows

```
Checkout workflow:
  1. View cart
  2. Enter shipping
  3. Enter payment
  4. Confirm order
  5. See confirmation
```

### Step 2: Create Thin Vertical Slices

Each slice = one workflow step, fully implemented:

```
Slice 1: View cart
  - API: GET /cart
  - DB: cart table query
  - UI: Cart page
  - Tests: Integration test

Slice 2: Enter shipping
  - API: POST /checkout/shipping
  - DB: shipping_addresses table
  - UI: Shipping form
  - Tests: Integration test

Slice 3: Enter payment
  - API: POST /checkout/payment
  - DB: payment integration
  - UI: Payment form
  - Tests: Integration test
...
```

### Step 3: Identify Blockers

```
Slice 1 (View cart): None — can start
Slice 2 (Shipping): None — can start
Slice 3 (Payment): None — can start
Slice 4 (Confirmation email): Blocked by Slice 3 (needs payment to work)
```

## Slicing Heuristics

| If feature is... | Slice by... |
|------------------|-------------|
| Multi-step workflow | Each step |
| CRUD operations | Each entity type |
| Search/filter | Basic search, then advanced filters |
| User roles | Admin flow, user flow |
| Integrations | Core feature, then each integration |

## Anti-Patterns

### Horizontal Slicing (Avoid)
```
Issue: "Implement API layer"
Issue: "Implement database layer"
Issue: "Implement UI layer"
```
**Problem:** Can't demo anything until all layers done.

### Big Bang (Avoid)
```
Issue: "Implement entire feature"
```
**Problem:** No early feedback, hard to review, long review cycle.

### Speculative Slicing (Avoid)
```
Issue: "Implement for future scaling needs"
```
**Problem:** YAGNI, complexity before needed.

## Dependency Management

When Slice B depends on Slice A:
1. Complete Slice A first (or parallel if independent)
2. Publish Slice A, get its issue number
3. Reference A's number in B's "Blocked by" field
4. Publish Slice B

## Testing Per Slice

Each slice needs:
- Integration test covering the full slice
- Tests at module boundaries (not implementation details)
- Tests should pass after slice is complete
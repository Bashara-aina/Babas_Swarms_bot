# Logic/State Machine Prototyping

## When to Use This Branch

Use when the question is:
- "Does this logic feel right?"
- "Is this state model correct?"
- "Can I reason about this edge case?"
- "What happens in X state?"

## Approach

Build a **tiny interactive terminal app** that exercises the state machine through hard-to-reason-about cases.

## Example

```typescript
// prototype/logic-prototype.ts
// PURPOSE: Validate state transitions for OrderProcessor

type OrderState = 'pending' | 'paid' | 'shipped' | 'delivered' | 'cancelled';

interface Order {
  id: string;
  state: OrderState;
  items: string[];
}

const transitions: Record<OrderState, OrderState[]> = {
  pending: ['paid', 'cancelled'],
  paid: ['shipped', 'cancelled'],
  shipped: ['delivered'],
  delivered: [],
  cancelled: []
};

function canTransition(from: OrderState, to: OrderState): boolean {
  return transitions[from].includes(to);
}

// Interactive tester
const testCases = [
  { from: 'pending', to: 'paid', expected: true },
  { from: 'pending', to: 'delivered', expected: false },
  { from: 'shipped', to: 'cancelled', expected: false },
];

console.log('State Transition Matrix:');
for (const [from, toStates] of Object.entries(transitions)) {
  console.log(`${from} -> [${toStates.join(', ')}]`);
}

console.log('\nTest Cases:');
for (const tc of testCases) {
  const result = canTransition(tc.from, tc.to);
  const pass = result === tc.expected;
  console.log(`${pass ? '✓' : '✗'} ${tc.from} -> ${tc.to}: ${result} (expected ${tc.expected})`);
}
```

## Running

```bash
npx ts-node prototype/logic-prototype.ts
```

## Output Format

After every action, print the **full state** so the user can see what changed:

```
Current State: { id: 'order-1', state: 'paid', items: ['item-1'] }
Transition: paid -> shipped
New State: { id: 'order-1', state: 'shipped', items: ['item-1'] }
```
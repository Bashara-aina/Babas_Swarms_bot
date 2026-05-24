# Shoehorn Migration Patterns

Detailed reference for migrating from `as` type assertions to `@total-typescript/shoehorn`.

## Installation

```bash
npm i @total-typescript/shoehorn
# or
pnpm add @total-typescript/shoehorn
# or
yarn add @total-typescript/shoehorn
```

## Function Reference

| Function | Use When |
|----------|----------|
| `fromPartial()` | Passing partial data that still type-checks |
| `fromAny()` | Passing intentionally wrong data (autocomplete still works) |
| `fromExact()` | Forcing full object (swap with fromPartial later) |

## fromPartial()

For when you only care about a few properties of a large object.

```typescript
import { fromPartial } from "@total-typescript/shoehorn";

// Before: must specify ALL properties
const req = {
  body: { id: "123" },
  headers: {},
  cookies: {},
  params: {},
  query: {},
  // ... 20 more properties
};

// After: only specify what you need
const req = fromPartial({
  body: { id: "123" },
});
```

## fromAny()

For when you need to pass data that doesn't match the type (intentionally wrong).

```typescript
import { fromAny } from "@total-typescript/shoehorn";

// Before: ugly double-cast
const req = { body: { id: 123 } } as unknown as Request;

// After: cleaner
const req = fromAny({
  body: { id: 123 }, // wrong type, but works
});
```

## Migration Workflow

### Step 1: Find All `as` Assertions

```bash
# Find TypeScript test files with 'as' assertions
grep -r " as [A-Z]" --include="*.test.ts" --include="*.spec.ts" src/

# Find specific patterns
grep -r "as unknown as" --include="*.test.ts" src/
```

### Step 2: Replace Pattern by Pattern

**Pattern 1: Simple `as Type`**
```typescript
// Before
getUser({ id: "123" } as UserRequest)

// After
import { fromPartial } from "@total-typescript/shoehorn";
getUser(fromPartial({ id: "123" }))
```

**Pattern 2: Double `as unknown as Type`**
```typescript
// Before
getUser({ id: 123 } as unknown as Request)

// After
import { fromAny } from "@total-typescript/shoehorn";
getUser(fromAny({ id: 123 }))
```

### Step 3: Add Imports

```typescript
import { fromPartial, fromAny } from "@total-typescript/shoehorn";
```

### Step 4: Verify

```bash
npx tsc --noEmit
```

## Common Use Cases

### API Mocking
```typescript
// Only care about status code
const mockResponse = fromPartial({
  status: 200,
  data: { userId: "123" },
});
```

### Event Payloads
```typescript
// Only mock the fields your test cares about
const event = fromPartial({
  userId: "user-123",
  timestamp: new Date(),
});
```

### Database Records
```typescript
// Partial fixture for testing
const dbRecord = fromPartial({
  id: "rec-123",
  email: "test@example.com",
});
```

## When NOT to Use

- **Production code** — shoehorn is test-only
- **When you need full type safety** — use actual valid data
- **As a shortcut for lazy typing** — only for genuinely partial data

## Alternative Approaches

| Approach | Use When |
|----------|----------|
| `as` | Quick hack, will fix later |
| `fromPartial()` | Partial data, type-checking |
| `fromAny()` | Intentionally wrong data |
| Factory function | Repeated partial objects |
| Deep partial type | Truly partial everything |
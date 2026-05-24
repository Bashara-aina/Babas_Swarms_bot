# Feedback Loop Patterns

How to construct fast, deterministic debugging loops.

## What Makes a Good Loop

| Property | Good | Bad |
|----------|------|-----|
| **Speed** | < 2 seconds | > 30 seconds |
| **Determinism** | Always same result | Flaky 50% of the time |
| **Signal** | Specific assertion | "didn't crash" |
| **Isolation** | Single code path | Full system boot |

## Loop Construction Order

Try in this order, moving to next only when needed:

### 1. Failing Test (Best)
```typescript
test('user cannot checkout with empty cart', async () => {
  const cart = createEmptyCart();
  await expect(checkout(cart)).rejects.toThrow('Cart is empty');
});
```
**Why:** Fast, deterministic, self-documenting, regression-proof.

### 2. HTTP Script
```bash
curl -X POST http://localhost:3000/api/checkout \
  -H 'Content-Type: application/json' \
  -d '{"cartId": "empty-cart"}' \
  | jq .error
```
**When:** API endpoint, dev server running.

### 3. CLI with Snapshot Diff
```bash
echo '{"input": "test"}' | node my-script.js > /tmp/output.txt
diff /tmp/output.txt /tmp/expected.txt
```

### 4. Headless Browser Script
```typescript
import { chromium } from 'playwright';
const browser = await chromium.launch();
const page = await browser.newPage();
await page.goto('/checkout');
// ... interact and assert
```

### 5. Replay Captured Trace
```typescript
// Save real request to disk
const request = captureHttpRequest('/api/checkout');
writeFile('test/fixtures/checkout-request.json', request);

// Replay in isolation
const replayed = await replayRequest(request);
expect(replayed.status).toBe(400);
```

### 6. Throwaway Harness
```typescript
// Minimal system subset for debugging
const mockDb = new InMemoryDatabase();
const service = new CheckoutService(mockDb);
await service.checkout({ cartId: 'test' });
```

### 7. Bisection Harness
```bash
#!/bin/bash
for commit in $(git log --oneline A..B); do
  git checkout $commit
  if ./run-test.sh; then
    echo "$commit: PASS"
  else
    echo "$commit: FAIL"
    exit 1
  fi
done
```

## Making Loops Faster

1. **Cache setup** — run once, use memory cache for subsequent runs
2. **Skip unrelated init** — only boot what's needed
3. **Narrow scope** — test just the buggy function, not the whole flow
4. **Parallelize** — run multiple iterations in parallel
5. **Skip full boot** — embed test directly in code (temporary)

## Making Signal Sharper

```typescript
// Bad signal
expect(result).toBeDefined();

// Good signal
expect(result.error).toBe('CART_IS_EMPTY');
expect(result.code).toBe('EMPTY_CART_FOR_CHECKOUT');
```

## Handling Non-Determinism

For race conditions, timing bugs:
1. **Raise reproduction rate** — run 100×, not 10×
2. **Parallelize** — divide iterations across cores
3. **Add stress** — increase load, shrink timeouts
4. **Inject sleeps** — narrow the timing window
5. **Freeze time** — if possible, mock Date.now()

## When All Else Fails

If you cannot build any loop after 30+ minutes:
1. **Stop and tell the user**
2. **List what you tried**
3. **Ask for one of:**
   - Access to reproducing environment
   - Captured artifact (HAR, logs, core dump, video)
   - Permission for production instrumentation
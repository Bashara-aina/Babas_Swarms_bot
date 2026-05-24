# Mocking Guidelines

## When to Mock

Mock at **boundaries** where:
1. The external dependency is slow, non-deterministic, or expensive
2. You're not testing the external system itself
3. You need to control test conditions (errors, time, etc.)

## What to Mock

| Mock This | Don't Mock This |
|-----------|------------------|
| External APIs (Stripe, Slack) | Internal collaborators |
| Databases (for unit tests) | Your own modules |
| File system | Domain logic |
| Time/Date utilities | Public interfaces |

## The Mocking Pyramid

```
        ┌─────────────┐
        │  External  │  ← Don't mock (integration tests)
        │    APIs    │
       ┌┴─────────────┴┐
       │  Databases   │  ← Mock for unit, real for integration
       │ (boundaries) │
      ┌┴───────────────┴┐
      │  Internal      │  ← Mock only when truly needed
      │ Collaborators  │
     ┌┴────────────────┴┐
     │   Your Domain    │  ← Never mock
     │    Objects       │
     └──────────────────┘
```

## Rules

1. **Mock external systems, not internal structure**
2. **If you mock your own code, you're not testing your code**
3. **Integration tests should use real implementations**
4. **Unit tests can mock boundaries (DB, APIs)**

## Good Mock Example

```typescript
// Mocking external API boundary
test('checkout sends receipt email', async () => {
  const sendEmail = jest.spyOn(emailClient, 'send').mockResolvedValue();
  
  await checkout(cart, paymentMethod);
  
  expect(sendEmail).toHaveBeenCalledWith(
    expect.objectContaining({
      to: 'user@example.com',
      subject: 'Order Confirmation'
    })
  );
});
```

## Bad Mock Example

```typescript
// Mocking internal collaborator
test('checkout calls internal processor', async () => {
  const processor = jest.spyOn(internalProcessor, 'process');
  
  await checkout(cart, paymentMethod);
  
  expect(processor).toHaveBeenCalled(); // Too coupled
});
```

## Testing Private Methods

Don't test private methods directly. If a private method is complex enough to need testing:
1. It's a sign it should be a separate module with its own tests
2. Make it public (or protected with internal visibility)

## Time Mocking

Use time mocking for:
- Caching tests
- Expiration logic
- Scheduled tasks

```typescript
beforeEach(() => {
  jest.useFakeTimers();
});

afterEach(() => {
  jest.useRealTimers();
});
```
# Good Tests vs Bad Tests

## Good Tests (Integration Style)

Good tests verify behavior through **public interfaces**:
- Exercise code paths through actual API calls
- Read like specifications: "user can checkout with valid cart"
- Survive refactors because they test behavior, not structure
- Focus on _what_ the system does, not _how_

## Bad Tests (Implementation Coupling)

Bad tests are coupled to implementation details:
- Mock internal collaborators directly
- Test private methods
- Query databases directly instead of through interfaces
- Break when you refactor internal structure

## Warning Signs

Your test breaks when you refactor, but behavior hasn't changed → implementation coupling

You rename an internal function and tests fail → those tests were testing implementation

## Examples

### Good Test
```typescript
// Tests behavior through public interface
test('user can checkout with valid cart', async () => {
  const cart = createCartWithItems([{ id: 'item-1', price: 100 }]);
  const result = await checkout(cart, paymentMethod);
  
  expect(result.status).toBe('success');
  expect(result.orderId).toBeDefined();
});
```

### Bad Test
```typescript
// Tests implementation details
test('checkout calls processPayment and updateInventory', async () => {
  const processPayment = jest.spyOn(paymentService, 'process');
  const updateInventory = jest.spyOn(inventoryService, 'update');
  
  await checkout(cart, paymentMethod);
  
  expect(processPayment).toHaveBeenCalledWith(paymentMethod, 100);
  expect(updateInventory).toHaveBeenCalledWith('item-1');
});
```

## Key Principle

> Code can change entirely; tests shouldn't.

If your test reads like it's describing the implementation rather than the behavior, it's a bad test.
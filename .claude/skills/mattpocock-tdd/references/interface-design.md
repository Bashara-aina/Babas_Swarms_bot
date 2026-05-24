# Interface Design for Testability

## Key Principle

Design interfaces that are **easy to use correctly** and **hard to use incorrectly**.

## Interface Design Rules

### 1. Make Invalid States Unrepresentable

```typescript
// Bad: allows invalid state
interface User {
  name: string;
  email: string | null; // null = not set
}

// Good: invalid state cannot exist
interface User {
  name: string;
  email: NonEmptyEmail; // wrapped type that guarantees validity
}
```

### 2. Simplify Common Cases

```typescript
// Bad: everything is hard
function createUser(input: {
  name: string;
  email: string;
  role: Role;
  sendWelcomeEmail: boolean;
  createDefaultProfile: boolean;
}): User { ... }

// Good: sensible defaults, advanced options optional
function createUser(
  name: string,
  email: Email
): User { ... }

// Or use builder pattern for advanced cases
function createUser(): UserBuilder {
  return new UserBuilder();
}
```

### 3. Separate Concerns

```typescript
// Bad: mixed concerns
function processPayment(
  amount: number,
  currency: string,
  customerId: string,
  shippingAddress: Address,
  billingAddress: Address,
  inventoryUpdates: InventoryUpdate[],
  emailReceipt: boolean
): PaymentResult { ... }

// Good: separated concerns
function checkout(
  cart: Cart,
  customer: Customer,
  shippingAddress: Address
): CheckoutResult { ... }
// Internally coordinates payment, inventory, email
```

### 4. Prefer Specific Over Generic

```typescript
// Bad: too generic
function update(id: string, data: any): void { ... }

// Good: specific intent
function updateShippingAddress(
  customerId: CustomerID,
  newAddress: Address
): void { ... }
```

## Testing Benefits

Good interfaces:
- Require fewer mocks (boundaries are clear)
- Make tests read like specifications
- Survive refactors (behavior is the interface contract)

## Dependency Injection Pattern

Inject dependencies through constructors or setters:

```typescript
class OrderService {
  constructor(
    private paymentGateway: PaymentGateway,
    private inventoryService: InventoryService,
    private emailService: EmailService
  ) {}
  
  // Easy to test with mocks
}
```
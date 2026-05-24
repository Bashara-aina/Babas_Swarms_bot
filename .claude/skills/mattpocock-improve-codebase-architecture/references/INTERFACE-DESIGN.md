# Interface Design for Architecture

How to design good seams and deep modules.

## Interface Design Principles

### 1. Make Invalid States Unrepresentable

```typescript
// Bad: allows invalid state
interface User {
  name: string;
  email: string | null; // null = not set, what does this mean?
}

// Good: invalid state cannot exist
interface User {
  name: NonEmptyString;
  email: ValidEmail;
}

// Even better: wrap primitive types
type NonEmptyString = string & { __type: 'NonEmpty' };
type ValidEmail = string & { __type: 'ValidEmail' };
```

### 2. Small Interface, Deep Implementation

```typescript
// Shallow: big interface with complex internals exposed
interface Config {
  getString(key: string): string;
  getNumber(key: string): number;
  getBoolean(key: string): boolean;
  getObject(key: string): object;
  getArray(key: string): array;
  setString(key: string, value: string): void;
  // ... lots of methods = shallow
}

// Deep: single focused method
interface Config {
  get<T>(key: ConfigKey<T>): T;
  set<T>(key: ConfigKey<T>, value: T): void;
}
```

### 3. Prefer Specific Over Generic

```typescript
// Bad: too generic
interface Database {
  query(sql: string): any;
  execute(sql: string): any;
}

// Good: specific intent
interface UserRepository {
  findById(id: UserID): Promise<User | null>;
  findByEmail(email: Email): Promise<User | null>;
  save(user: User): Promise<void>;
}
```

### 4. Commands and Queries Separated (CQRS-lite)

```typescript
// Mixed interface (harder to test, reason about)
interface OrderService {
  updateOrder(order: Order): Order; // command + query
}

// Separated (clearer, more testable)
interface OrderCommands {
  updateOrder(order: Order): Promise<void>;
}
interface OrderQueries {
  getOrder(id: OrderID): Promise<Order>;
}
```

## Seam Placement

### Finding Good Seams

Look for:
1. **Natural boundaries** — where behavior changes
2. **Dependency inversion points** — where you'd inject a mock
3. **Consistent abstraction levels** — don't mix high-level and low-level
4. **Change likelihood** — put seams where change happens

### Signs of Bad Seams

- Leak implementation details across seam
- Exposes internal state directly
- Different abstraction levels on same seam
- Tests require many mocks at this seam

## Testing at Seams

```typescript
// Good: test at the seam with real implementation
test('UserRepository returns user from database', async () => {
  const repo = new PostgresUserRepository(realDb);
  const user = await repo.findByEmail('test@example.com');
  expect(user?.email).toBe('test@example.com');
});

// Bad: test implementation details
test('UserRepository calls correct SQL', async () => {
  const repo = new PostgresUserRepository(mockDb);
  await repo.findByEmail('test@example.com');
  expect(mockDb.query).toHaveBeenCalledWith(
    expect.stringContaining('SELECT')
  );
});
```

## Refactoring to Deep Modules

1. **Identify shallow modules** (deletion test)
2. **Group related functionality** into a single interface
3. **Move complexity behind the seam**
4. **Keep interface small**
5. **Verify with tests** at the new seam
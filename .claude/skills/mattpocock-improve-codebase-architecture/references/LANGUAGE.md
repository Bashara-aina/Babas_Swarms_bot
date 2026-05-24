# Architecture Language

Precise definitions for architecture discussions. Use these terms consistently — they are the vocabulary for this skill.

## Core Vocabulary

### Module
Anything with an interface and an implementation: function, class, package, slice.

### Interface
Everything a caller must know to use a module:
- Types and parameters
- Invariants (things that must always be true)
- Error modes
- Ordering requirements
- Configuration

Not just the type signature — the full contract.

### Implementation
The code inside a module — the hidden internals.

### Depth / Leverage
**Deep** = high leverage. Lots of behavior behind a small interface.

**Shallow** = interface nearly as complex as the implementation. Little leverage.

```
Deep Module:
  Interface: createUser(name, email) → UserID
  Implementation: validates, hashes password, creates DB record, sends welcome email, logs audit

Shallow Module:
  Interface: validateEmail(email) → boolean
  Implementation: just calls another validator
```

### Seam
Where an interface lives. A place where behavior can be altered without editing in place.

```
Seam: the place where one module ends and another begins
Good: HTTP handler calls Service.someMethod(userID)
Bad: HTTP handler directly manipulates user record in database
```

Use "seam," not "boundary."

### Adapter
A concrete thing satisfying an interface at a seam.

```
DatabaseAdapter implements UserRepository
MockAdapter implements UserRepository (for tests)
```

### Leverage
What callers get from module depth. More behavior per interface element = more leverage.

### Locality
What maintainers get from depth. Change, bugs, and knowledge concentrated in one place.

## Key Principles

### Deletion Test
Imagine deleting the module:
- **Complexity vanishes** → it was a pass-through (shallow)
- **Complexity reappears across N callers** → it was earning its keep (deep)

### Interface Is Test Surface
What you can test without mocking. Larger interface = more to test, but also more functionality per test.

### Seam Detection
- **One adapter** = hypothetical seam (possible future boundary)
- **Two adapters** = real seam (already split, even if not formalized)

## Language to Avoid

| Instead of | Use |
|------------|-----|
| "component" | module, seam |
| "service" | module (unless it's a Service in the domain sense) |
| "API" | interface |
| "boundary" | seam |
| "handler" | module (be specific about what it handles) |
| "controller" | module (be specific about what it controls) |
| "wrapper" | adapter, facade |

## Deep Module Example

```typescript
// Shallow: validates email
interface EmailValidator {
  isValid(email: string): boolean;
}

// Deep: manages email communication
interface EmailGateway {
  sendWelcome(userId: UserID): Promise<void>;
  sendPasswordReset(userId: UserID, token: string): Promise<void>;
  sendNotification(userId: UserID, message: string): Promise<void>;
}
```

The deep module provides more leverage per interface element and higher locality — all email logic lives together.
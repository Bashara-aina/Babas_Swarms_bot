# CONTEXT.md Format

Format for domain glossary entries in `CONTEXT.md`.

## Purpose

`CONTEXT.md` captures the project's domain language — terms that are meaningful to domain experts, not implementation details.

## Format

```markdown
# Context: [Domain Name]

## Glossary

### Term
Precise definition. What it means, what it doesn't mean.
- **Synonyms to avoid**: term1, term2
- **Related terms**: term3, term4

### AnotherTerm
...
```

## Rules

1. **Only domain terms** — not implementation details
2. **Precise definitions** — no ambiguity
3. **Exclude synonyms** — say what a term means, not just what it sounds like
4. **Update inline** — add terms as they are resolved during discussion
5. **No code** — no type signatures, function names, or file paths

## Example

```markdown
# Context: Order Processing

## Glossary

### Order
A customer's request for products. Created when checkout completes.
- **Not**: a line item, a shipment, a payment
- **Synonyms to avoid**: "cart order", "pending order"

### Cancellation
User-initiated abort of an Order before it ships. Results in full refund.
- **Not**: a refund (that's a Payment concept), a return (that's post-delivery)
```

## Single vs Multi-Context

### Single Context
`CONTEXT.md` at repo root. Use this for small-to-medium repos.

### Multi-Context
See `CONTEXT-MAP.md` at root pointing to context-specific `CONTEXT.md` files.
Use this when different bounded contexts need different glossaries.
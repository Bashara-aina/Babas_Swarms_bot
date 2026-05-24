# Deep Modules

## Definition

A deep module has:
- **Small, simple interface** (few parameters, clear purpose)
- **Deep implementation** (significant logic behind that interface)

## Shallow Module (Avoid)

```typescript
// Shallow: big interface, little implementation
function processUser(
  id: string,
  name: string,
  email: string,
  age: number,
  address: string,
  phone: string,
  preferences: Preferences,
  settings: Settings
): UserDTO { ... }
```

## Deep Module (Aim For)

```typescript
// Deep: small interface, rich implementation
function createUser(input: CreateUserInput): UserDTO { ... }

interface CreateUserInput {
  id: string;
  name: string;
  email: string;
  // Only expose what's needed - hide the complexity
}
```

## Why Deep Modules Matter for Testing

1. **Small interfaces = fewer test cases** to cover
2. **Rich implementations** can be tested thoroughly without updating tests
3. **Changes to implementation** don't break tests at the interface

## Design Principle

> Many inputs, one output. Rich logic behind a simple door.

## Example

### Before (Shallow)
```typescript
export function calculatePrice(
  basePrice: number,
  discountPercent: number,
  taxPercent: number,
  shippingCost: number,
  handlingFee: number
): number {
  return basePrice - (basePrice * discountPercent / 100) + 
         (basePrice * taxPercent / 100) + shippingCost + handlingFee;
}
```

### After (Deep)
```typescript
export interface PricingInput {
  basePrice: number;
  discount?: Discount;
  taxInfo: TaxInfo;
  shippingMethod: ShippingMethod;
}

export function calculatePrice(input: PricingInput): Money {
  const subtotal = applyDiscount(input.basePrice, input.discount);
  const tax = calculateTax(subtotal, input.taxInfo);
  const shipping = calculateShipping(input.shippingMethod);
  return new Money(subtotal + tax + shipping);
}
```

## Refactoring to Deep Modules

1. Identify modules with many parameters
2. Group related parameters into structs/objects
3. Move validation and complex logic into the implementation
4. Keep the interface simple
# cekwajar.id UI/UX Enhancement Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Transform cekwajar.id into a premium financial audit tool with best-of-the-best UI/UX — emerald+amber palette, shimmer skeletons (Civora-style), theme customizer (Shadboard-style), animated number tickers, and bento-grid dashboard.

**Architecture:** CSS variables-based design system (Tailwind CSS 4) + React component library + settings context for theme customization. All animations use CSS keyframes with `prefers-reduced-motion` respect. Component variants via CVA (already in use).

**Tech Stack:** Next.js 16.2.3, React 19, Tailwind CSS 4, shadcn/ui (existing), CVA (existing), Lucide icons, framer-motion (if needed), js-cookie (existing)

**Base path:** `cekwajar.id-20260415T173403Z-3-001/cekwajar.id/`

---

## File Map

### New files to create:
- `src/lib/animations.css` — Motion tokens, keyframes, utility classes
- `src/components/ui/number-ticker.tsx` — Animated counter
- `src/components/ui/toast.tsx` — Enhanced toast notification
- `src/components/shared/Skeletons/DashboardSkeleton.tsx` — Civora-style dashboard skeleton
- `src/components/shared/Skeletons/TableSkeleton.tsx` — Table loading skeleton
- `src/components/shared/Skeletons/FormSkeleton.tsx` — Form loading skeleton
- `src/components/shared/StatsGrid/StatsGrid.tsx` — Bento stat cards
- `src/components/shared/PageHeader/PageHeader.tsx` — Page title + description
- `src/components/forms/IDRInput.tsx` — Indonesian currency input
- `src/components/shared/Customizer/Customizer.tsx` — Shadboard-style theme panel
- `src/components/shared/Customizer/settings-context.tsx` — Settings state
- `src/components/shared/PremiumGate.tsx` — Redesigned premium gate
- `src/components/shared/StatCard.tsx` — Dashboard stat card with trend

### Files to modify:
- `src/app/globals.css` — Add CSS variables + import animations.css
- `src/components/ui/button.tsx` — Add premium variant + hover lift
- `src/components/ui/card.tsx` — Add hover lift + gradient variants
- `src/components/ui/badge.tsx` — Add premium/info variants + scale-in animation
- `src/components/ui/skeleton.tsx` — Add shimmer animation
- `src/app/page.tsx` — Homepage hero + trust signals + tool card animations
- `src/app/wajar-slip/page.tsx` — NumberTicker + verdict animations
- `src/app/dashboard/page.tsx` — StatsGrid + skeleton loading

---

## PHASE 1: Foundation — Design Tokens & Motion System

### Task 1: Create animations.css with motion tokens

**File:** Create: `src/lib/animations.css`

- [ ] **Step 1: Create the file with all motion tokens and keyframes**

```css
/* ═══════════════════════════════════════════════════════════════════════════
 * cekwajar.id — Animation System
 * Motion tokens, keyframes, and utility classes
 * ═══════════════════════════════════════════════════════════════════════════ */

/* ─── Motion Tokens ─────────────────────────────────────────────────────── */
:root {
  /* Durations */
  --duration-instant: 75ms;
  --duration-fast: 150ms;
  --duration-normal: 250ms;
  --duration-slow: 400ms;
  --duration-slower: 600ms;
  --duration-count: 1200ms;

  /* Easings */
  --ease-out: cubic-bezier(0, 0, 0.2, 1);
  --ease-in: cubic-bezier(0.4, 0, 1, 1);
  --ease-in-out: cubic-bezier(0.4, 0, 0.2, 1);
  --ease-spring: cubic-bezier(0.34, 1.56, 0.64, 1);
  --ease-bounce: cubic-bezier(0.68, -0.55, 0.265, 1.55);
}

/* ─── Keyframes ─────────────────────────────────────────────────────────── */
@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

@keyframes fadeInUp {
  from { opacity: 0; transform: translateY(12px); }
  to { opacity: 1; transform: translateY(0); }
}

@keyframes fadeInDown {
  from { opacity: 0; transform: translateY(-12px); }
  to { opacity: 1; transform: translateY(0); }
}

@keyframes slideInRight {
  from { opacity: 0; transform: translateX(20px); }
  to { opacity: 1; transform: translateX(0); }
}

@keyframes scaleIn {
  from { opacity: 0; transform: scale(0.95); }
  to { opacity: 1; transform: scale(1); }
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

@keyframes shimmer {
  0% { background-position: -200% 0; }
  100% { background-position: 200% 0; }
}

@keyframes countUp {
  from { opacity: 0; transform: translateY(8px); }
  to { opacity: 1; transform: translateY(0); }
}

@keyframes checkmark {
  0% { stroke-dashoffset: 24; }
  100% { stroke-dashoffset: 0; }
}

@keyframes confetti {
  0% { transform: translateY(0) rotate(0deg); opacity: 1; }
  100% { transform: translateY(-100px) rotate(720deg); opacity: 0; }
}

@keyframes slideOutRight {
  from { opacity: 1; transform: translateX(0); }
  to { opacity: 0; transform: translateX(100%); }
}

/* ─── Animation Utility Classes ─────────────────────────────────────────── */
.animate-fade-in { animation: fadeIn var(--duration-normal) var(--ease-out) both; }
.animate-fade-in-up { animation: fadeInUp var(--duration-slow) var(--ease-out) both; }
.animate-fade-in-down { animation: fadeInDown var(--duration-slow) var(--ease-out) both; }
.animate-slide-in-right { animation: slideInRight var(--duration-slow) var(--ease-out) both; }
.animate-scale-in { animation: scaleIn var(--duration-normal) var(--ease-spring) both; }
.animate-pulse { animation: pulse 2s var(--ease-in-out) infinite; }
.animate-spin { animation: spin 1s linear infinite; }
.animate-shimmer {
  background: linear-gradient(90deg, #e2e8f0 25%, #f1f5f9 50%, #e2e8f0 75%);
  background-size: 200% 100%;
  animation: shimmer 1.5s infinite;
}

/* Stagger delays */
.stagger-1 { animation-delay: 100ms; }
.stagger-2 { animation-delay: 200ms; }
.stagger-3 { animation-delay: 300ms; }
.stagger-4 { animation-delay: 400ms; }
.stagger-5 { animation-delay: 500ms; }

/* ─── Reduced Motion ─────────────────────────────────────────────────────── */
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
  }
}
```

- [ ] **Step 2: Import in globals.css**

Modify `src/app/globals.css` to add `@import "./lib/animations.css";` after the Tailwind import.

Run: `grep -n "import" src/app/globals.css`

Expected output: animation imports after tailwind import

---

### Task 2: Enhance Button with premium variant and hover lift

**File:** Modify: `src/components/ui/button.tsx`

- [ ] **Step 1: Read the current file**

Run: `cat src/components/ui/button.tsx`

- [ ] **Step 2: Add premium variant and hover animation**

Replace the `buttonVariants` CVA with enhanced version:

```tsx
const buttonVariants = cva(
  'inline-flex items-center justify-center gap-1.5 whitespace-nowrap rounded-md text-sm font-medium transition-all duration-150 ease-out focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-500 disabled:pointer-events-none disabled:opacity-50 active:scale-[0.98]',
  {
    variants: {
      variant: {
        default: 'bg-emerald-600 text-white hover:bg-emerald-700 hover:shadow-md hover:-translate-y-0.5',
        destructive: 'bg-red-600 text-white hover:bg-red-700 hover:shadow-md hover:-translate-y-0.5',
        outline: 'border border-slate-200 bg-white hover:bg-slate-50 hover:border-slate-300',
        secondary: 'bg-slate-100 text-slate-900 hover:bg-slate-200',
        ghost: 'hover:bg-slate-100 hover:text-slate-900',
        link: 'text-emerald-600 underline-offset-4 hover:underline',
        premium: 'bg-gradient-to-r from-violet-600 to-purple-600 text-white hover:from-violet-700 hover:to-purple-700 hover:shadow-lg hover:-translate-y-0.5',
      },
      size: {
        default: 'h-9 px-4 py-2',
        sm: 'h-8 rounded-md px-3 text-xs',
        lg: 'h-11 rounded-md px-8 text-base',
        icon: 'h-9 w-9',
      },
    },
    defaultVariants: {
      variant: 'default',
      size: 'default',
    },
  }
)
```

- [ ] **Step 3: Commit**

```bash
cd cekwajar.id-20260415T173403Z-3-001/cekwajar.id
git add src/components/ui/button.tsx src/lib/animations.css src/app/globals.css
git commit -m "feat(ui): add motion system + premium button variant with hover lift"
```

---

### Task 3: Enhance Card with hover lift and gradient variants

**File:** Modify: `src/components/ui/card.tsx`

- [ ] **Step 1: Read the current file**

Run: `cat src/components/ui/card.tsx`

- [ ] **Step 2: Replace with enhanced version**

```tsx
// ══════════════════════════════════════════════════════════════════════════════
// cekwajar.id — Card Component (shadcn/ui style)
// ══════════════════════════════════════════════════════════════════════════════

import * as React from 'react'
import { cn } from '@/lib/utils'

const Card = React.forwardRef<HTMLDivElement, React.HTMLAttributes<HTMLDivElement> & { hoverable?: boolean }>(
  ({ className, hoverable, ...props }, ref) => (
    <div
      ref={ref}
      className={cn(
        'rounded-xl border border-slate-200 bg-white text-slate-900 shadow-sm transition-all duration-250 ease-out',
        hoverable && 'hover:border-emerald-200 hover:shadow-lg hover:-translate-y-0.5 cursor-pointer',
        className
      )}
      {...props}
    />
  )
)
Card.displayName = 'Card'

const CardGradient = React.forwardRef<HTMLDivElement, React.HTMLAttributes<HTMLDivElement>>(
  ({ className, ...props }, ref) => (
    <div
      ref={ref}
      className={cn(
        'relative rounded-xl border border-slate-200 bg-white text-slate-900 shadow-sm overflow-hidden transition-all duration-250 ease-out hover:shadow-lg hover:-translate-y-0.5',
        className
      )}
      {...props}
    >
      <div className="absolute inset-0 bg-gradient-to-tr from-emerald-50 via-white to-amber-50/30 opacity-40 pointer-events-none" />
      <div className="relative">{props.children}</div>
    </div>
  )
)
CardGradient.displayName = 'CardGradient'

const CardHeader = React.forwardRef<HTMLDivElement, React.HTMLAttributes<HTMLDivElement>>(
  ({ className, ...props }, ref) => (
    <div ref={ref} className={cn('flex flex-col space-y-1.5 p-6', className)} {...props} />
  )
)
CardHeader.displayName = 'CardHeader'

const CardTitle = React.forwardRef<HTMLParagraphElement, React.HTMLAttributes<HTMLHeadingElement>>(
  ({ className, ...props }, ref) => (
    <h3 ref={ref} className={cn('font-semibold leading-none tracking-tight', className)} {...props} />
  )
)
CardTitle.displayName = 'CardTitle'

const CardDescription = React.forwardRef<
  HTMLParagraphElement,
  React.HTMLAttributes<HTMLParagraphElement>
>(({ className, ...props }, ref) => (
  <p ref={ref} className={cn('text-sm text-slate-500', className)} {...props} />
))
CardDescription.displayName = 'CardDescription'

const CardContent = React.forwardRef<HTMLDivElement, React.HTMLAttributes<HTMLDivElement>>(
  ({ className, ...props }, ref) => (
    <div ref={ref} className={cn('p-6 pt-0', className)} {...props} />
  )
)
CardContent.displayName = 'CardContent'

const CardFooter = React.forwardRef<HTMLDivElement, React.HTMLAttributes<HTMLDivElement>>(
  ({ className, ...props }, ref) => (
    <div ref={ref} className={cn('flex items-center p-6 pt-0', className)} {...props} />
  )
)
CardFooter.displayName = 'CardFooter'

export { Card, CardGradient, CardHeader, CardTitle, CardDescription, CardContent, CardFooter }
```

- [ ] **Step 3: Commit**

```bash
git add src/components/ui/card.tsx
git commit -m "feat(ui): enhance Card with hoverable + gradient variants"
```

---

### Task 4: Enhance Badge with premium/info variants and animation

**File:** Modify: `src/components/ui/badge.tsx`

- [ ] **Step 1: Read the current file**

Run: `cat src/components/ui/badge.tsx`

- [ ] **Step 2: Replace with enhanced version**

```tsx
// ══════════════════════════════════════════════════════════════════════════════
// cekwajar.id — Badge Component (shadcn/ui style)
// ══════════════════════════════════════════════════════════════════════════════

import * as React from 'react'
import { cva, type VariantProps } from 'class-variance-authority'
import { cn } from '@/lib/utils'

const badgeVariants = cva(
  'inline-flex items-center rounded-md border px-2.5 py-0.5 text-xs font-semibold transition-colors focus:outline-none',
  {
    variants: {
      variant: {
        default: 'border-transparent bg-emerald-100 text-emerald-800',
        secondary: 'border-transparent bg-slate-100 text-slate-800',
        destructive: 'border-transparent bg-red-100 text-red-800',
        outline: 'text-slate-900 border-slate-300',
        success: 'border-transparent bg-green-100 text-green-800',
        warning: 'border-transparent bg-amber-100 text-amber-800',
        premium: 'border-transparent bg-gradient-to-r from-violet-100 to-purple-100 text-violet-800',
        info: 'border-transparent bg-blue-100 text-blue-800',
        error: 'border-transparent bg-red-100 text-red-800',
      },
    },
    defaultVariants: {
      variant: 'default',
    },
  }
)

export interface BadgeProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof badgeVariants> {}

function Badge({ className, variant, ...props }: BadgeProps) {
  return (
    <div
      className={cn(
        badgeVariants({ variant }),
        'animate-scale-in',
        className
      )}
      {...props}
    />
  )
}

export { Badge, badgeVariants }
```

- [ ] **Step 3: Commit**

```bash
git add src/components/ui/badge.tsx
git commit -m "feat(ui): add premium/info/error badge variants + scale-in animation"
```

---

### Task 5: Enhance Skeleton with shimmer effect

**File:** Modify: `src/components/ui/skeleton.tsx`

- [ ] **Step 1: Read the current file**

Run: `cat src/components/ui/skeleton.tsx`

- [ ] **Step 2: Replace with shimmer-enhanced skeleton**

```tsx
// ══════════════════════════════════════════════════════════════════════════════
// cekwajar.id — Skeleton Component (shadcn/ui style)
// ══════════════════════════════════════════════════════════════════════════════

import * as React from 'react'
import { cn } from '@/lib/utils'

function Skeleton({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn('animate-shimmer rounded-md bg-slate-200', className)}
      {...props}
    />
  )
}

export { Skeleton }
```

- [ ] **Step 3: Commit**

```bash
git add src/components/ui/skeleton.tsx
git commit -m "feat(ui): add shimmer animation to skeleton"
```

---

## PHASE 2: Core Animation Components

### Task 6: NumberTicker Component

**Files:** Create: `src/components/ui/number-ticker.tsx`

- [ ] **Step 1: Create NumberTicker component**

```tsx
// ══════════════════════════════════════════════════════════════════════════════
// cekwajar.id — NumberTicker Component
// Animated counter for IDR values in results
// ══════════════════════════════════════════════════════════════════════════════

'use client'

import { useEffect, useRef, useState } from 'react'
import { cn } from '@/lib/utils'

interface NumberTickerProps {
  value: number
  prefix?: string
  suffix?: string
  duration?: number
  locale?: string
  className?: string
  decimals?: number
}

export function NumberTicker({
  value,
  prefix = '',
  suffix = '',
  duration = 1200,
  locale = 'id-ID',
  className,
  decimals = 0,
}: NumberTickerProps) {
  const [display, setDisplay] = useState(0)
  const startTimeRef = useRef<number | null>(null)
  const rafRef = useRef<number | null>(null)

  useEffect(() => {
    const start = 0
    const end = value
    startTimeRef.current = null

    const easeOutCubic = (t: number) => 1 - Math.pow(1 - t, 3)

    const animate = (currentTime: number) => {
      if (startTimeRef.current === null) {
        startTimeRef.current = currentTime
      }

      const elapsed = currentTime - startTimeRef.current
      const progress = Math.min(elapsed / duration, 1)
      const eased = easeOutCubic(progress)
      const current = start + (end - start) * eased

      setDisplay(decimals > 0 ? Math.round(current * Math.pow(10, decimals)) / Math.pow(10, decimals) : Math.floor(current))

      if (progress < 1) {
        rafRef.current = requestAnimationFrame(animate)
      }
    }

    rafRef.current = requestAnimationFrame(animate)

    return () => {
      if (rafRef.current !== null) {
        cancelAnimationFrame(rafRef.current)
      }
    }
  }, [value, duration, decimals])

  const formatted = display.toLocaleString(locale, {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  })

  return (
    <span className={cn('font-variant-numeric: tabular-nums', className)}>
      {prefix}
      {formatted}
      {suffix}
    </span>
  )
}
```

- [ ] **Step 2: Verify the component compiles**

Run: `cd cekwajar.id-20260415T173403Z-3-001/cekwajar.id && npx tsc --noEmit src/components/ui/number-ticker.tsx 2>&1 | head -20`

Expected: No errors

- [ ] **Step 3: Commit**

```bash
git add src/components/ui/number-ticker.tsx
git commit -m "feat(ui): add NumberTicker component for animated IDR counters"
```

---

### Task 7: IDRInput — Indonesian Currency Formatter

**Files:** Create: `src/components/forms/IDRInput.tsx`

- [ ] **Step 1: Create IDRInput component**

```tsx
// ══════════════════════════════════════════════════════════════════════════════
// cekwajar.id — IDRInput Component
// Indonesian Rupiah input with real-time formatting
// As user types "2500000" → displays "2.500.000"
// ══════════════════════════════════════════════════════════════════════════════

'use client'

import { useState, useCallback, useEffect } from 'react'
import { Input } from '@/components/ui/input'
import { cn } from '@/lib/utils'

interface IDRInputProps {
  value: string
  onChange: (value: string) => void
  placeholder?: string
  className?: string
  disabled?: boolean
}

export function IDRInput({
  value,
  onChange,
  placeholder = '0',
  className,
  disabled,
}: IDRInputProps) {
  // displayValue is the formatted string shown to user
  const [displayValue, setDisplayValue] = useState('')
  const [isFocused, setIsFocused] = useState(false)

  // Sync displayValue when value changes from parent (e.g., form reset)
  useEffect(() => {
    if (!isFocused && value) {
      const num = parseInt(value.replace(/\D/g, ''), 10)
      if (!isNaN(num)) {
        setDisplayValue(num.toLocaleString('id-ID'))
      } else {
        setDisplayValue('')
      }
    }
  }, [value, isFocused])

  const handleFocus = useCallback(() => {
    setIsFocused(true)
    // Show raw number for easy editing
    if (value) {
      setDisplayValue(value)
    }
  }, [value])

  const handleBlur = useCallback(() => {
    setIsFocused(false)
    // Format on blur
    if (displayValue) {
      const num = parseInt(displayValue.replace(/\D/g, ''), 10)
      if (!isNaN(num)) {
        const formatted = num.toLocaleString('id-ID')
        setDisplayValue(formatted)
        onChange(num.toString())
      }
    }
  }, [displayValue, onChange])

  const handleChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const raw = e.target.value.replace(/\D/g, '')
      setDisplayValue(raw)
      onChange(raw)
    },
    [onChange]
  )

  return (
    <div className="relative">
      <span className="absolute left-3 top-1/2 -translate-y-1/2 text-sm text-slate-400 pointer-events-none">
        Rp
      </span>
      <Input
        type="text"
        inputMode="numeric"
        value={displayValue}
        onChange={handleChange}
        onFocus={handleFocus}
        onBlur={handleBlur}
        placeholder={placeholder}
        disabled={disabled}
        className={cn('pl-8 font-mono text-right', className)}
      />
    </div>
  )
}
```

- [ ] **Step 2: Verify compilation**

Run: `cd cekwajar.id-20260415T173403Z-3-001/cekwajar.id && npx tsc --noEmit src/components/forms/IDRInput.tsx 2>&1 | head -20`

Expected: No errors

- [ ] **Step 3: Commit**

```bash
git add src/components/forms/IDRInput.tsx
git commit -m "feat(forms): add IDRInput with real-time Indonesian currency formatting"
```

---

### Task 8: Toast Component

**Files:** Create: `src/components/ui/toast.tsx`

Note: The project already has `@radix-ui/react-toast` installed. Create an enhanced toast wrapper:

- [ ] **Step 1: Create enhanced toast**

```tsx
// ══════════════════════════════════════════════════════════════════════════════
// cekwajar.id — Toast Component
// Enhanced toast notifications with slide-in animation
// ══════════════════════════════════════════════════════════════════════════════

'use client'

import * as React from 'react'
import * as ToastPrimitives from '@radix-ui/react-toast'
import { X, CheckCircle, AlertCircle, AlertTriangle, Info } from 'lucide-react'
import { cn } from '@/lib/utils'

const ToastProvider = ToastPrimitives.Provider

const ToastViewport = React.forwardRef<
  React.ElementRef<typeof ToastPrimitives.Viewport>,
  React.ComponentPropsWithoutRef<typeof ToastPrimitives.Viewport>
>(({ className, ...props }, ref) => (
  <ToastPrimitives.Viewport
    ref={ref}
    className={cn(
      'fixed top-4 right-4 z-[100] flex flex-col gap-2 w-full max-w-sm',
      className
    )}
    {...props}
  />
))
ToastViewport.displayName = ToastPrimitives.Viewport.displayName

const toastVariants = {
  default: {
    container: 'border-slate-200 bg-white',
    icon: CheckCircle,
    iconClassName: 'text-emerald-500',
  },
  success: {
    container: 'border-emerald-200 bg-emerald-50',
    icon: CheckCircle,
    iconClassName: 'text-emerald-500',
  },
  error: {
    container: 'border-red-200 bg-red-50',
    icon: AlertCircle,
    iconClassName: 'text-red-500',
  },
  warning: {
    container: 'border-amber-200 bg-amber-50',
    icon: AlertTriangle,
    iconClassName: 'text-amber-500',
  },
  info: {
    container: 'border-blue-200 bg-blue-50',
    icon: Info,
    iconClassName: 'text-blue-500',
  },
} as const

type ToastVariant = keyof typeof toastVariants

const Toast = React.forwardRef<
  React.ElementRef<typeof ToastPrimitives.Root>,
  React.ComponentPropsWithoutRef<typeof ToastPrimitives.Root> & {
    variant?: ToastVariant
  }
>(({ className, variant = 'default', ...props }, ref) => {
  const config = toastVariants[variant]
  return (
    <ToastPrimitives.Root
      ref={ref}
      className={cn(
        'group pointer-events-auto relative flex w-full items-center gap-3 overflow-hidden rounded-xl border p-4 shadow-lg transition-all animate-slide-in-right',
        'data-[swipe=cancel]:translate-x-0',
        'data-[swipe=end]:animate-slideOutRight',
        'data-[swipe=move]:translate-x-[var(--radix-toast-swipe-move-x)]',
        'data-[state=closed]:animate-fade-out',
        config.container,
        className
      )}
      {...props}
    />
  )
})
Toast.displayName = ToastPrimitives.Root.displayName

const ToastAction = React.forwardRef<
  React.ElementRef<typeof ToastPrimitives.Action>,
  React.ComponentPropsWithoutRef<typeof ToastPrimitives.Action>
>(({ className, ...props }, ref) => (
  <ToastPrimitives.Action
    ref={ref}
    className={cn(
      'inline-flex h-8 shrink-0 items-center justify-center rounded-md border bg-transparent px-3 text-sm font-medium transition-colors hover:bg-slate-100 focus:outline-none focus:ring-2 disabled:pointer-events-none disabled:opacity-50',
      className
    )}
    {...props}
  />
))
ToastAction.displayName = ToastPrimitives.Action.displayName

const ToastClose = React.forwardRef<
  React.ElementRef<typeof ToastPrimitives.Close>,
  React.ComponentPropsWithoutRef<typeof ToastPrimitives.Close>
>(({ className, ...props }, ref) => (
  <ToastPrimitives.Close
    ref={ref}
    className={cn(
      'absolute right-2 top-2 rounded-md p-1 text-slate-500 opacity-0 transition-opacity hover:text-slate-900 focus:opacity-100 focus:outline-none focus:ring-2 group-hover:opacity-100',
      className
    )}
    toast-close=""
    {...props}
  >
    <X className="h-4 w-4" />
  </ToastPrimitives.Close>
))
ToastClose.displayName = ToastPrimitives.Close.displayName

const ToastTitle = React.forwardRef<
  React.ElementRef<typeof ToastPrimitives.Title>,
  React.ComponentPropsWithoutRef<typeof ToastPrimitives.Title>
>(({ className, ...props }, ref) => (
  <ToastPrimitives.Title
    ref={ref}
    className={cn('text-sm font-semibold', className)}
    {...props}
  />
))
ToastTitle.displayName = ToastPrimitives.Title.displayName

const ToastDescription = React.forwardRef<
  React.ElementRef<typeof ToastPrimitives.Description>,
  React.ComponentPropsWithoutRef<typeof ToastPrimitives.Description>
>(({ className, ...props }, ref) => (
  <ToastPrimitives.Description
    ref={ref}
    className={cn('text-sm text-slate-500', className)}
    {...props}
  />
))
ToastDescription.displayName = ToastPrimitives.Description.displayName

type ToastProps = React.ComponentPropsWithoutRef<typeof Toast>
type ToastActionElement = React.ReactElement<typeof ToastAction>

export {
  type ToastProps,
  type ToastActionElement,
  ToastProvider,
  ToastViewport,
  Toast,
  ToastTitle,
  ToastDescription,
  ToastClose,
  ToastAction,
}
```

- [ ] **Step 2: Create toast hook**

```tsx
// ══════════════════════════════════════════════════════════════════════════════
// cekwajar.id — useToast Hook
// ══════════════════════════════════════════════════════════════════════════════

'use client'

import { useState, useCallback } from 'react'

export type ToastVariant = 'default' | 'success' | 'error' | 'warning' | 'info'

interface ToastItem {
  id: string
  title?: string
  description?: string
  variant?: ToastVariant
  duration?: number
}

let toastCount = 0

export function useToast() {
  const [toasts, setToasts] = useState<ToastItem[]>([])

  const toast = useCallback(({ title, description, variant = 'default', duration = 5000 }: Omit<ToastItem, 'id'>) => {
    const id = `toast-${++toastCount}`
    setToasts(prev => [...prev.slice(-2), { id, title, description, variant, duration }])
    setTimeout(() => {
      setToasts(prev => prev.filter(t => t.id !== id))
    }, duration)
    return id
  }, [])

  const dismiss = useCallback((id: string) => {
    setToasts(prev => prev.filter(t => t.id !== id))
  }, [])

  return { toast, dismiss, toasts }
}
```

Create: `src/hooks/use-toast.ts`

```tsx
// Re-export from the toast component file
export { useToast, type ToastVariant } from '@/components/ui/toast'
```

Actually, merge useToast into the toast.tsx file instead:

Add at the end of `src/components/ui/toast.tsx`:

```tsx
// ══════════════════════════════════════════════════════════════════════════════
// useToast hook
// ══════════════════════════════════════════════════════════════════════════════

export type ToastVariant = 'default' | 'success' | 'error' | 'warning' | 'info'

interface ToastItem {
  id: string
  title?: string
  description?: string
  variant?: ToastVariant
  duration?: number
}

let toastCount = 0

export function useToast() {
  const [toasts, setToasts] = useState<ToastItem[]>([])

  const toast = useCallback(({ title, description, variant = 'default', duration = 5000 }: Omit<ToastItem, 'id'>) => {
    const id = `toast-${++toastCount}`
    setToasts(prev => [...prev.slice(-2), { id, title, description, variant, duration }])
    setTimeout(() => {
      setToasts(prev => prev.filter(t => t.id !== id))
    }, duration)
    return id
  }, [])

  const dismiss = useCallback((id: string) => {
    setToasts(prev => prev.filter(t => t.id !== id))
  }, [])

  return { toast, dismiss, toasts }
}
```

- [ ] **Step 3: Create ToastContainer component**

```tsx
// Add to src/components/ui/toast.tsx
// ToastContainer — renders all active toasts

export function ToastContainer({ toasts, dismiss }: { toasts: ToastItem[], dismiss: (id: string) => void }) {
  return (
    <ToastProvider>
      {toasts.map(t => (
        <Toast key={t.id} variant={t.variant} onOpenChange={(open) => !open && dismiss(t.id)}>
          <div className="flex items-start gap-3">
            {t.variant && toastVariants[t.variant] && (
              <toastVariants[t.variant].icon className={cn('h-5 w-5 flex-shrink-0 mt-0.5', toastVariants[t.variant].iconClassName)} />
            )}
            <div className="grid gap-1">
              {t.title && <ToastTitle>{t.title}</ToastTitle>}
              {t.description && <ToastDescription>{t.description}</ToastDescription>}
            </div>
          </div>
          <ToastClose />
        </Toast>
      ))}
      <ToastViewport />
    </ToastProvider>
  )
}
```

- [ ] **Step 4: Commit**

```bash
git add src/components/ui/toast.tsx
git commit -m "feat(ui): add enhanced toast with slide-in animation and variants"
```

---

## PHASE 3: Civora-Style Shared Components

### Task 9: Civora Dashboard Skeleton

**Files:** Create: `src/components/shared/Skeletons/DashboardSkeleton.tsx`

- [ ] **Step 1: Create DashboardSkeleton**

```tsx
// ══════════════════════════════════════════════════════════════════════════════
// cekwajar.id — Dashboard Skeleton (Civora-style)
// ══════════════════════════════════════════════════════════════════════════════

import * as React from 'react'
import { Skeleton } from '@/components/ui/skeleton'

export function DashboardSkeleton() {
  return (
    <div className="space-y-6 animate-fade-in-up">
      {/* Page header */}
      <div className="space-y-2">
        <Skeleton className="h-8 w-48" />
        <Skeleton className="h-4 w-72" />
      </div>

      {/* Stats row — 4 cards */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {[...Array(4)].map((_, i) => (
          <div key={i} className="rounded-xl border border-slate-200 bg-white p-6 space-y-3">
            <div className="flex items-center justify-between">
              <Skeleton className="h-4 w-24" />
              <Skeleton className="h-4 w-4 rounded-full" />
            </div>
            <Skeleton className="h-8 w-20" />
            <Skeleton className="h-3 w-16" />
          </div>
        ))}
      </div>

      {/* Charts row — 2 charts */}
      <div className="grid gap-4 md:grid-cols-2">
        <div className="rounded-xl border border-slate-200 bg-white p-6 space-y-4">
          <Skeleton className="h-5 w-32" />
          <Skeleton className="h-40 w-full" />
        </div>
        <div className="rounded-xl border border-slate-200 bg-white p-6 space-y-4">
          <Skeleton className="h-5 w-32" />
          <div className="space-y-2">
            {[...Array(5)].map((_, i) => (
              <div key={i} className="flex items-center gap-3">
                <Skeleton className="h-8 w-8 rounded-full" />
                <Skeleton className="h-4 flex-1" />
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Table skeleton */}
      <div className="rounded-xl border border-slate-200 bg-white p-6 space-y-4">
        <div className="flex items-center justify-between">
          <Skeleton className="h-5 w-24" />
          <Skeleton className="h-9 w-64" />
        </div>
        <div className="space-y-3">
          <div className="flex gap-4 border-b border-slate-100 pb-3">
            {[...Array(5)].map((_, i) => (
              <Skeleton key={i} className="h-4 flex-1" />
            ))}
          </div>
          {[...Array(5)].map((_, i) => (
            <div key={i} className="flex gap-4 py-2">
              {[...Array(5)].map((_, j) => (
                <Skeleton key={j} className="h-4 flex-1" />
              ))}
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
```

- [ ] **Step 2: Create TableSkeleton**

```tsx
// Create: src/components/shared/Skeletons/TableSkeleton.tsx

import * as React from 'react'
import { Skeleton } from '@/components/ui/skeleton'

export function TableSkeleton({ rows = 8 }: { rows?: number }) {
  return (
    <div className="space-y-4 animate-fade-in-up">
      {/* Search bar */}
      <div className="flex items-center gap-4">
        <Skeleton className="h-9 w-64" />
        <Skeleton className="h-9 w-32" />
      </div>

      {/* Table */}
      <div className="rounded-xl border border-slate-200 bg-white">
        <div className="p-4">
          {/* Header row */}
          <div className="flex gap-4 border-b border-slate-100 pb-3 mb-3">
            {[...Array(5)].map((_, i) => (
              <Skeleton key={i} className="h-4 flex-1" />
            ))}
          </div>
          {/* Data rows */}
          {[...Array(rows)].map((_, i) => (
            <div key={i} className="flex gap-4 py-3 border-b border-slate-50 last:border-0">
              {[...Array(5)].map((_, j) => (
                <Skeleton key={j} className="h-4 flex-1" />
              ))}
            </div>
          ))}
        </div>
        {/* Pagination */}
        <div className="flex items-center justify-between border-t border-slate-100 p-4">
          <Skeleton className="h-4 w-24" />
          <div className="flex gap-2">
            {[...Array(5)].map((_, i) => (
              <Skeleton key={i} className="h-8 w-8" />
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}
```

- [ ] **Step 3: Create FormSkeleton**

```tsx
// Create: src/components/shared/Skeletons/FormSkeleton.tsx

import * as React from 'react'
import { Skeleton } from '@/components/ui/skeleton'
import { Button } from '@/components/ui/button'

export function FormSkeleton() {
  return (
    <div className="space-y-8 animate-fade-in-up">
      {/* Section 1 */}
      <div className="space-y-4">
        <div className="flex items-center gap-2">
          <Skeleton className="h-5 w-5 rounded" />
          <Skeleton className="h-5 w-24" />
        </div>
        <div className="grid gap-4 md:grid-cols-2">
          <div className="space-y-2">
            <Skeleton className="h-4 w-16" />
            <Skeleton className="h-10 w-full rounded-md" />
          </div>
          <div className="space-y-2">
            <Skeleton className="h-4 w-20" />
            <Skeleton className="h-10 w-full rounded-md" />
          </div>
        </div>
      </div>

      {/* Section 2 */}
      <div className="space-y-4">
        <div className="flex items-center gap-2">
          <Skeleton className="h-5 w-5 rounded" />
          <Skeleton className="h-5 w-20" />
        </div>
        <div className="grid gap-4 md:grid-cols-3">
          {[...Array(3)].map((_, i) => (
            <div key={i} className="space-y-2">
              <Skeleton className="h-4 w-12" />
              <Skeleton className="h-10 w-full rounded-md" />
            </div>
          ))}
        </div>
      </div>

      {/* Action buttons */}
      <div className="flex gap-3 justify-end pt-4">
        <Skeleton className="h-10 w-24 rounded-md" />
        <Skeleton className="h-10 w-32 rounded-md" />
      </div>
    </div>
  )
}
```

- [ ] **Step 4: Create Skeletons index**

```tsx
// Create: src/components/shared/Skeletons/index.ts

export { DashboardSkeleton } from './DashboardSkeleton'
export { TableSkeleton } from './TableSkeleton'
export { FormSkeleton } from './FormSkeleton'
```

- [ ] **Step 5: Commit**

```bash
git add src/components/shared/Skeletons/
git commit -m "feat(skeletons): add Civora-style dashboard, table, and form skeletons"
```

---

### Task 10: StatsGrid — Bento Dashboard Stats

**Files:** Create: `src/components/shared/StatsGrid/StatsGrid.tsx`

- [ ] **Step 1: Create StatsGrid component**

```tsx
// ══════════════════════════════════════════════════════════════════════════════
// cekwajar.id — StatsGrid Component (Civora-style bento grid)
// ══════════════════════════════════════════════════════════════════════════════

import * as React from 'react'
import { Card, CardContent } from '@/components/ui/card'
import { NumberTicker } from '@/components/ui/number-ticker'
import { TrendingUp, TrendingDown, Minus, type LucideIcon } from 'lucide-react'
import { cn } from '@/lib/utils'

interface StatItem {
  title: string
  value: number
  icon: LucideIcon
  prefix?: string
  suffix?: string
  trend?: number
  trendLabel?: string
  color?: 'emerald' | 'amber' | 'blue' | 'red' | 'purple'
}

interface StatsGridProps {
  stats: StatItem[]
  className?: string
}

const colorMap = {
  emerald: 'bg-emerald-50 border-emerald-100 text-emerald-600',
  amber: 'bg-amber-50 border-amber-100 text-amber-600',
  blue: 'bg-blue-50 border-blue-100 text-blue-600',
  red: 'bg-red-50 border-red-100 text-red-600',
  purple: 'bg-purple-50 border-purple-100 text-purple-600',
}

const iconColorMap = {
  emerald: 'text-emerald-500',
  amber: 'text-amber-500',
  blue: 'text-blue-500',
  red: 'text-red-500',
  purple: 'text-purple-500',
}

export function StatsGrid({ stats, className }: StatsGridProps) {
  return (
    <div className={cn('grid gap-4 md:grid-cols-2 lg:grid-cols-4', className)}>
      {stats.map((stat, i) => {
        const Icon = stat.icon
        const color = stat.color || 'emerald'
        const isPositive = stat.trend && stat.trend > 0
        const isNegative = stat.trend && stat.trend < 0
        const TrendIcon = isPositive ? TrendingUp : isNegative ? TrendingDown : Minus
        const trendColor = isPositive ? 'text-emerald-600' : isNegative ? 'text-red-600' : 'text-slate-400'

        return (
          <Card
            key={stat.title}
            hoverable
            className="relative overflow-hidden animate-fade-in-up"
            style={{ animationDelay: `${i * 100}ms` }}
          >
            <CardContent className="p-6">
              {/* Background gradient */}
              <div className="absolute inset-0 bg-gradient-to-tr from-slate-50 via-white to-slate-50/50 pointer-events-none" />

              <div className="relative">
                <div className="flex items-center justify-between mb-3">
                  <span className="text-sm font-medium text-slate-500">{stat.title}</span>
                  <div className={cn('p-2 rounded-lg', colorMap[color])}>
                    <Icon className={cn('h-4 w-4', iconColorMap[color])} />
                  </div>
                </div>

                <div className="text-2xl font-bold tracking-tight">
                  <NumberTicker
                    value={stat.value}
                    prefix={stat.prefix}
                    suffix={stat.suffix}
                    duration={1000}
                  />
                </div>

                {stat.trend !== undefined && (
                  <div className="flex items-center gap-1 mt-2">
                    <TrendIcon className={cn('h-3 w-3', trendColor)} />
                    <span className={cn('text-xs font-medium', trendColor)}>
                      {isPositive ? '+' : ''}{stat.trend}%
                    </span>
                    {stat.trendLabel && (
                      <span className="text-xs text-slate-400">{stat.trendLabel}</span>
                    )}
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        )
      })}
    </div>
  )
}
```

- [ ] **Step 2: Create index**

```tsx
// Create: src/components/shared/StatsGrid/index.ts

export { StatsGrid } from './StatsGrid'
```

- [ ] **Step 3: Commit**

```bash
git add src/components/shared/StatsGrid/
git commit -m "feat(dashboard): add Civora-style StatsGrid with NumberTicker and trends"
```

---

### Task 11: PageHeader Component

**Files:** Create: `src/components/shared/PageHeader/PageHeader.tsx`

- [ ] **Step 1: Create PageHeader**

```tsx
// ══════════════════════════════════════════════════════════════════════════════
// cekwajar.id — PageHeader Component
// Consistent page title + description with icon
// ══════════════════════════════════════════════════════════════════════════════

import * as React from 'react'
import { cn } from '@/lib/utils'
import type { LucideIcon } from 'lucide-react'

interface PageHeaderProps {
  title: string
  description?: string
  icon?: LucideIcon
  iconClassName?: string
  className?: string
  actions?: React.ReactNode
}

export function PageHeader({
  title,
  description,
  icon: Icon,
  iconClassName,
  className,
  actions,
}: PageHeaderProps) {
  return (
    <div className={cn('flex items-start justify-between gap-4 mb-6', className)}>
      <div className="flex items-center gap-3">
        {Icon && (
          <div className="p-2.5 rounded-xl bg-emerald-50 border border-emerald-100">
            <Icon className={cn('h-5 w-5 sm:h-6 sm:w-6 text-emerald-600', iconClassName)} />
          </div>
        )}
        <div>
          <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-slate-900">
            {title}
          </h1>
          {description && (
            <p className="text-sm sm:text-base text-slate-500 mt-0.5">{description}</p>
          )}
        </div>
      </div>
      {actions && <div className="flex items-center gap-2">{actions}</div>}
    </div>
  )
}
```

- [ ] **Step 2: Commit**

```bash
git add src/components/shared/PageHeader/PageHeader.tsx
git commit -m "feat(shared): add PageHeader component"
```

---

## PHASE 4: Theme Customizer (Shadboard-style)

### Task 12: Settings Context

**Files:** Create: `src/components/shared/Customizer/settings-context.tsx`

- [ ] **Step 1: Create settings context**

```tsx
// ══════════════════════════════════════════════════════════════════════════════
// cekwajar.id — Settings Context (Shadboard-style)
// Persists theme, radius, and color preferences in a cookie
// ══════════════════════════════════════════════════════════════════════════════

'use client'

import * as React from 'react'
import Cookies from 'js-cookie'

interface Settings {
  theme: 'light' | 'dark' | 'system'
  radius: number
  accentColor: string
}

interface SettingsContextValue {
  settings: Settings
  setTheme: (theme: Settings['theme']) => void
  setRadius: (radius: number) => void
  setAccentColor: (color: string) => void
}

const SettingsContext = React.createContext<SettingsContextValue | null>(null)

const COOKIE_KEY = 'cekwajar-settings'

const defaults: Settings = {
  theme: 'light',
  radius: 0.5,
  accentColor: 'emerald',
}

function getSettings(): Settings {
  try {
    const raw = Cookies.get(COOKIE_KEY)
    if (raw) return { ...defaults, ...JSON.parse(raw) }
  } catch {}
  return defaults
}

function saveSettings(s: Settings) {
  Cookies.set(COOKIE_KEY, JSON.stringify(s), { expires: 365, sameSite: 'lax' })
}

export function SettingsProvider({ children }: { children: React.ReactNode }) {
  const [settings, setSettingsState] = React.useState<Settings>(getSettings)

  const setSettings = React.useCallback((partial: Partial<Settings>) => {
    setSettingsState(prev => {
      const next = { ...prev, ...partial }
      saveSettings(next)
      return next
    })
  }, [])

  const setTheme = React.useCallback((theme: Settings['theme']) => {
    setSettings({ theme })
  }, [setSettings])

  const setRadius = React.useCallback((radius: number) => {
    setSettings({ radius })
  }, [setSettings])

  const setAccentColor = React.useCallback((accentColor: string) => {
    setSettings({ accentColor })
  }, [setSettings])

  // Apply theme class to <html> element
  React.useEffect(() => {
    const root = document.documentElement
    root.classList.remove('dark')
    if (settings.theme === 'dark') {
      root.classList.add('dark')
    }
    // Apply radius
    root.style.setProperty('--radius', `${settings.radius}rem`)
    // Apply accent color via CSS variable
    root.style.setProperty('--accent', `var(--${settings.accentColor}-500)`)
  }, [settings])

  return (
    <SettingsContext.Provider value={{ settings, setTheme, setRadius, setAccentColor }}>
      {children}
    </SettingsContext.Provider>
  )
}

export function useSettings() {
  const ctx = React.useContext(SettingsContext)
  if (!ctx) throw new Error('useSettings must be used within SettingsProvider')
  return ctx
}
```

- [ ] **Step 2: Update root layout to wrap with provider**

Modify `src/app/layout.tsx` to wrap with SettingsProvider:

Add import: `import { SettingsProvider } from '@/components/shared/Customizer/settings-context'`

Wrap children: `<SettingsProvider>{children}</SettingsProvider>`

```tsx
// Read the file first
// Then edit to add SettingsProvider around {children}
```

- [ ] **Step 3: Commit**

```bash
git add src/components/shared/Customizer/settings-context.tsx
git commit -m "feat(customizer): add settings context with cookie persistence"
```

---

### Task 13: Customizer Panel Component

**Files:** Create: `src/components/shared/Customizer/Customizer.tsx`

- [ ] **Step 1: Create Customizer panel**

```tsx
// ══════════════════════════════════════════════════════════════════════════════
// cekwajar.id — Theme Customizer Panel (Shadboard-style)
// Floating panel for live theme customization
// ══════════════════════════════════════════════════════════════════════════════

'use client'

import * as React from 'react'
import { Sheet, SheetContent, SheetTrigger } from '@/components/ui/sheet'
import { Button } from '@/components/ui/button'
import { useSettings } from './settings-context'
import { Settings, Palette, RotateCcw } from 'lucide-react'
import { cn } from '@/lib/utils'

const ACCENT_COLORS = [
  { name: 'emerald', label: 'Emerald', class: 'bg-emerald-500' },
  { name: 'blue', label: 'Blue', class: 'bg-blue-500' },
  { name: 'violet', label: 'Violet', class: 'bg-violet-500' },
  { name: 'amber', label: 'Amber', class: 'bg-amber-500' },
  { name: 'rose', label: 'Rose', class: 'bg-rose-500' },
  { name: 'slate', label: 'Slate', class: 'bg-slate-500' },
]

const RADII = [0, 0.3, 0.5, 0.75, 1]

const THEMES = [
  { value: 'light', label: 'Light' },
  { value: 'dark', label: 'Dark' },
  { value: 'system', label: 'System' },
] as const

export function Customizer() {
  const { settings, setTheme, setRadius, setAccentColor } = useSettings()
  const [open, setOpen] = React.useState(false)

  const handleReset = () => {
    setTheme('light')
    setRadius(0.5)
    setAccentColor('emerald')
  }

  return (
    <Sheet open={open} onOpenChange={setOpen}>
      <SheetTrigger asChild>
        <Button
          variant="outline"
          size="icon"
          className="fixed bottom-6 right-6 z-50 rounded-full shadow-lg hover:shadow-xl transition-shadow"
          aria-label="Customize theme"
        >
          <Settings className="h-4 w-4" />
        </Button>
      </SheetTrigger>
      <SheetContent side="end" className="w-80 p-6">
        <div className="space-y-6">
          {/* Header */}
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Palette className="h-5 w-5 text-emerald-600" />
              <h2 className="font-semibold">Kustomisasi</h2>
            </div>
            <Button variant="ghost" size="sm" onClick={handleReset}>
              <RotateCcw className="h-3 w-3 mr-1" />
              Reset
            </Button>
          </div>

          {/* Theme */}
          <div className="space-y-3">
            <label className="text-sm font-medium text-slate-700">Mode</label>
            <div className="flex gap-2">
              {THEMES.map(t => (
                <button
                  key={t.value}
                  onClick={() => setTheme(t.value)}
                  className={cn(
                    'flex-1 py-2 px-3 text-sm rounded-lg border transition-all',
                    settings.theme === t.value
                      ? 'border-emerald-500 bg-emerald-50 text-emerald-700'
                      : 'border-slate-200 hover:border-slate-300'
                  )}
                >
                  {t.label}
                </button>
              ))}
            </div>
          </div>

          {/* Accent Color */}
          <div className="space-y-3">
            <label className="text-sm font-medium text-slate-700">Warna Ak센</label>
            <div className="grid grid-cols-6 gap-2">
              {ACCENT_COLORS.map(c => (
                <button
                  key={c.name}
                  onClick={() => setAccentColor(c.name)}
                  className={cn(
                    'h-8 rounded-lg transition-all',
                    c.class,
                    settings.accentColor === c.name
                      ? 'ring-2 ring-offset-2 ring-slate-400 scale-110'
                      : 'hover:scale-105'
                  )}
                  title={c.label}
                />
              ))}
            </div>
          </div>

          {/* Border Radius */}
          <div className="space-y-3">
            <label className="text-sm font-medium text-slate-700">
              Border Radius — <span className="text-slate-500">{settings.radius}</span>
            </label>
            <div className="flex gap-2">
              {RADII.map(r => (
                <button
                  key={r}
                  onClick={() => setRadius(r)}
                  className={cn(
                    'flex-1 h-10 rounded-lg border-2 transition-all flex items-center justify-center text-xs font-medium',
                    settings.radius === r
                      ? 'border-emerald-500 bg-emerald-50 text-emerald-700'
                      : 'border-slate-200 hover:border-slate-300'
                  )}
                >
                  {r === 0 ? 'Sharp' : `${r}`}
                </button>
              ))}
            </div>
          </div>
        </div>
      </SheetContent>
    </Sheet>
  )
}
```

- [ ] **Step 2: Create Customizer index**

```tsx
// Create: src/components/shared/Customizer/index.ts

export { Customizer } from './Customizer'
export { SettingsProvider, useSettings } from './settings-context'
```

- [ ] **Step 3: Add Customizer to layout**

Modify `src/app/layout.tsx` to add `<Customizer />` before `</body>`:

```tsx
import { Customizer } from '@/components/shared/Customizer'
```

Add before closing body tag: `<Customizer />`

- [ ] **Step 4: Commit**

```bash
git add src/components/shared/Customizer/
git commit -m "feat(customizer): add Shadboard-style theme customizer panel"
```

---

## PHASE 5: Page Enhancements

### Task 14: Homepage Hero Enhancement

**Files:** Modify: `src/app/page.tsx`

- [ ] **Step 1: Read the current homepage**

Run: `cat cekwajar.id-20260415T173403Z-3-001/cekwajar.id/src/app/page.tsx`

- [ ] **Step 2: Identify the hero section and add enhancements**

The homepage needs:
- Staggered entrance animation on hero elements
- Trust signals section (shield, users, star icons)
- Animated tool cards with hover effects
- Better visual hierarchy with gradient background

Apply these changes:
1. Add `animate-fade-in-up` with `stagger-*` delays to hero text elements
2. Add gradient background to hero section
3. Add trust signals row below CTA
4. Add `group-hover:scale-x-100` animation to tool card top borders

Run: `cd cekwajar.id-20260415T173403Z-3-001/cekwajar.id && npx tsc --noEmit src/app/page.tsx 2>&1 | head -20`

Expected: No new errors introduced

- [ ] **Step 3: Commit**

```bash
git add src/app/page.tsx
git commit -m "feat(homepage): add staggered hero animations and trust signals"
```

---

### Task 15: Wajar-Slip Result Animations

**Files:** Modify: `src/app/wajar-slip/page.tsx`

- [ ] **Step 1: Read the current page**

Run: `wc -l cekwajar.id-20260415T173403Z-3-001/cekwajar.id/src/app/wajar-slip/page.tsx`

The page is 798 lines. Focus on the verdict result section (search for "verdict" or "SESUAI").

- [ ] **Step 2: Add NumberTicker to calculation rows**

Find the calculation table and replace static number displays with `<NumberTicker value={row.value} prefix="Rp " />`.

Find violation cards and add `animate-fade-in-up` with `style={{ animationDelay: }}`.

- [ ] **Step 3: Add confetti for clean verdict**

At the top of the component, add confetti trigger:

```tsx
// Confetti state for clean verdict
const [showConfetti, setShowConfetti] = useState(false)

useEffect(() => {
  if (verdict === 'SESUAI' && violations.length === 0) {
    setShowConfetti(true)
    const t = setTimeout(() => setShowConfetti(false), 3000)
    return () => clearTimeout(t)
  }
}, [verdict, violations])
```

Add confetti overlay near verdict display:

```tsx
{showConfetti && (
  <div className="fixed inset-0 pointer-events-none z-50">
    {[...Array(20)].map((_, i) => (
      <div
        key={i}
        className="absolute w-2 h-2 rounded-full animate-confetti"
        style={{
          left: `${Math.random() * 100}%`,
          top: '40%',
          backgroundColor: ['#10b981', '#f59e0b', '#8b5cf6'][i % 3],
          animationDelay: `${Math.random() * 300}ms`,
          animationDuration: `${600 + Math.random() * 400}ms`,
        }}
      />
    ))}
  </div>
)}
```

- [ ] **Step 4: Verify compilation**

Run: `cd cekwajar.id-20260415T173403Z-3-001/cekwajar.id && npx tsc --noEmit src/app/wajar-slip/page.tsx 2>&1 | head -30`

- [ ] **Step 5: Commit**

```bash
git add src/app/wajar-slip/page.tsx
git commit -m "feat(wajar-slip): add NumberTicker and confetti to verdict results"
```

---

### Task 16: Dashboard with StatsGrid and Skeleton

**Files:** Modify: `src/app/dashboard/page.tsx`

- [ ] **Step 1: Read the current dashboard**

Run: `cat cekwajar.id-20260415T173403Z-3-001/cekwajar.id/src/app/dashboard/page.tsx`

- [ ] **Step 2: Enhance dashboard with StatsGrid**

Replace static stat display with StatsGrid:

```tsx
import { StatsGrid } from '@/components/shared/StatsGrid'
import { DashboardSkeleton } from '@/components/shared/Skeletons'
import { PageHeader } from '@/components/shared/PageHeader'
import { FileText, AlertTriangle, TrendingDown, Sparkles } from 'lucide-react'
import { Suspense } from 'react'

// Example stats (replace with real data from Supabase)
const stats = [
  { title: 'Audit Bulan Ini', value: 12, icon: FileText, trend: 20, trendLabel: 'vs bulan lalu', color: 'emerald' as const },
  { title: 'Pelanggaran Ditemukan', value: 3, icon: AlertTriangle, trend: -25, trendLabel: 'vs bulan lalu', color: 'red' as const },
  { title: 'Total Hemat', value: 4750000, icon: TrendingDown, prefix: 'Rp ', trend: 15, trendLabel: 'vs bulan lalu', color: 'blue' as const },
  { title: 'Tier Saat Ini', value: 0, suffix: ' Pro', icon: Sparkles, trend: 0, color: 'purple' as const },
]

// Wrap content in Suspense + skeleton
<Suspense fallback={<DashboardSkeleton />}>
  <PageHeader
    title="Dashboard"
    description="Ringkasan aktivitas audit slip gaji kamu"
    icon={FileText}
  />
  <StatsGrid stats={stats} />
  {/* Audit history timeline */}
</Suspense>
```

- [ ] **Step 3: Commit**

```bash
git add src/app/dashboard/page.tsx
git commit -m "feat(dashboard): add StatsGrid with NumberTicker and DashboardSkeleton"
```

---

## PHASE 6: PremiumGate Redesign + Final Polish

### Task 17: PremiumGate Enhancement

**Files:** Modify: `src/components/shared/PremiumGate.tsx`

- [ ] **Step 1: Read the current PremiumGate**

Run: `cat cekwajar.id-20260415T173403Z-3-001/cekwajar.id/src/components/shared/PremiumGate.tsx`

- [ ] **Step 2: Replace with soft fade teaser version**

```tsx
// ══════════════════════════════════════════════════════════════════════════════
// cekwajar.id — PremiumGate Component
// Soft blur with tease — doesn't fully hide content
// ══════════════════════════════════════════════════════════════════════════════

'use client'

import * as React from 'react'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { Sparkles, Lock } from 'lucide-react'
import { cn } from '@/lib/utils'

interface PremiumGateProps {
  children: React.ReactNode
  isUnlocked: boolean
  requiredTier?: 'basic' | 'pro' | 'enterprise'
  title?: string
  description?: string
  className?: string
}

export function PremiumGate({
  children,
  isUnlocked,
  title = 'Fitur Premium',
  description = 'Upgrade ke Pro untuk akses fitur ini',
  className,
}: PremiumGateProps) {
  if (isUnlocked) return <>{children}</>

  return (
    <div className={cn('relative', className)}>
      {/* Teaser — show a blurred hint */}
      <div className="filter blur-sm pointer-events-none select-none opacity-50">
        {children}
      </div>

      {/* Overlay gate */}
      <div className="absolute inset-0 flex items-center justify-center">
        <Card className="w-full max-w-sm mx-4 animate-scale-in shadow-xl border-emerald-200">
          <CardContent className="p-6 text-center">
            <div className="w-14 h-14 bg-gradient-to-br from-violet-100 to-purple-100 rounded-2xl flex items-center justify-center mx-auto mb-4">
              <Sparkles className="h-7 w-7 text-violet-600" />
            </div>
            <h3 className="font-semibold text-lg mb-1">{title}</h3>
            <p className="text-sm text-slate-500 mb-4">{description}</p>
            <Button className="w-full gap-2 bg-gradient-to-r from-violet-600 to-purple-600 hover:from-violet-700 hover:to-purple-700">
              <Sparkles className="h-4 w-4" />
              Upgrade ke Pro
            </Button>
            <p className="text-xs text-slate-400 mt-3">
              Mulai dari Rp 49.000/bulan
            </p>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
```

- [ ] **Step 3: Commit**

```bash
git add src/components/shared/PremiumGate.tsx
git commit -m "feat(premium): redesign PremiumGate with blur-tease pattern"
```

---

### Task 18: Globals.css — Add Complete CSS Variables

**File:** Modify: `src/app/globals.css`

- [ ] **Step 1: Replace globals.css with full design system**

```css
@import "tailwindcss";
@import "./lib/animations.css";

/* ═══════════════════════════════════════════════════════════════════════════
 * cekwajar.id — Design System Variables
 * ═══════════════════════════════════════════════════════════════════════════ */

:root {
  /* Primary — Emerald: Trust, growth */
  --emerald-50:  #ecfdf5;
  --emerald-100: #d1fae5;
  --emerald-200: #a7f3d0;
  --emerald-300: #6ee7b7;
  --emerald-400: #34d399;
  --emerald-500: #10b981;
  --emerald-600: #059669;
  --emerald-700: #047857;
  --emerald-800: #065f46;
  --emerald-900: #064e3b;

  /* Accent — Amber: Highlights, warnings */
  --amber-50:    #fffbeb;
  --amber-100:   #fef3c7;
  --amber-200:  #fde68a;
  --amber-400:  #fbbf24;
  --amber-500:  #f59e0b;
  --amber-600:  #d97706;

  /* Premium — Violet */
  --violet-50:  #f5f3ff;
  --violet-100: #ede9fe;
  --violet-200: #ddd6fe;
  --violet-500: #8b5cf6;
  --violet-600: #7c3aed;

  /* Neutrals — Slate */
  --slate-50:   #f8fafc;
  --slate-100:  #f1f5f9;
  --slate-200:  #e2e8f0;
  --slate-300:  #cbd5e1;
  --slate-400:  #94a3b8;
  --slate-500:  #64748b;
  --slate-600:  #475569;
  --slate-700:  #334155;
  --slate-800:  #1e293b;
  --slate-900:  #0f172a;

  /* Semantic */
  --success:    var(--emerald-600);
  --warning:    var(--amber-500);
  --error:      #ef4444;
  --premium:    var(--violet-500);

  /* Surfaces */
  --background: var(--slate-50);
  --surface:   #ffffff;
  --surface-raised: #ffffff;

  /* Text */
  --text-primary:   var(--slate-900);
  --text-secondary: var(--slate-600);
  --text-muted:    var(--slate-400);
  --text-inverse:  #ffffff;

  /* Borders */
  --border:        var(--slate-200);
  --border-strong: var(--slate-300);
  --border-focus:  var(--emerald-500);

  /* Radius */
  --radius: 0.5rem;
}

@theme inline {
  --color-background: var(--background);
  --color-foreground: var(--text-primary);
  --font-sans: var(--font-geist-sans);
  --font-mono: var(--font-geist-mono);
  --color-emerald-50: var(--emerald-50);
  --color-emerald-100: var(--emerald-100);
  --color-emerald-200: var(--emerald-200);
  --color-emerald-300: var(--emerald-300);
  --color-emerald-400: var(--emerald-400);
  --color-emerald-500: var(--emerald-500);
  --color-emerald-600: var(--emerald-600);
  --color-emerald-700: var(--emerald-700);
  --color-emerald-800: var(--emerald-800);
  --color-emerald-900: var(--emerald-900);
  --color-amber-50: var(--amber-50);
  --color-amber-100: var(--amber-100);
  --color-amber-400: var(--amber-400);
  --color-amber-500: var(--amber-500);
  --color-amber-600: var(--amber-600);
  --color-violet-50: var(--violet-50);
  --color-violet-100: var(--violet-100);
  --color-violet-200: var(--violet-200);
  --color-violet-500: var(--violet-500);
  --color-violet-600: var(--violet-600);
  --color-slate-50: var(--slate-50);
  --color-slate-100: var(--slate-100);
  --color-slate-200: var(--slate-200);
  --color-slate-300: var(--slate-300);
  --color-slate-400: var(--slate-400);
  --color-slate-500: var(--slate-500);
  --color-slate-600: var(--slate-600);
  --color-slate-700: var(--slate-700);
  --color-slate-800: var(--slate-800);
  --color-slate-900: var(--slate-900);
  --radius: calc(var(--radius) * 1rem);
}

/* Dark mode */
.dark {
  --background: var(--slate-900);
  --surface: var(--slate-800);
  --text-primary: var(--slate-50);
  --text-secondary: var(--slate-300);
  --text-muted: var(--slate-500);
  --border: var(--slate-700);
}

body {
  background: var(--background);
  color: var(--text-primary);
  font-family: var(--font-sans);
}

/* Focus ring */
*:focus-visible {
  outline: 2px solid var(--emerald-500);
  outline-offset: 2px;
}
```

- [ ] **Step 2: Verify the build still works**

Run: `cd cekwajar.id-20260415T173403Z-3-001/cekwajar.id && npm run build 2>&1 | tail -30`

Expected: Successful build

- [ ] **Step 3: Commit**

```bash
git add src/app/globals.css
git commit -m "feat(design-system): add complete CSS variable design system"
```

---

## Self-Review Checklist

- [ ] All tasks have exact file paths
- [ ] All code is complete (no TODOs or placeholders)
- [ ] All new files are imported/used in existing files
- [ ] Button variants match the spec (premium, outline hover, etc.)
- [ ] Skeleton shimmer is in animations.css and used by Skeleton component
- [ ] NumberTicker uses `id-ID` locale for Indonesian number formatting
- [ ] Settings context uses js-cookie (already in package.json)
- [ ] Customizer panel is added to layout
- [ ] PremiumGate uses blur-tease pattern instead of full block
- [ ] All animations respect `prefers-reduced-motion`

---

## Spec Coverage Map

| Spec Section | Tasks |
|---|---|
| 1.1 Color Palette | Task 18 (globals.css) |
| 1.2 Typography | Task 18 (globals.css — inherits Geist) |
| 1.3 Number Formatting | Task 6 (NumberTicker), Task 7 (IDRInput) |
| 1.4 Shadow System | Task 18 (globals.css) |
| 1.5 Border Radius | Task 12-13 (Settings context + Customizer) |
| 1.6 Motion System | Task 1 (animations.css) |
| 2.1 Button | Task 2 |
| 2.2 Card | Task 3 |
| 2.3 Input | Task 7 (IDRInput) |
| 2.4 Badge | Task 4 |
| 2.5 Toast | Task 8 |
| 2.6 Skeleton | Tasks 5, 9 |
| 2.7 NumberTicker | Task 6 |
| 3.1 Homepage | Task 14 |
| 3.2 Wajar Slip | Task 15 |
| 3.3 Dashboard | Task 16 |
| 3.6 Pricing | Task 12-13 (Customizer) |
| 4. Micro-interactions | Tasks 1-5, 6, 8 |
| 5. Theme Customizer | Tasks 12-13 |
| 6. Accessibility | Task 1 (prefers-reduced-motion in animations.css) |

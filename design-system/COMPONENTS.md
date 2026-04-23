# Component Patterns — COMPONENTS.md

> **Version:** 1.0.0 | **Last updated:** 2026-04-16
> **Design level:** Linear / Vercel / Stripe production quality

---

## Table of Contents

1. [Card](#1-card)
2. [Button](#2-button)
3. [Form Inputs](#3-form-inputs)
4. [Empty States](#4-empty-states)
5. [Badge / Tag](#5-badge--tag)
6. [Avatar](#6-avatar)
7. [Skeleton Loader](#7-skeleton-loader)
8. [Toast / Notification](#8-toast--notification)

---

## 1. Card

### Design Rules
- **Separation:** Surface elevation (background color shift) NOT colored borders
- **Border radius:** `--radius-lg` (0.75rem) for cards
- **Border:** `1px solid oklch(from var(--color-text) l c h / 0.08)` — alpha-blended, never solid gray
- **Padding:** `var(--space-6)` internal padding
- **Inner radius:** `calc(var(--radius-lg) - var(--space-3))` — maintains visual consistency

### Light Mode
```css
.card {
  background-color: var(--color-surface);
  border: 1px solid oklch(from var(--color-text) l c h / 0.08);
  border-radius: var(--radius-lg);
  padding: var(--space-6);
  box-shadow: var(--shadow-sm);
  transition: transform var(--duration-fast) var(--ease-spring),
              box-shadow var(--duration-fast) var(--ease-default);
}

.card:hover {
  transform: translateY(-4px);
  box-shadow: var(--shadow-md);
}
```

### Dark Mode
```css
[data-theme="dark"] .card {
  background-color: var(--color-surface);
  border-color: oklch(from var(--color-text) l c h / 0.12);
}
```

### States

| State | Visual Treatment |
|---|---|
| Default | `--shadow-sm`, no transform |
| Hover | `translateY(-4px)`, `--shadow-md` |
| Active / Pressed | `translateY(0)`, `scale(0.99)`, `--shadow-sm` |
| Disabled | 50% opacity, `cursor: not-allowed` |
| Loading | Skeleton overlay (see Skeleton Loader) |

### React/TSX

```tsx
interface CardProps {
  children: React.ReactNode;
  variant?: 'default' | 'bordered' | 'elevated';
  padding?: 'sm' | 'md' | 'lg';
  className?: string;
  onClick?: () => void;
}

export function Card({
  children,
  variant = 'default',
  padding = 'md',
  className = '',
  onClick,
}: CardProps) {
  const paddingClass = {
    sm: 'p-4',
    md: 'p-6',
    lg: 'p-8',
  }[padding];

  return (
    <div
      role={onClick ? 'button' : undefined}
      onClick={onClick}
      onKeyDown={onClick ? (e) => e.key === 'Enter' && onClick() : undefined}
      tabIndex={onClick ? 0 : undefined}
      className={cn(
        'bg-surface border-border rounded-lg',
        'transition-all duration-normal ease-spring',
        'hover:shadow-md hover:-translate-y-1',
        'active:translate-y-0 active:scale-[0.99]',
        paddingClass,
        className
      )}
    >
      {children}
    </div>
  );
}
```

---

## 2. Button

### Design Rules
- **Primary button:** Solid `--color-primary` background, white text, `--radius-md`, **44px min height**
- **Secondary button:** Transparent background, `--color-border` border, `--color-text` text
- **Ghost button:** Transparent background, no border, `--color-text-muted` text
- **Destructive:** Solid `--color-error` background
- **NEVER gradient buttons** — solid accent only
- **Font weight:** 500 (medium)
- **Horizontal padding:** `--space-4` minimum

### Button Tokens
```css
.btn-primary {
  background-color: var(--color-primary);
  color: #ffffff;
  border-radius: var(--radius-md);
  min-height: 44px;
  padding-inline: var(--space-4);
  font-weight: 500;
  transition: background-color var(--duration-fast) var(--ease-default),
              transform var(--duration-micro) var(--ease-spring);
}

.btn-primary:hover:not(:disabled) {
  background-color: var(--color-primary-hover);
}

.btn-primary:active:not(:disabled) {
  transform: scale(0.97);
}

.btn-secondary {
  background-color: transparent;
  color: var(--color-text);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  min-height: 44px;
  padding-inline: var(--space-4);
  font-weight: 500;
}

.btn-ghost {
  background-color: transparent;
  color: var(--color-text-muted);
  border-radius: var(--radius-md);
  min-height: 44px;
  padding-inline: var(--space-3);
}

.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  pointer-events: none;
}
```

### React/TSX

```tsx
import { Loader2 } from 'lucide-react';
import { cn } from '@/lib/utils'; // your cn() utility

type ButtonVariant = 'primary' | 'secondary' | 'ghost' | 'destructive';
type ButtonSize = 'sm' | 'md' | 'lg' | 'icon';

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
  size?: ButtonSize;
  loading?: boolean;
  leftIcon?: React.ReactNode;
  rightIcon?: React.ReactNode;
}

const variantClasses: Record<ButtonVariant, string> = {
  primary: 'bg-primary text-white hover:bg-primary-hover',
  secondary: 'bg-transparent border border-border text-text hover:bg-surface-offset',
  ghost: 'bg-transparent text-text-muted hover:bg-surface-offset hover:text-text',
  destructive: 'bg-error text-white hover:opacity-90',
};

const sizeClasses: Record<ButtonSize, string> = {
  sm: 'h-8 px-3 text-sm rounded-md',
  md: 'h-11 px-4 text-sm rounded-md',
  lg: 'h-12 px-6 text-base rounded-lg',
  icon: 'h-10 w-10 p-0 rounded-md',
};

export function Button({
  variant = 'primary',
  size = 'md',
  loading = false,
  leftIcon,
  rightIcon,
  className,
  children,
  disabled,
  ...props
}: ButtonProps) {
  return (
    <button
      disabled={disabled || loading}
      className={cn(
        'inline-flex items-center justify-center gap-2 font-medium',
        'transition-all duration-fast ease-spring',
        'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary',
        'disabled:opacity-50 disabled:cursor-not-allowed disabled:pointer-events-none',
        variantClasses[variant],
        sizeClasses[size],
        className
      )}
      {...props}
    >
      {loading ? (
        <Loader2 className="h-4 w-4 animate-spin" />
      ) : leftIcon ? (
        leftIcon
      ) : null}
      {children}
      {!loading && rightIcon}
    </button>
  );
}
```

### Dark Mode

```css
[data-theme="dark"] .btn-primary {
  background-color: var(--color-primary);
}
[data-theme="dark"] .btn-primary:hover:not(:disabled) {
  background-color: var(--color-primary-hover);
}
[data-theme="dark"] .btn-secondary {
  background-color: var(--color-surface);
  border-color: var(--color-border);
}
```

### Accessibility

- Minimum 44×44px touch target
- `focus-visible` ring: 3px solid `--color-primary`, 2px offset
- Loading state disables button AND shows spinner — never just spinner
- Icon-only buttons require `aria-label`

```tsx
// Icon-only button
<Button variant="ghost" size="icon" aria-label="Close dialog">
  <X className="h-4 w-4" />
</Button>
```

---

## 3. Form Inputs

### Design Rules
- **Every input must have a visible `<label>`** — never placeholder-only
- **Validation:** on blur, NOT on every keystroke
- **Error message:** below the specific field in `--color-error`, specific message
- **Height:** 44px minimum
- **Border radius:** `--radius-md`
- **Focus:** border transitions to `--color-primary`, subtle ring

### Input Tokens
```css
.input {
  height: 44px;
  padding-inline: var(--space-3);
  background-color: var(--color-input-bg);
  border: 1px solid var(--color-input-border);
  border-radius: var(--radius-md);
  color: var(--color-text);
  font-size: var(--text-base);
  transition: border-color var(--duration-fast) var(--ease-out),
              box-shadow var(--duration-fast) var(--ease-out);
}

.input:focus-visible {
  outline: none;
  border-color: var(--color-primary);
  box-shadow: 0 0 0 3px oklch(from var(--color-primary) l c h / 0.2);
}

.input::placeholder {
  color: var(--color-text-faint);
}

.input:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  background-color: var(--color-surface-offset);
}

.input-error {
  border-color: var(--color-error);
}

.input-error:focus-visible {
  border-color: var(--color-error);
  box-shadow: 0 0 0 3px oklch(from var(--color-error) l c h / 0.2);
}
```

### React/TSX — Form Components

```tsx
interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label: string;
  error?: string;
  hint?: string;
}

export const Input = React.forwardRef<HTMLInputElement, InputProps>(
  ({ label, error, hint, id, className, ...props }, ref) => {
    const inputId = id ?? label.toLowerCase().replace(/\s+/g, '-');
    const errorId = `${inputId}-error`;
    const hintId = `${inputId}-hint`;

    return (
      <div className="flex flex-col gap-1.5">
        <label
          htmlFor={inputId}
          className="text-sm font-medium text-text"
        >
          {label}
          {props.required && (
            <span className="text-error ml-1" aria-hidden="true">*</span>
          )}
        </label>

        <input
          ref={ref}
          id={inputId}
          aria-invalid={error ? 'true' : 'false'}
          aria-describedby={error ? errorId : hint ? hintId : undefined}
          className={cn(
            'h-11 px-3 bg-surface border border-border rounded-md',
            'text-base text-text placeholder:text-text-faint',
            'transition-all duration-fast ease-out',
            'focus:outline-none focus:border-primary focus:ring-2',
            'focus:ring-primary/20',
            'disabled:opacity-50 disabled:cursor-not-allowed',
            error && 'border-error focus:border-error focus:ring-error/20',
            className
          )}
          {...props}
        />

        {hint && !error && (
          <p id={hintId} className="text-xs text-text-muted">
            {hint}
          </p>
        )}

        {error && (
          <p id={errorId} role="alert" className="text-sm text-error flex items-center gap-1">
            <XCircle className="h-3 w-3" />
            {error}
          </p>
        )}
      </div>
    );
  }
);
Input.displayName = 'Input';
```

### Validation Behavior

```tsx
// Controlled form with blur validation
function ContactForm() {
  const [email, setEmail] = useState('');
  const [emailError, setEmailError] = useState('');
  const [touched, setTouched] = useState(false);

  const validateEmail = (value: string) => {
    if (!value) return 'Email is required';
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value))
      return 'Enter a valid email address';
    return '';
  };

  // Validate on BLUR, not on change
  const handleBlur = () => {
    setTouched(true);
    setEmailError(validateEmail(email));
  };

  const showError = touched && emailError;

  return (
    <form>
      <Input
        label="Email address"
        type="email"
        value={email}
        onChange={(e) => setEmail(e.target.value)}
        onBlur={handleBlur}
        error={showError ? emailError : undefined}
        required
      />
    </form>
  );
}
```

---

## 4. Empty States

**Every empty state needs three things:**
1. **Warm, specific message** — not "No items"
2. **Primary action** — what to do next
3. **Visual** — icon or illustration

### Pattern

```tsx
interface EmptyStateProps {
  icon: React.ReactNode;
  title: string;
  description: string;
  action?: {
    label: string;
    onClick: () => void;
  };
}

export function EmptyState({ icon, title, description, action }: EmptyStateProps) {
  return (
    <div className="flex flex-col items-center justify-center text-center py-16 px-8">
      <div className="text-text-faint mb-4">
        {icon}
      </div>
      <h3 className="text-lg font-medium text-text mb-2">
        {title}
      </h3>
      <p className="text-sm text-text-muted max-w-xs mb-6">
        {description}
      </p>
      {action && (
        <Button variant="primary" onClick={action.onClick}>
          {action.label}
        </Button>
      )}
    </div>
  );
}

// Usage examples:
<EmptyState
  icon={<Inbox className="h-12 w-12" />}
  title="No emails yet"
  description="When you receive emails, they'll appear here. Send your first message to get started."
  action={{ label: 'Compose email', onClick: () => {} }}
/>

<EmptyState
  icon={<Search className="h-12 w-12" />}
  title="No search results"
  description="We couldn't find anything matching your search. Try different keywords or check for typos."
/>
```

---

## 5. Badge / Tag

```tsx
type BadgeVariant = 'default' | 'success' | 'warning' | 'error' | 'info';

const badgeClasses: Record<BadgeVariant, string> = {
  default: 'bg-surface-offset text-text-muted',
  success: 'bg-success-bg text-success',
  warning: 'bg-warning-bg text-warning',
  error:   'bg-error-bg text-error',
  info:    'bg-info-bg text-info',
};

interface BadgeProps {
  variant?: BadgeVariant;
  children: React.ReactNode;
  className?: string;
}

export function Badge({ variant = 'default', children, className }: BadgeProps) {
  return (
    <span
      className={cn(
        'inline-flex items-center px-2.5 py-0.5',
        'rounded-full text-xs font-medium',
        badgeClasses[variant],
        className
      )}
    >
      {children}
    </span>
  );
}

// Usage
<Badge variant="success">Active</Badge>
<Badge variant="warning">Pending</Badge>
<Badge variant="error">Failed</Badge>
```

---

## 6. Avatar

```tsx
interface AvatarProps {
  src?: string;
  alt: string;
  fallback: string; // 2-letter initials
  size?: 'sm' | 'md' | 'lg' | 'xl';
  className?: string;
}

const sizeClasses = {
  sm:  'h-8 w-8 text-xs',
  md:  'h-10 w-10 text-sm',
  lg:  'h-12 w-12 text-base',
  xl:  'h-16 w-16 text-lg',
};

export function Avatar({ src, alt, fallback, size = 'md', className }: AvatarProps) {
  return (
    <div
      className={cn(
        'relative inline-flex items-center justify-center rounded-full',
        'bg-surface-offset text-text-muted font-medium',
        'overflow-hidden',
        sizeClasses[size],
        className
      )}
    >
      {src ? (
        <img
          src={src}
          alt={alt}
          className="h-full w-full object-cover"
          loading="lazy"
        />
      ) : (
        <span>{fallback}</span>
      )}
    </div>
  );
}
```

---

## 7. Skeleton Loader

Skeleton loaders communicate **loading state without spinners.** Use shimmer animation.

```css
@keyframes shimmer {
  0%   { background-position: -200% 0; }
  100% { background-position: 200% 0; }
}

.skeleton {
  background: linear-gradient(
    90deg,
    var(--color-skeleton) 25%,
    var(--color-skeleton-shine) 50%,
    var(--color-skeleton) 75%
  );
  background-size: 200% 100%;
  animation: shimmer 1.5s var(--ease-linear) infinite;
  border-radius: var(--radius-md);
}
```

```tsx
export function CardSkeleton() {
  return (
    <div className="bg-surface border border-border rounded-lg p-6 space-y-4">
      <div className="flex items-center gap-3">
        <div className="skeleton h-10 w-10 rounded-full" />
        <div className="space-y-2 flex-1">
          <div className="skeleton h-4 w-3/4 rounded" />
          <div className="skeleton h-3 w-1/2 rounded" />
        </div>
      </div>
      <div className="space-y-2">
        <div className="skeleton h-3 w-full rounded" />
        <div className="skeleton h-3 w-5/6 rounded" />
        <div className="skeleton h-3 w-4/6 rounded" />
      </div>
      <div className="flex gap-2">
        <div className="skeleton h-8 w-20 rounded-md" />
        <div className="skeleton h-8 w-20 rounded-md" />
      </div>
    </div>
  );
}
```

---

## 8. Toast / Notification

Use **sonner** (Emil Kowalski) — accessible, lightweight, beautiful.

```tsx
import { Toaster, toast } from 'sonner';

export function ToasterProvider() {
  return (
    <Toaster
      position="bottom-right"
      toastOptions={{
        unstyled: true,
        classNames: {
          toast: 'bg-surface border border-border rounded-lg shadow-lg p-4',
          title: 'text-text font-medium text-sm',
          description: 'text-text-muted text-sm',
          success: 'border-l-4 border-l-success',
          error: 'border-l-4 border-l-error',
          warning: 'border-l-4 border-l-warning',
          info: 'border-l-4 border-l-primary',
        },
      }}
    />
  );
}

// Usage
toast.success('Changes saved');
toast.error('Failed to save — check your connection');
toast.warning('You have unsaved changes');
toast.info('Update available');
```

---

*Last reviewed: 2026-04-16 | Component philosophy: Radix primitives + Tailwind styling, no opinionated UI library defaults*

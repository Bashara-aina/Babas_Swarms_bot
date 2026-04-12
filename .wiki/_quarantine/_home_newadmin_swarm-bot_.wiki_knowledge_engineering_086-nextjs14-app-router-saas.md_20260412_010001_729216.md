---
{
  "page_path": "/home/newadmin/swarm-bot/.wiki/knowledge/engineering/086-nextjs14-app-router-saas.md",
  "reason": "daily_fast_scan: score=0.000 < 0.3",
  "score": 0.0,
  "quarantined_at": "2026-04-12T01:00:01.729239"
}
---

---
source_id: 086
title: "Next.js 14 App Router SaaS Architecture Patterns"
source_type: ENGINEERING
authority: INDUSTRY
url: "https://nextjs.org/docs/app"
last_verified: "2026-04-11"
tags: [nextjs, app-router, saas, multi-tenant, server-components, react]
cekwajar_impact: HIGH
legion_can_act: YES
---

# Next.js 14 App Router SaaS Architecture Patterns

## Why This Matters for cekwajar.id
cekwajar.id's frontend is built on Next.js 14 App Router. Understanding the correct architecture patterns for multi-tenancy, server/client component boundaries, and data fetching ensures maintainable code, proper auth integration with Supabase, and optimal performance for the payroll/HR SaaS product.

## Core Knowledge

### App Router vs Pages Router
App Router (Next.js 13+) is now the default and recommended approach:
- **Server Components**: Default, reducing client-side JS bundle
- **Client Components**: Use `'use client'` directive for interactivity
- **Route Groups**: `()` for organization without affecting URL
- **Layouts**: Shared UI across routes with nested composition
- **Server Actions**: Mutate data directly without API routes

### Recommended SaaS Project Structure
```
app/
├── (auth)/
│   ├── login/page.tsx
│   ├── register/page.tsx
│   └── layout.tsx
├── (dashboard)/
│   ├── layout.tsx          # Auth check wrapper
│   ├── employees/
│   │   ├── page.tsx        # List employees
│   │   └── [id]/page.tsx   # Employee detail
│   ├── payroll/
│   │   └── page.tsx
│   └── settings/
│       └── page.tsx
├── api/
│   └── webhooks/
│       └── midtrans/route.ts
├── layout.tsx              # Root layout
└── page.tsx               # Landing/marketing
```

### Multi-Tenant Pattern with Subdomains
```typescript
// middleware.ts - Edge middleware for tenant resolution
import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

export function middleware(request: NextRequest) {
  const hostname = request.headers.get('host') || '';
  const subdomain = hostname.split('.')[0];
  
  // Skip for main domain, api, etc.
  if (subdomain === 'www' || subdomain === 'api') {
    return NextResponse.next();
  }
  
  // Add tenant context to headers for downstream use
  const response = NextResponse.next();
  response.headers.set('x-tenant-id', subdomain);
  return response;
}

export const config = {
  matcher: ['/((?!_next/static|_next/image|favicon.ico).*)'],
};
```

### Server Components Data Fetching
```typescript
// app/(dashboard)/employees/page.tsx
import { createServerClient } from '@supabase/ssr';
import { cookies } from 'next/headers';

export default async function EmployeesPage() {
  const cookieStore = await cookies();
  const supabase = createServerClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
    {
      cookies: {
        getAll: () => cookieStore.getAll(),
        setAll: (cookiesToSet) => {
          cookiesToSet.forEach(({ name, value, options }) => {
            cookieStore.set(name, value, options);
          });
        },
      },
    }
  );
  
  const { data: employees } = await supabase
    .from('employees')
    .select('*')
    .order('created_at', { ascending: false });
    
  return <EmployeeList employees={employees ?? []} />;
}
```

### Client Components for Interactivity
```typescript
// components/EmployeeForm.tsx
'use client';

import { useState } from 'react';
import { createClient } from '@supabase/supabase-js';

export function EmployeeForm({ companyId }: { companyId: string }) {
  const [loading, setLoading] = useState(false);
  const supabase = createClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!
  );
  
  async function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setLoading(true);
    const formData = new FormData(e.currentTarget);
    
    await supabase.from('employees').insert({
      company_id: companyId,
      name: formData.get('name'),
      email: formData.get('email'),
      // ... other fields
    });
    
    setLoading(false);
  }
  
  return (
    <form onSubmit={handleSubmit}>
      <input name="name" required />
      <input name="email" type="email" required />
      <button disabled={loading}>
        {loading ? 'Saving...' : 'Add Employee'}
      </button>
    </form>
  );
}
```

### Server Actions for Mutations
```typescript
// app/actions/employees.ts
'use server';

import { createServerClient } from '@supabase/ssr';
import { revalidatePath } from 'next/cache';

export async function createEmployee(formData: FormData) {
  const cookieStore = await cookies();
  const supabase = createServerClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
    {
      cookies: {
        getAll: () => cookieStore.getAll(),
      },
    }
  );
  
  const { data: { user } } = await supabase.auth.getUser();
  if (!user) throw new Error('Unauthorized');
  
  const { error } = await supabase.from('employees').insert({
    company_id: user.id,
    name: formData.get('name'),
    email: formData.get('email'),
  });
  
  if (error) throw new Error(error.message);
  
  revalidatePath('/employees');
}
```

## Edge Cases and Common Mistakes

### Common Mistakes
1. **Overusing Client Components**: Default to Server Components, only use `'use client'` when needed
2. **Missing Suspense boundaries**: Wrap async components in `<Suspense>`
3. **Auth in Server Components**: Always verify with `supabase.auth.getUser()`, not just `getSession()`
4. **Cookies in Server Components**: Use `import { cookies } from 'next/headers'` (async)
5. **Mutating State in Server Components**: Use Server Actions, not client-side state

### ISR Considerations for Payroll Data
```typescript
// For semi-static payroll reports
export const revalidate = 3600; // Revalidate every hour

export default async function PayrollReport() {
  // This page will be cached and revalidated hourly
}
```

## cekwajar.id Implementation Notes

- **File to update**: `app/` directory structure
- **Function to modify/create**: Server Actions in `app/actions/`, Server Components for data fetching
- **Data source to query**: Supabase `employees`, `payroll`, `bpjs_contributions` tables
- **Update frequency**: On code changes only
- **Legion action**: Can implement new pages and Server Actions autonomously

## Monetization Angle
Modern React Server Components architecture reduces bundle size by 40-60%, improving Core Web Vitals and SEO — critical for organic customer acquisition.

## Sources and Cross-References
- Official URL: https://nextjs.org/docs/app
- Next.js App Router Tutorial: https://nextjs.org/docs/app/building-your-application
- Makerkit Next.js SaaS Patterns: https://makerkit.dev/courses/nextjs-app-router/introduction

---
source_id: 088
title: "Vercel Zero Downtime Deployment with Edge Middleware"
source_type: ENGINEERING
authority: INDUSTRY
url: "https://vercel.com/docs/routing-middleware"
last_verified: "2026-04-11"
tags: [vercel, deployment, edge-middleware, zero-downtime, blue-green, nextjs]
cekwajar_impact: HIGH
legion_can_act: YES
---

# Vercel Zero Downtime Deployment with Edge Middleware

## Why This Matters for cekwajar.id
cekwajar.id is a SaaS payroll platform — downtime means users cannot access payslips, submit reports, or process payroll. Vercel's Edge Middleware enables:
- Blue-green deployments (no downtime)
- A/B feature rollouts
- Geo-based routing
- Authentication pre-checks before pages load

## Core Knowledge

### Edge Middleware vs Serverless Functions

| Feature | Edge Middleware | Serverless Functions |
|---------|-----------------|---------------------|
| Runtime | V8 (Edge) | Node.js |
| Cold Start | < 5ms | 100-500ms |
| Geographic | Runs at edge | Runs in selected region |
| Use Case | Auth, redirects, rewrites | Complex business logic |

### Middleware Execution Order
```
Request → Edge Middleware → Route → Server Component → Response
```

### Basic Middleware Structure
```typescript
// middleware.ts (root of project)
import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

export function middleware(request: NextRequest) {
  // Check for auth token
  const token = request.cookies.get('auth-token');
  
  if (!token && request.nextUrl.pathname.startsWith('/dashboard')) {
    // Redirect to login
    return NextResponse.redirect(new URL('/login', request.url));
  }
  
  // Continue to route
  return NextResponse.next();
}

export const config = {
  matcher: ['/dashboard/:path*', '/api/:path*'],
};
```

### Blue-Green Deployment Pattern
```typescript
// middleware.ts - Route users to stable deployment
import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

export function middleware(request: NextRequest) {
  // Check if this is a dashboard route
  if (request.nextUrl.pathname.startsWith('/dashboard')) {
    // Get deployment info from header (set by Vercel)
    const deploymentId = request.headers.get('x-vercel-deployment-id');
    
    // For critical routes, ensure we're on a stable deployment
    // This can be extended with feature flags
    const response = NextResponse.next();
    
    // Add deployment tracking
    response.headers.set('x-deployment-id', deploymentId || 'unknown');
    
    return response;
  }
  
  return NextResponse.next();
}
```

### Rewrites with Edge Middleware
```typescript
// middleware.ts - Multi-tenant subdomain routing
import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

export function middleware(request: NextRequest) {
  const hostname = request.headers.get('host') || '';
  const subdomain = hostname.split('.')[0];
  
  // Skip for main domain and vercel preview URLs
  if (
    subdomain === 'www' ||
    subdomain === 'api' ||
    hostname.includes('vercel.app')
  ) {
    return NextResponse.next();
  }
  
  // Rewrite tenant requests to dashboard with tenant context
  const url = request.nextUrl.clone();
  url.pathname = `/dashboard/tenant/${subdomain}${url.pathname}`;
  
  return NextResponse.rewrite(url);
}
```

### Authentication Pre-check
```typescript
// middleware.ts - JWT verification at edge
import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';
import { jwtVerify } from 'jose';

const JWT_SECRET = new TextEncoder().encode(
  process.env.JWT_SECRET
);

export async function middleware(request: NextRequest) {
  const token = request.cookies.get('supabase-auth-token')?.value;
  
  if (request.nextUrl.pathname.startsWith('/dashboard')) {
    if (!token) {
      return NextResponse.redirect(new URL('/login', request.url));
    }
    
    try {
      // Verify JWT at the edge
      const { payload } = await jwtVerify(token, JWT_SECRET);
      
      // Add user info to headers for downstream
      const response = NextResponse.next();
      response.headers.set('x-user-id', payload.sub || '');
      return response;
    } catch {
      // Invalid token, redirect to login
      return NextResponse.redirect(new URL('/login', request.url));
    }
  }
  
  return NextResponse.next();
}
```

### Deployment Configuration
```json
// vercel.json
{
  "framework": "nextjs",
  "buildCommand": "npm run build",
  "devCommand": "npm run dev",
  "installCommand": "npm install",
  "regions": ["sin1"],
  "runtime": "nodejs20.x",
  "routes": [
    {
      "src": "/api/webhooks/(.*)",
      "dest": "/api/webhooks/$1"
    }
  ]
}
```

### Health Check Endpoint
```typescript
// app/api/health/route.ts
import { NextResponse } from 'next/server';

export async function GET() {
  return NextResponse.json({
    status: 'ok',
    timestamp: new Date().toISOString(),
    deployment: process.env.VERCEL_GIT_COMMIT_SHA || 'local',
  });
}
```

## Edge Cases and Common Mistakes

### Common Mistakes
1. **Middleware on static assets**: Exclude with `config.matcher`
2. **Missing edge-compatible imports**: No Node.js APIs at edge (use `jose` for JWT)
3. **Blocking operations**: Edge middleware is async, avoid synchronous operations
4. **Large response bodies**: Edge middleware shouldn't process response bodies
5. **Missing CORS headers**: API routes need explicit CORS handling

### Edge Runtime Limitations
- No filesystem access
- No native Node.js modules (use polyfills)
- Limited CPU time (50ms soft limit)
- No WebSockets (use Serverless for that)

## cekwajar.id Implementation Notes

- **File to update**: `middleware.ts` (root), `vercel.json`
- **Function to modify/create**: Auth middleware, tenant routing middleware
- **Data source to query**: JWT tokens, cookies
- **Update frequency**: On deployment
- **Legion action**: Can implement middleware, needs Vercel CLI for local testing

## Monetization Angle
Zero-downtime deployments enable:
- Continuous delivery without user impact
- Slower rollout of features (reduces bug blast radius)
- Better reliability for enterprise customers (SLA requirements)

## Sources and Cross-References
- Official URL: https://vercel.com/docs/routing-middleware
- Vercel Blue-Green: https://vercel.com/kb/guide/blue_green_deployments_on_vercel
- Edge Runtime: https://vercel.com/docs/edge-network/edge-runtime

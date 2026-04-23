---
title: Api Rate Limiting
type: concept
status: active
tags:
- /
- home
- newadmin
- swarm-bot
- engineering
created: '2026-04-14'
updated: '2026-04-14'
summary: 'Without rate limiting:'
wikilinks: []
confidence: medium
source: research
---

# API Rate Limiting for Next.js Supabase SaaS

## Why This Matters for cekwajar.id
Without rate limiting:
- Malicious actors can brute-force login endpoints
- Abusive users can spam API endpoints
- Costly Supabase API calls multiply uncontrollably
- Data scraping competitors can steal employee data

Rate limiting is your **first line of defense** against API abuse.

## Core Knowledge

### Rate Limiting Strategies

| Strategy | Description | Best For |
|----------|-------------|----------|
| Token Bucket | Burst allowed, then limited | API endpoints |
| Sliding Window | Rolling time window | User-facing APIs |
| Fixed Window | Fixed time periods | Simple use cases |
| IP-based | Per-IP limits | Anonymous endpoints |

### Supabase Auth Rate Limits

Supabase Auth has built-in rate limits on authentication endpoints:

| Endpoint | Limited By | Default Limit |
|----------|------------|---------------|
| `/auth/v1/signup` | Per user + project-wide | 10/hour email |
| `/auth/v1/otp` | Per user | 10/hour OTP |
| `/auth/v1/recover` | Per user | 5/hour |
| `/auth/v1/verify` | IP Address | 100/hour |
| `/auth/v1/token` (refresh) | IP Address | 50/hour |

Configure in Supabase Dashboard: **Authentication > Rate Limits**

### Custom Rate Limiting Middleware

```typescript
// lib/rate-limit.ts
import { Ratelimit } from '@upstash/ratelimit';
import { Redis } from '@upstash/redis';

// For Supabase Edge Functions or Serverless
const ratelimit = new Ratelimit({
 redis: Redis.fromEnv(),
 limiter: Ratelimit.slidingWindow(10, '10 s'), // 10 requests per 10 seconds
 analytics: true,
 prefix: 'ratelimit:api',
});

export async function checkRateLimit(identifier: string) {
 const result = await ratelimit.limit(identifier);
 
 return {
 success: result.success,
 remaining: result.remaining,
 reset: result.reset,
 headers: {
 'X-RateLimit-Limit': '10',
 'X-RateLimit-Remaining': result.remaining.toString(),
 'X-RateLimit-Reset': result.reset.toString(),
 'Retry-After': result.retryAfter?.toString() || '0',
 },
 };
}
```

### Next.js Route Handler Rate Limiting

```typescript
// app/api/employees/route.ts
import { checkRateLimit } from '@/lib/rate-limit';
import { NextResponse } from 'next/server';
import { createServerClient } from '@supabase/ssr';
import { cookies } from 'next/headers';

export async function GET(request: Request) {
 const ip = request.headers.get('x-forwarded-for') || 'anonymous';
 
 // Rate limit by IP for anonymous, by user ID for authenticated
 const identifier = ip;
 const { success, headers, remaining } = await checkRateLimit(identifier);
 
 if (!success) {
 return NextResponse.json(
 { error: 'Too many requests' },
 { status: 429, headers }
 );
 }
 
 // Continue with authenticated request
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
 
 const { data: employees } = await supabase
 .from('employees')
 .select('*')
 .order('created_at', { ascending: false });
 
 return NextResponse.json({ employees }, { headers });
}
```

### Upstash Redis Integration

```bash
npm install @upstash/ratelimit @upstash/redis
```

```typescript
// .env.local
UPSTASH_REDIS_REST_URL=your-redis-url
UPSTASH_REDIS_REST_TOKEN=your-token
```

### Supabase Row-Level Rate Limiting

For Supabase, you can also implement rate limiting via database functions:

```sql
-- Create rate limiting table
CREATE TABLE IF NOT EXISTS api_usage (
 id uuid primary key default gen_random_uuid(),
 user_id uuid references auth.users(id),
 endpoint text not null,
 request_count int default 1,
 window_start timestamptz default now(),
 unique(user_id, endpoint, window_start)
);

-- Function to check and increment usage
CREATE OR REPLACE FUNCTION check_api_limit(
 p_user_id uuid,
 p_endpoint text,
 p_limit int DEFAULT 100,
 p_window interval DEFAULT '1 hour'
) RETURNS boolean
LANGUAGE plpgsql
AS $$
DECLARE
 current_count int;
BEGIN
 -- Get current count for user/endpoint in window
 SELECT request_count INTO current_count
 FROM api_usage
 WHERE user_id = p_user_id
 AND endpoint = p_endpoint
 AND window_start > now() - p_window;
 
 IF current_count IS NULL THEN
 -- First request in window
 INSERT INTO api_usage (user_id, endpoint)
 VALUES (p_user_id, p_endpoint);
 RETURN TRUE;
 ELSIF current_count < p_limit THEN
 -- Increment count
 UPDATE api_usage
 SET request_count = request_count + 1
 WHERE user_id = p_user_id
 AND endpoint = p_endpoint
 AND window_start > now() - p_window;
 RETURN TRUE;
 ELSE
 -- Limit exceeded
 RETURN FALSE;
 END IF;
END;
$$;

-- Apply rate limit in RLS policy
CREATE POLICY "Rate limited employee access"
ON employees FOR SELECT
TO authenticated
USING (
 check_api_limit(auth.uid(), 'employees', 100, '1 hour'::interval)
);
```

### Middleware-Level Rate Limiting for All Routes

```typescript
// middleware.ts
import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

// Simple in-memory rate limiter for edge
const ipRequests = new Map<string, { count: number; reset: number }>();

export function middleware(request: NextRequest) {
 const ip = request.headers.get('x-forwarded-for') || 'anonymous';
 const now = Date.now();
 const windowMs = 60 * 1000; // 1 minute
 const maxRequests = 60; // 60 per minute
 
 const record = ipRequests.get(ip);
 
 if (record) {
 // Reset if window passed
 if (now > record.reset) {
 ipRequests.set(ip, { count: 1, reset: now + windowMs });
 } else if (record.count >= maxRequests) {
 return new NextResponse(
 JSON.stringify({ error: 'Too many requests' }),
 { status: 429, headers: { 'Content-Type': 'application/json' } }
 );
 } else {
 record.count++;
 }
 } else {
 ipRequests.set(ip, { count: 1, reset: now + windowMs });
 }
 
 return NextResponse.next();
}

export const config = {
 matcher: ['/api/:path*'],
};
```

### Error Responses

Always return proper 429 responses:

```typescript
// Consistent error format
function rateLimitExceeded(retryAfter: number) {
 return NextResponse.json(
 {
 error: 'Too Many Requests',
 message: 'API rate limit exceeded. Please slow down.',
 retryAfter,
 },
 {
 status: 429,
 headers: {
 'Retry-After': retryAfter.toString(),
 'X-RateLimit-Limit': '60',
 'X-RateLimit-Remaining': '0',
 },
 }
 );
}
```

## Edge Cases and Common Mistakes

### Common Mistakes
1. **No rate limiting on auth endpoints**: Login/signup
2. **Rate limits too aggressive**: Users get locked out
3. **Not returning 429**: Silently failing doesn't help clients
4. **IP spoofing**: Don't trust x-forwarded-for without validation
5. **No monitoring**: Track rate limit hits for anomaly detection

### Production Checklist
- [ ] Rate limiting on all `/api/` routes
- [ ] Stricter limits on auth endpoints (signup, login, password reset)
- [ ] 429 responses include `Retry-After` header
- [ ] Logs track rate limit violations
- [ ] Monitoring/alerting for spike in 429s

## cekwajar.id Implementation Notes

- **File to update**: `middleware.ts`, `lib/rate-limit.ts`, API route handlers
- **Function to modify/create**: `checkRateLimit()`, rate limit middleware
- **Data source to query**: Upstash Redis or Supabase `api_usage` table
- **Update frequency**: Continuous (no updates needed once configured)
- **Legion action**: Can implement rate limiting middleware, needs Bashara review for limits

## Monetization Angle
Rate limiting protects:
- Supabase API costs from runaway usage
- Prevents service disruption from DDoS
- Enables fair pricing tiers (different limits per plan)

## Sources and Cross-References
- Supabase Rate Limits: https://supabase.com/docs/guides/auth/rate-limits
- Upstash Ratelimit: https://upstash.com/docs/ratelimit
- OWASP Rate Limiting: https://owasp.org/www-community/Security_Expectations

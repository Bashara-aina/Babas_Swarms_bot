// ==============================================================================
// cekwajar.id — In-memory rate limiter
// Stage 10: swap for Upstash/Vercel KV when multi-instance deploy lands
// ==============================================================================

import type { NextRequest } from 'next/server'
import { NextResponse } from 'next/server'

interface Entry {
  count: number
  resetAt: number
}

const buckets = new Map<string, Map<string, Entry>>()

export interface RateLimitOptions {
  limit: number
  windowMs: number
}

export interface RateLimitResult {
  ok: boolean
  remaining: number
  resetAt: number
}

function getClientIp(request: NextRequest): string {
  const forwarded = request.headers.get('x-forwarded-for')
  if (forwarded) return forwarded.split(',')[0].trim()
  return request.headers.get('x-real-ip') ?? 'unknown'
}

export function rateLimit(
  request: NextRequest,
  key: string,
  options: RateLimitOptions,
): RateLimitResult {
  const ip = getClientIp(request)
  const identifier = `${ip}:${key}`
  let bucket = buckets.get(key)
  if (!bucket) {
    bucket = new Map()
    buckets.set(key, bucket)
  }

  const now = Date.now()
  const entry = bucket.get(identifier)
  if (!entry || now > entry.resetAt) {
    const resetAt = now + options.windowMs
    bucket.set(identifier, { count: 1, resetAt })
    return { ok: true, remaining: options.limit - 1, resetAt }
  }

  if (entry.count >= options.limit) {
    return { ok: false, remaining: 0, resetAt: entry.resetAt }
  }

  entry.count += 1
  return {
    ok: true,
    remaining: options.limit - entry.count,
    resetAt: entry.resetAt,
  }
}

export function rateLimitResponse(
  result: RateLimitResult,
  message = 'Terlalu banyak permintaan. Coba lagi beberapa saat lagi.',
) {
  const retryAfter = Math.max(
    0,
    Math.ceil((result.resetAt - Date.now()) / 1000),
  )
  return NextResponse.json(
    {
      success: false,
      error: { code: 'RATE_LIMITED', message },
    },
    {
      status: 429,
      headers: {
        'Retry-After': String(retryAfter),
        'X-RateLimit-Remaining': '0',
        'X-RateLimit-Reset': String(Math.ceil(result.resetAt / 1000)),
      },
    },
  )
}

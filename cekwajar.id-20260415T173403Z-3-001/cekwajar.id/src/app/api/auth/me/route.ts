// ══════════════════════════════════════════════════════════════════════════════
// cekwajar.id — GET /api/auth/me
// Returns current user tier (for client-side tier detection)
// ══════════════════════════════════════════════════════════════════════════════

import { NextResponse } from 'next/server'
import { getCurrentUser } from '@/lib/auth/getCurrentUser'

export const runtime = 'nodejs'

export async function GET() {
  const { tier, profile } = await getCurrentUser()

  return NextResponse.json({
    tier,
    profile: profile ? {
      email: profile.email,
      full_name: profile.full_name,
      subscription_tier: profile.subscription_tier,
    } : null,
  })
}

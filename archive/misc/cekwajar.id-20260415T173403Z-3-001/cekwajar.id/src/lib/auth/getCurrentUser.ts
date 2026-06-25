// ══════════════════════════════════════════════════════════════════════════════
// cekwajar.id — Server-side Current User Helper
// Used in all API routes and server components
// ══════════════════════════════════════════════════════════════════════════════

import { createClient } from '@/lib/supabase/server'
import type { SubscriptionTier } from '@/types'

export interface CurrentUser {
  user: import('@supabase/supabase-js').User
  tier: SubscriptionTier
  profile: {
    id: string
    email: string
    full_name: string | null
    subscription_tier: SubscriptionTier
    created_at: string
    updated_at: string
  } | null
  supabase: Awaited<ReturnType<typeof createClient>>
}

/**
 * Get the currently authenticated user and their subscription tier.
 * Returns null user if not authenticated.
 */
export async function getCurrentUser(): Promise<CurrentUser | { user: null; tier: 'free'; profile: null; supabase: Awaited<ReturnType<typeof createClient>> }> {
  const supabase = await createClient()

  const { data: { user } } = await supabase.auth.getUser()

  if (!user) {
    return { user: null, tier: 'free', profile: null, supabase }
  }

  const { data: profile } = await supabase
    .from('user_profiles')
    .select('*')
    .eq('id', user.id)
    .single()

  return {
    user,
    tier: (profile?.subscription_tier as SubscriptionTier) ?? 'free',
    profile: profile as CurrentUser['profile'],
    supabase,
  }
}

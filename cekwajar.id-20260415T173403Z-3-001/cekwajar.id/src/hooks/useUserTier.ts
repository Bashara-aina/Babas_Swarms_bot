'use client'

// ==============================================================================
// cekwajar.id — useUserTier Hook
// Client-side subscription tier detection from DB
// ==============================================================================

import { useState, useEffect } from 'react'
import { createClient } from '@/lib/supabase/client'
import type { SubscriptionTier } from '@/types'

export function useUserTier(): SubscriptionTier {
  const [tier, setTier] = useState<SubscriptionTier>('free')
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    async function fetchTier() {
      try {
        const supabase = createClient()
        const { data: { user } } = await supabase.auth.getUser()

        if (!user) {
          setTier('free')
          setLoading(false)
          return
        }

        const { data } = await supabase
          .from('user_profiles')
          .select('subscription_tier')
          .eq('id', user.id)
          .single()

        setTier((data?.subscription_tier ?? 'free') as SubscriptionTier)
      } catch {
        setTier('free')
      } finally {
        setLoading(false)
      }
    }

    fetchTier()
  }, [])

  return tier
}

export function useUserTierWithLoading(): { tier: SubscriptionTier; loading: boolean } {
  const [tier, setTier] = useState<SubscriptionTier>('free')
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    async function fetchTier() {
      try {
        const supabase = createClient()
        const { data: { user } } = await supabase.auth.getUser()

        if (!user) {
          setTier('free')
          setLoading(false)
          return
        }

        const { data } = await supabase
          .from('user_profiles')
          .select('subscription_tier')
          .eq('id', user.id)
          .single()

        setTier((data?.subscription_tier ?? 'free') as SubscriptionTier)
      } catch {
        setTier('free')
      } finally {
        setLoading(false)
      }
    }

    fetchTier()
  }, [])

  return { tier, loading }
}

'use client'

// ==============================================================================
// cekwajar.id — Cookie Consent Banner
// Shown on first visit; stores consent in localStorage + DB if logged in
// ==============================================================================

import { useState, useEffect } from 'react'
import Link from 'next/link'
import { Button } from '@/components/ui/button'
import { createClient } from '@/lib/supabase/client'

export function CookieConsent() {
  const [visible, setVisible] = useState(false)

  useEffect(() => {
    const consent = localStorage.getItem('cookie_consent')
    if (!consent) {
      setVisible(true)
    }
  }, [])

  async function recordConsent(status: 'accepted' | 'rejected') {
    try {
      const supabase = createClient()
      const { data: { user } } = await supabase.auth.getUser()

      if (!user) return

      await supabase.from('user_consents').insert({
        user_id: user.id,
        consent_type: 'cookie',
        consent_status: status,
        ip_address: null, // Not collecting IP for privacy
        user_agent: navigator.userAgent,
      })
    } catch {
      // Non-critical: consent still stored in localStorage
    }
  }

  if (!visible) return null

  function handleAccept() {
    localStorage.setItem('cookie_consent', 'accepted')
    setVisible(false)
    recordConsent('accepted')
  }

  function handleDecline() {
    localStorage.setItem('cookie_consent', 'rejected')
    setVisible(false)
    recordConsent('rejected')
  }

  return (
    <div className="fixed bottom-0 left-0 right-0 z-50 border-t bg-white p-4 shadow-lg">
      <div className="mx-auto flex max-w-5xl flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <p className="text-sm text-slate-600">
          Kami menggunakan cookie untuk meningkatkan pengalaman kamu.{' '}
          <Link href="/privacy-policy" className="underline hover:text-emerald-600">
            Baca Kebijakan Privasi kami
          </Link>
          .
        </p>
        <div className="flex gap-2">
          <Button size="sm" variant="outline" onClick={handleDecline}>
            Tolak
          </Button>
          <Button size="sm" className="bg-emerald-600 hover:bg-emerald-700" onClick={handleAccept}>
            Setuju
          </Button>
        </div>
      </div>
    </div>
  )
}

// ══════════════════════════════════════════════════════════════════════════════
// cekwajar.id — Auth Server Actions
// ══════════════════════════════════════════════════════════════════════════════

'use server'

import { createClient } from '@/lib/supabase/server'
import { redirect } from 'next/navigation'

/**
 * Sign out the current user and redirect to home page.
 */
export async function signOut() {
  const supabase = await createClient()
  await supabase.auth.signOut()
  redirect('/')
}

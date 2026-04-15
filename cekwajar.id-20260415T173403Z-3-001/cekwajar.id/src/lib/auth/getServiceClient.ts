// ══════════════════════════════════════════════════════════════════════════════
// cekwajar.id — Service Role Supabase Client
// For webhooks and Edge Functions — bypasses RLS
// ══════════════════════════════════════════════════════════════════════════════

import { createClient } from '@supabase/supabase-js'

/**
 * Returns a Supabase client with service role key.
 * Use ONLY in webhook handlers and server-side Edge Functions.
 * NEVER use in client-side code or browser.
 */
export function getServiceClient() {
  return createClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.SUPABASE_SERVICE_ROLE_KEY!,
    {
      auth: {
        // Service role client should never persist sessions
        persistSession: false,
        autoRefreshToken: false,
      },
    }
  )
}

// ══════════════════════════════════════════════════════════════════════════════
// cekwajar.id — Sign Up Page
// Email magic link registration
// ══════════════════════════════════════════════════════════════════════════════

'use client'

import { useState } from 'react'
import Link from 'next/link'
import { createClient } from '@/lib/supabase/client'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { CheckCircle } from 'lucide-react'

export default function SignupPage() {
  const [email, setEmail] = useState('')
  const [loading, setLoading] = useState(false)
  const [magicLinkSent, setMagicLinkSent] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function handleSignup(e: React.FormEvent) {
    e.preventDefault()
    if (!email) return

    setLoading(true)
    setError(null)
    const supabase = createClient()
    const { error } = await supabase.auth.signInWithOtp({
      email,
      options: {
        emailRedirectTo: `${window.location.origin}/auth/callback`,
        data: { email },
      },
    })
    setLoading(false)

    if (error) {
      setError(error.message)
    } else {
      setMagicLinkSent(true)
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-muted px-4">
      <div className="w-full max-w-md space-y-6">
        {/* Logo */}
        <div className="text-center">
          <Link href="/" className="inline-flex items-center gap-2">
            <svg viewBox="0 0 24 24" className="h-8 w-8 text-emerald-600" fill="none" stroke="currentColor" strokeWidth="2">
              <rect x="3" y="3" width="7" height="7" rx="1" />
              <rect x="14" y="3" width="7" height="7" rx="1" />
              <rect x="14" y="14" width="7" height="7" rx="1" />
              <rect x="3" y="14" width="7" height="7" rx="1" />
            </svg>
            <span className="text-xl font-bold text-emerald-700">cekwajar.id</span>
          </Link>
        </div>

        <Card className="border-border shadow-sm">
          <CardHeader className="text-center">
            <CardTitle className="text-2xl font-bold">Daftar Gratis</CardTitle>
            <CardDescription>
              Tidak perlu kartu kredit. Mulai dalam 30 detik.
            </CardDescription>
          </CardHeader>

          <CardContent className="space-y-4">
            {magicLinkSent ? (
              <Alert className="border-emerald-200 bg-emerald-50">
                <CheckCircle className="h-4 w-4 text-emerald-600" />
                <AlertDescription className="text-emerald-700">
                  <strong>Cek inbox kamu!</strong> Link aktivasi dikirim ke <strong>{email}</strong>.
                </AlertDescription>
              </Alert>
            ) : (
              <form onSubmit={handleSignup} className="space-y-3">
                <div>
                  <Input
                    type="email"
                    placeholder="email@kamu.com"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    required
                    className="h-11"
                    disabled={loading}
                  />
                </div>
                {error && (
                  <p className="text-sm text-red-500">{error}</p>
                )}
                <Button
                  type="submit"
                  className="w-full bg-emerald-600 hover:bg-emerald-700"
                  disabled={loading}
                >
                  {loading ? 'Menyimpan...' : 'Daftar dengan Email'}
                </Button>
              </form>
            )}

            {/* Already have account */}
            <p className="text-center text-sm text-muted-foreground">
              Sudah punya akun?{' '}
              <Link href="/auth/login" className="font-medium text-emerald-600 hover:underline">
                Masuk di sini
              </Link>
            </p>

            {/* Terms notice */}
            <p className="text-center text-xs text-muted-foreground">
              Dengan mendaftar, kamu setuju dengan{' '}
              <Link href="/privacy-policy" className="underline hover:text-emerald-600">
                Kebijakan Privasi
              </Link>{' '}
              dan{' '}
              <Link href="/terms" className="underline hover:text-emerald-600">
                Syarat &amp; Ketentuan
              </Link>
              .
            </p>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}

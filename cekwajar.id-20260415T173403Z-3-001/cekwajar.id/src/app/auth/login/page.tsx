// ══════════════════════════════════════════════════════════════════════════════
// cekwajar.id — Login Page
// Email magic link + Google OAuth
// ══════════════════════════════════════════════════════════════════════════════

'use client'

import { useState, Suspense } from 'react'
import { useSearchParams, useRouter } from 'next/navigation'
import Link from 'next/link'
import { createClient } from '@/lib/supabase/client'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { CheckCircle } from 'lucide-react'

// Google SVG icon
const GoogleIcon = () => (
  <svg viewBox="0 0 24 24" className="h-5 w-5">
    <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" fill="#4285F4" />
    <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853" />
    <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" fill="#FBBC05" />
    <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335" />
  </svg>
)

// Inner component that uses useSearchParams (must be inside Suspense)
function LoginForm() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const errorParam = searchParams.get('error')

  const [email, setEmail] = useState('')
  const [loading, setLoading] = useState(false)
  const [magicLinkSent, setMagicLinkSent] = useState(false)
  const [error, setError] = useState<string | null>(
    errorParam === 'auth_failed' ? 'Autentikasi gagal. Silakan coba lagi.' : null
  )

  async function handleGoogleLogin() {
    const supabase = createClient()
    const { error } = await supabase.auth.signInWithOAuth({
      provider: 'google',
      options: {
        redirectTo: `${window.location.origin}/auth/callback`,
      },
    })
    if (error) setError(error.message)
  }

  async function handleMagicLink(e: React.FormEvent) {
    e.preventDefault()
    if (!email) return

    setLoading(true)
    setError(null)
    const supabase = createClient()
    const { error } = await supabase.auth.signInWithOtp({
      email,
      options: {
        emailRedirectTo: `${window.location.origin}/auth/callback`,
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
    <Card className="border-slate-200 shadow-sm">
      <CardHeader className="text-center">
        <CardTitle className="text-2xl font-bold">Masuk ke cekwajar.id</CardTitle>
        <CardDescription>
          Gratis selamanya untuk fitur dasar.
        </CardDescription>
      </CardHeader>

      <CardContent className="space-y-4">
        {/* Google OAuth */}
        <Button
          onClick={handleGoogleLogin}
          variant="outline"
          className="w-full gap-2 border-slate-300 hover:bg-slate-50"
        >
          <GoogleIcon />
          Masuk dengan Google
        </Button>

        {/* Divider */}
        <div className="relative">
          <div className="absolute inset-0 flex items-center">
            <div className="w-full border-t border-slate-200" />
          </div>
          <div className="relative flex justify-center text-xs uppercase">
            <span className="bg-white px-2 text-slate-400">atau</span>
          </div>
        </div>

        {/* Magic link form */}
        {magicLinkSent ? (
          <Alert className="border-emerald-200 bg-emerald-50">
            <CheckCircle className="h-4 w-4 text-emerald-600" />
            <AlertDescription className="text-emerald-700">
              <strong>Cek inbox kamu!</strong> Link masuk dikirim ke <strong>{email}</strong>.
              Klik link tersebut untuk masuk.
            </AlertDescription>
          </Alert>
        ) : (
          <form onSubmit={handleMagicLink} className="space-y-3">
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
              {loading ? 'Mengirim...' : 'Kirim Link Masuk'}
            </Button>
          </form>
        )}

        {/* Privacy notice */}
        <p className="text-center text-xs text-slate-400">
          Dengan masuk, kamu setuju dengan{' '}
          <Link href="/privacy" className="underline hover:text-slate-600">
            Kebijakan Privasi
          </Link>{' '}
          dan{' '}
          <Link href="/terms" className="underline hover:text-slate-600">
            Syarat &amp; Ketentuan
          </Link>
          .
        </p>
      </CardContent>
    </Card>
  )
}

export default function LoginPage() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-slate-50 px-4">
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

        <Suspense fallback={
          <Card className="border-slate-200 shadow-sm">
            <CardContent className="flex items-center justify-center py-12">
              <p className="text-sm text-slate-400">Memuat...</p>
            </CardContent>
          </Card>
        }>
          <LoginForm />
        </Suspense>

        {/* Sign up link */}
        <p className="text-center text-sm text-slate-500">
          Belum punya akun?{' '}
          <Link href="/auth/signup" className="font-medium text-emerald-600 hover:underline">
            Daftar gratis
          </Link>
        </p>
      </div>
    </div>
  )
}

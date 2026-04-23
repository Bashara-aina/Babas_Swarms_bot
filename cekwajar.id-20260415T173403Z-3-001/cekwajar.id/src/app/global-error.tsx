'use client'

import { useEffect } from 'react'

export default function GlobalError({
  error,
  reset,
}: {
  error: Error & { digest?: string }
  reset: () => void
}) {
  useEffect(() => {
    console.error(error)
  }, [error])

  return (
    <html lang="id">
      <body
        style={{
          fontFamily:
            'system-ui, -apple-system, BlinkMacSystemFont, sans-serif',
          margin: 0,
          minHeight: '100vh',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          padding: '3rem 1rem',
          background: '#f8fafc',
          color: '#0f172a',
        }}
      >
        <div style={{ maxWidth: '28rem', width: '100%', textAlign: 'center' }}>
          <h1 style={{ fontSize: '1.5rem', fontWeight: 700, margin: 0 }}>
            Aplikasi mengalami masalah
          </h1>
          <p style={{ marginTop: '0.5rem', color: '#475569' }}>
            Terjadi error tak terduga. Muat ulang halaman untuk mencoba lagi.
          </p>
          {error.digest && (
            <p
              style={{
                marginTop: '0.5rem',
                fontSize: '0.75rem',
                color: '#64748b',
                fontFamily: 'monospace',
              }}
            >
              Ref: {error.digest}
            </p>
          )}
          <button
            onClick={reset}
            style={{
              marginTop: '1.5rem',
              padding: '0.625rem 1.25rem',
              background: '#059669',
              color: '#fff',
              border: 0,
              borderRadius: '0.5rem',
              fontSize: '0.875rem',
              fontWeight: 500,
              cursor: 'pointer',
            }}
          >
            Muat ulang
          </button>
        </div>
      </body>
    </html>
  )
}

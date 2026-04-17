'use client'

// ══════════════════════════════════════════════════════════════════════════════
// cekwajar.id — Settings Context
// Persists theme/radius/accent to cookies via js-cookie
// ══════════════════════════════════════════════════════════════════════════════

import * as React from 'react'
import Cookies from 'js-cookie'

const COOKIE_KEY = 'cekwajar-settings'

export type AccentColor = 'emerald' | 'amber' | 'violet' | 'blue'
export type BorderRadius = 'none' | 'sm' | 'md' | 'lg' | 'xl' | 'full'

interface Settings {
  accentColor: AccentColor
  borderRadius: BorderRadius
}

interface SettingsContextValue {
  settings: Settings
  setAccentColor: (color: AccentColor) => void
  setBorderRadius: (radius: BorderRadius) => void
  isMounted: boolean
}

const defaultSettings: Settings = {
  accentColor: 'emerald',
  borderRadius: 'lg',
}

const SettingsContext = React.createContext<SettingsContextValue | null>(null)

function loadFromCookie(): Settings {
  try {
    const raw = Cookies.get(COOKIE_KEY)
    if (raw) {
      return { ...defaultSettings, ...JSON.parse(raw) }
    }
  } catch {
    // ignore parse errors
  }
  return defaultSettings
}

function saveToCookie(settings: Settings) {
  Cookies.set(COOKIE_KEY, JSON.stringify(settings), {
    expires: 365,
    sameSite: 'Lax',
  })
}

export function SettingsProvider({ children }: { children: React.ReactNode }) {
  const [settings, setSettings] = React.useState<Settings>(defaultSettings)
  const [isMounted, setIsMounted] = React.useState(false)

  // Load from cookie on mount (client-side only)
  React.useEffect(() => {
    setSettings(loadFromCookie())
    setIsMounted(true)
  }, [])

  const setAccentColor = React.useCallback((color: AccentColor) => {
    setSettings((prev) => {
      const next = { ...prev, accentColor: color }
      saveToCookie(next)
      return next
    })
  }, [])

  const setBorderRadius = React.useCallback((radius: BorderRadius) => {
    setSettings((prev) => {
      const next = { ...prev, borderRadius: radius }
      saveToCookie(next)
      return next
    })
  }, [])

  return (
    <SettingsContext.Provider
      value={{ settings, setAccentColor, setBorderRadius, isMounted }}
    >
      {children}
    </SettingsContext.Provider>
  )
}

export function useSettings() {
  const ctx = React.useContext(SettingsContext)
  if (!ctx) throw new Error('useSettings must be used within SettingsProvider')
  return ctx
}

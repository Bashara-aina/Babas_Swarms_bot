'use client'

import * as React from 'react'

type Theme = 'light' | 'dark' | 'system'

interface ThemeContextValue {
  theme: Theme
  resolvedTheme: 'light' | 'dark'
  setTheme: (theme: Theme) => void
  toggleTheme: () => void
}

const ThemeContext = React.createContext<ThemeContextValue>({
  theme: 'system',
  resolvedTheme: 'light',
  setTheme: () => {},
  toggleTheme: () => {},
})

export function useAppTheme() {
  return React.useContext(ThemeContext)
}

function getResolvedTheme(theme: Theme): 'light' | 'dark' {
  if (theme === 'system') {
    return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'
  }
  return theme
}

function applyTheme(theme: Theme) {
  const root = document.documentElement
  const resolved = getResolvedTheme(theme)
  root.classList.remove('light', 'dark')
  root.classList.add(resolved)
}

export function ThemeProvider({ children }: { children: React.ReactNode }) {
  const [theme, setThemeState] = React.useState<Theme>('system')
  const [resolvedTheme, setResolvedTheme] = React.useState<'light' | 'dark'>('light')
  const [mounted, setMounted] = React.useState(false)

  // Sync with localStorage and system preference on mount
  React.useEffect(() => {
    const stored = localStorage.getItem('theme') as Theme | null
    const initial = stored ?? 'system'
    setThemeState(initial)
    const resolved = getResolvedTheme(initial)
    setResolvedTheme(resolved)
    applyTheme(initial)
    setMounted(true)

    // Listen for system preference changes
    const mq = window.matchMedia('(prefers-color-scheme: dark)')
    const handler = () => {
      if (theme === 'system') {
        const resolved = getResolvedTheme('system')
        setResolvedTheme(resolved)
        applyTheme('system')
      }
    }
    mq.addEventListener('change', handler)
    return () => mq.removeEventListener('change', handler)
  }, [theme])

  const setTheme = React.useCallback((newTheme: Theme) => {
    setThemeState(newTheme)
    localStorage.setItem('theme', newTheme)
    const resolved = getResolvedTheme(newTheme)
    setResolvedTheme(resolved)
    applyTheme(newTheme)
  }, [])

  const toggleTheme = React.useCallback(() => {
    // Toggle between light and dark (never cycle to system from toggle)
    const next = resolvedTheme === 'dark' ? 'light' : 'dark'
    setTheme(next)
  }, [resolvedTheme, setTheme])

  return (
    <ThemeContext.Provider value={{ theme, resolvedTheme, setTheme, toggleTheme }}>
      {children}
    </ThemeContext.Provider>
  )
}

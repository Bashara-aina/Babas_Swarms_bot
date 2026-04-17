'use client'

// ══════════════════════════════════════════════════════════════════════════════
// cekwajar.id — ConfettiEffect
// Canvas-confetti burst for SESUAI celebration moments
// ══════════════════════════════════════════════════════════════════════════════

import { useEffect } from 'react'

interface ConfettiEffectProps {
  /** Trigger the burst immediately on mount */
  fire?: boolean
  /** Optional: particle count multiplier (default 1) */
  intensity?: number
}

/**
 * Fires a confetti burst using canvas-confetti.
 * Respects prefers-reduced-motion — silent no-op if user prefers reduced motion.
 */
export function ConfettiEffect({ fire = true, intensity = 1 }: ConfettiEffectProps) {
  useEffect(() => {
    if (!fire) return

    const mediaQuery = window.matchMedia('(prefers-reduced-motion: no-preference)')
    if (!mediaQuery.matches) return

    const loadAndFire = async () => {
      try {
        const confetti = (await import('canvas-confetti')).default

        const count = Math.floor(200 * intensity)
        const defaults = {
          origin: { y: 0.7 },
          colors: ['#10b981', '#059669', '#34d399', '#6ee7b7'],
        }

        const fire = (particleRatio: number, opts: confetti.Options) =>
          confetti({
            ...defaults,
            ...opts,
            particleCount: Math.floor(count * particleRatio),
          })

        fire(0.25, { spread: 26, startVelocity: 55 })
        fire(0.2, { spread: 60 })
        fire(0.35, { spread: 100, decay: 0.91 })
        fire(0.1, { spread: 120, startVelocity: 25, decay: 0.92 })
        fire(0.1, { spread: 120, startVelocity: 45 })
      } catch {
        // canvas-confetti not available — silent fallback
      }
    }

    loadAndFire()
  }, [fire, intensity])

  return null
}

// src/components/WordmarkLogo.tsx
// cekwajar.id — Refined wordmark v2
// Typographic split: cek (light, verb) · wajar (extrabold, verdict, emerald) · .id (teal, identity)
// Props interface unchanged from v1 — drop-in replacement.

import React from 'react'
import { cn } from '@/lib/utils'

interface WordmarkLogoProps {
  size?: 'sm' | 'md' | 'lg'
  className?: string
  iconColor?: string   // defaults to emerald #10b981
  showIcon?: boolean   // defaults to true
}

const SIZE_CONFIG = {
  sm: { iconSize: 16, fontSize: 14, gap: 6,  iconStroke: 3.8 },
  md: { iconSize: 22, fontSize: 18, gap: 8,  iconStroke: 4.2 },
  lg: { iconSize: 30, fontSize: 24, gap: 10, iconStroke: 4.5 },
}

export function WordmarkLogo({
  size = 'md',
  className,
  iconColor = '#10b981',
  showIcon = true,
}: WordmarkLogoProps) {
  const { iconSize, fontSize, gap, iconStroke } = SIZE_CONFIG[size]

  return (
    <span
      className={cn('inline-flex items-center select-none', className)}
      style={{ gap, lineHeight: 1 }}
      aria-label="cekwajar.id"
    >
      {showIcon && (
        <svg
          width={iconSize}
          height={iconSize}
          viewBox="0 0 32 32"
          fill="none"
          xmlns="http://www.w3.org/2000/svg"
          aria-hidden="true"
          style={{ flexShrink: 0 }}
        >
          {/* The "cek" mark: asymmetric checkmark with curved right arm.
              Short left arm (grounding stroke) + long curved right arm
              (confident sweep) = "data point finding its position in range" */}
          <path
            d="M 4 18 L 11 25 Q 20 10 28 8"
            stroke={iconColor}
            strokeWidth={iconStroke}
            strokeLinecap="round"
            strokeLinejoin="round"
          />
        </svg>
      )}

      {/* Wordmark — three typographic weights, one reading unit */}
      <span
        style={{
          fontFamily: 'var(--font-sans, "Plus Jakarta Sans", sans-serif)',
          fontSize,
          lineHeight: 1,
          display: 'inline-flex',
          alignItems: 'baseline',
          letterSpacing: '-0.01em',
        }}
      >
        {/* "cek" — the action. Light weight recedes, leads the eye into "wajar" */}
        <span
          style={{
            fontWeight: 300,
            color: 'var(--foreground, #0f172a)',
          }}
        >
          cek
        </span>

        {/* "wajar" — the verdict. Extrabold, emerald. This is the brand name. */}
        <span
          style={{
            fontWeight: 800,
            color: iconColor,
            letterSpacing: '-0.03em',
          }}
        >
          wajar
        </span>

        {/* ".id" — Indonesia identity. Teal, slightly muted weight.
            Tighter to "wajar" than in v1 — it belongs to the brand name,
            not the action word. */}
        <span
          style={{
            fontWeight: 400,
            color: 'var(--color-tool-hidup-accent, #14b8a6)',
            letterSpacing: '0em',
          }}
        >
          .id
        </span>
      </span>
    </span>
  )
}

export default WordmarkLogo

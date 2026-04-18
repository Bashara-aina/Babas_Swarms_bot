import Link from 'next/link'
import { cn } from '@/lib/utils'

interface WordmarkLogoProps {
  size?: 'sm' | 'md' | 'lg'
  className?: string
  iconColor?: string
  showIcon?: boolean
}

const SIZE_CONFIG = {
  sm: { iconSize: 16, fontSize: 14, gap: 6, iconStroke: 3.8 },
  md: { iconSize: 22, fontSize: 18, gap: 8, iconStroke: 4.2 },
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
    <Link
      href="/"
      className={cn('inline-flex items-center select-none hover:opacity-90 transition-opacity', className)}
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
          <path
            d="M 4 18 L 11 25 Q 20 10 28 8"
            stroke={iconColor}
            strokeWidth={iconStroke}
            strokeLinecap="round"
            strokeLinejoin="round"
          />
        </svg>
      )}

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
        <span style={{ fontWeight: 300, color: 'var(--foreground, #0f172a)' }}>
          cek
        </span>
        <span style={{ fontWeight: 800, color: iconColor, letterSpacing: '-0.03em' }}>
          wajar
        </span>
        <span style={{ fontWeight: 400, color: 'var(--color-tool-hidup-accent, #14b8a6)', letterSpacing: '0em' }}>
          .id
        </span>
      </span>
    </Link>
  )
}

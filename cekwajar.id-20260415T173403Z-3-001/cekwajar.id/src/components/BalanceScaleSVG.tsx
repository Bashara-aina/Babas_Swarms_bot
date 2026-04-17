import { cn } from '@/lib/utils'

interface BalanceScaleSVGProps {
  className?: string
  opacity?: number
}

export function BalanceScaleSVG({ className, opacity = 0.06 }: BalanceScaleSVGProps) {
  return (
    <svg
      viewBox="0 0 200 160"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className={cn('text-emerald-500', className)}
      style={{ opacity }}
      aria-hidden="true"
    >
      {/* Center pole */}
      <rect x="98" y="20" width="4" height="110" fill="currentColor" />
      {/* Base */}
      <rect x="70" y="130" width="60" height="6" rx="3" fill="currentColor" />
      <rect x="85" y="120" width="30" height="12" rx="2" fill="currentColor" />
      {/* Crossbar */}
      <rect x="30" y="38" width="140" height="4" rx="2" fill="currentColor" />
      {/* Left chain */}
      <rect x="46" y="42" width="2" height="30" fill="currentColor" />
      {/* Right chain */}
      <rect x="152" y="42" width="2" height="30" fill="currentColor" />
      {/* Left pan */}
      <path d="M26 72 Q47 82 68 72" stroke="currentColor" strokeWidth="3" fill="none" strokeLinecap="round"/>
      {/* Right pan */}
      <path d="M132 72 Q153 82 174 72" stroke="currentColor" strokeWidth="3" fill="none" strokeLinecap="round"/>
      {/* Top pivot dot */}
      <circle cx="100" cy="22" r="6" fill="currentColor" />
    </svg>
  )
}

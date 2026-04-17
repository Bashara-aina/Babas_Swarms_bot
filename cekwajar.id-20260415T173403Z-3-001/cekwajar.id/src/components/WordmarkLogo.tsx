import Link from 'next/link'
import { cn } from '@/lib/utils'

interface WordmarkLogoProps {
  className?: string
  size?: 'sm' | 'md' | 'lg'
}

const sizeMap = {
  sm: 'text-lg',
  md: 'text-xl',
  lg: 'text-3xl',
}

export function WordmarkLogo({ className, size = 'md' }: WordmarkLogoProps) {
  return (
    <Link href="/" className={cn('flex items-center gap-0 hover:opacity-90 transition-opacity', className)}>
      <span className={cn('font-normal text-foreground tracking-tight', sizeMap[size])}>
        cek
      </span>
      <span className={cn('font-bold text-emerald-600 dark:text-emerald-400 tracking-tight', sizeMap[size])}>
        wajar
      </span>
      <span className={cn('font-normal text-muted-foreground text-sm ml-0.5 self-end mb-0.5', size === 'lg' ? 'text-base' : 'text-xs')}>
        .id
      </span>
    </Link>
  )
}

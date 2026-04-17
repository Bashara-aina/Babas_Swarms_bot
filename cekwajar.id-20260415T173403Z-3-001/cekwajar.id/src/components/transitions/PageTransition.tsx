'use client'

// ══════════════════════════════════════════════════════════════════════════════
// cekwajar.id — Page Transition Component
// Wraps page content with framer-motion AnimatePresence for smooth transitions
// ══════════════════════════════════════════════════════════════════════════════

import { motion, AnimatePresence, useReducedMotion } from 'framer-motion'
import { usePathname } from 'next/navigation'
import { ReactNode } from 'react'

// ─── Variants ─────────────────────────────────────────────────────────────────

const pageVariants = {
  initial: { opacity: 0, y: 8 },
  animate: { opacity: 1, y: 0 },
  exit: { opacity: 0, y: -8 },
}

const dashboardVariants = {
  initial: { opacity: 0, scale: 0.97 },
  animate: { opacity: 1, scale: 1 },
  exit: { opacity: 0, scale: 0.97 },
}

const resultVariants = {
  initial: { opacity: 0, x: 24 },
  animate: { opacity: 1, x: 0 },
  exit: { opacity: 0, x: -24 },
}

const modalVariants = {
  initial: { opacity: 0, scale: 0.95 },
  animate: { opacity: 1, scale: 1 },
  exit: { opacity: 0, scale: 0.95 },
}

const TRANSITION = { duration: 0.25, ease: [0.25, 0.1, 0.25, 1] as const }

// ─── Bento card stagger ────────────────────────────────────────────────────────

export const bentoStagger = {
  container: {
    animate: {
      transition: {
        staggerChildren: 0.1,
      },
    },
  },
  item: {
    initial: { opacity: 0, y: 12 },
    animate: {
      opacity: 1,
      y: 0,
      transition: { duration: 0.3, ease: 'easeOut' },
    },
  },
}

// ─── Component ────────────────────────────────────────────────────────────────

type PageType = 'default' | 'dashboard' | 'result' | 'modal'

function getPageType(pathname: string): PageType {
  if (pathname === '/dashboard') return 'dashboard'
  if (
    pathname.startsWith('/wajar-gaji') ||
    pathname.startsWith('/wajar-tanah') ||
    pathname.startsWith('/wajar-kabur') ||
    pathname.startsWith('/wajar-hidup') ||
    pathname.startsWith('/wajar-slip/result')
  )
    return 'result'
  if (
    pathname.startsWith('/upgrade') ||
    pathname.startsWith('/auth')
  )
    return 'modal'
  return 'default'
}

function getVariants(pageType: PageType) {
  switch (pageType) {
    case 'dashboard': return dashboardVariants
    case 'result':    return resultVariants
    case 'modal':     return modalVariants
    default:          return pageVariants
  }
}

interface PageTransitionProps {
  children: ReactNode
  className?: string
}

export function PageTransition({ children, className }: PageTransitionProps) {
  const pathname = usePathname()
  const prefersReducedMotion = useReducedMotion()

  // Skip animations if user prefers reduced motion
  if (prefersReducedMotion) {
    return <>{children}</>
  }

  const pageType = getPageType(pathname)
  const variants = getVariants(pageType)

  return (
    <AnimatePresence mode="wait" initial={false}>
      <motion.div
        key={pathname}
        variants={variants}
        initial="initial"
        animate="animate"
        exit="exit"
        transition={TRANSITION}
        className={className}
      >
        {children}
      </motion.div>
    </AnimatePresence>
  )
}

// ─── Skeleton shimmer variant (for loading states) ───────────────────────────

export const shimmerVariants = {
  initial: { opacity: 0 },
  animate: {
    opacity: 1,
    transition: { duration: 0.4 },
  },
}

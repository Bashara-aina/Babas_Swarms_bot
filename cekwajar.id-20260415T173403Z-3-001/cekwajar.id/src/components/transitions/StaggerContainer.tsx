'use client'

// ══════════════════════════════════════════════════════════════════════════════
// cekwajar.id — Dashboard Bento Grid with Stagger Animation
// Wraps bento/card grids with staggered entrance animations
// ══════════════════════════════════════════════════════════════════════════════

import { motion } from 'framer-motion'
import { useReducedMotion } from 'framer-motion'
import { ReactNode } from 'react'

interface StaggerItemProps {
  children: ReactNode
  className?: string
}

export function StaggerItem({ children, className }: StaggerItemProps) {
  if (useReducedMotion()) {
    return <>{children}</>
  }
  return (
    <motion.div
      variants={{
        initial: { opacity: 0, y: 12 },
        animate: {
          opacity: 1,
          y: 0,
          transition: { duration: 0.3, ease: 'easeOut' },
        },
      }}
      initial="initial"
      animate="animate"
      className={className}
    >
      {children}
    </motion.div>
  )
}

interface StaggerContainerProps {
  children: ReactNode
  className?: string
  delay?: number
}

export function StaggerContainer({ children, className, delay = 0.1 }: StaggerContainerProps) {
  if (useReducedMotion()) {
    return <>{children}</>
  }
  return (
    <motion.div
      variants={{
        animate: {
          transition: {
            staggerChildren: delay,
          },
        },
      }}
      initial="initial"
      animate="animate"
      className={className}
    >
      {children}
    </motion.div>
  )
}

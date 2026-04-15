// ══════════════════════════════════════════════════════════════════════════════
// cekwajar.id — Utility Functions
// ══════════════════════════════════════════════════════════════════════════════

import { clsx, type ClassValue } from 'clsx'
import { twMerge } from 'tailwind-merge'

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export function formatIDR(amount: number, compact = false): string {
  if (compact && amount >= 1_000_000) {
    return `Rp ${(amount / 1_000_000).toFixed(1)}M`
  }
  return new Intl.NumberFormat('id-ID', {
    style: 'currency',
    currency: 'IDR',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(amount)
}

export function formatNumber(value: number): string {
  return new Intl.NumberFormat('id-ID').format(value)
}

export function parseIDR(input: string): number {
  const cleaned = input.replace(/[^\d]/g, '')
  return parseInt(cleaned, 10) || 0
}

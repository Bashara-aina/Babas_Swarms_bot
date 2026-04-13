"use client"

import { motion } from "framer-motion"
import { cn } from "@/lib/utils"

const MONTHS = [
  "Jan", "Feb", "Mar", "Apr",
  "Mei", "Jun", "Jul", "Agu",
  "Sep", "Okt", "Nov", "Des",
]

interface MonthPickerProps {
  value: number
  onChange: (month: number) => void
  error?: string
}

export function MonthPicker({ value, onChange, error }: MonthPickerProps) {
  return (
    <div className="flex flex-col gap-2">
      <label className="text-sm font-medium text-slate-700 dark:text-slate-300">
        Periode Slip <span className="text-brand-danger" aria-hidden="true">•</span>
      </label>

      <div className="grid grid-cols-4 gap-2" role="group" aria-label="Pilih bulan">
        {MONTHS.map((name, i) => {
          const month = i + 1
          const isActive = value === month
          const isDecember = month === 12

          return (
            <motion.button
              key={month}
              type="button"
              onClick={() => onChange(month)}
              whileTap={{ scale: 0.9 }}
              className={cn(
                "relative h-11 rounded-xl text-sm font-semibold transition-all duration-150",
                "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-primary focus-visible:ring-offset-1",
                isActive
                  ? "bg-brand-primary text-white shadow-md"
                  : "bg-slate-100 text-slate-600 hover:bg-slate-200 dark:bg-slate-700 dark:text-slate-300 dark:hover:bg-slate-600"
              )}
              aria-pressed={isActive}
              aria-label={`${name}${isDecember ? " (Desember — khusus)" : ""}`}
            >
              {name}
              {isDecember && (
                <span
                  title="Desember: perhitungan berbeda (Pasal 17)"
                  className={cn(
                    "absolute -right-0.5 -top-0.5 h-2 w-2 rounded-full",
                    isActive ? "bg-amber-300" : "bg-amber-400"
                  )}
                  aria-hidden="true"
                />
              )}
            </motion.button>
          )
        })}
      </div>

      {value === 12 && (
        <p className="rounded-lg bg-amber-50 px-3 py-2 text-xs text-amber-700 dark:bg-amber-950/50 dark:text-amber-300">
          ⚠️ Desember menggunakan rekonsiliasi Pasal 17, bukan TER bulanan. Hasil bisa berbeda dari bulan lain.
        </p>
      )}

      {error && (
        <p className="flex items-center gap-1 text-xs text-red-500" role="alert">
          <span aria-hidden="true">⚠️</span> {error}
        </p>
      )}
    </div>
  )
}

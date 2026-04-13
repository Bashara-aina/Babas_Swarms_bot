"use client"

import { motion } from "framer-motion"
import { cn } from "@/lib/utils"
import type { PTKPStatus } from "@/lib/pph21-ter"

interface Option {
  value: PTKPStatus
  label: string
  desc: string
  category: "A" | "B" | "C"
}

interface Group {
  title: string
  emoji: string
  options: Option[]
}

const GROUPS: Group[] = [
  {
    title: "Lajang / Belum Menikah",
    emoji: "🧑",
    options: [
      { value: "TK/0", label: "TK/0", desc: "0 tanggungan", category: "A" },
      { value: "TK/1", label: "TK/1", desc: "1 tanggungan", category: "A" },
      { value: "TK/2", label: "TK/2", desc: "2 tanggungan", category: "B" },
      { value: "TK/3", label: "TK/3", desc: "3 tanggungan", category: "B" },
    ],
  },
  {
    title: "Menikah",
    emoji: "👫",
    options: [
      { value: "K/0", label: "K/0", desc: "0 tanggungan", category: "A" },
      { value: "K/1", label: "K/1", desc: "1 tanggungan", category: "B" },
      { value: "K/2", label: "K/2", desc: "2 tanggungan", category: "C" },
      { value: "K/3", label: "K/3", desc: "3 tanggungan", category: "C" },
    ],
  },
  {
    title: "Menikah — Gabung Penghasilan",
    emoji: "👫💼",
    options: [
      { value: "K/I/0", label: "K/I/0", desc: "0 tanggungan", category: "C" },
      { value: "K/I/1", label: "K/I/1", desc: "1 tanggungan", category: "C" },
      { value: "K/I/2", label: "K/I/2", desc: "2 tanggungan", category: "C" },
      { value: "K/I/3", label: "K/I/3", desc: "3 tanggungan", category: "C" },
    ],
  },
]

const CATEGORY_COLORS: Record<"A" | "B" | "C", string> = {
  A: "bg-blue-50 text-blue-700 dark:bg-blue-950 dark:text-blue-300",
  B: "bg-emerald-50 text-emerald-700 dark:bg-emerald-950 dark:text-emerald-300",
  C: "bg-purple-50 text-purple-700 dark:bg-purple-950 dark:text-purple-300",
}

interface PTKPSelectorProps {
  value: PTKPStatus | ""
  onChange: (value: PTKPStatus) => void
  error?: string
}

export function PTKPSelector({ value, onChange, error }: PTKPSelectorProps) {
  return (
    <div className="flex flex-col gap-3">
      <div className="flex items-center justify-between">
        <label className="text-sm font-medium text-slate-700 dark:text-slate-300">
          Status PTKP <span className="text-brand-danger" aria-hidden="true">•</span>
        </label>
        <span className="rounded-full bg-amber-50 px-2 py-0.5 text-xs text-amber-700 dark:bg-amber-950 dark:text-amber-300">
          💡 Tidak yakin? Pilih TK/0
        </span>
      </div>

      <div className="space-y-4">
        {GROUPS.map((group) => (
          <div key={group.title} className="space-y-2">
            <p className="flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wide text-text-muted dark:text-slate-400">
              <span>{group.emoji}</span> {group.title}
            </p>
            <div className="grid grid-cols-2 gap-2 sm:grid-cols-4">
              {group.options.map((option) => {
                const isActive = value === option.value
                return (
                  <motion.button
                    key={option.value}
                    type="button"
                    onClick={() => onChange(option.value)}
                    whileTap={{ scale: 0.95 }}
                    className={cn(
                      "relative flex flex-col items-center rounded-xl border-2 p-3 text-center transition-all duration-150",
                      "min-h-[72px] cursor-pointer select-none",
                      isActive
                        ? "border-brand-primary bg-blue-50 shadow-md dark:border-blue-400 dark:bg-blue-950"
                        : "border-slate-200 bg-white hover:border-slate-300 hover:shadow-card dark:border-slate-700 dark:bg-slate-800 dark:hover:border-slate-600"
                    )}
                    aria-pressed={isActive}
                    aria-label={`${option.label} — ${option.desc}`}
                  >
                    <span
                      className={cn(
                        "text-sm font-bold",
                        isActive ? "text-brand-primary dark:text-blue-400" : "text-slate-800 dark:text-slate-200"
                      )}
                    >
                      {option.label}
                    </span>
                    <span
                      className={cn(
                        "mt-0.5 text-xs",
                        isActive ? "text-blue-600 dark:text-blue-300" : "text-text-muted dark:text-slate-400"
                      )}
                    >
                      {option.desc}
                    </span>
                    <span
                      className={cn(
                        "mt-1.5 rounded-full px-1.5 py-0.5 text-[10px] font-semibold",
                        CATEGORY_COLORS[option.category]
                      )}
                    >
                      TER {option.category}
                    </span>

                    {isActive && (
                      <motion.span
                        layoutId="ptkp-indicator"
                        className="absolute -right-1 -top-1 flex h-4 w-4 items-center justify-center rounded-full bg-brand-primary text-white shadow"
                        initial={false}
                      >
                        <svg
                          className="h-2.5 w-2.5"
                          fill="none"
                          viewBox="0 0 24 24"
                          stroke="currentColor"
                          strokeWidth={3}
                        >
                          <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                        </svg>
                      </motion.span>
                    )}
                  </motion.button>
                )
              })}
            </div>
          </div>
        ))}
      </div>

      {error && (
        <p className="flex items-center gap-1 text-xs text-red-500" role="alert">
          <span aria-hidden="true">⚠️</span> {error}
        </p>
      )}
    </div>
  )
}

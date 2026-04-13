"use client"

import { forwardRef, useRef, useState, useCallback } from "react"
import { motion, AnimatePresence } from "framer-motion"
import { X, Check } from "lucide-react"
import { cn } from "@/lib/utils"

interface CurrencyInputProps {
  value: number
  onChange: (value: number) => void
  label: string
  required?: boolean
  optional?: boolean
  error?: string
  hint?: string
  placeholder?: string
  disabled?: boolean
  className?: string
}

function parseToNumber(raw: string): number {
  const digits = raw.replace(/\D/g, "")
  return digits ? parseInt(digits, 10) : 0
}

function formatIndonesian(n: number): string {
  if (n === 0) return ""
  return new Intl.NumberFormat("id-ID").format(n)
}

export const CurrencyInput = forwardRef<HTMLInputElement, CurrencyInputProps>(
  function CurrencyInput(
    { value, onChange, label, required, optional, error, hint, placeholder = "0", disabled, className },
    _ref
  ) {
    const inputRef = useRef<HTMLInputElement>(null)
    const [isFocused, setIsFocused] = useState(false)
    const [showCheck, setShowCheck] = useState(false)
    const checkTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null)

    const displayValue = isFocused
      ? value === 0 ? "" : formatIndonesian(value)
      : value === 0 ? "" : formatIndonesian(value)

    const handleChange = useCallback(
      (e: React.ChangeEvent<HTMLInputElement>) => {
        const parsed = parseToNumber(e.target.value)
        onChange(parsed)

        if (parsed > 0) {
          if (checkTimeoutRef.current) clearTimeout(checkTimeoutRef.current)
          setShowCheck(false)
          checkTimeoutRef.current = setTimeout(() => {
            setShowCheck(true)
            checkTimeoutRef.current = setTimeout(() => setShowCheck(false), 2000)
          }, 400)
        } else {
          setShowCheck(false)
        }
      },
      [onChange]
    )

    const handleClear = () => {
      onChange(0)
      setShowCheck(false)
      inputRef.current?.focus()
    }

    const hasValue = value > 0

    return (
      <div className={cn("flex flex-col gap-1", className)}>
        <label className="flex items-center gap-1 text-sm font-medium text-slate-700 dark:text-slate-300">
          {label}
          {required && (
            <span className="text-brand-danger" aria-hidden="true">
              •
            </span>
          )}
          {optional && (
            <span className="text-xs font-normal text-text-muted">(opsional)</span>
          )}
        </label>

        <div
          className={cn(
            "relative flex items-center overflow-hidden rounded-xl border bg-white transition-all duration-150 dark:bg-slate-800",
            isFocused
              ? "border-brand-primary shadow-focus ring-2 ring-brand-primary/15 dark:border-brand-primary"
              : error
              ? "border-red-400 dark:border-red-500"
              : "border-slate-200 dark:border-slate-600",
            disabled && "cursor-not-allowed opacity-50"
          )}
        >
          {/* Rp prefix */}
          <span
            className={cn(
              "flex h-12 select-none items-center border-r px-3 text-sm font-semibold transition-colors",
              isFocused
                ? "border-brand-primary/30 bg-blue-50 text-brand-primary dark:border-brand-primary/30 dark:bg-blue-950 dark:text-blue-400"
                : "border-slate-200 bg-slate-50 text-slate-500 dark:border-slate-600 dark:bg-slate-700 dark:text-slate-400"
            )}
          >
            Rp
          </span>

          <input
            ref={inputRef}
            type="text"
            inputMode="numeric"
            disabled={disabled}
            placeholder={placeholder}
            value={displayValue}
            onChange={handleChange}
            onFocus={() => setIsFocused(true)}
            onBlur={() => setIsFocused(false)}
            className={cn(
              "h-12 flex-1 bg-transparent px-3 font-mono text-base text-slate-900 placeholder-slate-300 outline-none dark:text-slate-100 dark:placeholder-slate-600",
              "min-w-0"
            )}
            aria-invalid={!!error}
          />

          {/* Clear & check icons */}
          <div className="flex items-center gap-1 pr-3">
            <AnimatePresence>
              {showCheck && hasValue && (
                <motion.span
                  key="check"
                  initial={{ scale: 0, opacity: 0 }}
                  animate={{ scale: 1, opacity: 1 }}
                  exit={{ scale: 0, opacity: 0 }}
                  transition={{ type: "spring", stiffness: 400, damping: 20 }}
                  className="flex h-5 w-5 items-center justify-center rounded-full bg-brand-accent/15 text-brand-accent"
                >
                  <Check className="h-3 w-3" strokeWidth={3} />
                </motion.span>
              )}
            </AnimatePresence>

            <AnimatePresence>
              {hasValue && !disabled && (
                <motion.button
                  key="clear"
                  type="button"
                  onClick={handleClear}
                  initial={{ scale: 0, opacity: 0 }}
                  animate={{ scale: 1, opacity: 1 }}
                  exit={{ scale: 0, opacity: 0 }}
                  transition={{ duration: 0.15 }}
                  className="flex h-6 w-6 items-center justify-center rounded-full text-slate-400 transition-colors hover:bg-slate-100 hover:text-slate-600 dark:hover:bg-slate-700 dark:hover:text-slate-300"
                  aria-label="Hapus nilai"
                >
                  <X className="h-3.5 w-3.5" />
                </motion.button>
              )}
            </AnimatePresence>
          </div>
        </div>

        <AnimatePresence>
          {error && (
            <motion.p
              initial={{ opacity: 0, y: -4 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -4 }}
              className="flex items-center gap-1 text-xs text-red-500"
              role="alert"
            >
              <span aria-hidden="true">⚠️</span> {error}
            </motion.p>
          )}
          {hint && !error && (
            <motion.p
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="text-xs text-text-muted dark:text-slate-400"
            >
              {hint}
            </motion.p>
          )}
        </AnimatePresence>
      </div>
    )
  }
)

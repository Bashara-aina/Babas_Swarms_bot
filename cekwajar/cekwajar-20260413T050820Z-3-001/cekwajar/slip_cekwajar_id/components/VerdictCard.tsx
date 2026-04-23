"use client"

import { useRef, useCallback } from "react"
import { motion, AnimatePresence } from "framer-motion"
import { RefreshCw, Copy, Check } from "lucide-react"
import { useState } from "react"
import { cn } from "@/lib/utils"
import { type SlipResult, type VerdictType } from "@/lib/pph21-ter"
import { REGULATION_META, REGULATION_SOURCES, BPJS_JP } from "@/lib/regulations"

const VERDICT_CONFIG: Record<
  VerdictType,
  {
    emoji: string
    label: string
    subLabel: string
    containerClass: string
    badgeClass: string
    textClass: string
    borderClass: string
  }
> = {
  WAJAR: {
    emoji: "✅",
    label: "WAJAR",
    subLabel: "Potongan gaji kamu sesuai regulasi!",
    containerClass: "bg-emerald-50 dark:bg-emerald-950/40",
    badgeClass: "bg-emerald-100 border-emerald-400 dark:bg-emerald-900 dark:border-emerald-500",
    textClass: "text-emerald-700 dark:text-emerald-300",
    borderClass: "border-emerald-200 dark:border-emerald-800",
  },
  PERLU_DICEK: {
    emoji: "⚠️",
    label: "PERLU DICEK",
    subLabel: "Ada beberapa hal yang perlu kamu periksa.",
    containerClass: "bg-amber-50 dark:bg-amber-950/40",
    badgeClass: "bg-amber-100 border-amber-400 dark:bg-amber-900 dark:border-amber-500",
    textClass: "text-amber-700 dark:text-amber-300",
    borderClass: "border-amber-200 dark:border-amber-800",
  },
  TIDAK_WAJAR: {
    emoji: "❌",
    label: "TIDAK WAJAR",
    subLabel: "Kamu kelebihan dipotong!",
    containerClass: "bg-red-50 dark:bg-red-950/40",
    badgeClass: "bg-red-100 border-red-400 dark:bg-red-900 dark:border-red-500",
    textClass: "text-red-700 dark:text-red-300",
    borderClass: "border-red-200 dark:border-red-800",
  },
}

const tableRowVariants = {
  hidden: { opacity: 0, x: -16 },
  visible: (i: number) => ({
    opacity: 1,
    x: 0,
    transition: { delay: i * 0.08, duration: 0.3, ease: "easeOut" },
  }),
}

function RowStatus({ correct, illegal }: { correct: boolean; illegal?: boolean }) {
  if (illegal) return <span className="text-sm font-bold text-red-600">🚫 Ilegal</span>
  if (correct) return <span className="text-sm text-emerald-600">✅</span>
  return <span className="text-sm text-red-500">❌</span>
}

function formatIDR(n: number): string {
  if (n === 0) return "—"
  return new Intl.NumberFormat("id-ID", {
    style: "currency",
    currency: "IDR",
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(n)
}

interface VerdictCardProps {
  result: SlipResult
  onReset: () => void
  resultRef?: React.RefObject<HTMLDivElement>
}

export function VerdictCard({ result, onReset, resultRef }: VerdictCardProps) {
  const cfg = VERDICT_CONFIG[result.verdict]
  const [copied, setCopied] = useState(false)
  const [screenshotFailed, setScreenshotFailed] = useState(false)
  const cardRef = useRef<HTMLDivElement>(null)

  const bpjsRows = [
    result.bpjsKesehatan,
    result.bpjsJht,
    result.bpjsJp,
    ...(result.bpjsJkk.charged > 0 ? [result.bpjsJkk] : []),
    ...(result.bpjsJkm.charged > 0 ? [result.bpjsJkm] : []),
  ]

  const handleCopyShare = useCallback(async () => {
    const verdictText =
      result.verdict === "WAJAR"
        ? "WAJAR ✅"
        : result.verdict === "PERLU_DICEK"
        ? "PERLU DICEK ⚠️"
        : "TIDAK WAJAR ❌"

    const overchargeText =
      result.totalOvercharge > 0
        ? `\nKelebihan potongan: ${formatIDR(result.totalOvercharge)}/bulan`
        : ""

    const text =
      `Hasil cek slip gaji gue: ${verdictText}${overchargeText}\n` +
      `Berdasarkan PMK 168/2023 (TER) & PP 44/2015 (BPJS)\n\n` +
      `Cek punya lo juga → cekwajar.id/slip\n\n` +
      `#CekWajar #GajiAman #PPh21 #SlipGaji`

    await navigator.clipboard.writeText(text)
    setCopied(true)
    setTimeout(() => setCopied(false), 2500)
  }, [result])

  const handleScreenshot = useCallback(async () => {
    const target = resultRef?.current ?? cardRef.current
    if (!target) return
    try {
      const { default: html2canvas } = await import("html2canvas")
      const canvas = await html2canvas(target, { scale: 2, useCORS: true })
      const link = document.createElement("a")
      link.download = "wajar-slip-hasil.png"
      link.href = canvas.toDataURL()
      link.click()
    } catch {
      setScreenshotFailed(true)
      setTimeout(() => setScreenshotFailed(false), 3000)
      handleCopyShare()
    }
  }, [resultRef, handleCopyShare])

  return (
    <div ref={cardRef} className="flex flex-col gap-4">
      {/* Verdict hero */}
      <motion.div
        initial={{ scale: 0.85, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        transition={{ type: "spring", stiffness: 300, damping: 20 }}
        className={cn("rounded-2xl border-2 p-6 text-center", cfg.containerClass, cfg.borderClass)}
      >
        <motion.div
          initial={{ scale: 0.6 }}
          animate={{ scale: 1 }}
          transition={{ type: "spring", stiffness: 400, damping: 15, delay: 0.1 }}
          className="mb-3 text-5xl"
          aria-hidden="true"
        >
          {cfg.emoji}
        </motion.div>

        <div
          className={cn(
            "mx-auto mb-2 inline-flex items-center rounded-full border-2 px-4 py-1.5",
            cfg.badgeClass
          )}
        >
          <span className={cn("text-lg font-black tracking-tight", cfg.textClass)}>
            {cfg.label}
          </span>
        </div>

        <p className={cn("text-sm font-medium", cfg.textClass)}>{cfg.subLabel}</p>

        {result.totalOvercharge > 0 && (
          <motion.div
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
            className="mt-4 rounded-xl bg-white/60 px-4 py-3 dark:bg-slate-900/40"
          >
            <p className="text-xs font-medium text-slate-500 dark:text-slate-400">
              Estimasi kelebihan potongan
            </p>
            <p className="font-mono text-2xl font-black text-red-600 dark:text-red-400">
              {formatIDR(result.totalOvercharge)}
              <span className="ml-1 text-sm font-normal">/bulan</span>
            </p>
            <p className="mt-0.5 text-xs text-slate-400">
              ≈ {formatIDR(result.totalOvercharge * 12)}/tahun jika tidak diperbaiki
            </p>
          </motion.div>
        )}

        {result.isDecember && (
          <p className="mt-3 text-xs text-amber-600 dark:text-amber-400">
            ⚠️ Desember: menggunakan rekonsiliasi Pasal 17, bukan TER. Konsultasikan ke HRD.
          </p>
        )}

        {result.jp_cap_unverified && (
          <div className="mt-3 rounded-xl border border-amber-200 bg-amber-50 px-3 py-2 dark:border-amber-800 dark:bg-amber-950/30">
            <p className="text-xs font-medium text-amber-700 dark:text-amber-300">
              ℹ️ Batas upah JP 2026 (Rp11.004.000) belum resmi terverifikasi — estimasi. Cek sirkular BPJS terbaru.
            </p>
          </div>
        )}
      </motion.div>

      {/* Always show breakdown table */}
      <div className="overflow-hidden rounded-2xl border border-slate-200 bg-white dark:border-slate-700 dark:bg-slate-800">
        <div className="border-b border-slate-100 bg-slate-50 px-4 py-3 dark:border-slate-700 dark:bg-slate-700/50">
          <h3 className="text-xs font-semibold uppercase tracking-wide text-muted-foreground dark:text-slate-400">
            Rincian Komponen
          </h3>
        </div>

        <div className="divide-y divide-slate-100 dark:divide-slate-700">
          {/* Header row */}
          <div className="grid grid-cols-4 gap-1 px-4 py-2">
            {["Komponen", "Seharusnya", "Di Slip", "Status"].map((h) => (
              <span key={h} className="text-[11px] font-semibold uppercase tracking-wide text-muted-foreground dark:text-slate-400">
                {h}
              </span>
            ))}
          </div>

          {/* PPh 21 row — hide in December (Pasal 17, not TER) */}
          {!result.isDecember && !result.pph21DataIncomplete && (
            <motion.div
              key="pph21-row"
              custom={0}
              initial="hidden"
              animate="visible"
              variants={tableRowVariants}
              className={cn(
                "grid grid-cols-4 items-center gap-1 px-4 py-3",
                result.pph21.isIllegal
                  ? "bg-red-50/60 dark:bg-red-950/20"
                  : !result.pph21.isCorrect
                  ? "bg-amber-50/40 dark:bg-amber-950/10"
                  : ""
              )}
            >
              <div className="min-w-0">
                <p className="truncate text-xs font-semibold text-slate-700 dark:text-slate-200">
                  {result.pph21.label}
                </p>
                {result.pph21.note && (
                  <p className="mt-0.5 text-[10px] leading-tight text-muted-foreground dark:text-slate-400 line-clamp-2">
                    {result.pph21.note}
                  </p>
                )}
              </div>
              <span className="font-mono text-xs text-slate-600 dark:text-slate-300">
                {formatIDR(result.pph21.expected)}
              </span>
              <span className={cn("font-mono text-xs font-semibold",
                !result.pph21.isCorrect ? "text-amber-600 dark:text-amber-400" : "text-slate-700 dark:text-slate-200"
              )}>
                {formatIDR(result.pph21.charged)}
              </span>
              <RowStatus correct={result.pph21.isCorrect} />
            </motion.div>
          )}

          {/* PPh 21 — December without annual_gross: show amber incomplete row */}
          {result.isDecember && result.pph21DataIncomplete && (
            <motion.div
              key="pph21-incomplete"
              custom={0}
              initial="hidden"
              animate="visible"
              variants={tableRowVariants}
              className="grid grid-cols-4 items-center gap-1 px-4 py-3 bg-amber-50/40 dark:bg-amber-950/10"
            >
              <div>
                <p className="text-xs font-semibold text-slate-700 dark:text-slate-200">PPh 21</p>
                <p className="text-[10px] text-amber-600 dark:text-amber-400">
                  Isi total penghasilan tahunan untuk hasil akurat
                </p>
              </div>
              <span className="font-mono text-xs text-slate-400">—</span>
              <span className="font-mono text-xs font-semibold text-slate-700 dark:text-slate-200">
                {formatIDR(result.pph21.charged)}
              </span>
              <span className="text-sm text-amber-500">⚠️</span>
            </motion.div>
          )}

          {/* PPh 21 — December WITH annual_gross: show Pasal 17 note instead of TER row */}
          {result.isDecember && !result.pph21DataIncomplete && (
            <div className="col-span-4 px-4 py-3 rounded-xl bg-purple-50 dark:bg-purple-950/40 mx-4 my-1">
              <p className="text-xs text-purple-700 dark:text-purple-300">
                🗓️ PPh 21 Desember menggunakan rekonsiliasi Pasal 17 — tidak diperiksa via TER.
                {result.pph21?.note && <span> {result.pph21.note}</span>}
              </p>
            </div>
          )}

          {/* BPJS rows — always shown, including December */}
          {bpjsRows.map((row, i) => (
            <motion.div
              key={row.label}
              custom={i + 1}
              initial="hidden"
              animate="visible"
              variants={tableRowVariants}
              className={cn(
                "grid grid-cols-4 items-center gap-1 px-4 py-3",
                row.isIllegal
                  ? "bg-red-50/60 dark:bg-red-950/20"
                  : !row.isCorrect
                  ? "bg-amber-50/40 dark:bg-amber-950/10"
                  : ""
              )}
            >
              <div className="min-w-0">
                <p className="truncate text-xs font-semibold text-slate-700 dark:text-slate-200">
                  {row.label}
                </p>
                {row.note && (
                  <p className="mt-0.5 text-[10px] leading-tight text-muted-foreground dark:text-slate-400 line-clamp-2">
                    {row.note}
                  </p>
                )}
              </div>
              <span className="font-mono text-xs text-slate-600 dark:text-slate-300">
                {row.isIllegal ? (
                  <span className="text-[10px] text-red-500">—</span>
                ) : (
                  formatIDR(row.expected)
                )}
              </span>
              <span
                className={cn(
                  "font-mono text-xs font-semibold",
                  row.isIllegal
                    ? "text-red-600 dark:text-red-400"
                    : !row.isCorrect
                    ? "text-amber-600 dark:text-amber-400"
                    : "text-slate-700 dark:text-slate-200"
                )}
              >
                {formatIDR(row.charged)}
              </span>
              <RowStatus correct={row.isCorrect} illegal={row.isIllegal} />
            </motion.div>
          ))}
        </div>
      </div>

      {/* Explanation card */}
      <motion.div
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.4 }}
        className="rounded-2xl border border-slate-200 bg-white px-5 py-4 dark:border-slate-700 dark:bg-slate-800"
      >
        <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-muted-foreground dark:text-slate-400">
          📋 Penjelasan
        </p>
        <p className="text-sm leading-relaxed text-slate-600 dark:text-slate-300">
          {result.explanation}
        </p>
        {result.legalBasis.length > 0 && (
          <div className="mt-3 flex flex-wrap gap-1.5">
            {result.legalBasis.map((ref) => (
              <span
                key={ref}
                className="rounded-full bg-slate-100 px-2 py-0.5 text-[11px] font-medium text-slate-500 dark:bg-slate-700 dark:text-slate-400"
              >
                {ref}
              </span>
            ))}
          </div>
        )}
      </motion.div>

      {/* TER info */}
      {!result.isDecember && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.5 }}
          className="flex items-center justify-between rounded-xl bg-blue-50 px-4 py-3 dark:bg-blue-950/30"
        >
          <div>
            <p className="text-xs text-blue-600 dark:text-blue-400">
              Status {result.terCategory !== "A" ? "B/C" : "A"} — TER Kategori{" "}
              <strong>{result.terCategory}</strong>
            </p>
            <p className="font-mono text-sm font-bold text-blue-700 dark:text-blue-300">
              {(result.terRate * 100).toFixed(2)}% dari{" "}
              {new Intl.NumberFormat("id-ID", {
                style: "currency",
                currency: "IDR",
                minimumFractionDigits: 0,
              }).format(result.gross)}
            </p>
          </div>
          <span className="rounded-full bg-blue-100 px-2 py-1 text-xs font-semibold text-blue-700 dark:bg-blue-900 dark:text-blue-300">
            PMK 168/2023
          </span>
        </motion.div>
      )}

      {/* Action buttons */}
      <motion.div
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.55 }}
        className="flex flex-col gap-2 sm:flex-row"
      >
        <button
          type="button"
          onClick={handleScreenshot}
          aria-label="Ambil screenshot hasil audit"
          className="flex flex-1 items-center justify-center gap-2 rounded-xl border border-slate-200 bg-white px-4 py-3 text-sm font-semibold text-slate-700 shadow-card transition-all hover:shadow-card-hover active:scale-95 dark:border-slate-600 dark:bg-slate-800 dark:text-slate-200"
        >
          📸 Screenshot Hasil
        </button>

        <button
          type="button"
          onClick={handleCopyShare}
          aria-label={copied ? "Teks hasil sudah disalin" : "Salin dan bagikan ke TikTok"}
          className="flex flex-1 items-center justify-center gap-2 rounded-xl border border-slate-200 bg-white px-4 py-3 text-sm font-semibold text-slate-700 shadow-card transition-all hover:shadow-card-hover active:scale-95 dark:border-slate-600 dark:bg-slate-800 dark:text-slate-200"
        >
          {copied ? (
            <>
              <Check className="h-4 w-4 text-emerald-600" /> Tersalin!
            </>
          ) : (
            <>
              <Copy className="h-4 w-4" /> Share ke TikTok
            </>
          )}
        </button>

        <button
          type="button"
          onClick={onReset}
          aria-label="Cek slip gaji lain"
          className="flex flex-1 items-center justify-center gap-2 rounded-xl bg-brand-primary px-4 py-3 text-sm font-semibold text-white shadow-md transition-all hover:bg-blue-700 active:scale-95"
        >
          <RefreshCw className="h-4 w-4" /> Cek Slip Lain
        </button>
      </motion.div>

      <AnimatePresence>
        {screenshotFailed && (
          <motion.p
            initial={{ opacity: 0, y: 4 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0 }}
            className="text-center text-xs text-amber-600 dark:text-amber-400"
          >
            Screenshot gagal — teks berhasil disalin ✅
          </motion.p>
        )}
      </AnimatePresence>

      {/* Dasar Hukum — collapsible regulation sources */}
      <details className="rounded-2xl border border-slate-200 bg-white px-4 py-3 dark:border-slate-700 dark:bg-slate-800">
        <summary className="cursor-pointer list-none text-sm font-semibold text-slate-700 dark:text-slate-200">
          📋 Dasar Hukum
        </summary>
        <div className="mt-3 grid gap-2 text-xs">
          {Object.values(REGULATION_SOURCES).map((source) => (
            <a
              key={source.name}
              href={source.url}
              target="_blank"
              rel="noopener noreferrer"
              className="flex flex-col gap-0.5 rounded-lg border border-slate-100 px-3 py-2.5 text-left text-slate-600 transition-colors hover:border-slate-300 hover:text-slate-900 dark:border-slate-700 dark:text-slate-300 dark:hover:border-slate-500 dark:hover:text-slate-100"
            >
              <span className="flex items-center gap-2 font-medium">
                {source.name}
                {source.verified ? (
                  <span className="rounded bg-emerald-100 px-1.5 py-0.5 text-[10px] font-semibold text-emerald-700 dark:bg-emerald-900/50 dark:text-emerald-300">
                    ✅
                  </span>
                ) : (
                  <span className="rounded bg-amber-100 px-1.5 py-0.5 text-[10px] font-semibold text-amber-700 dark:bg-amber-900/50 dark:text-amber-300">
                    ⚠️ Sedang diverifikasi
                  </span>
                )}
              </span>
              <span className="text-[11px] leading-tight opacity-90">{source.description}</span>
              <span className="text-[11px] opacity-70">Berlaku: {source.effective}</span>
            </a>
          ))}
        </div>
        {process.env.NEXT_PUBLIC_JP_CAP_2026_VERIFIED !== "true" && (
          <div className="mt-2 rounded-lg border border-amber-200 bg-amber-50 px-3 py-2 dark:border-amber-800 dark:bg-amber-950/30">
            <p className="text-[11px] font-semibold text-amber-700 dark:text-amber-300">
              ⚠️ Batas Upah JP 2026
            </p>
            <p className="text-[11px] text-amber-600 dark:text-amber-400">
              Rp {new Intl.NumberFormat("id-ID").format(BPJS_JP.wage_cap_2026)}{" "}
              — estimasi, belum dikonfirmasi dari Perpres resmi. Berlaku mulai 1
              Maret 2026. Cek:{" "}
              <a
                href="https://peraturan.bpk.go.id"
                target="_blank"
                rel="noopener noreferrer"
                className="underline"
              >
                peraturan.bpk.go.id
              </a>
            </p>
          </div>
        )}
        <p className="mt-3 border-t border-slate-100 pt-3 text-[11px] text-slate-500 dark:border-slate-700 dark:text-slate-400">
          Data regulasi versi {REGULATION_META.version}. Terakhir diperbarui{" "}
          {REGULATION_META.last_updated}.
        </p>
      </details>

      <p className="text-center text-xs text-muted-foreground dark:text-slate-400">
        Data tidak disimpan. Perhitungan berdasarkan{" "}
        <a
          href="https://djponline.pajak.go.id"
          target="_blank"
          rel="noopener noreferrer"
          className="text-brand-primary underline-offset-2 hover:underline dark:text-blue-400"
        >
          PMK 168/2023
        </a>{" "}
        &amp; regulasi BPJS terbaru. cekwajar.id
      </p>
    </div>
  )
}

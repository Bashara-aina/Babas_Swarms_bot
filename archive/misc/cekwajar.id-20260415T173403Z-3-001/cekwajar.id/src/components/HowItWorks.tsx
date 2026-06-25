// ══════════════════════════════════════════════════════════════════════════════
// cekwajar.id — HowItWorks Component
// 5-step visual flow for homepage
// ══════════════════════════════════════════════════════════════════════════════

import { Upload, FileText, BarChart3, Calculator, CheckCircle } from 'lucide-react'
import type { LucideIcon } from 'lucide-react'

interface HowItWorksStep {
  icon: LucideIcon
  title: string
  description: string
  color?: string
  iconColor?: string
}

interface HowItWorksProps {
  steps?: HowItWorksStep[]
}

const defaultSteps = [
  {
    icon: Upload,
    title: 'Upload slip gaji',
    description: 'Upload slip gaji kamu dalam format foto atau PDF',
    color: 'bg-amber-100 text-amber-700',
    iconColor: 'text-amber-600',
  },
  {
    icon: FileText,
    title: 'AI menganalisis',
    description: 'AI mendeteksi 7 jenis pelanggaran umum dalam 30 detik',
    color: 'bg-blue-100 text-blue-700',
    iconColor: 'text-blue-600',
  },
  {
    icon: BarChart3,
    title: 'Verdict ditampilkan',
    description: 'Lihat detail pelanggaran dengan jumlah kerugian kamu',
    color: 'bg-purple-100 text-purple-700',
    iconColor: 'text-purple-600',
  },
  {
    icon: Calculator,
    title: 'Hitung wajar',
    description: 'Dapatkan perbandingan dengan standar UMR dan benchmark',
    color: 'bg-emerald-100 text-emerald-700',
    iconColor: 'text-emerald-600',
  },
  {
    icon: CheckCircle,
    title: 'Langkah selanjutnya',
    description: 'Dapatkan panduan praktis untuk mengklaim hak kamu',
    color: 'bg-teal-100 text-teal-700',
    iconColor: 'text-teal-600',
  },
]

export function HowItWorks({ steps = defaultSteps }: HowItWorksProps) {
  return (
    <section className="px-4 py-12 lg:py-16 bg-white">
      <div className="mx-auto max-w-3xl">
        <h2 className="text-center text-xl font-bold text-foreground sm:text-2xl">
          Cara Kerja
        </h2>
        <p className="mt-2 text-center text-sm text-muted-foreground">
          Audit slip gaji dalam 4 langkah sederhana
        </p>

        {/* Desktop: horizontal timeline */}
        <div className="hidden md:block mt-10">
          <div className="relative flex items-start justify-between">
            {/* Connector line */}
            <div className="absolute top-5 left-0 right-0 h-0.5 bg-muted" />
            <div className="absolute top-5 left-0 right-0 flex justify-center px-8">
              <div className="h-0.5 bg-gradient-to-r from-amber-200 via-blue-200 via-purple-200 via-emerald-200 to-teal-200 w-full max-w-xl" />
            </div>

            {steps.map((step, index) => {
              const Icon = step.icon
              const color = step.color ?? 'bg-emerald-100 text-emerald-700'
              const iconColor = step.iconColor ?? 'text-emerald-600'
              return (
                <div key={`${step.title}-${index}`} className="relative z-10 flex flex-col items-center" style={{ width: `${100 / steps.length}%` }}>
                  {/* Icon circle */}
                  <div className={`flex h-10 w-10 items-center justify-center rounded-full ${color} shadow-sm`}>
                    <Icon className={`h-5 w-5 ${iconColor}`} />
                  </div>
                  {/* Step number */}
                  <span className="mt-2 text-xs font-semibold text-muted-foreground">
                    Langkah {index + 1}
                  </span>
                  {/* Title */}
                  <span className="mt-1 text-center text-sm font-semibold text-foreground leading-tight">
                    {step.title}
                  </span>
                  {/* Description */}
                  <span className="mt-1 text-center text-xs text-muted-foreground leading-tight px-2">
                    {step.description}
                  </span>
                </div>
              )
            })}
          </div>
        </div>

        {/* Mobile: vertical list */}
        <div className="mt-8 md:hidden space-y-4">
          {steps.map((step, index) => {
            const Icon = step.icon
            const color = step.color ?? 'bg-emerald-100 text-emerald-700'
            const iconColor = step.iconColor ?? 'text-emerald-600'
            return (
              <div key={`${step.title}-${index}`} className="flex gap-4">
                {/* Number column */}
                <div className="flex flex-col items-center">
                  <div className={`flex h-9 w-9 shrink-0 items-center justify-center rounded-full ${color}`}>
                    <Icon className={`h-4 w-4 ${iconColor}`} />
                  </div>
                  {index < steps.length - 1 && (
                    <div className="w-px flex-1 bg-muted my-1" />
                  )}
                </div>
                {/* Content */}
                <div className="pb-4">
                  <div className="text-xs font-semibold text-muted-foreground">
                    Langkah {index + 1}
                  </div>
                  <div className="text-sm font-semibold text-foreground mt-0.5">
                    {step.title}
                  </div>
                  <div className="text-xs text-muted-foreground mt-0.5">
                    {step.description}
                  </div>
                </div>
              </div>
            )
          })}
        </div>
      </div>
    </section>
  )
}

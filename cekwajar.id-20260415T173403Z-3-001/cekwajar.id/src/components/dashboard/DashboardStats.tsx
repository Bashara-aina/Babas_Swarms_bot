'use client'

// ══════════════════════════════════════════════════════════════════════════════
// cekwajar.id — Dashboard Stats
// Client component that fetches real audit/benchmark counts from Supabase
// Fixes hardcoded zero stats
// ══════════════════════════════════════════════════════════════════════════════

import { useState, useEffect } from 'react'
import { Card, CardContent } from '@/components/ui/card'
import { Zap, Calculator, TrendingUp, Clock } from 'lucide-react'
import { createClient } from '@/lib/supabase/client'
import { cn } from '@/lib/utils'

const DAILY_LIMIT = 3

interface Stats {
  todayAudits: number
  totalAudits: number
  weekBenchmarks: number
  weekSalarySubmissions: number
  loading: boolean
}

export function DashboardStats({ userId }: { userId: string }) {
  const [stats, setStats] = useState<Stats>({
    todayAudits: 0,
    totalAudits: 0,
    weekBenchmarks: 0,
    weekSalarySubmissions: 0,
    loading: true,
  })

  useEffect(() => {
    const fetchStats = async () => {
      const supabase = createClient()

      const today = new Date()
      today.setHours(0, 0, 0, 0)
      const weekAgo = new Date(Date.now() - 7 * 24 * 60 * 60 * 1000)

      // Run all queries concurrently
      const [todayResult, totalResult, benchmarksResult, submissionsResult] =
        await Promise.allSettled([
          // Audits today
          supabase
            .from('payslip_audits')
            .select('id', { count: 'exact', head: true })
            .eq('user_id', userId)
            .gte('created_at', today.toISOString()),

          // Total audits
          supabase
            .from('payslip_audits')
            .select('id', { count: 'exact', head: true })
            .eq('user_id', userId),

          // Benchmark queries this week (global — no user_id in salary_benchmarks)
          supabase
            .from('salary_benchmarks')
            .select('id', { count: 'exact', head: true })
            .gte('updated_at', weekAgo.toISOString()),

          // Salary submissions this week (anonymous crowdsource, no user tracking)
          supabase
            .from('salary_submissions')
            .select('id', { count: 'exact', head: true })
            .eq('is_validated', true)
            .gte('created_at', weekAgo.toISOString()),
        ])

      const todayCount =
        todayResult.status === 'fulfilled' ? todayResult.value.count ?? 0 : 0
      const totalCount =
        totalResult.status === 'fulfilled' ? totalResult.value.count ?? 0 : 0
      const benchmarkCount =
        benchmarksResult.status === 'fulfilled'
          ? benchmarksResult.value.count ?? 0
          : 0
      const submissionCount =
        submissionsResult.status === 'fulfilled'
          ? submissionsResult.value.count ?? 0
          : 0

      setStats({
        todayAudits: todayCount,
        totalAudits: totalCount,
        weekBenchmarks: benchmarkCount,
        weekSalarySubmissions: submissionCount,
        loading: false,
      })
    }

    if (userId) fetchStats()
  }, [userId])

  return (
    <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
      {/* Audit Hari Ini */}
      <Card className="bg-muted border-border dark:bg-muted dark:border-border">
        <CardContent className="p-4">
          <div className="flex items-center gap-2">
            <div className="rounded-lg bg-muted-foreground/10 p-2">
              <Zap className="h-4 w-4 text-muted-foreground" />
            </div>
            <div>
              <p className="text-xs text-muted-foreground">Audit Hari Ini</p>
              <p className="text-lg font-bold text-foreground">
                {stats.loading ? (
                  <span className="animate-pulse">—</span>
                ) : (
                  `${stats.todayAudits} / ${DAILY_LIMIT}`
                )}
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Total Audit */}
      <Card className="bg-emerald-50 dark:bg-emerald-950/50 border-emerald-200 dark:border-emerald-800">
        <CardContent className="p-4">
          <div className="flex items-center gap-2">
            <div className="rounded-lg bg-emerald-200 p-2 dark:bg-emerald-800">
              <Calculator className="h-4 w-4 text-emerald-700 dark:text-emerald-300" />
            </div>
            <div>
              <p className="text-xs text-emerald-600 dark:text-emerald-400">
                Total Audit
              </p>
              <p className="text-lg font-bold text-emerald-900 dark:text-emerald-100">
                {stats.loading ? (
                  <span className="animate-pulse">—</span>
                ) : (
                  stats.totalAudits.toLocaleString('id-ID')
                )}
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Gaji Ditemukan (benchmarks this week) */}
      <Card className="bg-blue-50 dark:bg-blue-950/50 border-blue-200 dark:border-blue-800">
        <CardContent className="p-4">
          <div className="flex items-center gap-2">
            <div className="rounded-lg bg-blue-200 p-2 dark:bg-blue-800">
              <TrendingUp className="h-4 w-4 text-blue-700 dark:text-blue-300" />
            </div>
            <div>
              <p className="text-xs text-blue-600 dark:text-blue-400">
                Gaji Ditemukan
              </p>
              <p className="text-lg font-bold text-blue-900 dark:text-blue-100">
                {stats.loading ? (
                  <span className="animate-pulse">—</span>
                ) : (
                  stats.weekBenchmarks.toLocaleString('id-ID')
                )}
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Minggu Ini (validated salary submissions this week) */}
      <Card className="bg-purple-50 dark:bg-purple-950/50 border-purple-200 dark:border-purple-800">
        <CardContent className="p-4">
          <div className="flex items-center gap-2">
            <div className="rounded-lg bg-purple-200 p-2 dark:bg-purple-800">
              <Clock className="h-4 w-4 text-purple-700 dark:text-purple-300" />
            </div>
            <div>
              <p className="text-xs text-purple-600 dark:text-purple-400">
                Minggu Ini
              </p>
              <p className="text-lg font-bold text-purple-900 dark:text-purple-100">
                {stats.loading ? (
                  <span className="animate-pulse">—</span>
                ) : (
                  stats.weekSalarySubmissions.toLocaleString('id-ID')
                )}
              </p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

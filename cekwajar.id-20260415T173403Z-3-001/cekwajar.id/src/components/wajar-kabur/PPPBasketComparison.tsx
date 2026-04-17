// ══════════════════════════════════════════════════════════════════════════════
// cekwajar.id — PPPBasketComparison
// Visual PPP basket comparison between Indonesia and target country
// ══════════════════════════════════════════════════════════════════════════════

'use client'

import { Card, CardContent } from '@/components/ui/card'
import { TrendingUp, TrendingDown, Globe } from 'lucide-react'

interface PPPBasketComparisonProps {
  countryName: string
  currencyCode: string
  exchangeRate: number
  idSalary: number
  nominalEquivalent: number
  userPowerIntlUSD: number
  offerSalary: number | null
  offerPowerIntlUSD: number | null
  realRatio: number | null
  isPPPBetter: boolean | null
  pppYear: number
  className?: string
}

function formatIDR(amount: number): string {
  return `Rp ${amount.toLocaleString('id-ID')}`
}

function formatCurrency(amount: number, code: string): string {
  return `${amount.toLocaleString('id-ID', { minimumFractionDigits: 0, maximumFractionDigits: 0 })} ${code}`
}

export function PPPBasketComparison({
  countryName,
  currencyCode,
  exchangeRate,
  idSalary,
  nominalEquivalent,
  userPowerIntlUSD,
  offerSalary,
  offerPowerIntlUSD,
  realRatio,
  isPPPBetter,
  pppYear,
  className,
}: PPPBasketComparisonProps) {
  const hasOffer = offerSalary !== null && offerPowerIntlUSD !== null

  return (
    <Card className={className}>
      <CardContent className="p-4">
        <div className="mb-4 text-center">
          <div className="mb-2 mx-auto w-10 h-10 rounded-full bg-blue-100 flex items-center justify-center">
            <Globe className="h-5 w-5 text-blue-600" />
          </div>
          <h3 className="text-sm font-semibold text-foreground">Bandingkan Paket Belanja</h3>
          <p className="text-xs text-muted-foreground mt-0.5">
            {countryName} · Kurs {formatIDR(exchangeRate)}/USD · PPP {pppYear}
          </p>
        </div>

        {/* PPP Dollar Indicator */}
        <div className="flex items-center justify-center gap-2 p-3 bg-muted rounded-lg mb-4">
          <span className="text-xs text-muted-foreground">Daya Beli Global</span>
          <span className="text-base font-bold text-foreground">
            ${userPowerIntlUSD.toLocaleString('id-ID', { minimumFractionDigits: 0, maximumFractionDigits: 0 })}
          </span>
          <span className="text-xs text-muted-foreground">/bulan</span>
        </div>

        {/* Two Column Comparison */}
        <div className="grid grid-cols-2 gap-3 mb-4">
          {/* Indonesia */}
          <div className="text-center p-3 bg-muted rounded-lg border border-border">
            <div className="text-xs text-muted-foreground mb-1">🇮🇩 Gaji di Indonesia</div>
            <div className="text-sm font-bold text-foreground">{formatIDR(idSalary)}</div>
            <div className="text-[10px] text-muted-foreground mt-0.5">
              = ${userPowerIntlUSD.toLocaleString('id-ID', { minimumFractionDigits: 0 })} PPP
            </div>
          </div>

          {/* Target Country */}
          <div className="text-center p-3 bg-blue-50 rounded-lg border border-blue-100">
            <div className="text-xs text-muted-foreground mb-1">Nominal Setara</div>
            <div className="text-sm font-bold text-blue-700">
              {formatCurrency(nominalEquivalent, currencyCode)}
            </div>
            <div className="text-[10px] text-blue-500 mt-0.5">
              = ${userPowerIntlUSD.toLocaleString('id-ID', { minimumFractionDigits: 0 })} PPP
            </div>
          </div>
        </div>

        {/* Offer Comparison */}
        {hasOffer && offerPowerIntlUSD !== null && realRatio !== null && isPPPBetter !== null && (
          <div
            className={`rounded-lg p-3 text-center ${
              isPPPBetter
                ? 'bg-emerald-50 border border-emerald-200'
                : 'bg-red-50 border border-red-200'
            }`}
          >
            <div className="flex items-center justify-center gap-2 mb-1">
              {isPPPBetter ? (
                <TrendingUp className="h-4 w-4 text-emerald-600" />
              ) : (
                <TrendingDown className="h-4 w-4 text-red-600" />
              )}
              <span className="text-xs font-medium text-muted-foreground">
                {isPPPBetter ? 'Penawaran lebih baik dari PPP' : 'Penawaran di bawah PPP'}
              </span>
            </div>
            <div className={`text-lg font-bold ${isPPPBetter ? 'text-emerald-700' : 'text-red-700'}`}>
              {realRatio.toFixed(2)}× daya beli
            </div>
            {offerSalary !== null && (
              <div className="text-xs text-muted-foreground mt-0.5">
                Tawaran: {formatCurrency(offerSalary, currencyCode)} = ${offerPowerIntlUSD.toLocaleString('id-ID')} PPP
              </div>
            )}
          </div>
        )}

        {!hasOffer && (
          <div className="text-center p-3 bg-muted rounded-lg text-xs text-muted-foreground">
            Masukkan tawaran gaji di atas untuk melihat perbandingan daya beli
          </div>
        )}

        {/* PPP basket info */}
        <div className="mt-3 text-center text-[10px] text-muted-foreground">
          Sumber PPP: World Bank {pppYear} · Purchasing Power Parity
        </div>
      </CardContent>
    </Card>
  )
}

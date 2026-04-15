// ==============================================================================
// cekwajar.id — PropertyPriceBar component
// Horizontal bar showing P25-P50-P75 range with user price marker
// ==============================================================================

interface PropertyPriceBarProps {
  userPricePerSqm: number
  p25: number
  p50: number
  p75: number
}

function formatIDR(amount: number): string {
  return `Rp ${amount.toLocaleString('id-ID')}`
}

export function PropertyPriceBar({
  userPricePerSqm,
  p25,
  p50,
  p75,
}: PropertyPriceBarProps) {
  const maxPrice = Math.max(p75 * 1.2, userPricePerSqm * 1.1)
  const minPrice = Math.min(p25 * 0.8, userPricePerSqm * 0.9)

  const range = maxPrice - minPrice

  const userPos = Math.min(100, Math.max(0, ((userPricePerSqm - minPrice) / range) * 100))
  const p25Pos = ((p25 - minPrice) / range) * 100
  const p50Pos = ((p50 - minPrice) / range) * 100
  const p75Pos = ((p75 - minPrice) / range) * 100

  return (
    <div className="w-full">
      {/* Labels */}
      <div className="flex justify-between text-xs text-slate-500 mb-1">
        <span>{formatIDR(Math.round(minPrice))}</span>
        <span className="font-medium text-slate-700">Median</span>
        <span>{formatIDR(Math.round(maxPrice))}</span>
      </div>

      {/* Bar */}
      <div className="h-8 bg-slate-100 rounded-full relative overflow-hidden">
        {/* P25 marker */}
        <div
          className="absolute top-0 bottom-0 w-0.5 bg-slate-400 z-10"
          style={{ left: `${p25Pos}%` }}
          title={`P25: ${formatIDR(p25)}`}
        />
        {/* P50 marker (median) */}
        <div
          className="absolute top-0 bottom-0 w-1 bg-emerald-500 z-20"
          style={{ left: `${p50Pos}%` }}
          title={`Median: ${formatIDR(p50)}`}
        />
        {/* P75 marker */}
        <div
          className="absolute top-0 bottom-0 w-0.5 bg-slate-400 z-10"
          style={{ left: `${p75Pos}%` }}
          title={`P75: ${formatIDR(p75)}`}
        />
        {/* User price marker */}
        <div
          className="absolute top-1 bottom-1 w-2 bg-blue-500 rounded-full z-30"
          style={{ left: `${userPos}%` }}
          title={`Harga kamu: ${formatIDR(userPricePerSqm)}`}
        />
      </div>

      {/* Legend */}
      <div className="flex items-center justify-center gap-4 mt-2 text-xs text-slate-500">
        <div className="flex items-center gap-1">
          <div className="w-2 h-2 rounded-full bg-emerald-500" />
          <span>Median (P50)</span>
        </div>
        <div className="flex items-center gap-1">
          <div className="w-2 h-2 rounded-full bg-blue-500" />
          <span>Harga kamu</span>
        </div>
      </div>
    </div>
  )
}
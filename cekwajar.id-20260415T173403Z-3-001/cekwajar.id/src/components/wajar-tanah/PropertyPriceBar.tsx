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
      <div className="flex justify-between text-xs text-muted-foreground mb-1">
        <span>{formatIDR(Math.round(minPrice))}</span>
        <span className="font-medium text-foreground">Median</span>
        <span>{formatIDR(Math.round(maxPrice))}</span>
      </div>

      {/* Bar */}
      <div className="h-8 bg-muted rounded-full relative overflow-hidden">
        {/* P25 marker */}
        <div
          className="absolute top-0 bottom-0 w-0.5 opacity-50 z-10"
          style={{ left: `${p25Pos}%`, backgroundColor: 'hsl(var(--muted-foreground))' }}
          title={`P25: ${formatIDR(p25)}`}
        />
        {/* P50 marker (median) */}
        <div
          className="absolute top-0 bottom-0 w-1 z-20"
          style={{ left: `${p50Pos}%`, backgroundColor: 'var(--tool-accent, hsl(var(--emerald-500)))' }}
          title={`Median: ${formatIDR(p50)}`}
        />
        {/* P75 marker */}
        <div
          className="absolute top-0 bottom-0 w-0.5 opacity-50 z-10"
          style={{ left: `${p75Pos}%`, backgroundColor: 'hsl(var(--muted-foreground))' }}
          title={`P75: ${formatIDR(p75)}`}
        />
        {/* User price marker */}
        <div
          className="absolute top-1 bottom-1 w-2 rounded-full z-30"
          style={{ left: `${userPos}%`, backgroundColor: 'hsl(var(--primary))' }}
          title={`Harga kamu: ${formatIDR(userPricePerSqm)}`}
        />
      </div>

      {/* Legend */}
      <div className="flex items-center justify-center gap-4 mt-2 text-xs text-muted-foreground">
        <div className="flex items-center gap-1">
          <div className="w-2 h-2 rounded-full" style={{ backgroundColor: 'var(--tool-accent, hsl(var(--emerald-500)))' }} />
          <span>Median (P50)</span>
        </div>
        <div className="flex items-center gap-1">
          <div className="w-2 h-2 rounded-full" style={{ backgroundColor: 'hsl(var(--primary))' }} />
          <span>Harga kamu</span>
        </div>
      </div>
    </div>
  )
}
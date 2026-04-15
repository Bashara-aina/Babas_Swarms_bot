// ==============================================================================
// cekwajar.id — Exchange rates via Frankfurter.app
// Free API (European Central Bank), no key required
// ==============================================================================

const rateCache = new Map<string, { rate: number; expiresAt: number }>()

export async function getExchangeRate(
  fromCurrency: string,
  toCurrency: string
): Promise<number | null> {
  if (fromCurrency === toCurrency) return 1

  const cacheKey = `${fromCurrency}_${toCurrency}`
  const cached = rateCache.get(cacheKey)

  if (cached && cached.expiresAt > Date.now()) {
    return cached.rate
  }

  try {
    const url = `https://api.frankfurter.app/latest?from=${fromCurrency}&to=${toCurrency}`
    const response = await fetch(url, { next: { revalidate: 3600 } })

    if (!response.ok) throw new Error(`Frankfurter API error: ${response.status}`)

    const data = await response.json()
    const rate = data.rates?.[toCurrency]

    if (!rate) return null

    rateCache.set(cacheKey, { rate, expiresAt: Date.now() + 86400000 })
    return rate
  } catch {
    return null
  }
}
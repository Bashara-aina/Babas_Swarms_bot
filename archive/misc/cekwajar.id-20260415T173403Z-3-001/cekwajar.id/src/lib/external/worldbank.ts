// ==============================================================================
// cekwajar.id — World Bank PPP integration
// Free API, no key required. Caches in Supabase for 30 days.
// ==============================================================================

import { getServiceClient } from '@/lib/supabase/server'

interface WorldBankPPPData {
  countryCode: string
  countryName: string
  pppFactor: number
  year: number
  fetchedAt: string
}

export async function getWorldBankPPP(countryCode: string): Promise<WorldBankPPPData | null> {
  const supabase = await getServiceClient()

  // Check cache first
  const { data: cached } = await supabase
    .from('ppp_reference')
    .select('country_name, ppp_factor, ppp_year, fetched_at')
    .eq('country_code', countryCode)
    .single()

  if (cached && cached.ppp_factor) {
    const cacheAge = Date.now() - new Date(cached.fetched_at).getTime()
    if (cacheAge < 30 * 24 * 60 * 60 * 1000) {
      return {
        countryCode,
        countryName: cached.country_name ?? '',
        pppFactor: Number(cached.ppp_factor),
        year: cached.ppp_year ?? 0,
        fetchedAt: cached.fetched_at,
      }
    }
  }

  // Fetch from World Bank API
  const url = `https://api.worldbank.org/v2/country/${countryCode}/indicator/PA.NUS.PPP?format=json&mrv=1`

  try {
    const response = await fetch(url, {
      next: { revalidate: 86400 },
    })

    if (!response.ok) throw new Error(`World Bank API error: ${response.status}`)

    const [meta, data] = await response.json()
    const latest = data?.find((d: { value: number | null }) => d.value !== null)

    if (!latest) return null

    const result: WorldBankPPPData = {
      countryCode,
      countryName: latest.country?.value ?? '',
      pppFactor: latest.value,
      year: parseInt(latest.date, 10),
      fetchedAt: new Date().toISOString(),
    }

    // Update cache
    const sb = await getServiceClient()
    await sb.from('ppp_reference').update({
        ppp_factor: result.pppFactor,
        ppp_year: result.year,
        fetched_at: result.fetchedAt,
      })
      .eq('country_code', countryCode)

    return result
  } catch (error) {
    console.error('World Bank API failed:', error)
    if (cached?.ppp_factor) {
      return {
        countryCode,
        countryName: cached.country_name ?? '',
        pppFactor: Number(cached.ppp_factor),
        year: cached.ppp_year ?? 0,
        fetchedAt: cached.fetched_at,
      }
    }
    return null
  }
}
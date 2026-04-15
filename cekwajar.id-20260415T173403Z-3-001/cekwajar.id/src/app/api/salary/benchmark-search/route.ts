// ==============================================================================
// cekwajar.id — GET /api/salary/benchmark-search
// Search job categories for autocomplete dropdown
// Query params: q (search term)
// ==============================================================================

import { NextRequest, NextResponse } from 'next/server'
import { z } from 'zod'
import { createClient } from '@/lib/supabase/server'

export const runtime = 'nodejs'
export const dynamic = 'force-dynamic'

// --- Zod Schema ---------------------------------------------------------------

const QuerySchema = z.object({
  q: z.string().min(1, 'Search term is required').max(100),
})

// --- Handler ------------------------------------------------------------------

export async function GET(request: NextRequest) {
  const searchParams = request.nextUrl.searchParams

  const parsed = QuerySchema.safeParse({
    q: searchParams.get('q'),
  })

  if (!parsed.success) {
    return NextResponse.json(
      { error: { code: 'INVALID_PARAMS', message: parsed.error.issues[0].message } },
      { status: 400 }
    )
  }

  const { q } = parsed.data
  const supabase = await createClient()

  // First try exact match
  const { data: exactMatch } = await supabase
    .from('job_categories')
    .select('id, title, industry')
    .ilike('title', `%${q}%`)
    .eq('is_active', true)
    .limit(5)

  // Then fuzzy match
  const { data: fuzzyMatches } = await supabase.rpc('search_job_categories_fuzzy', {
    search_term: q,
    threshold: 0.2,
  })

  // Combine and dedupe
  const seen = new Set<string>()
  const results: Array<{ id: string; title: string; industry: string | null; matchType: 'exact' | 'fuzzy' }> = []

  if (exactMatch) {
    for (const match of exactMatch) {
      if (!seen.has(match.id)) {
        seen.add(match.id)
        results.push({
          id: match.id,
          title: match.title,
          industry: match.industry,
          matchType: 'exact',
        })
      }
    }
  }

  if (fuzzyMatches) {
    for (const match of fuzzyMatches) {
      if (!seen.has(match.id)) {
        seen.add(match.id)
        results.push({
          id: match.id,
          title: match.title,
          industry: null,
          matchType: 'fuzzy',
        })
      }
    }
  }

  return NextResponse.json({
    success: true,
    data: {
      results: results.slice(0, 10),
      query: q,
    },
  })
}

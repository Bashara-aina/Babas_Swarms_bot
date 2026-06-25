'use client'

import { usePathname, useRouter } from 'next/navigation'
import { useAppTheme } from '@/components/providers'
import { GlobalNav as SourceGlobalNav } from '@/source-ui/nav'

const PATH_TO_PAGE: Record<string, string> = {
  '/': 'home',
  '/pricing': 'pricing',
  '/wajar-slip': 'wajar-slip',
  '/wajar-gaji': 'wajar-gaji',
  '/wajar-tanah': 'wajar-tanah',
  '/wajar-kabur': 'wajar-kabur',
  '/wajar-hidup': 'wajar-hidup',
}

const PAGE_TO_PATH: Record<string, string> = {
  home: '/',
  pricing: '/pricing',
  kontak: '/kontak',
  privacy: '/privacy-policy',
  terms: '/terms',
  'wajar-slip': '/wajar-slip',
  'wajar-gaji': '/wajar-gaji',
  'wajar-tanah': '/wajar-tanah',
  'wajar-kabur': '/wajar-kabur',
  'wajar-hidup': '/wajar-hidup',
}

export function GlobalNav() {
  const pathname = usePathname()
  const router = useRouter()
  const { resolvedTheme, toggleTheme } = useAppTheme()

  return (
    <SourceGlobalNav
      currentPage={PATH_TO_PAGE[pathname] ?? 'home'}
      onNavigate={(page: string) => router.push(PAGE_TO_PATH[page] ?? '/')}
      darkMode={resolvedTheme === 'dark'}
      onToggleDark={toggleTheme}
    />
  )
}

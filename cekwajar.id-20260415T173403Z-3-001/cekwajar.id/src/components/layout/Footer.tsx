'use client'

import { useRouter } from 'next/navigation'
import { SiteFooter } from '@/source-ui/nav'

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

export function Footer() {
  const router = useRouter()
  return <SiteFooter onNavigate={(page: string) => router.push(PAGE_TO_PATH[page] ?? '/')} />
}

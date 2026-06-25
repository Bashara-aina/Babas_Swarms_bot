'use client'

import { useRouter } from 'next/navigation'
import { PricingPage } from '@/source-ui/pages'

export default function Page() {
  const router = useRouter()
  const onNavigate = (page: string) => {
    const map: Record<string, string> = {
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
    router.push(map[page] ?? '/')
  }
  return <PricingPage onNavigate={onNavigate} />
}

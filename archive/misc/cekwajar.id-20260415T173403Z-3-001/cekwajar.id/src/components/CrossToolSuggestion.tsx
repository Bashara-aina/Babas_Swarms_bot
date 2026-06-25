import Link from 'next/link'
import { ArrowRight } from 'lucide-react'
import { cn } from '@/lib/utils'

interface CrossToolSuggestionProps {
  fromTool: 'wajar-slip' | 'wajar-gaji' | 'wajar-tanah' | 'wajar-kabur' | 'wajar-hidup'
  className?: string
}

const suggestions: Record<string, { href: string; text: string; subtext: string; color: string }[]> = {
  'wajar-slip': [
    {
      href: '/wajar-gaji',
      text: 'Cek apakah gajimu wajar di pasaran',
      subtext: 'Benchmark dengan ribuan data gaji posisi yang sama',
      color: 'border-blue-200 hover:border-blue-400 dark:border-blue-800',
    },
  ],
  'wajar-gaji': [
    {
      href: '/wajar-slip',
      text: 'Audit slip gaji kamu',
      subtext: 'Pastikan potongan PPh21 dan BPJS sudah benar',
      color: 'border-amber-200 hover:border-amber-400 dark:border-amber-800',
    },
    {
      href: '/wajar-kabur',
      text: 'Bandingkan dengan gaji di luar negeri',
      subtext: 'Berapa nilai riil gajimu jika kerja di SG, AU, atau US?',
      color: 'border-indigo-200 hover:border-indigo-400 dark:border-indigo-800',
    },
  ],
  'wajar-tanah': [
    {
      href: '/wajar-hidup',
      text: 'Cek biaya hidup di kota tersebut',
      subtext: 'Berapa habis per bulan jika pindah ke sana?',
      color: 'border-teal-200 hover:border-teal-400 dark:border-teal-800',
    },
  ],
  'wajar-kabur': [
    {
      href: '/wajar-hidup',
      text: 'Bandingkan biaya hidup kota asal vs tujuan',
      subtext: 'Lihat perbedaan pengeluaran bulanan secara detail',
      color: 'border-teal-200 hover:border-teal-400 dark:border-teal-800',
    },
  ],
  'wajar-hidup': [
    {
      href: '/wajar-kabur',
      text: 'Hitung daya beli gajimu di luar negeri',
      subtext: 'PPP-adjusted comparison untuk 30+ negara',
      color: 'border-indigo-200 hover:border-indigo-400 dark:border-indigo-800',
    },
  ],
}

export function CrossToolSuggestion({ fromTool, className }: CrossToolSuggestionProps) {
  const items = suggestions[fromTool] ?? []
  if (items.length === 0) return null

  return (
    <div className={cn('mt-8 space-y-3', className)}>
      <p className="text-sm font-medium text-muted-foreground">Juga cek:</p>
      {items.map(item => (
        <Link
          key={item.href}
          href={item.href}
          className={cn(
            'group flex items-center justify-between p-4 rounded-xl border-2 bg-background',
            'hover:shadow-sm transition-all duration-200',
            item.color
          )}
        >
          <div>
            <p className="font-semibold text-sm text-foreground group-hover:text-emerald-600 dark:group-hover:text-emerald-400 transition-colors">
              {item.text}
            </p>
            <p className="text-xs text-muted-foreground mt-0.5">{item.subtext}</p>
          </div>
          <ArrowRight className="w-4 h-4 text-muted-foreground group-hover:translate-x-1 transition-transform flex-shrink-0 ml-4" />
        </Link>
      ))}
    </div>
  )
}

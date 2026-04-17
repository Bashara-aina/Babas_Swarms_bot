'use client'

import { useEffect, useState } from 'react'

export function AuditCounter() {
  const [count, setCount] = useState<string>('...')

  useEffect(() => {
    fetch('/api/stats/audit-count')
      .then(res => res.json())
      .then(data => {
        if (data.count) {
          setCount(new Intl.NumberFormat('id-ID').format(data.count))
        }
      })
      .catch(() => setCount('ratusan'))
  }, [])

  return <strong className="text-foreground font-semibold">{count}</strong>
}

export const fmtMoney = (v) => (v || 0).toLocaleString('es-EC', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 })
export const fmtMoneyK = (v) => {
  const n = v || 0
  if (n >= 1e6) return `$${(n / 1e6).toFixed(2)}M`
  if (n >= 1e3) return `$${(n / 1e3).toFixed(0)}K`
  return `$${Math.round(n)}`
}
export const fmtNum = (v) => (v || 0).toLocaleString('es-EC')
export const fmtPct = (v, d = 0) => `${(v || 0).toFixed(d)}%`
export const humanize = (k) => k.replace(/_/g, ' ').replace(/^\w/, (c) => c.toUpperCase())

import { useCountUp } from '../useCountUp'

const fmtMoney = (v) => (v || 0).toLocaleString('es-EC', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 })
const fmtNum = (v) => (v || 0).toLocaleString('es-EC')

function Readout({ eyebrow, value, cls = '', money = false, frac = 1, idx = 0 }) {
  const n = useCountUp(typeof value === 'number' ? value : 0)
  const display = typeof value !== 'number' ? value : money ? fmtMoney(n) : fmtNum(n)
  const w = Math.max(5, Math.min(100, frac * 100))
  return (
    <div className={`readout ${cls} ${money ? 'money' : ''}`} style={{ animationDelay: `${idx * 70}ms` }}>
      <div className="ro-eyebrow"><span className="pip" />{eyebrow}</div>
      <div className="ro-value">{display}</div>
      <div className="ro-bar"><span style={{ width: `${w}%` }} /></div>
    </div>
  )
}

export default function Stats({ resumen }) {
  if (!resumen) {
    return (
      <div className="stats">
        {Array.from({ length: 6 }).map((_, i) => (
          <div className="readout" key={i} style={{ animationDelay: `${i * 70}ms` }}>
            <div className="ro-eyebrow"><span className="pip" />Inicializando</div>
            <div className="ro-value" style={{ color: 'var(--dim)' }}>···</div>
            <div className="ro-bar"><span style={{ width: '12%' }} /></div>
          </div>
        ))}
      </div>
    )
  }
  const n = resumen.por_nivel || {}
  const total = resumen.total || 0
  const f = (x) => (total ? (x || 0) / total : 0)
  return (
    <div className="stats">
      <Readout idx={0} eyebrow="Siniestros · total" value={total} frac={1} />
      <Readout idx={1} eyebrow="Alerta roja" value={n.ROJO || 0} cls="rojo" frac={f(n.ROJO)} />
      <Readout idx={2} eyebrow="Revisión doc." value={n.AMARILLO || 0} cls="amarillo" frac={f(n.AMARILLO)} />
      <Readout idx={3} eyebrow="Flujo normal" value={n.VERDE || 0} cls="verde" frac={f(n.VERDE)} />
      <Readout idx={4} eyebrow="Monto en revisión" value={resumen.monto_en_revision} money frac={1} />
      <Readout idx={5} eyebrow="Ahorro potencial" value={resumen.ahorro_estimado} money frac={1} />
    </div>
  )
}

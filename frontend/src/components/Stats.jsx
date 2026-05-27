function Card({ label, value, cls = '' }) {
  return (
    <div className={`card ${cls}`}>
      <div className="v">{value}</div>
      <div className="l">{label}</div>
    </div>
  )
}

export default function Stats({ resumen }) {
  if (!resumen) return <div className="stats"><div className="card"><div className="l">Cargando…</div></div></div>
  const n = resumen.por_nivel || {}
  const monto = (resumen.monto_en_revision || 0).toLocaleString('es-EC', {
    style: 'currency', currency: 'USD', maximumFractionDigits: 0,
  })
  return (
    <div className="stats">
      <Card label="Siniestros" value={resumen.total} />
      <Card label="🔴 Rojo" value={n.ROJO || 0} cls="rojo" />
      <Card label="🟡 Amarillo" value={n.AMARILLO || 0} cls="amarillo" />
      <Card label="🟢 Verde" value={n.VERDE || 0} cls="verde" />
      <Card label="Monto en revisión" value={monto} />
    </div>
  )
}
